"""
Historical Data Backfill DAG

Configurable one-time (or re-runnable) DAG to backfill NHL historical data.
Processes seasons in parallel chunks while respecting API rate limits.

Uses the new NHL API: https://api-web.nhle.com/v1/

Default season range: 2021-2022 through 2024-2025 (configurable via
dag_run.conf: ``start_season`` and ``end_season`` as YYYY integers).

Checkpoint logic: seasons whose game count already meets the expected
threshold in the database are skipped automatically.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Any

import pendulum
from airflow.decorators import dag, task
from airflow.providers.postgres.operators.postgres import PostgresOperator

logger = logging.getLogger(__name__)

TIMEZONE = pendulum.timezone("UTC")

DEFAULT_ARGS = {
    "owner": "kopitar-data-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
}

NEW_NHL_API_BASE = "https://api-web.nhle.com/v1"

# Default season range (start year of the season, e.g. 2021 = "20212022")
DEFAULT_START_SEASON = 2021
DEFAULT_END_SEASON = 2024

# Minimum games expected in a full NHL regular season (used for checkpoint check)
MIN_GAMES_PER_SEASON = 900  # ~1312 regular-season games; 900 is a safe threshold

# Chunk size for parallel extraction
CHUNK_SIZE = 2  # seasons per parallel task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _season_str(year: int) -> str:
    """Convert a start-year integer to an NHL season string (e.g. 2021 → '20212022')."""
    return f"{year}{year + 1}"


def _season_date_range(season: str) -> tuple[date, date]:
    """
    Return (start_date, end_date) for a regular season.

    NHL seasons run roughly October through June of the following year.
    """
    start_year = int(season[:4])
    end_year = int(season[4:])
    return date(start_year, 10, 1), date(end_year, 6, 30)


# ---------------------------------------------------------------------------
# DAG definition (TaskFlow API)
# ---------------------------------------------------------------------------


@dag(
    dag_id="kopitar_historical_backfill",
    default_args=DEFAULT_ARGS,
    description="Configurable backfill of NHL historical data (new API)",
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1, tzinfo=TIMEZONE),
    catchup=False,
    max_active_runs=1,
    tags=["nhl", "historical", "backfill", "etl"],
    params={
        "start_season": DEFAULT_START_SEASON,
        "end_season": DEFAULT_END_SEASON,
    },
)
def kopitar_historical_backfill():
    """
    # Historical NHL Data Backfill

    ## Configuration (pass via dag_run.conf)
    - ``start_season`` (int): First season start-year (default: 2021 → 20212022)
    - ``end_season``   (int): Last season start-year  (default: 2024 → 20242025)

    ## Process
    1. **resolve_seasons** — Determine which seasons to process and filter
       out seasons already present in the DB (checkpoint logic).
    2. **extract_season_chunk_<N>** — Parallel extraction of season chunks.
    3. **transform_chunk_<N>** — Transform raw API data per chunk.
    4. **load_chunk_<N>** — Upsert into staging/production tables.
    5. **calculate_historical_metrics** — Compute fatigue & advanced metrics.
    6. **optimize_database** — Index creation and ANALYZE (PostgresOperator).

    ## Manual Execution
    ```bash
    airflow dags trigger kopitar_historical_backfill \\
      -c '{"start_season": 2018, "end_season": 2024}'
    ```
    """

    # -----------------------------------------------------------------------
    # Step 1 — Resolve which seasons need processing
    # -----------------------------------------------------------------------

    @task(task_id="resolve_seasons")
    def resolve_seasons(**context) -> list[list[str]]:
        """
        Determine the target season range from dag_run.conf, check the DB for
        seasons already fully loaded, and return season strings chunked for
        parallel extraction.

        Returns a list of chunks, e.g. [["20212022", "20222023"], ["20232024", ...]].
        """
        from kopitar.etl.loaders.database_loader import DatabaseLoader

        conf = context.get("params", {})
        start_year: int = int(conf.get("start_season", DEFAULT_START_SEASON))
        end_year: int = int(conf.get("end_season", DEFAULT_END_SEASON))

        all_seasons = [_season_str(y) for y in range(start_year, end_year + 1)]
        logger.info(
            "Target seasons (%d): %s", len(all_seasons), all_seasons
        )

        # Checkpoint: skip seasons with sufficient games already in the DB
        loader = DatabaseLoader()
        seasons_to_process: list[str] = []
        for season in all_seasons:
            try:
                count: int = loader.get_game_count_for_season(season)
                if count >= MIN_GAMES_PER_SEASON:
                    logger.info(
                        "Season %s already has %d games in DB — skipping",
                        season,
                        count,
                    )
                else:
                    logger.info(
                        "Season %s has only %d games in DB — will process",
                        season,
                        count,
                    )
                    seasons_to_process.append(season)
            except Exception as exc:
                logger.warning(
                    "Could not check DB for season %s (%s) — including it",
                    season,
                    exc,
                )
                seasons_to_process.append(season)

        logger.info(
            "%d season(s) to process after checkpoint: %s",
            len(seasons_to_process),
            seasons_to_process,
        )

        # Chunk for parallel processing
        chunks = [
            seasons_to_process[i: i + CHUNK_SIZE]
            for i in range(0, len(seasons_to_process), CHUNK_SIZE)
        ]
        return chunks

    # -----------------------------------------------------------------------
    # Step 2 — Extract (one task per chunk, dynamic task mapping)
    # -----------------------------------------------------------------------

    @task(task_id="extract_season_chunk")
    def extract_season_chunk(chunk: list[str]) -> dict[str, Any]:
        """
        Extract schedule and boxscores for a list of seasons.

        Returns a dict keyed by season string with sub-keys:
          ``status``, ``games`` (list of raw boxscore dicts), ``error`` (if any).

        Errors within a single season are caught and logged so other seasons
        in the chunk still proceed.
        """
        import asyncio
        import aiohttp

        async def _fetch_season(session: aiohttp.ClientSession, season: str) -> dict:
            start_date, end_date = _season_date_range(season)
            # Fetch schedule day-by-day in a single call using the club-schedule endpoint
            # New API: /v1/schedule/{date} returns a week view; we loop monthly.
            raw_games: list[dict] = []
            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                url = f"{NEW_NHL_API_BASE}/schedule/{date_str}"
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 404:
                            # No games that day
                            current += timedelta(days=7)
                            continue
                        resp.raise_for_status()
                        data = await resp.json()
                except Exception as exc:
                    logger.warning(
                        "Failed to fetch schedule %s for season %s: %s",
                        date_str, season, exc
                    )
                    current += timedelta(days=7)
                    continue

                for week_day in data.get("gameWeek", []):
                    for game in week_day.get("games", []):
                        # Regular-season games only (gameType == 2)
                        if (
                            game.get("gameType") == 2
                            and game.get("season") == season
                            and game.get("gameState") == "OFF"
                        ):
                            raw_games.append(game)

                # Advance by 7 days (schedule endpoint returns a week view)
                current += timedelta(days=7)

            # Deduplicate by game id
            seen: set[int] = set()
            unique_games: list[dict] = []
            for g in raw_games:
                gid = g.get("id")
                if gid and gid not in seen:
                    seen.add(gid)
                    unique_games.append(g)

            logger.info(
                "Season %s: found %d unique completed regular-season games",
                season, len(unique_games)
            )

            # Fetch boxscores for each game
            async def _boxscore(game_id: int) -> dict | None:
                url = f"{NEW_NHL_API_BASE}/gamecenter/{game_id}/boxscore"
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=30)
                    ) as r:
                        r.raise_for_status()
                        return await r.json()
                except Exception as exc:
                    logger.warning(
                        "Boxscore fetch failed for game %s: %s", game_id, exc
                    )
                    return None

            boxscores_raw = await asyncio.gather(
                *[_boxscore(g["id"]) for g in unique_games]
            )
            boxscores = [b for b in boxscores_raw if b is not None]
            return {"status": "success", "games": boxscores}

        async def _run_chunk() -> dict[str, Any]:
            results: dict[str, Any] = {}
            connector = aiohttp.TCPConnector(limit=10)
            async with aiohttp.ClientSession(
                headers={"User-Agent": "Kopitar-NHL-Analytics/1.0"},
                connector=connector,
            ) as session:
                for season in chunk:
                    try:
                        results[season] = await _fetch_season(session, season)
                    except Exception as exc:
                        logger.error(
                            "Season %s extraction failed: %s", season, exc
                        )
                        results[season] = {"status": "error", "error": str(exc), "games": []}
            return results

        return asyncio.run(_run_chunk())

    # -----------------------------------------------------------------------
    # Step 3 — Transform
    # -----------------------------------------------------------------------

    @task(task_id="transform_chunk")
    def transform_chunk(chunk_results: dict[str, Any]) -> dict[str, Any]:
        """
        Transform raw boxscore dicts from one chunk into normalized records.

        Returns a dict with keys: ``games``, ``goalie_stats``.
        Errors for individual games are logged and skipped.
        """
        from kopitar.etl.transformers.game_transformer import GameTransformer

        transformer = GameTransformer()
        games: list[dict] = []
        goalie_stats: list[dict] = []

        for season, season_data in chunk_results.items():
            if season_data.get("status") != "success":
                logger.warning(
                    "Skipping season %s (status: %s, error: %s)",
                    season,
                    season_data.get("status"),
                    season_data.get("error"),
                )
                continue

            for raw in season_data.get("games", []):
                game_id: int = raw.get("id", 0)
                try:
                    game_record = transformer.transform_game(raw)
                    game_record["season"] = season  # Ensure season tag
                    games.append(game_record)
                except Exception as exc:
                    logger.error(
                        "transform_game failed for game %s in season %s: %s",
                        game_id, season, exc
                    )
                    continue

                try:
                    gs_records = transformer.transform_goalie_stats(raw, game_id)
                    goalie_stats.extend(gs_records)
                except Exception as exc:
                    logger.error(
                        "transform_goalie_stats failed for game %s in season %s: %s",
                        game_id, season, exc
                    )

        logger.info(
            "Chunk transform complete: %d games, %d goalie stat records",
            len(games), len(goalie_stats)
        )
        return {"games": games, "goalie_stats": goalie_stats}

    # -----------------------------------------------------------------------
    # Step 4 — Load
    # -----------------------------------------------------------------------

    @task(task_id="load_chunk")
    def load_chunk(transformed: dict[str, Any]) -> str:
        """
        Upsert transformed records into the database.

        Returns a summary string.
        """
        from kopitar.etl.loaders.database_loader import DatabaseLoader

        loader = DatabaseLoader()
        try:
            games_loaded = loader.load_games(transformed["games"])
            stats_loaded = loader.load_goalie_stats(transformed["goalie_stats"])
        except Exception as exc:
            loader.rollback()
            raise RuntimeError(f"Historical load failed: {exc}") from exc

        return f"Loaded {games_loaded} games, {stats_loaded} goalie stat records"

    # -----------------------------------------------------------------------
    # Step 5 — Calculate historical fatigue metrics
    # -----------------------------------------------------------------------

    @task(task_id="calculate_historical_metrics")
    def calculate_historical_metrics(load_summaries: list[str]) -> str:
        """
        Compute fatigue metrics for all historical goalie records now in the DB.

        Triggered once all chunks have been loaded.
        """
        from kopitar.etl.transformers.fatigue_transformer import FatigueTransformer
        from kopitar.etl.loaders.database_loader import DatabaseLoader

        transformer = FatigueTransformer()
        loader = DatabaseLoader()

        # Retrieve goalie game records that lack fatigue entries
        pending: list[dict] = loader.get_goalie_games_without_fatigue()
        logger.info("%d goalie-game records need fatigue calculation", len(pending))

        updated = 0
        errors = 0
        for record in pending:
            try:
                game_history = loader.get_player_game_history(
                    player_id=record["player_id"], lookback_days=30
                )
                travel_history = loader.get_team_travel_history(
                    team_id=record["team_id"], lookback_days=14
                )
                fatigue_rec = transformer.build_fatigue_record(
                    player_id=record["player_id"],
                    game_id=record["game_id"],
                    game_date=record["game_date"],
                    game_history=game_history,
                    travel_history=travel_history,
                )
                loader.upsert_fatigue_metrics(fatigue_rec)
                updated += 1
            except Exception as exc:
                logger.error(
                    "Fatigue calc failed for player %s game %s: %s",
                    record.get("player_id"), record.get("game_id"), exc
                )
                errors += 1

        return f"Historical fatigue: {updated} updated, {errors} errors"

    # -----------------------------------------------------------------------
    # Wire up task graph
    # -----------------------------------------------------------------------

    chunks: list[list[str]] = resolve_seasons()

    # Dynamic map: one extract/transform/load pipeline per chunk
    extracted = extract_season_chunk.expand(chunk=chunks)
    transformed = transform_chunk.expand(chunk_results=extracted)
    load_results = load_chunk.expand(transformed=transformed)

    # Post-load metrics (waits for all chunks via the list input)
    metrics_result = calculate_historical_metrics(load_results)

    # Database optimization (classic operator)
    optimize_db = PostgresOperator(
        task_id="optimize_database",
        postgres_conn_id="kopitar_postgres",
        sql="""
        -- Indexes for common query patterns
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_date
            ON games(game_date);
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_season
            ON games(season);
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_goalie_stats_player_game
            ON goalie_game_stats(player_id, game_id);
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fatigue_player_date
            ON player_fatigue_metrics(player_id, calculation_date);

        -- Refresh statistics
        ANALYZE games;
        ANALYZE goalie_game_stats;
        ANALYZE player_fatigue_metrics;

        -- Materialized views
        REFRESH MATERIALIZED VIEW CONCURRENTLY player_season_stats;
        REFRESH MATERIALIZED VIEW CONCURRENTLY team_season_stats;
        """,
    )

    metrics_result >> optimize_db


kopitar_historical_backfill()
