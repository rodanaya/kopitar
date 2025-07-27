import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from scipy import stats
# Add the parent directory to path to import utility modules
# Correct path adjustment assuming app.py is in kopitar/dashboard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import database utility using the correct path
try:
    # Assumes db_utils.py is in kopitar/database
    from database.db_utils import get_db
except ImportError as e:
    st.error(f"Failed to import database utilities. Ensure 'kopitar/database/db_utils.py' exists. Error: {e}")
    st.stop()

# Set up basic logging for the dashboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Custom CSS Injection ---
def inject_custom_css():
    st.markdown("""
        <style>
            /* Base body styling */
            .stApp {
                background-color: #f0f2f6; /* Light grey background */
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; /* Modern font */
            }

            /* Main content area */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }

            /* Sidebar styling */
            .stSidebar > div:first-child {
                 background-color: #ffffff;
                 border-right: 1px solid #e6e6e6;
                 padding-top: 1rem;
            }
            .stSidebar .stRadio > label {
                padding-top: 10px;
                padding-bottom: 10px;
            }

            /* Titles */
            h1, h2, h3 {
                color: #1a1a1a; /* Darker text for titles */
            }
            h1 {
                border-bottom: 2px solid #0068c9; /* Accent color border */
                padding-bottom: 0.3em;
            }
            h2 {
                 color: #0068c9; /* Accent color for h2 */
            }


            /* Metric styling */
            .stMetric {
                background-color: #ffffff;
                border: 1px solid #e6e6e6;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .stMetric > label { /* Metric label */
                color: #555;
            }
            .stMetric > div { /* Metric value */
                font-size: 1.75em;
                font-weight: 600;
                color: #1a1a1a;
            }

            /* Dataframe styling */
            .stDataFrame {
                border: 1px solid #e6e6e6;
                border-radius: 8px;
            }

            /* Plotly chart background */
            .plotly-chart {
                 border-radius: 8px;
                 background-color: #ffffff;
                 padding: 10px;
                 border: 1px solid #e6e6e6;
                 box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

        </style>
    """, unsafe_allow_html=True)

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="NHL Performance Analysis Dashboard",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
@st.cache_data(ttl=3600) # Cache DB connection and seasons for an hour
def get_db_connection_and_seasons():
    """Connects to DB and fetches available seasons. Caches the result."""
    try:
        db = get_db()
        seasons_query = "SELECT DISTINCT season FROM games ORDER BY season DESC"
        seasons_df = db.execute_query(seasons_query)
        available_seasons = seasons_df['season'].astype(str).tolist() if not seasons_df.empty else []
        logger.info(f"Fetched available seasons: {available_seasons}")
        return db, available_seasons
    except Exception as e:
        logger.error(f"Database connection or season fetch error: {e}")
        st.error(f"Database connection error: {e}")
        st.stop() # Stop execution if DB connection fails

# --- Sidebar Navigation and Filters ---
def sidebar_nav(available_seasons):
    """Creates the sidebar navigation and filters."""
    with st.sidebar:
        st.title("🏒 NHL Performance Analysis")
        st.success("Connected to Database") # Connection checked in get_db_connection_and_seasons

        # Navigation
        nav_options = ["Overview", "Player Analysis", "Goalie Deep Dive",
                       "Back-to-Back Analysis", "Playoff vs Regular Season",
                       "Travel Impact", "Custom Query"]
        nav = st.radio("Navigation", nav_options)

        # Filters
        st.subheader("Filters")

        # Season selection - ensure default is valid
        default_season = [available_seasons[0]] if available_seasons else []
        selected_seasons = st.multiselect(
            "Select Seasons", available_seasons, default=default_season
        )

        # Game type selection
        game_types_options = ["Regular Season", "Playoffs"]
        selected_game_types_ui = st.multiselect(
            "Game Types", game_types_options, default=["Regular Season"]
        )

        # Position selection
        positions_options = ["Goalie", "Defenseman", "Forward"]
        selected_positions_ui = st.multiselect(
            "Positions", positions_options, default=positions_options
        )

        # Convert UI selections to database values
        db_game_types = []
        if "Regular Season" in selected_game_types_ui: db_game_types.append("R")
        if "Playoffs" in selected_game_types_ui: db_game_types.append("P")

        db_positions = []
        if "Goalie" in selected_positions_ui: db_positions.append("G")
        if "Defenseman" in selected_positions_ui: db_positions.append("D")
        if "Forward" in selected_positions_ui: db_positions.append("F")

        # Placeholder for Export button
        # if st.button("Export Current View"):
        #     st.info("Export functionality not yet implemented.")

        return {
            "nav": nav,
            "seasons": [int(s) for s in selected_seasons], # Convert seasons to int for queries
            "game_types": db_game_types,
            "positions": db_positions
        }

