"""Initial schema - all tables

Revision ID: 001
Revises: None
Create Date: 2026-05-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # conferences                                                          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "conferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_conferences_nhl_id", "conferences", ["nhl_id"], unique=True)

    # ------------------------------------------------------------------ #
    # divisions                                                            #
    # ------------------------------------------------------------------ #
    op.create_table(
        "divisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_short", sa.String(50), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=False),
        sa.Column("conference_id", sa.Integer(), sa.ForeignKey("conferences.id"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_divisions_nhl_id", "divisions", ["nhl_id"], unique=True)

    # ------------------------------------------------------------------ #
    # venues                                                               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state_province", sa.String(50), nullable=True),
        sa.Column("country", sa.String(50), nullable=False, server_default="Canada"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timezone_id", sa.String(50), nullable=False),
        sa.Column("timezone_offset", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("opened", sa.Integer(), nullable=True),
        sa.Column("surface", sa.String(50), nullable=True, server_default="Ice"),
        sa.Column("address", sa.Text(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venues_nhl_id", "venues", ["nhl_id"])

    # ------------------------------------------------------------------ #
    # teams                                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location_name", sa.String(100), nullable=False),
        sa.Column("team_name", sa.String(100), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=False),
        sa.Column("tricode", sa.String(3), nullable=False),
        sa.Column("division_id", sa.Integer(), sa.ForeignKey("divisions.id"), nullable=False),
        sa.Column("conference_id", sa.Integer(), sa.ForeignKey("conferences.id"), nullable=False),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("franchise_id", sa.Integer(), nullable=True),
        sa.Column("first_year_of_play", sa.String(8), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True),
        sa.Column("secondary_color", sa.String(7), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("official_site_url", sa.String(500), nullable=True),
        sa.Column("twitter_hashtag", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_teams_nhl_id", "teams", ["nhl_id"], unique=True)
    op.create_index("ix_teams_tricode", "teams", ["tricode"])

    # ------------------------------------------------------------------ #
    # players                                                              #
    # ------------------------------------------------------------------ #
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_city", sa.String(100), nullable=True),
        sa.Column("birth_state_province", sa.String(50), nullable=True),
        sa.Column("birth_country", sa.String(50), nullable=True),
        sa.Column("nationality", sa.String(50), nullable=True),
        sa.Column("height", sa.String(10), nullable=True),
        sa.Column("height_inches", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(20), nullable=False),
        sa.Column("shoots_catches", sa.String(10), nullable=True),
        sa.Column("current_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("nhl_debut", sa.Date(), nullable=True),
        sa.Column("rookie", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("captain", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("alternate_captain", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("headshot_url", sa.String(500), nullable=True),
        sa.Column("action_shot_url", sa.String(500), nullable=True),
        sa.Column("nhl_profile_url", sa.String(500), nullable=True),
        sa.Column("draft_year", sa.Integer(), nullable=True),
        sa.Column("draft_round", sa.Integer(), nullable=True),
        sa.Column("draft_pick", sa.Integer(), nullable=True),
        sa.Column("draft_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_players_nhl_id", "players", ["nhl_id"], unique=True)
    op.create_index("ix_players_last_name", "players", ["last_name"])
    op.create_index("ix_players_full_name", "players", ["full_name"])
    op.create_index("ix_players_position", "players", ["position"])

    # ------------------------------------------------------------------ #
    # player_seasons                                                       #
    # ------------------------------------------------------------------ #
    op.create_table(
        "player_seasons",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("season", sa.String(8), nullable=False),
        sa.Column("season_type", sa.String(20), nullable=False, server_default="regular"),
        sa.Column("jersey_number", sa.String(3), nullable=True),
        sa.Column("games_played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("plus_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shooting_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("time_on_ice_per_game", sa.String(10), nullable=True),
        sa.Column("time_on_ice_total_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_time_on_ice", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_time_on_ice", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("game_winning_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overtime_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=True),
        sa.Column("losses", sa.Integer(), nullable=True),
        sa.Column("overtime_losses", sa.Integer(), nullable=True),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("shots_against", sa.Integer(), nullable=True),
        sa.Column("goals_against", sa.Integer(), nullable=True),
        sa.Column("goals_against_average", sa.Float(), nullable=True),
        sa.Column("save_percentage", sa.Float(), nullable=True),
        sa.Column("shutouts", sa.Integer(), nullable=True),
        sa.Column("quality_starts", sa.Integer(), nullable=True),
        sa.Column("really_bad_starts", sa.Integer(), nullable=True),
        sa.Column("goals_saved_above_expected", sa.Float(), nullable=True),
        sa.Column("salary", sa.Integer(), nullable=True),
        sa.Column("cap_hit", sa.Integer(), nullable=True),
        sa.Column("rookie_season", sa.Boolean(), nullable=False, server_default=sa.false()),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_player_seasons_player_id", "player_seasons", ["player_id"])
    op.create_index("ix_player_seasons_season", "player_seasons", ["season"])

    # ------------------------------------------------------------------ #
    # games                                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nhl_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(8), nullable=False),
        sa.Column("game_type", sa.String(10), nullable=False),
        sa.Column("game_number", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("away_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("game_date", sa.DateTime(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("game_state", sa.String(20), nullable=False, server_default="Preview"),
        sa.Column("current_period", sa.Integer(), nullable=True),
        sa.Column("current_period_ordinal", sa.String(10), nullable=True),
        sa.Column("current_period_time_remaining", sa.String(10), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_scores", sa.JSON(), nullable=True),
        sa.Column("attendance", sa.Integer(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("officials", sa.JSON(), nullable=True),
        sa.Column("weather_conditions", sa.Text(), nullable=True),
        sa.Column("temperature", sa.String(20), nullable=True),
        sa.Column("broadcast_info", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_games_nhl_id", "games", ["nhl_id"], unique=True)
    op.create_index("ix_games_season", "games", ["season"])
    op.create_index("ix_games_game_date", "games", ["game_date"])
    op.create_index("ix_games_home_team_id", "games", ["home_team_id"])
    op.create_index("ix_games_away_team_id", "games", ["away_team_id"])
    op.create_index("ix_games_game_type", "games", ["game_type"])

    # ------------------------------------------------------------------ #
    # periods                                                              #
    # ------------------------------------------------------------------ #
    op.create_table(
        "periods",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("period_number", sa.Integer(), nullable=False),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("ordinal", sa.String(10), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("home_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_blocks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_blocks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_giveaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_giveaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_takeaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_takeaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_faceoff_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_faceoff_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_power_play_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_power_play_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_power_play_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_power_play_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("home_penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_periods_game_id", "periods", ["game_id"])

    # ------------------------------------------------------------------ #
    # game_team_stats                                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "game_team_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("home_away", sa.String(4), nullable=False),
        sa.Column("won", sa.Boolean(), nullable=False),
        sa.Column("overtime", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("shootout", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shooting_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("power_play_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("short_handed_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_kill_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_kill_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("giveaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("takeaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("corsi_for", sa.Integer(), nullable=True),
        sa.Column("corsi_against", sa.Integer(), nullable=True),
        sa.Column("fenwick_for", sa.Integer(), nullable=True),
        sa.Column("fenwick_against", sa.Integer(), nullable=True),
        sa.Column("expected_goals_for", sa.Float(), nullable=True),
        sa.Column("expected_goals_against", sa.Float(), nullable=True),
        sa.Column("high_danger_chances_for", sa.Integer(), nullable=True),
        sa.Column("high_danger_chances_against", sa.Integer(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_game_team_stats_game_id", "game_team_stats", ["game_id"])
    op.create_index("ix_game_team_stats_team_id", "game_team_stats", ["team_id"])

    # ------------------------------------------------------------------ #
    # player_game_stats                                                    #
    # ------------------------------------------------------------------ #
    op.create_table(
        "player_game_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("home_away", sa.String(4), nullable=False),
        sa.Column("jersey_number", sa.String(3), nullable=True),
        sa.Column("position", sa.String(10), nullable=False),
        sa.Column("time_on_ice", sa.String(10), nullable=True),
        sa.Column("time_on_ice_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shifts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("plus_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shooting_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("power_play_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_time_on_ice", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_time_on_ice", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_time_on_ice", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faceoff_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("giveaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("takeaways", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("game_winning_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("game_tying_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overtime_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shootout_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shootout_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalties", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("major_penalties", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("misconduct_penalties", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scratched", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("injured", sa.Boolean(), nullable=False, server_default=sa.false()),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_player_game_stats_player_id", "player_game_stats", ["player_id"])
    op.create_index("ix_player_game_stats_game_id", "player_game_stats", ["game_id"])

    # ------------------------------------------------------------------ #
    # goalie_game_stats                                                    #
    # ------------------------------------------------------------------ #
    op.create_table(
        "goalie_game_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("home_away", sa.String(4), nullable=False),
        sa.Column("jersey_number", sa.String(3), nullable=True),
        sa.Column("starter", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("time_on_ice", sa.String(10), nullable=True),
        sa.Column("time_on_ice_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(10), nullable=True),
        sa.Column("shots_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("save_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("goals_against_average", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("low_danger_shots_against", sa.Integer(), nullable=True),
        sa.Column("low_danger_saves", sa.Integer(), nullable=True),
        sa.Column("medium_danger_shots_against", sa.Integer(), nullable=True),
        sa.Column("medium_danger_saves", sa.Integer(), nullable=True),
        sa.Column("high_danger_shots_against", sa.Integer(), nullable=True),
        sa.Column("high_danger_saves", sa.Integer(), nullable=True),
        sa.Column("power_play_shots_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("power_play_goals_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_shots_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_handed_goals_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_shots_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("even_strength_goals_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_goals_against", sa.Float(), nullable=True),
        sa.Column("goals_saved_above_expected", sa.Float(), nullable=True),
        sa.Column("penalty_shots_faced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_shots_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shootout_shots_faced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shootout_saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rebounds_allowed", sa.Integer(), nullable=True),
        sa.Column("rebound_goals_against", sa.Integer(), nullable=True),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pulled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pulled_time", sa.Integer(), nullable=True),
        sa.Column("quality_start", sa.Boolean(), nullable=True),
        sa.Column("really_bad_start", sa.Boolean(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_goalie_game_stats_player_id", "goalie_game_stats", ["player_id"])
    op.create_index("ix_goalie_game_stats_game_id", "goalie_game_stats", ["game_id"])

    # ------------------------------------------------------------------ #
    # player_advanced_stats                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "player_advanced_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("corsi_for", sa.Integer(), nullable=True),
        sa.Column("corsi_against", sa.Integer(), nullable=True),
        sa.Column("corsi_percentage", sa.Float(), nullable=True),
        sa.Column("fenwick_for", sa.Integer(), nullable=True),
        sa.Column("fenwick_against", sa.Integer(), nullable=True),
        sa.Column("fenwick_percentage", sa.Float(), nullable=True),
        sa.Column("expected_goals_for", sa.Float(), nullable=True),
        sa.Column("expected_goals_against", sa.Float(), nullable=True),
        sa.Column("expected_goals_percentage", sa.Float(), nullable=True),
        sa.Column("individual_expected_goals", sa.Float(), nullable=True),
        sa.Column("individual_corsi_for", sa.Integer(), nullable=True),
        sa.Column("individual_fenwick_for", sa.Integer(), nullable=True),
        sa.Column("offensive_zone_starts", sa.Integer(), nullable=True),
        sa.Column("defensive_zone_starts", sa.Integer(), nullable=True),
        sa.Column("neutral_zone_starts", sa.Integer(), nullable=True),
        sa.Column("on_the_fly_starts", sa.Integer(), nullable=True),
        sa.Column("on_ice_shooting_percentage", sa.Float(), nullable=True),
        sa.Column("on_ice_save_percentage", sa.Float(), nullable=True),
        sa.Column("pdo", sa.Float(), nullable=True),
        sa.Column("relative_corsi", sa.Float(), nullable=True),
        sa.Column("relative_fenwick", sa.Float(), nullable=True),
        sa.Column("relative_expected_goals", sa.Float(), nullable=True),
        sa.Column("quality_of_competition", sa.Float(), nullable=True),
        sa.Column("quality_of_teammates", sa.Float(), nullable=True),
        sa.Column("game_score", sa.Float(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_player_advanced_stats_player_id", "player_advanced_stats", ["player_id"])
    op.create_index("ix_player_advanced_stats_game_id", "player_advanced_stats", ["game_id"])

    # ------------------------------------------------------------------ #
    # travel_logs                                                          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "travel_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=True),
        sa.Column("departure_city", sa.String(100), nullable=False),
        sa.Column("arrival_city", sa.String(100), nullable=False),
        sa.Column("departure_venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=True),
        sa.Column("arrival_venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=True),
        sa.Column("departure_date", sa.DateTime(), nullable=False),
        sa.Column("departure_time", sa.DateTime(), nullable=True),
        sa.Column("arrival_date", sa.DateTime(), nullable=False),
        sa.Column("arrival_time", sa.DateTime(), nullable=True),
        sa.Column("travel_type", sa.String(20), nullable=False),
        sa.Column("distance_miles", sa.Float(), nullable=False),
        sa.Column("flight_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("departure_timezone", sa.String(50), nullable=False),
        sa.Column("arrival_timezone", sa.String(50), nullable=False),
        sa.Column("timezone_change_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("eastward_travel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("charter_flight", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("commercial_flight", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("delays_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("layovers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("back_to_back_travel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("same_day_game", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("road_trip_game_number", sa.Integer(), nullable=True),
        sa.Column("departure_altitude", sa.Float(), nullable=True),
        sa.Column("arrival_altitude", sa.Float(), nullable=True),
        sa.Column("altitude_change", sa.Float(), nullable=True),
        sa.Column("departure_temperature", sa.Float(), nullable=True),
        sa.Column("arrival_temperature", sa.Float(), nullable=True),
        sa.Column("temperature_change", sa.Float(), nullable=True),
        sa.Column("players_traveling", sa.Integer(), nullable=True),
        sa.Column("injured_players", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("travel_difficulty_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fatigue_impact_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("travel_details", sa.JSON(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_travel_logs_team_id", "travel_logs", ["team_id"])
    op.create_index("ix_travel_logs_game_id", "travel_logs", ["game_id"])
    op.create_index("ix_travel_logs_departure_date", "travel_logs", ["departure_date"])

    # ------------------------------------------------------------------ #
    # player_fatigue_metrics                                               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "player_fatigue_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("calculation_date", sa.DateTime(), nullable=False),
        sa.Column("games_last_7_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("games_last_14_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("games_last_30_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("toi_last_3_games", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("toi_last_7_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("toi_last_14_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("days_since_last_game", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("consecutive_games", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("back_to_back_games", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("miles_traveled_last_7_days", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("miles_traveled_last_14_days", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("timezone_changes_last_7_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eastward_travel_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("three_in_four_nights", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("four_in_six_nights", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("games_in_last_10_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots_faced_last_3_games", sa.Integer(), nullable=True),
        sa.Column("high_danger_shots_last_3_games", sa.Integer(), nullable=True),
        sa.Column("save_attempts_last_3_games", sa.Integer(), nullable=True),
        sa.Column("player_age_at_game", sa.Float(), nullable=True),
        sa.Column("nhl_experience_years", sa.Float(), nullable=True),
        sa.Column("injury_report_status", sa.String(50), nullable=True),
        sa.Column("missed_practice_last_week", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_fatigue_index", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("travel_fatigue_index", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("workload_fatigue_index", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("composite_fatigue_index", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("position_adjustment", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("goalie_workload_multiplier", sa.Float(), nullable=True),
        sa.Column("team_back_to_back", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("home_stand_game_number", sa.Integer(), nullable=True),
        sa.Column("road_trip_game_number", sa.Integer(), nullable=True),
        sa.Column("altitude_change", sa.Float(), nullable=True),
        sa.Column("temperature_change", sa.Float(), nullable=True),
        sa.Column("predicted_performance_drop", sa.Float(), nullable=True),
        sa.Column("confidence_interval_lower", sa.Float(), nullable=True),
        sa.Column("confidence_interval_upper", sa.Float(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_player_fatigue_metrics_player_id", "player_fatigue_metrics", ["player_id"])
    op.create_index("ix_player_fatigue_metrics_game_id", "player_fatigue_metrics", ["game_id"])
    op.create_index("ix_player_fatigue_metrics_calculation_date", "player_fatigue_metrics", ["calculation_date"])

    # ------------------------------------------------------------------ #
    # predictions                                                          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("prediction_type", sa.String(30), nullable=False),
        sa.Column("model_type", sa.String(30), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("prediction_date", sa.DateTime(), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("lower_bound", sa.Float(), nullable=True),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("feature_importance", sa.JSON(), nullable=True),
        sa.Column("input_features", sa.JSON(), nullable=False),
        sa.Column("fatigue_index", sa.Float(), nullable=True),
        sa.Column("home_away", sa.String(4), nullable=False),
        sa.Column("opponent_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("back_to_back", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("days_rest", sa.Float(), nullable=False),
        sa.Column("travel_distance", sa.Float(), nullable=True),
        sa.Column("timezone_change", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("prediction_error", sa.Float(), nullable=True),
        sa.Column("absolute_error", sa.Float(), nullable=True),
        sa.Column("squared_error", sa.Float(), nullable=True),
        sa.Column("correct_prediction", sa.Boolean(), nullable=True),
        sa.Column("within_confidence_interval", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_predictions_player_id", "predictions", ["player_id"])
    op.create_index("ix_predictions_game_id", "predictions", ["game_id"])
    op.create_index("ix_predictions_prediction_date", "predictions", ["prediction_date"])
    op.create_index("ix_predictions_prediction_type", "predictions", ["prediction_type"])

    # ------------------------------------------------------------------ #
    # model_performance                                                    #
    # ------------------------------------------------------------------ #
    op.create_table(
        "model_performance",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_type", sa.String(30), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("prediction_type", sa.String(30), nullable=False),
        sa.Column("evaluation_start_date", sa.DateTime(), nullable=False),
        sa.Column("evaluation_end_date", sa.DateTime(), nullable=False),
        sa.Column("total_predictions", sa.Integer(), nullable=False),
        sa.Column("valid_predictions", sa.Integer(), nullable=False),
        sa.Column("mean_absolute_error", sa.Float(), nullable=True),
        sa.Column("mean_squared_error", sa.Float(), nullable=True),
        sa.Column("root_mean_squared_error", sa.Float(), nullable=True),
        sa.Column("r_squared", sa.Float(), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("auc_roc", sa.Float(), nullable=True),
        sa.Column("confidence_calibration_score", sa.Float(), nullable=True),
        sa.Column("predictions_in_confidence_interval", sa.Float(), nullable=True),
        sa.Column("home_game_performance", sa.JSON(), nullable=True),
        sa.Column("away_game_performance", sa.JSON(), nullable=True),
        sa.Column("back_to_back_performance", sa.JSON(), nullable=True),
        sa.Column("high_fatigue_performance", sa.JSON(), nullable=True),
        sa.Column("goalie_performance", sa.JSON(), nullable=True),
        sa.Column("forward_performance", sa.JSON(), nullable=True),
        sa.Column("defense_performance", sa.JSON(), nullable=True),
        sa.Column("performance_trend", sa.String(20), nullable=True),
        sa.Column("trend_coefficient", sa.Float(), nullable=True),
        sa.Column("top_features", sa.JSON(), nullable=True),
        sa.Column("feature_stability", sa.Float(), nullable=True),
        sa.Column("baseline_improvement", sa.Float(), nullable=True),
        sa.Column("overfitting_score", sa.Float(), nullable=True),
        sa.Column("drift_detection_score", sa.Float(), nullable=True),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("prediction_latency_ms", sa.Float(), nullable=True),
        sa.Column("memory_usage_mb", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_performance_model_type", "model_performance", ["model_type"])
    op.create_index("ix_model_performance_model_version", "model_performance", ["model_version"])
    op.create_index("ix_model_performance_prediction_type", "model_performance", ["prediction_type"])

    # ------------------------------------------------------------------ #
    # users                                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("display_name", sa.String(150), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("subscription_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("verification_sent_at", sa.DateTime(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("reset_token", sa.String(255), nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("api_key", sa.String(255), nullable=True),
        sa.Column("api_key_created", sa.DateTime(), nullable=True),
        sa.Column("api_calls_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_quota_daily", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("organization", sa.String(200), nullable=True),
        sa.Column("team_affiliations", sa.JSON(), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("dashboard_layout", sa.JSON(), nullable=True),
        sa.Column("notification_preferences", sa.JSON(), nullable=True),
        sa.Column("subscription_start", sa.DateTime(), nullable=True),
        sa.Column("subscription_end", sa.DateTime(), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("total_queries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("favorite_players", sa.JSON(), nullable=True),
        sa.Column("favorite_teams", sa.JSON(), nullable=True),
        # SoftDeleteMixin
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_api_key", "users", ["api_key"], unique=True)

    # ------------------------------------------------------------------ #
    # user_sessions                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_token", sa.String(255), nullable=False),
        sa.Column("refresh_token", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_type", sa.String(50), nullable=True),
        sa.Column("browser", sa.String(100), nullable=True),
        sa.Column("operating_system", sa.String(100), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_reason", sa.String(100), nullable=True),
        sa.Column("suspicious_activity", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("page_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_data", sa.JSON(), nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False, server_default="nhl_api"),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        # TimestampMixin — note: UserSession defines its own created_at override
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_session_token", "user_sessions", ["session_token"], unique=True)
    op.create_index("ix_user_sessions_refresh_token", "user_sessions", ["refresh_token"], unique=True)


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.drop_table("model_performance")
    op.drop_table("predictions")
    op.drop_table("player_fatigue_metrics")
    op.drop_table("travel_logs")
    op.drop_table("player_advanced_stats")
    op.drop_table("goalie_game_stats")
    op.drop_table("player_game_stats")
    op.drop_table("game_team_stats")
    op.drop_table("periods")
    op.drop_table("games")
    op.drop_table("player_seasons")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("venues")
    op.drop_table("divisions")
    op.drop_table("conferences")
