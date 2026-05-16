"""
Daily Data Pipeline DAG

Runs daily at 4 AM UTC to process the previous day's NHL games.
Includes data extraction, transformation, fatigue metric computation,
validation, loading, and model prediction refresh.

Uses the new NHL API: https://api-web.nhle.com/v1/
"""

import logging
from datetime import datetime, timedelta, date

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
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

NEW_NHL_API_BASE = "https://api-web.nhle.com/v1"


# ---------------------------------------------------------------------------
# DAG definition (TaskFlow API)
# ---------------------------------------------------------------------------


@dag(
    dag_id="kopitar_daily_pipeline",
    default_args=DEFAULT_ARGS,
    description="Daily NHL data extraction, transformation, fatigue computation, and loading",
    schedule="0 4 * * *",  # 4 AM UTC daily
    start_date=datetime(2024, 1, 1, tzinfo=TIMEZONE),
    catchup=False,
    max_active_runs=1,
    tags=["nhl", "daily", "etl"],
)
def kopitar_daily_pipeline():
    """
    # Daily NHL Data Pipeline

    Processes the previous day's NHL games.

    ## Pipeline Steps

    1. **extract_games** — Fetch schedule + boxscores from new NHL API
    2. **transform_games** — Normalise raw API responses
    3. **validate_data** — Quality checks on transformed data
    4. **load_to_database** — Upsert into production tables
    5. **compute_fatigue_metrics** — FatigueCalculator for every goalie who played
    6. **update_model_predictions** — Refresh predictions for goalies with games in next 3 days
    7. **update_cache** — Warm Redis cache
    8. **data_quality_check** — Post-load SQL assertions (PostgresOperator)
    9. **trigger_model_retraining** — Weekly retraining trigger (Sundays)

    ## Manual trigger with custom date
    ```bash
    airflow dags trigger kopitar_daily_pipeline -c '{"target_date": "2024-01-15"}'
    ```
    """

    # -----------------------------------------------------------------------
    # Step 1 — Extract
    # -----------------------------------------------------------------------

    @task(task_id="extract_games")
    def extract_games(**context) -> list[dict]:
        """
        Fetch yesterday's schedule and boxscores from api-web.nhle.com/v1/.

        Returns a list of raw boxscore dicts (one per completed game).
        Partial failures (single team/game missing) are logged and skipped;
        the DAG is NOT failed as a whole.
        """
        import asyncio
        import aiohttp

        execution_date = context["execution_date"]
        # Support manual override via dag_run.conf
        conf = context.get("dag_run", None)
        conf_dict = getattr(conf, "conf", {}) or {}
        if conf_dict.get("target_date"):
            target_date_str: str = conf_dict["target_date"]
        else:
            target_date: date = execution_date.date() - timedelta(days=1)
            target_date_str = target_date.strftime("%Y-%m-%d")

        async def _fetch_all() -> list[dict]:
            boxscores: list[dict] = []

            async with aiohttp.ClientSession(
                headers={"User-Agent": "Kopitar-NHL-Analytics/1.0"}
            ) as session:
                # 1. Fetch schedule for the target date
                schedule_url = f"{NEW_NHL_API_BASE}/schedule/{target_date_str}"
                try:
                    async with session.get(schedule_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        resp.raise_for_status()
                        schedule_data: dict = await resp.json()
                except Exception as exc:
                    logger.error("Failed to fetch schedule for %s: %s", target_date_str, exc)
                    return []

                # Collect game IDs for completed (gameState == "OFF") games
                game_ids: list[int] = []
                for day in schedule_data.get("gameWeek", []):
                    if day.get("date") != target_date_str:
                        continue
                    for game in day.get("games", []):
                        if game.get("gameState") == "OFF":
                            game_ids.append(game["id"])

                logger.info(
                    "Found %d completed games on %s", len(game_ids), target_date_str
                )

                # 2. Fetch boxscore for each game (best-effort per game)
                async def _fetch_boxscore(game_id: int) -> dict | None:
                    url = f"{NEW_NHL_API_BASE}/gamecenter/{game_id}/boxscore"
                    try:
                        async with session.get(
                            url, timeout=aiohttp.ClientTimeout(total=30)
                        ) as r:
                            r.raise_for_status()
                            return await r.json()
                    except Exception as exc:
                        logger.warning(
                            "Could not fetch boxscore for game %s: %s", game_id, exc
                        )
                        return None

                results = await asyncio.gather(
                    *[_fetch_boxscore(gid) for gid in game_ids]
                )
                boxscores = [r for r in results if r is not None]

            return boxscores

        return asyncio.run(_fetch_all())

    # -----------------------------------------------------------------------
    # Step 2 — Transform
    # -----------------------------------------------------------------------

    @task(task_id="transform_games")
    def transform_games(raw_boxscores: list[dict]) -> dict:
        """
        Normalise raw boxscore dicts using GameTransformer.

        Returns a dict with keys: ``games``, ``goalie_stats``.
        """
        from kopitar.etl.transformers.game_transformer import GameTransformer

        transformer = GameTransformer()
        games: list[dict] = []
        goalie_stats: list[dict] = []

        for raw in raw_boxscores:
            game_id: int = raw.get("id", 0)

            try:
                game_record = transformer.transform_game(raw)
                games.append(game_record)
            except Exception as exc:
                logger.error("transform_game failed for game %s: %s", game_id, exc)
                continue

            try:
                goalie_records = transformer.transform_goalie_stats(raw, game_id)
                goalie_stats.extend(goalie_records)
            except Exception as exc:
                logger.error(
                    "transform_goalie_stats failed for game %s: %s", game_id, exc
                )

        logger.info(
            "Transformed %d games, %d goalie stat records",
            len(games),
            len(goalie_stats),
        )
        return {"games": games, "goalie_stats": goalie_stats}

    # -----------------------------------------------------------------------
    # Step 3 — Validate
    # -----------------------------------------------------------------------

    @task(task_id="validate_data")
    def validate_data(transformed: dict) -> dict:
        """
        Run lightweight quality checks on transformed data before loading.

        Raises ValueError if critical checks fail so Airflow marks the task
        as failed and triggers retries.
        """
        games: list[dict] = transformed.get("games", [])
        goalie_stats: list[dict] = transformed.get("goalie_stats", [])

        errors: list[str] = []

        for game in games:
            gid = game.get("nhl_id")
            if game.get("game_type") not in (1, 2, 3):
                errors.append(f"Game {gid}: unexpected game_type {game.get('game_type')}")
            if game.get("away_score") is not None and game["away_score"] < 0:
                errors.append(f"Game {gid}: negative away_score")
            if game.get("home_score") is not None and game["home_score"] < 0:
                errors.append(f"Game {gid}: negative home_score")

        for gs in goalie_stats:
            pid = gs.get("player_id")
            if gs.get("shots_against", 0) < gs.get("saves", 0):
                errors.append(
                    f"Goalie {pid}: saves ({gs['saves']}) > shots_against ({gs['shots_against']})"
                )
            if not (0.0 <= (gs.get("save_pct") or 0.0) <= 1.0):
                errors.append(f"Goalie {pid}: save_pct out of range: {gs.get('save_pct')}")

        if errors:
            raise ValueError(f"Data validation failed with {len(errors)} error(s): {errors}")

        logger.info(
            "Validation passed: %d games, %d goalie stat records",
            len(games),
            len(goalie_stats),
        )
        return transformed

    # -----------------------------------------------------------------------
    # Step 4 — Load
    # -----------------------------------------------------------------------

    @task(task_id="load_to_database")
    def load_to_database(validated: dict) -> dict:
        """
        Upsert validated game and goalie-stat records into the database.

        Returns the same ``validated`` dict so downstream tasks can use it.
        """
        from kopitar.etl.loaders.database_loader import DatabaseLoader

        loader = DatabaseLoader()
        try:
            games_loaded = loader.load_games(validated["games"])
            stats_loaded = loader.load_goalie_stats(validated["goalie_stats"])
            loader.refresh_materialized_views()
            logger.info(
                "Loaded %d games, %d goalie stat records", games_loaded, stats_loaded
            )
        except Exception as exc:
            loader.rollback()
            raise RuntimeError(f"Database loading failed: {exc}") from exc

        return validated

    # -----------------------------------------------------------------------
    # Step 5 — Compute fatigue metrics
    # -----------------------------------------------------------------------

    @task(task_id="compute_fatigue_metrics")
    def compute_fatigue_metrics(loaded: dict) -> list[int]:
        """
        Run FatigueCalculator for each goalie who appeared in yesterday's games.

        Errors for a single goalie are caught and logged; other goalies still
        get processed.  Returns a list of player_ids that were updated.
        """
        from kopitar.etl.transformers.fatigue_transformer import FatigueTransformer
        from kopitar.etl.loaders.database_loader import DatabaseLoader

        transformer = FatigueTransformer()
        loader = DatabaseLoader()

        goalie_stats: list[dict] = loaded.get("goalie_stats", [])
        games: list[dict] = loaded.get("games", [])

        # Build a quick lookup: game_id → game_date
        game_dates: dict[int, str] = {
            g["nhl_id"]: g["game_date"] for g in games if g.get("nhl_id")
        }

        updated_players: list[int] = []

        for gs in goalie_stats:
            player_id: int = gs.get("player_id")
            game_id: int = gs.get("game_id")
            game_date: str | None = game_dates.get(game_id)

            if not player_id or not game_id or not game_date:
                logger.warning(
                    "Skipping fatigue calc — missing fields: player_id=%s game_id=%s",
                    player_id,
                    game_id,
                )
                continue

            try:
                game_history = loader.get_player_game_history(
                    player_id=player_id, lookback_days=30
                )
                travel_history = loader.get_team_travel_history(
                    team_id=gs.get("team_id"), lookback_days=14
                )

                fatigue_record = transformer.build_fatigue_record(
                    player_id=player_id,
                    game_id=game_id,
                    game_date=game_date,
                    game_history=game_history,
                    travel_history=travel_history,
                )
                loader.upsert_fatigue_metrics(fatigue_record)
                updated_players.append(player_id)

            except Exception as exc:
                logger.error(
                    "Fatigue computation failed for player %s, game %s: %s",
                    player_id,
                    game_id,
                    exc,
                )

        logger.info("Fatigue metrics updated for %d goalie(s)", len(updated_players))
        return updated_players

    # -----------------------------------------------------------------------
    # Step 6 — Update model predictions
    # -----------------------------------------------------------------------

    @task(task_id="update_model_predictions")
    def update_model_predictions(**context) -> str:
        """
        Trigger prediction refresh for goalies with upcoming games in the
        next 3 days.

        Uses the new API schedule endpoint to identify those goalies.
        """
        import asyncio
        import aiohttp
        from kopitar.ml.model_manager import ModelManager

        execution_date = context["execution_date"]
        today: date = execution_date.date()
        horizon_end: date = today + timedelta(days=3)

        async def _upcoming_game_ids() -> list[int]:
            game_ids: list[int] = []
            async with aiohttp.ClientSession(
                headers={"User-Agent": "Kopitar-NHL-Analytics/1.0"}
            ) as session:
                for delta in range(1, 4):
                    check_date = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                    url = f"{NEW_NHL_API_BASE}/schedule/{check_date}"
                    try:
                        async with session.get(
                            url, timeout=aiohttp.ClientTimeout(total=20)
                        ) as resp:
                            resp.raise_for_status()
                            data = await resp.json()
                            for day in data.get("gameWeek", []):
                                if day.get("date") == check_date:
                                    game_ids.extend(
                                        g["id"] for g in day.get("games", [])
                                    )
                    except Exception as exc:
                        logger.warning(
                            "Could not fetch schedule for %s: %s", check_date, exc
                        )
            return game_ids

        upcoming_ids = asyncio.run(_upcoming_game_ids())
        if not upcoming_ids:
            return "No upcoming games in next 3 days; skipping prediction refresh"

        model_manager = ModelManager()
        result = model_manager.refresh_predictions_for_games(upcoming_ids)
        return f"Predictions refreshed for {len(upcoming_ids)} upcoming games: {result}"

    # -----------------------------------------------------------------------
    # Step 7 — Update cache
    # -----------------------------------------------------------------------

    @task(task_id="update_cache")
    def update_cache(loaded: dict) -> str:
        """Warm Redis cache with latest game and goalie-stat data."""
        from kopitar.etl.loaders.cache_loader import CacheLoader

        cache_loader = CacheLoader()
        cache_loader.update_latest_games(loaded["games"])
        cache_loader.update_goalie_stats_cache(loaded["goalie_stats"])
        return f"Cache updated: {len(loaded['games'])} games, {len(loaded['goalie_stats'])} goalie records"

    # -----------------------------------------------------------------------
    # Step 9 — Weekly model retraining
    # -----------------------------------------------------------------------

    @task(task_id="trigger_model_retraining")
    def trigger_model_retraining(**context) -> str:
        """Trigger ML model retraining on Sundays only."""
        from kopitar.ml.model_manager import ModelManager

        execution_date = context["execution_date"]
        if execution_date.weekday() != 6:  # 6 == Sunday
            return "No model retraining needed today"

        model_manager = ModelManager()
        result = model_manager.trigger_retraining(
            model_types=["fatigue_predictor", "performance_predictor"],
            background=True,
        )
        return f"Model retraining triggered: {result}"

    # -----------------------------------------------------------------------
    # Wire up task dependencies
    # -----------------------------------------------------------------------

    raw = extract_games()
    transformed = transform_games(raw)
    validated = validate_data(transformed)
    loaded = load_to_database(validated)

    # Fan-out after load
    fatigue_ids = compute_fatigue_metrics(loaded)
    predictions = update_model_predictions()
    cache_result = update_cache(loaded)

    # Post-load SQL quality check (classic Operator; must reference the DAG)
    data_quality_check = PostgresOperator(
        task_id="data_quality_check",
        postgres_conn_id="kopitar_postgres",
        sql="""
        SELECT
            'games' AS table_name,
            COUNT(*) AS record_count,
            COUNT(CASE WHEN home_score < 0 OR away_score < 0 THEN 1 END) AS invalid_scores
        FROM games
        WHERE game_date::date = '{{ macros.ds_add(ds, -1) }}'
        UNION ALL
        SELECT
            'goalie_game_stats' AS table_name,
            COUNT(*) AS record_count,
            COUNT(CASE WHEN save_pct < 0 OR save_pct > 1 THEN 1 END) AS invalid_stats
        FROM goalie_game_stats gs
        JOIN games g ON gs.game_id = g.nhl_id
        WHERE g.game_date::date = '{{ macros.ds_add(ds, -1) }}';
        """,
    )

    retraining_result = trigger_model_retraining()

    # Dependency edges for tasks not connected via XCom data flow
    loaded >> data_quality_check
    [fatigue_ids, predictions, cache_result, data_quality_check] >> retraining_result


kopitar_daily_pipeline()