# --- Data Fetching Functions (Cached) ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_overview_data(_db, seasons, game_types):
    """Fetches data needed for the overview page."""
    if not seasons or not game_types: return None, None, None, None

    params = {'seasons': tuple(seasons), 'game_types': tuple(game_types)}

    # Summary stats query
    summary_query = """
    SELECT
        COUNT(DISTINCT g.game_id) as total_games,
        COUNT(DISTINCT p.player_id) as total_players,
        COUNT(DISTINCT CASE WHEN p.position_type = 'G' THEN p.player_id END) as goalies,
        COUNT(DISTINCT CASE WHEN p.position_type = 'D' THEN p.player_id END) as defensemen,
        COUNT(DISTINCT CASE WHEN p.position_type = 'F' THEN p.player_id END) as forwards
    FROM games g
    LEFT JOIN (
        SELECT DISTINCT player_id, game_id FROM goalie_game_logs WHERE season IN :seasons AND game_type IN :game_types
        UNION
        SELECT DISTINCT player_id, game_id FROM skater_game_logs WHERE season IN :seasons AND game_type IN :game_types
    ) gl ON g.game_id = gl.game_id
    LEFT JOIN players p ON gl.player_id = p.player_id AND p.season IN :seasons -- Join players for the relevant seasons
    WHERE g.season IN :seasons AND g.game_type IN :game_types
    """
    summary_df = _db.execute_query(summary_query, params)

    # B2B stats query
    b2b_query = """
    SELECT
        g.season,
        SUM(CASE WHEN g.is_back_to_back = true THEN 1 ELSE 0 END) as b2b_games,
        COUNT(*) as total_games,
        ROUND(100.0 * SUM(CASE WHEN g.is_back_to_back = true THEN 1 ELSE 0 END) / COUNT(*), 1) as b2b_percentage
    FROM games g
    WHERE g.season IN :seasons AND g.game_type IN :game_types
    GROUP BY g.season ORDER BY g.season
    """
    b2b_df = _db.execute_query(b2b_query, params)

    # Top goalies query
    goalie_query = """
    SELECT
        p.full_name as player_name, t.name as team_name,
        COUNT(DISTINCT g.game_id) as games_played,
        AVG(g.save_percentage) as save_percentage,
        AVG(g.goals_against) as goals_against_avg,
        SUM(CASE WHEN g.decision = 'W' THEN 1 ELSE 0 END) as wins
    FROM goalie_game_logs g
    JOIN players p ON g.player_id = p.player_id AND g.season = p.season -- Ensure player season matches log season
    JOIN teams t ON g.team_id = t.team_id AND g.season = t.season -- Ensure team season matches log season
    WHERE g.season IN :seasons AND g.game_type IN :game_types
    GROUP BY p.player_id, p.full_name, t.name -- Group by player_id for uniqueness
    HAVING COUNT(DISTINCT g.game_id) >= 10
    ORDER BY AVG(g.save_percentage) DESC NULLS LAST
    LIMIT 10
    """
    top_goalies_df = _db.execute_query(goalie_query, params)

    # Top skaters query
    skater_query = """
    SELECT
        p.full_name as player_name, p.position_type, t.name as team_name,
        COUNT(DISTINCT s.game_id) as games_played,
        SUM(s.goals) as goals, SUM(s.assists) as assists, SUM(s.points) as points,
        ROUND(AVG(s.time_on_ice_mins), 1) as avg_toi
    FROM skater_game_logs s
    JOIN players p ON s.player_id = p.player_id AND s.season = p.season
    JOIN teams t ON s.team_id = t.team_id AND s.season = t.season
    WHERE s.season IN :seasons AND s.game_type IN :game_types
    -- Position filter will be applied in Python if needed, or add parameter here
    GROUP BY p.player_id, p.full_name, p.position_type, t.name
    HAVING COUNT(DISTINCT s.game_id) >= 10
    ORDER BY SUM(s.points) DESC NULLS LAST
    LIMIT 10
    """
    top_skaters_df = _db.execute_query(skater_query, params)

    return summary_df, b2b_df, top_goalies_df, top_skaters_df

@st.cache_data(ttl=600)
def fetch_player_logs(_db, player_id, position_type, seasons, game_types):
    """Fetches game logs for a specific player."""
    if not seasons or not game_types: return pd.DataFrame()

    params = {'player_id': player_id, 'seasons': tuple(seasons), 'game_types': tuple(game_types)}
    base_query_select = """
        SELECT logs.*, t.name as team_name, opp.name as opponent_name,
               gm.away_score, gm.home_score,
               CASE WHEN logs.home_away = 'Home' THEN gm.home_score ELSE gm.away_score END as team_score,
               CASE WHEN logs.home_away = 'Home' THEN gm.away_score ELSE gm.home_score END as opponent_score
        FROM {log_table} logs
        JOIN teams t ON logs.team_id = t.team_id AND logs.season = t.season
        JOIN teams opp ON logs.opponent_id = opp.team_id AND logs.season = opp.season
        JOIN games gm ON logs.game_id = gm.game_id
        WHERE logs.player_id = :player_id
          AND logs.season IN :seasons
          AND logs.game_type IN :game_types
        ORDER BY logs.game_date
    """
    if position_type == 'G':
        query = base_query_select.format(log_table='goalie_game_logs')
    else:
        query = base_query_select.format(log_table='skater_game_logs')

    return _db.execute_query(query, params)


# --- Page Rendering Functions ---

def render_overview(db, filters):
    """Renders the overview page."""
    st.title("📊 NHL Performance Overview")
    st.write("High-level statistics based on selected filters.")

    if not filters["seasons"] or not filters["game_types"]:
        st.warning("Please select at least one Season and Game Type in the sidebar.")
        return

    summary_df, b2b_df, top_goalies_df, top_skaters_df = fetch_overview_data(
        db, filters["seasons"], filters["game_types"]
    )

    if summary_df is None: # Check if data fetching failed or returned None
        st.error("Could not fetch overview data.")
        return

    # Display summary metrics
    if not summary_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Games", f"{summary_df['total_games'].iloc[0]:,}")
        col2.metric("Total Players", f"{summary_df['total_players'].iloc[0]:,}")
        col3.metric("Goalies", f"{summary_df['goalies'].iloc[0]:,}")
        col4.metric("Skaters", f"{summary_df['defensemen'].iloc[0] + summary_df['forwards'].iloc[0]:,}")
    else:
        st.info("No summary data available for the selected filters.")

    st.divider()

    # Display B2B stats
    if b2b_df is not None and not b2b_df.empty:
        st.subheader("Back-to-Back Games by Season")
        fig_b2b = px.bar(
            b2b_df, x='season', y='b2b_percentage', text='b2b_percentage',
            labels={'season': 'Season', 'b2b_percentage': 'Back-to-Back Games (%)'},
            title="Percentage of Back-to-Back Games by Season"
        )
        fig_b2b.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_b2b, use_container_width=True)
    else:
        st.info("No Back-to-Back game data available.")

    st.divider()

    # Display top performers
    col_g, col_s = st.columns(2)

    with col_g:
        if 'G' in filters["positions"] and top_goalies_df is not None and not top_goalies_df.empty:
            st.subheader("Top 10 Goalies by Save %")
            fig_g = px.bar(
                top_goalies_df, x='player_name', y='save_percentage', text='save_percentage',
                hover_data=['team_name', 'games_played', 'goals_against_avg', 'wins'],
                labels={'player_name': 'Goalie', 'save_percentage': 'Save Percentage'},
                title="Top 10 Goalies by Save % (min. 10 games)"
            )
            fig_g.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            fig_g.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            st.info("No Goalie data or 'Goalie' position not selected.")

    with col_s:
        # Filter top skaters based on selected positions (D/F)
        filtered_top_skaters = pd.DataFrame()
        if top_skaters_df is not None and not top_skaters_df.empty:
             skater_positions_selected = [p for p in filters["positions"] if p in ['D', 'F']]
             if skater_positions_selected:
                 filtered_top_skaters = top_skaters_df[top_skaters_df['position_type'].isin(skater_positions_selected)].head(10)

        if not filtered_top_skaters.empty:
            st.subheader("Top 10 Skaters by Points")
            filtered_top_skaters['points_per_game'] = filtered_top_skaters['points'] / filtered_top_skaters['games_played']
            fig_s = px.bar(
                filtered_top_skaters, x='player_name', y='points', text='points',
                hover_data=['team_name', 'position_type', 'games_played', 'goals', 'assists', 'points_per_game', 'avg_toi'],
                color='position_type',
                labels={'player_name': 'Player', 'points': 'Total Points', 'position_type': 'Position'},
                title="Top 10 Skaters by Points (min. 10 games)"
            )
            fig_s.update_traces(texttemplate='%{text}', textposition='outside')
            fig_s.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("No Skater data or 'Defenseman'/'Forward' positions not selected.")

# --- Back-to-Back Analysis Page ---
@st.cache_data(ttl=600)
def fetch_b2b_analysis_data(_db, position_type, seasons, game_types):
    """Fetches back-to-back analysis data for a given position."""
    if not seasons or not game_types: return pd.DataFrame()
    try:
        # Use the analysis function from db_utils
        # Note: The db_utils function might already filter by season/playoff internally
        # We pass the filters here for caching purposes, but the underlying function needs checking
        # Let's assume db.analyze_back_to_back_performance takes season and is_playoff
        is_playoff_filter = None # Default to both
        if game_types == ['R']: is_playoff_filter = False
        if game_types == ['P']: is_playoff_filter = True
        # Combine multiple seasons if needed, or run per season?
        # For now, let's assume the function handles multiple seasons or we analyze the first selected one
        season_to_analyze = seasons[0] if seasons else None

        df = _db.analyze_back_to_back_performance(
            position_type=position_type,
            season=str(season_to_analyze) if season_to_analyze else None, # Ensure string if needed by function
            is_playoff=is_playoff_filter
        )
        return df
    except Exception as e:
        logger.error(f"Error fetching B2B analysis data for {position_type}: {e}")
        st.error(f"Failed to fetch Back-to-Back analysis data for {position_type}.")
        return pd.DataFrame()

def render_b2b_analysis(db, filters):
    """Renders the Back-to-Back analysis page."""
    st.title("⏩ Back-to-Back Games Analysis")
    st.write("Comparing player performance in games played on consecutive days versus games with rest.")

    if not filters["seasons"] or not filters["game_types"]:
        st.warning("Please select at least one Season and Game Type in the sidebar.")
        return

    # Analyze Goalies if selected
    if 'G' in filters["positions"]:
        st.subheader("Goalie Back-to-Back Performance")
        goalie_b2b_df = fetch_b2b_analysis_data(db, 'G', filters["seasons"], filters["game_types"])

        if not goalie_b2b_df.empty:
            # Calculate difference and sort
            goalie_b2b_df['save_pct_diff'] = goalie_b2b_df['b2b_save_pct'] - goalie_b2b_df['rested_save_pct']
            goalie_b2b_df['ga_diff'] = goalie_b2b_df['b2b_goals_against'] - goalie_b2b_df['rested_goals_against']

            # Display top performers in B2B
            st.write("**Top 5 Goalies Improving in Back-to-Backs (Save %)**")
            st.dataframe(goalie_b2b_df.sort_values('save_pct_diff', ascending=False, na_position='last').head(5)[
                ['player_name', 'team_name', 'rested_save_pct', 'b2b_save_pct', 'save_pct_diff', 'rested_games', 'b2b_games']
            ], use_container_width=True)

            # Display worst performers in B2B
            st.write("**Top 5 Goalies Declining in Back-to-Backs (Save %)**")
            st.dataframe(goalie_b2b_df.sort_values('save_pct_diff', ascending=True, na_position='last').head(5)[
                 ['player_name', 'team_name', 'rested_save_pct', 'b2b_save_pct', 'save_pct_diff', 'rested_games', 'b2b_games']
            ], use_container_width=True)

            # Overall average comparison plot
            avg_rested_sv = goalie_b2b_df['rested_save_pct'].mean()
            avg_b2b_sv = goalie_b2b_df['b2b_save_pct'].mean()
            avg_rested_ga = goalie_b2b_df['rested_goals_against'].mean()
            avg_b2b_ga = goalie_b2b_df['b2b_goals_against'].mean()

            fig_g_avg = make_subplots(rows=1, cols=2, subplot_titles=("Avg Save %", "Avg Goals Against"))
            fig_g_avg.add_trace(go.Bar(x=['Rested', 'B2B'], y=[avg_rested_sv, avg_b2b_sv], name='Save %'), row=1, col=1)
            fig_g_avg.add_trace(go.Bar(x=['Rested', 'B2B'], y=[avg_rested_ga, avg_b2b_ga], name='Goals Against'), row=1, col=2)
            fig_g_avg.update_layout(title_text="Overall Goalie Performance: Rested vs. Back-to-Back")
            st.plotly_chart(fig_g_avg, use_container_width=True)

        else:
            st.info("No goalie back-to-back analysis data available for the selected filters (requires min. 5 rested / 3 B2B games per goalie).")
        st.divider()

    # Analyze Skaters if selected
    skater_positions = [p for p in filters["positions"] if p in ['D', 'F']]
    if skater_positions:
        st.subheader("Skater Back-to-Back Performance")
        # Fetch for 'D' and 'F' separately or combined? db_utils combines them if position_type='D' or 'F'
        # Let's fetch combined first, then potentially filter/split
        skater_b2b_df = fetch_b2b_analysis_data(db, 'F', filters["seasons"], filters["game_types"]) # Fetching 'F' might get both D/F based on db_utils logic
        if 'D' in skater_positions and 'F' in skater_positions and not skater_b2b_df.empty:
             # If db_utils only returned F, fetch D separately and combine
             if not all(pos in skater_b2b_df['position'].unique() for pos in ['D', 'C', 'L', 'R']): # Rough check
                 skater_b2b_df_d = fetch_b2b_analysis_data(db, 'D', filters["seasons"], filters["game_types"])
                 skater_b2b_df = pd.concat([skater_b2b_df, skater_b2b_df_d], ignore_index=True)
        elif 'D' in skater_positions and 'F' not in skater_positions:
             skater_b2b_df = fetch_b2b_analysis_data(db, 'D', filters["seasons"], filters["game_types"])


        if not skater_b2b_df.empty:
            # Calculate difference and sort
            skater_b2b_df['points_diff'] = skater_b2b_df['b2b_points'] - skater_b2b_df['rested_points']
            skater_b2b_df['toi_diff'] = skater_b2b_df['b2b_toi'] - skater_b2b_df['rested_toi']

            # Filter based on selected positions D/F before displaying
            skater_b2b_df_filtered = skater_b2b_df[skater_b2b_df['position'].isin(skater_positions)].copy() # Assuming 'position' column exists

            if not skater_b2b_df_filtered.empty:
                # Display top performers in B2B
                st.write("**Top 5 Skaters Improving in Back-to-Backs (Points/Game)**")
                st.dataframe(skater_b2b_df_filtered.sort_values('points_diff', ascending=False, na_position='last').head(5)[
                    ['player_name', 'position', 'team_name', 'rested_points', 'b2b_points', 'points_diff', 'rested_games', 'b2b_games']
                ], use_container_width=True)

                # Display worst performers in B2B
                st.write("**Top 5 Skaters Declining in Back-to-Backs (Points/Game)**")
                st.dataframe(skater_b2b_df_filtered.sort_values('points_diff', ascending=True, na_position='last').head(5)[
                    ['player_name', 'position', 'team_name', 'rested_points', 'b2b_points', 'points_diff', 'rested_games', 'b2b_games']
                ], use_container_width=True)

                # Overall average comparison plot
                avg_rested_pts = skater_b2b_df_filtered['rested_points'].mean()
                avg_b2b_pts = skater_b2b_df_filtered['b2b_points'].mean()
                avg_rested_toi = skater_b2b_df_filtered['rested_toi'].mean()
                avg_b2b_toi = skater_b2b_df_filtered['b2b_toi'].mean()

                fig_s_avg = make_subplots(rows=1, cols=2, subplot_titles=("Avg Points", "Avg Time on Ice"))
                fig_s_avg.add_trace(go.Bar(x=['Rested', 'B2B'], y=[avg_rested_pts, avg_b2b_pts], name='Points'), row=1, col=1)
                fig_s_avg.add_trace(go.Bar(x=['Rested', 'B2B'], y=[avg_rested_toi, avg_b2b_toi], name='TOI (mins)'), row=1, col=2)
                fig_s_avg.update_layout(title_text="Overall Skater Performance: Rested vs. Back-to-Back")
                st.plotly_chart(fig_s_avg, use_container_width=True)
            else:
                 st.info("No skater back-to-back analysis data available for the selected D/F positions.")

        else:
            st.info("No skater back-to-back analysis data available for the selected filters (requires min. 5 rested / 3 B2B games per skater).")

# --- Playoff vs Regular Season Analysis Page ---
@st.cache_data(ttl=600)
def fetch_playoff_analysis_data(_db, position_type, seasons, min_games=5):
    """Fetches playoff vs regular season analysis data."""
    if not seasons: return pd.DataFrame()
    try:
        # Assuming analyze_playoff_vs_regular takes season and min_games
        # Analyze the first selected season for simplicity, or modify db_utils to handle multiple
        season_to_analyze = seasons[0] if seasons else None
        df = _db.analyze_playoff_vs_regular(
            position_type=position_type,
            season=str(season_to_analyze) if season_to_analyze else None,
            min_games=min_games
        )
        return df
    except Exception as e:
        logger.error(f"Error fetching Playoff vs Regular analysis data for {position_type}: {e}")
        st.error(f"Failed to fetch Playoff vs Regular analysis data for {position_type}.")
        return pd.DataFrame()

def render_playoff_analysis(db, filters):
    """Renders the Playoff vs Regular Season analysis page."""
    st.title("🏆 Playoff vs Regular Season Analysis")
    st.write("Comparing player performance in playoff games versus regular season games.")

    if not filters["seasons"]:
        st.warning("Please select at least one Season in the sidebar.")
        return

    min_games_per_period = st.slider("Minimum games in Regular Season AND Playoffs:", min_value=1, max_value=15, value=5)

    # Analyze Goalies if selected
    if 'G' in filters["positions"]:
        st.subheader("Goalie Playoff vs Regular Season Performance")
        goalie_playoff_df = fetch_playoff_analysis_data(db, 'G', filters["seasons"], min_games=min_games_per_period)

        if not goalie_playoff_df.empty:
            # Calculate difference and sort
            goalie_playoff_df['save_pct_diff'] = goalie_playoff_df['playoff_save_pct'] - goalie_playoff_df['regular_season_save_pct']
            goalie_playoff_df['ga_diff'] = goalie_playoff_df['playoff_goals_against'] - goalie_playoff_df['regular_season_goals_against']

            # Display top playoff performers
            st.write(f"**Top 5 Goalies Improving in Playoffs (Save %, min {min_games_per_period} games each)**")
            st.dataframe(goalie_playoff_df.sort_values('save_pct_diff', ascending=False, na_position='last').head(5)[
                ['player_name', 'team_name', 'regular_season_save_pct', 'playoff_save_pct', 'save_pct_diff', 'regular_season_games', 'playoff_games']
            ], use_container_width=True)

            # Display biggest playoff decliners
            st.write(f"**Top 5 Goalies Declining in Playoffs (Save %, min {min_games_per_period} games each)**")
            st.dataframe(goalie_playoff_df.sort_values('save_pct_diff', ascending=True, na_position='last').head(5)[
                 ['player_name', 'team_name', 'regular_season_save_pct', 'playoff_save_pct', 'save_pct_diff', 'regular_season_games', 'playoff_games']
            ], use_container_width=True)

            # Overall average comparison plot
            avg_reg_sv = goalie_playoff_df['regular_season_save_pct'].mean()
            avg_playoff_sv = goalie_playoff_df['playoff_save_pct'].mean()
            avg_reg_ga = goalie_playoff_df['regular_season_goals_against'].mean()
            avg_playoff_ga = goalie_playoff_df['playoff_goals_against'].mean()

            fig_g_avg_playoff = make_subplots(rows=1, cols=2, subplot_titles=("Avg Save %", "Avg Goals Against"))
            fig_g_avg_playoff.add_trace(go.Bar(x=['Regular', 'Playoff'], y=[avg_reg_sv, avg_playoff_sv], name='Save %'), row=1, col=1)
            fig_g_avg_playoff.add_trace(go.Bar(x=['Regular', 'Playoff'], y=[avg_reg_ga, avg_playoff_ga], name='Goals Against'), row=1, col=2)
            fig_g_avg_playoff.update_layout(title_text="Overall Goalie Performance: Regular Season vs. Playoffs")
            st.plotly_chart(fig_g_avg_playoff, use_container_width=True)

        else:
            st.info(f"No goalie playoff vs regular season analysis data available (requires min. {min_games_per_period} games in both periods).")
        st.divider()

    # Analyze Skaters if selected
    skater_positions = [p for p in filters["positions"] if p in ['D', 'F']]
    if skater_positions:
        st.subheader("Skater Playoff vs Regular Season Performance")
        # Fetch for 'D' and 'F' separately or combined?
        skater_playoff_df_f = fetch_playoff_analysis_data(db, 'F', filters["seasons"], min_games=min_games_per_period)
        skater_playoff_df_d = fetch_playoff_analysis_data(db, 'D', filters["seasons"], min_games=min_games_per_period)
        skater_playoff_df = pd.concat([skater_playoff_df_f, skater_playoff_df_d], ignore_index=True)


        if not skater_playoff_df.empty:
            # Calculate difference and sort
            skater_playoff_df['points_diff'] = skater_playoff_df['playoff_points'] - skater_playoff_df['regular_season_points']
            skater_playoff_df['toi_diff'] = skater_playoff_df['playoff_toi'] - skater_playoff_df['regular_season_toi']

            # Filter based on selected positions D/F before displaying
            skater_playoff_df_filtered = skater_playoff_df[skater_playoff_df['position'].isin(skater_positions)].copy()

            if not skater_playoff_df_filtered.empty:
                # Display top playoff performers
                st.write(f"**Top 5 Skaters Improving in Playoffs (Points/Game, min {min_games_per_period} games each)**")
                st.dataframe(skater_playoff_df_filtered.sort_values('points_diff', ascending=False, na_position='last').head(5)[
                    ['player_name', 'position', 'team_name', 'regular_season_points', 'playoff_points', 'points_diff', 'regular_season_games', 'playoff_games']
                ], use_container_width=True)

                # Display biggest playoff decliners
                st.write(f"**Top 5 Skaters Declining in Playoffs (Points/Game, min {min_games_per_period} games each)**")
                st.dataframe(skater_playoff_df_filtered.sort_values('points_diff', ascending=True, na_position='last').head(5)[
                    ['player_name', 'position', 'team_name', 'regular_season_points', 'playoff_points', 'points_diff', 'regular_season_games', 'playoff_games']
                ], use_container_width=True)

                # Overall average comparison plot
                avg_reg_pts = skater_playoff_df_filtered['regular_season_points'].mean()
                avg_playoff_pts = skater_playoff_df_filtered['playoff_points'].mean()
                avg_reg_toi = skater_playoff_df_filtered['regular_season_toi'].mean()
                avg_playoff_toi = skater_playoff_df_filtered['playoff_toi'].mean()

                fig_s_avg_playoff = make_subplots(rows=1, cols=2, subplot_titles=("Avg Points", "Avg Time on Ice"))
                fig_s_avg_playoff.add_trace(go.Bar(x=['Regular', 'Playoff'], y=[avg_reg_pts, avg_playoff_pts], name='Points'), row=1, col=1)
                fig_s_avg_playoff.add_trace(go.Bar(x=['Regular', 'Playoff'], y=[avg_reg_toi, avg_playoff_toi], name='TOI (mins)'), row=1, col=2)
                fig_s_avg_playoff.update_layout(title_text="Overall Skater Performance: Regular Season vs. Playoffs")
                st.plotly_chart(fig_s_avg_playoff, use_container_width=True)
            else:
                 st.info("No skater playoff vs regular season analysis data available for the selected D/F positions.")

        else:
            st.info(f"No skater playoff vs regular season analysis data available (requires min. {min_games_per_period} games in both periods).")

# --- Travel Impact Analysis Page ---
@st.cache_data(ttl=600)
def fetch_travel_impact_data(_db, position_type, seasons, game_types):
    """Fetches game logs needed for travel impact analysis."""
    if not seasons or not game_types: return pd.DataFrame()
    try:
        # Fetch all logs for the selected filters, we'll process travel impact here
        if position_type == 'G':
            df = _db.get_goalie_game_logs(season=seasons[0] if seasons else None, game_type=game_types[0] if game_types else None) # Simplify for now
        elif position_type in ['D', 'F']:
             df = _db.get_skater_game_logs(season=seasons[0] if seasons else None, game_type=game_types[0] if game_types else None)
             # Filter further by D or F if needed
             if 'position' in df.columns:
                 if position_type == 'D':
                     df = df[df['position'] == 'D'].copy()
                 elif position_type == 'F':
                     df = df[df['position'].isin(['C', 'L', 'R'])].copy()
        else:
            return pd.DataFrame()

        # Add travel categories
        if 'distance_traveled' in df.columns:
             bins = [-1, 1, 500, 1500, 3000, float('inf')] # Add a bin for no travel (0-1 km)
             labels = ['No Travel', 'Short (<500km)', 'Medium (500-1500km)', 'Long (1500-3000km)', 'Very Long (>3000km)']
             df['travel_category'] = pd.cut(df['distance_traveled'], bins=bins, labels=labels, right=False) # Use right=False for bins like [0, 500)

        # Add timezone direction
        if 'timezone_diff' in df.columns:
            df['timezone_direction'] = 'None'
            df.loc[df['timezone_diff'] > 0, 'timezone_direction'] = 'Eastward'
            df.loc[df['timezone_diff'] < 0, 'timezone_direction'] = 'Westward'

        return df
    except Exception as e:
        logger.error(f"Error fetching travel impact data for {position_type}: {e}")
        st.error(f"Failed to fetch travel impact data for {position_type}.")
        return pd.DataFrame()

def render_travel_analysis(db, filters):
    """Renders the Travel Impact analysis page."""
    st.title("✈️ Travel Impact Analysis")
    st.write("Analyzing how travel distance and timezone changes affect player performance.")

    if not filters["seasons"] or not filters["game_types"]:
        st.warning("Please select at least one Season and Game Type in the sidebar.")
        return

    # Select primary metric based on position
    position_to_analyze = st.selectbox("Select Position to Analyze Travel Impact:", filters["positions"])

    if not position_to_analyze:
        st.warning("Please select at least one position in the sidebar.")
        return

    travel_df = fetch_travel_impact_data(db, position_to_analyze, filters["seasons"], filters["game_types"])

    if travel_df.empty:
        st.info(f"No data available for travel analysis for position {position_to_analyze} with selected filters.")
        return

    # Determine primary metric
    primary_metric = ""
    metric_label = ""
    if position_to_analyze == 'G':
        primary_metric = 'save_percentage'
        metric_label = 'Save Percentage'
    elif position_to_analyze in ['D', 'F']:
        primary_metric = 'points'
        metric_label = 'Points per Game' # Analyze points

    if primary_metric not in travel_df.columns or travel_df[primary_metric].isna().all():
         st.warning(f"Primary metric '{primary_metric}' not found or has no data for {position_to_analyze}.")
         return

    # --- Analysis by Travel Distance ---
    if 'travel_category' in travel_df.columns:
        st.subheader(f"{metric_label} by Travel Distance Category")
        # Calculate average performance per category
        travel_perf = travel_df.groupby('travel_category', observed=False)[primary_metric].agg(['mean', 'count']).reset_index()

        if not travel_perf.empty:
            fig_dist = px.bar(
                travel_perf,
                x='travel_category',
                y='mean',
                text='mean',
                labels={'travel_category': 'Travel Distance Category', 'mean': f'Average {metric_label}'},
                title=f"Average {metric_label} by Travel Distance"
            )
            fig_dist.update_traces(texttemplate='%{text:.3f}' if primary_metric == 'save_percentage' else '%{text:.2f}', textposition='outside')
            fig_dist.update_layout(xaxis={'categoryorder':'array', 'categoryarray':['No Travel', 'Short (<500km)', 'Medium (500-1500km)', 'Long (1500-3000km)', 'Very Long (>3000km)']})
            st.plotly_chart(fig_dist, use_container_width=True)
            st.dataframe(travel_perf, use_container_width=True) # Show table too
        else:
            st.info("Could not analyze performance by travel distance category.")

    # --- Analysis by Timezone Change ---
    if 'timezone_direction' in travel_df.columns:
        st.subheader(f"{metric_label} by Timezone Change Direction")
        # Calculate average performance per category
        tz_perf = travel_df.groupby('timezone_direction')[primary_metric].agg(['mean', 'count']).reset_index()

        if not tz_perf.empty:
            fig_tz = px.bar(
                tz_perf,
                x='timezone_direction',
                y='mean',
                text='mean',
                labels={'timezone_direction': 'Timezone Change Direction', 'mean': f'Average {metric_label}'},
                title=f"Average {metric_label} by Timezone Change"
            )
            fig_tz.update_traces(texttemplate='%{text:.3f}' if primary_metric == 'save_percentage' else '%{text:.2f}', textposition='outside')
            fig_tz.update_layout(xaxis={'categoryorder':'array', 'categoryarray':['Westward', 'None', 'Eastward']})
            st.plotly_chart(fig_tz, use_container_width=True)
            st.dataframe(tz_perf, use_container_width=True) # Show table too
        else:
            st.info("Could not analyze performance by timezone change direction.")


def render_player_analysis(db, filters):
    """Renders the player-specific analysis page."""
    st.title("👤 Player Performance Analysis")

    if not filters["seasons"] or not filters["game_types"]:
        st.warning("Please select at least one Season and Game Type in the sidebar.")
        return

    # Player search
    player_name_search = st.text_input("Search for a player by name:")

    if player_name_search:
        try:
            players_df = db.search_players(player_name_search)
        except Exception as e:
            st.error(f"Error searching for players: {e}")
            return

        if players_df.empty:
            st.warning(f"No players found matching: {player_name_search}")
        else:
            # Create selection options
            player_options = {
                f"{row['full_name']} ({row['position_type']}, ID: {row['player_id']})": row['player_id']
                for _, row in players_df.iterrows()
            }
            selected_player_label = st.selectbox("Select player:", player_options.keys())

            if selected_player_label:
                player_id = player_options[selected_player_label]
                player_info = players_df[players_df['player_id'] == player_id].iloc[0]
                position_type = player_info['position_type']

                # Display player info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader(player_info['full_name'])
                    st.write(f"Position: {player_info['position']} ({position_type})")
                with col2:
                    if pd.notna(player_info['height']): st.write(f"Height: {player_info['height']}")
                    if pd.notna(player_info['weight']): st.write(f"Weight: {player_info['weight']} lbs")
                with col3:
                    if pd.notna(player_info['nationality']): st.write(f"Nationality: {player_info['nationality']}")
                    if pd.notna(player_info['birth_date']): st.write(f"Birth Date: {player_info['birth_date']}")

                st.divider()

                # Fetch player logs
                logs_df = fetch_player_logs(db, player_id, position_type, filters["seasons"], filters["game_types"])

                if logs_df.empty:
                    st.warning("No game logs found for this player with the selected filters.")
                    return

                # --- Goalie Specific Analysis ---
                if position_type == 'G':
                    st.subheader("Performance Over Time (Goalie)")
                    fig_g1 = px.line(logs_df, x='game_date', y='save_percentage', title="Save Percentage by Game")
                    if len(logs_df) >= 5:
                        logs_df['rolling_save_pct'] = logs_df['save_percentage'].rolling(window=5, min_periods=1).mean()
                        fig_g1.add_scatter(x=logs_df['game_date'], y=logs_df['rolling_save_pct'], mode='lines', name='5-game Avg', line=dict(color='red', width=2))
                    st.plotly_chart(fig_g1, use_container_width=True)

                    st.subheader("Back-to-Back vs. Rested Performance (Goalie)")
                    logs_df['is_back_to_back'] = logs_df['back_to_back'].astype(bool) # Ensure boolean
                    b2b_stats_g = logs_df.groupby('is_back_to_back').agg(
                        avg_save_pct=('save_percentage', 'mean'),
                        avg_goals_against=('goals_against', 'mean'),
                        games=('game_id', 'count')
                    ).reset_index().rename(columns={'is_back_to_back': 'Back-to-Back Game'})
                    b2b_stats_g['Back-to-Back Game'] = b2b_stats_g['Back-to-Back Game'].map({False: 'Rested', True: 'B2B'})

                    if len(b2b_stats_g) > 1:
                        fig_g2 = make_subplots(rows=1, cols=2, subplot_titles=("Save Percentage", "Goals Against"))
                        fig_g2.add_trace(go.Bar(x=b2b_stats_g['Back-to-Back Game'], y=b2b_stats_g['avg_save_pct'], text=b2b_stats_g['avg_save_pct'].round(3), name='Avg Save %'), row=1, col=1)
                        fig_g2.add_trace(go.Bar(x=b2b_stats_g['Back-to-Back Game'], y=b2b_stats_g['avg_goals_against'], text=b2b_stats_g['avg_goals_against'].round(2), name='Avg GA'), row=1, col=2)
                        fig_g2.update_layout(title_text="Performance: Back-to-Back vs. Rested")
                        fig_g2.update_traces(texttemplate='%{text}', textposition='outside')
                        st.plotly_chart(fig_g2, use_container_width=True)
                        # Add significance test
                        rested_g = logs_df[logs_df['back_to_back'] == False]['save_percentage'].dropna()
                        b2b_g = logs_df[logs_df['back_to_back'] == True]['save_percentage'].dropna()
                        if len(rested_g) >= 2 and len(b2b_g) >= 2:
                            t_stat_g, p_value_g = stats.ttest_ind(rested_g, b2b_g, equal_var=False)
                            st.write(f"T-test (Save %): p-value = {p_value_g:.3f} {'(Significant)' if p_value_g < 0.05 else '(Not Significant)'}")

                # --- Skater Specific Analysis ---
                else: # D or F
                    st.subheader("Performance Over Time (Skater)")
                    fig_s1 = px.line(logs_df, x='game_date', y=['goals', 'assists', 'points'], title="Points by Game")
                    st.plotly_chart(fig_s1, use_container_width=True)

                    fig_s2 = px.line(logs_df, x='game_date', y='time_on_ice_mins', title="Ice Time by Game")
                    if len(logs_df) >= 5:
                        logs_df['rolling_toi'] = logs_df['time_on_ice_mins'].rolling(window=5, min_periods=1).mean()
                        fig_s2.add_scatter(x=logs_df['game_date'], y=logs_df['rolling_toi'], mode='lines', name='5-game Avg', line=dict(color='red', width=2))
                    st.plotly_chart(fig_s2, use_container_width=True)

                    st.subheader("Back-to-Back vs. Rested Performance (Skater)")
                    logs_df['is_back_to_back'] = logs_df['back_to_back'].astype(bool) # Ensure boolean
                    b2b_stats_s = logs_df.groupby('is_back_to_back').agg(
                        avg_points=('points', 'mean'),
                        avg_shots=('shots', 'mean'),
                        avg_toi=('time_on_ice_mins', 'mean'),
                        games=('game_id', 'count')
                    ).reset_index().rename(columns={'is_back_to_back': 'Back-to-Back Game'})
                    b2b_stats_s['Back-to-Back Game'] = b2b_stats_s['Back-to-Back Game'].map({False: 'Rested', True: 'B2B'})

                    if len(b2b_stats_s) > 1:
                        fig_s3 = make_subplots(rows=1, cols=3, subplot_titles=("Points", "Shots", "Time on Ice"))
                        fig_s3.add_trace(go.Bar(x=b2b_stats_s['Back-to-Back Game'], y=b2b_stats_s['avg_points'], text=b2b_stats_s['avg_points'].round(2), name='Avg Points'), row=1, col=1)
                        fig_s3.add_trace(go.Bar(x=b2b_stats_s['Back-to-Back Game'], y=b2b_stats_s['avg_shots'], text=b2b_stats_s['avg_shots'].round(2), name='Avg Shots'), row=1, col=2)
                        fig_s3.add_trace(go.Bar(x=b2b_stats_s['Back-to-Back Game'], y=b2b_stats_s['avg_toi'], text=b2b_stats_s['avg_toi'].round(1), name='Avg TOI'), row=1, col=3)
                        fig_s3.update_layout(title_text="Performance: Back-to-Back vs. Rested")
                        fig_s3.update_traces(texttemplate='%{text}', textposition='outside')
                        st.plotly_chart(fig_s3, use_container_width=True)
                        # Add significance test
                        rested_s = logs_df[logs_df['back_to_back'] == False]['points'].dropna()
                        b2b_s = logs_df[logs_df['back_to_back'] == True]['points'].dropna()
                        if len(rested_s) >= 2 and len(b2b_s) >= 2:
                            t_stat_s, p_value_s = stats.ttest_ind(rested_s, b2b_s, equal_var=False)
                            st.write(f"T-test (Points): p-value = {p_value_s:.3f} {'(Significant)' if p_value_s < 0.05 else '(Not Significant)'}")

                # --- Common Analysis (Goalie & Skater) ---
                st.divider()
                st.subheader("Game Logs")
                # Select columns to display - adjust as needed
                display_cols = [
                    'game_date', 'team_name', 'opponent_name', 'home_away',
                    'decision', 'save_percentage', 'goals_against', # Goalie
                    'points', 'goals', 'assists', 'shots', 'time_on_ice_mins', # Skater
                    'back_to_back', 'travel_distance', 'days_since_last_game'
                ]
                display_cols = [col for col in display_cols if col in logs_df.columns] # Keep only existing columns
                st.dataframe(logs_df[display_cols].sort_values('game_date', ascending=False), use_container_width=True)

    else:
        st.info("Enter a player name above to analyze their performance.")

# --- Main Application Logic ---
def main():
    """Runs the Streamlit application."""
    inject_custom_css() # Inject CSS styles
    db, available_seasons = get_db_connection_and_seasons()
    filters = sidebar_nav(available_seasons)

    # Render selected page
    if filters["nav"] == "Overview":
        render_overview(db, filters)
    elif filters["nav"] == "Player Analysis":
        render_player_analysis(db, filters)
    elif filters["nav"] == "Back-to-Back Analysis":
        render_b2b_analysis(db, filters)
    elif filters["nav"] == "Playoff vs Regular Season":
        render_playoff_analysis(db, filters)
    elif filters["nav"] == "Travel Impact":
        render_travel_analysis(db, filters) # Call the new function
    # Add placeholders or implementations for other pages
    elif filters["nav"] == "Goalie Deep Dive":
        st.title("🥅 Goalie Deep Dive Analysis")
        st.info("This section is under development. Use 'Player Analysis' and search for a goalie.")
    elif filters["nav"] == "Custom Query":
        st.title("🔍 Custom Database Query")
        st.warning("Direct query execution is not yet implemented.")
        # Potentially add a text area for SQL and execute using db.execute_query
        # query = st.text_area("Enter SQL Query:")
        # if st.button("Run Query"):
        #     if query:
        #         try:
        #             result_df = db.execute_query(query)
        #             st.dataframe(result_df)
        #         except Exception as e:
        #             st.error(f"Query failed: {e}")
        #     else:
        #         st.warning("Please enter a query.")

if __name__ == "__main__":
    logger.info("Starting Streamlit Dashboard...")
    main()
