"""
Kopitar - NHL Goaltender Fatigue Dashboard
Single-page Plotly Dash application with 4 fatigue analysis panels.
"""

import os
import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import Dash, dcc, html, Input, Output, callback

# ---------------------------------------------------------------------------
# Optional: dash-bootstrap-components
# ---------------------------------------------------------------------------
try:
    import dash_bootstrap_components as dbc
    _DBC = True
except ImportError:
    _DBC = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "nhl_data_20232024_R_GDF_teams.csv",
)

TOP_GOALIES = [
    "Vasilevskiy", "Shesterkin", "Hellebuyck", "Gibson", "Fleury",
    "Husso", "Sorokin", "Binnington", "Saros", "Kuemper",
    "Markstrom", "Ullmark", "Swayman", "Stolarz", "Wedgewood",
    "Murray", "DeSmith", "Samsonov", "Knight", "Dostal",
]

NHL_TEAMS = [
    "Anaheim Ducks", "Arizona Coyotes", "Boston Bruins", "Buffalo Sabres",
    "Calgary Flames", "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
    "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings", "Edmonton Oilers",
    "Florida Panthers", "Los Angeles Kings", "Minnesota Wild", "Montreal Canadiens",
    "Nashville Predators", "New Jersey Devils", "New York Islanders", "New York Rangers",
    "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins", "San Jose Sharks",
    "Seattle Kraken", "St. Louis Blues", "Tampa Bay Lightning", "Toronto Maple Leafs",
    "Utah Hockey Club", "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals",
    "Winnipeg Jets",
]

# Fatigue colour thresholds
def fatigue_color(val: float) -> str:
    if val <= 20:
        return "#2ecc71"      # green
    elif val <= 40:
        return "#f1c40f"      # yellow
    elif val <= 60:
        return "#e67e22"      # orange
    elif val <= 80:
        return "#e74c3c"      # red
    return "#8e1a0e"          # dark red


# ---------------------------------------------------------------------------
# Data generation / loading
# ---------------------------------------------------------------------------

def generate_demo_data(n: int = 500) -> pd.DataFrame:
    """Generate realistic synthetic goalie game-log data."""
    rng = np.random.default_rng(42)

    goalies = TOP_GOALIES[:10]
    teams = [
        "Tampa Bay Lightning", "New York Rangers", "Winnipeg Jets", "Anaheim Ducks",
        "Vegas Golden Knights", "St. Louis Blues", "New York Islanders", "St. Louis Blues",
        "Nashville Predators", "Colorado Avalanche",
    ]
    goalie_team = dict(zip(goalies, teams))

    records = []
    for _ in range(n):
        goalie = rng.choice(goalies)
        is_b2b = rng.random() < 0.18                  # ~18 % of games are B2B
        fatigue = rng.uniform(10, 90)
        # B2B games trend toward higher fatigue
        if is_b2b:
            fatigue = min(100.0, fatigue + rng.uniform(10, 25))

        # Save % inversely correlated with fatigue + noise
        base_sv = 0.920 - 0.0008 * fatigue + rng.normal(0, 0.012)
        if is_b2b:
            base_sv -= rng.uniform(0.003, 0.015)
        save_pct = float(np.clip(base_sv, 0.840, 0.975))

        records.append(
            {
                "player_name": goalie,
                "team": goalie_team[goalie],
                "game_date": pd.Timestamp("2023-10-01") + pd.Timedelta(days=int(rng.integers(0, 180))),
                "save_percentage": round(save_pct, 4),
                "composite_fatigue_index": round(fatigue, 1),
                "is_back_to_back": int(is_b2b),
                "workload": round(rng.uniform(20, 90), 1),
                "travel": round(rng.uniform(10, 95), 1),
                "schedule_density": round(rng.uniform(15, 85), 1),
                "rest_quality": round(rng.uniform(10, 90), 1),
                "consecutive_games": round(rng.uniform(5, 80), 1),
                "shot_volume": round(rng.uniform(20, 85), 1),
                "position": "G",
            }
        )
    return pd.DataFrame(records)


def load_data() -> pd.DataFrame:
    """Try to load CSV; if columns are missing or file absent, fall back to synthetic data."""
    required = {"player_name", "save_percentage", "composite_fatigue_index", "is_back_to_back"}
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            if required.issubset(set(df.columns)):
                logger.info("Loaded real data from %s (%d rows)", DATA_PATH, len(df))
                return df
            logger.warning("CSV found but missing required columns %s — using synthetic data.", required - set(df.columns))
        except Exception as exc:
            logger.warning("Could not read CSV (%s) — using synthetic data.", exc)
    logger.info("Generating synthetic demo data.")
    return generate_demo_data(500)


def build_team_fatigue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive per-team average composite_fatigue_index for all NHL teams.

    Strategy:
    1. Compute real averages from the goalie game log (df) where available.
    2. Load the full team list from the teams CSV to ensure all 32–33 teams appear.
    3. Fill any teams missing from the game log with seeded synthetic values.
    """
    teams_csv = os.path.join(os.path.dirname(DATA_PATH), "nhl_data_20232024_R_GDF_teams.csv")
    if os.path.exists(teams_csv):
        all_teams = pd.read_csv(teams_csv)["name"].tolist()
    else:
        all_teams = list(NHL_TEAMS)

    # Compute real averages from game log if columns exist
    if "team" in df.columns and "composite_fatigue_index" in df.columns:
        real_avgs = (
            df.groupby("team")["composite_fatigue_index"]
            .mean()
            .rename("avg_fatigue")
        )
    else:
        real_avgs = pd.Series(dtype=float, name="avg_fatigue")

    # Seeded synthetic fill for teams not in game log
    rng = np.random.default_rng(7)
    rows = []
    for team in all_teams:
        if team in real_avgs.index:
            rows.append({"team_name": team, "avg_fatigue": real_avgs[team]})
        else:
            rows.append({"team_name": team, "avg_fatigue": float(rng.uniform(15, 82))})

    team_df = pd.DataFrame(rows)

    team_df["avg_fatigue"] = team_df["avg_fatigue"].round(1)
    team_df = team_df.sort_values("avg_fatigue")
    team_df["color"] = team_df["avg_fatigue"].apply(fatigue_color)
    return team_df


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def build_league_fatigue_chart(team_df: pd.DataFrame) -> go.Figure:
    """Panel 1: horizontal bar chart of all teams by average fatigue index."""
    fig = go.Figure(
        go.Bar(
            x=team_df["avg_fatigue"],
            y=team_df["team_name"],
            orientation="h",
            marker_color=team_df["color"],
            text=team_df["avg_fatigue"].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Avg Fatigue Index: %{x:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        title=dict(text="League-Wide Average Composite Fatigue Index (2023-24)", font_size=15),
        xaxis=dict(title="Composite Fatigue Index (0–100)", range=[0, 105]),
        yaxis=dict(title="", tickfont_size=11),
        height=700,
        margin=dict(l=160, r=60, t=50, b=40),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        font_color="#e0e0e0",
        showlegend=False,
    )
    # Add colour-coded legend annotations
    legend_items = [
        (0, 20, "#2ecc71", "0-20 Rested"),
        (21, 40, "#f1c40f", "21-40 Mild"),
        (41, 60, "#e67e22", "41-60 Moderate"),
        (61, 80, "#e74c3c", "61-80 High"),
        (81, 100, "#8e1a0e", "81-100 Critical"),
    ]
    for i, (_, _, color, label) in enumerate(legend_items):
        fig.add_annotation(
            x=85 + i * 0,
            y=1.04 - i * 0.06,
            xref="paper",
            yref="paper",
            text=f"<span style='color:{color}'>■</span> {label}",
            showarrow=False,
            font=dict(size=11, color=color),
            align="left",
            xanchor="left",
        )
    return fig


def build_radar_chart(df: pd.DataFrame, goalie: str) -> go.Figure:
    """Panel 2: radar chart for a single goalie's 6 fatigue dimensions."""
    dims = ["Workload", "Travel", "Schedule Density", "Rest Quality", "Consecutive Games", "Shot Volume"]
    col_map = {
        "Workload": "workload",
        "Travel": "travel",
        "Schedule Density": "schedule_density",
        "Rest Quality": "rest_quality",
        "Consecutive Games": "consecutive_games",
        "Shot Volume": "shot_volume",
    }

    goalie_rows = df[df["player_name"] == goalie] if "player_name" in df.columns else pd.DataFrame()

    if goalie_rows.empty:
        # Synthesise plausible values per goalie seed
        rng = np.random.default_rng(abs(hash(goalie)) % (2**32))
        values = rng.uniform(20, 85, size=len(dims)).tolist()
    else:
        values = []
        for dim in dims:
            col = col_map[dim]
            if col in goalie_rows.columns:
                values.append(float(goalie_rows[col].mean()))
            else:
                rng = np.random.default_rng(abs(hash(goalie + dim)) % (2**32))
                values.append(float(rng.uniform(20, 85)))

    # Close the radar polygon
    theta = dims + [dims[0]]
    r = values + [values[0]]

    fig = go.Figure(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            fillcolor="rgba(231, 76, 60, 0.25)",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=6, color="#e74c3c"),
            name=goalie,
            hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont_size=9,
                gridcolor="#444",
                linecolor="#666",
            ),
            angularaxis=dict(
                tickfont_size=11,
                gridcolor="#444",
                linecolor="#666",
            ),
        ),
        title=dict(text=f"Fatigue Dimensions — {goalie} (2023-24)", font_size=14),
        height=420,
        margin=dict(l=60, r=60, t=60, b=40),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        font_color="#e0e0e0",
        showlegend=False,
    )
    return fig


def build_scatter_chart(df: pd.DataFrame) -> go.Figure:
    """Panel 3: scatter of Save% vs Fatigue Index with trend line."""
    required = {"composite_fatigue_index", "save_percentage"}
    if not required.issubset(df.columns):
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No data available")
        return fig

    plot_df = df[list(required | {"player_name", "team", "game_date"})].dropna(
        subset=list(required)
    ).copy()

    # Trend line via polyfit
    x_vals = plot_df["composite_fatigue_index"].values
    y_vals = plot_df["save_percentage"].values
    m, b = np.polyfit(x_vals, y_vals, 1)
    x_range = np.linspace(x_vals.min(), x_vals.max(), 100)
    y_trend = m * x_range + b

    hover_text = []
    for _, row in plot_df.iterrows():
        name = row.get("player_name", "Unknown")
        team = row.get("team", "")
        date = str(row.get("game_date", ""))[:10]
        hover_text.append(f"<b>{name}</b><br>{team}<br>{date}<br>Save%: {row['save_percentage']:.3f}<br>Fatigue: {row['composite_fatigue_index']:.1f}")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot_df["composite_fatigue_index"],
            y=plot_df["save_percentage"],
            mode="markers",
            marker=dict(
                color="#3498db",
                size=7,
                opacity=0.65,
                line=dict(width=0.5, color="#1a6fa8"),
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
            name="Game (G)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=y_trend,
            mode="lines",
            line=dict(color="#e74c3c", width=2, dash="dash"),
            name="Trend",
            hoverinfo="skip",
        )
    )

    slope_dir = "negative" if m < 0 else "positive"
    annotation_text = (
        f"Trend: {m:.5f}x + {b:.3f}<br>"
        f"({'Save% decreases' if slope_dir == 'negative' else 'Save% increases'} with fatigue)"
    )

    fig.update_layout(
        template="plotly_dark",
        title=dict(text="Save% vs Composite Fatigue Index (per game)", font_size=14),
        xaxis=dict(title="Composite Fatigue Index (0-100)", range=[0, 102]),
        yaxis=dict(title="Save Percentage", tickformat=".3f", range=[0.840, 0.980]),
        height=420,
        margin=dict(l=60, r=40, t=60, b=50),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        font_color="#e0e0e0",
        legend=dict(x=0.01, y=0.05),
        annotations=[
            dict(
                x=0.98, y=0.97,
                xref="paper", yref="paper",
                text=annotation_text,
                showarrow=False,
                font=dict(size=11, color="#e74c3c"),
                align="right",
                bgcolor="rgba(22,33,62,0.8)",
                bordercolor="#e74c3c",
                borderwidth=1,
            )
        ],
    )
    return fig


def build_b2b_boxplot(df: pd.DataFrame) -> go.Figure:
    """Panel 4: box plot comparing rested vs B2B save% for top goalies, sorted by drop."""
    required = {"player_name", "save_percentage", "is_back_to_back"}
    if not required.issubset(df.columns):
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No data available")
        return fig

    # Use only goalies that appear in TOP_GOALIES (or first 20 by count)
    goalie_counts = df["player_name"].value_counts()
    plot_goalies = [g for g in TOP_GOALIES if g in goalie_counts.index]
    if not plot_goalies:
        plot_goalies = goalie_counts.head(20).index.tolist()

    goalie_df = df[df["player_name"].isin(plot_goalies)].copy()
    goalie_df["is_back_to_back"] = goalie_df["is_back_to_back"].astype(int)

    # Compute per-goalie mean for sorting
    rested_means = (
        goalie_df[goalie_df["is_back_to_back"] == 0]
        .groupby("player_name")["save_percentage"]
        .mean()
        .rename("rested_mean")
    )
    b2b_means = (
        goalie_df[goalie_df["is_back_to_back"] == 1]
        .groupby("player_name")["save_percentage"]
        .mean()
        .rename("b2b_mean")
    )
    comparison = pd.concat([rested_means, b2b_means], axis=1).dropna()
    comparison["drop"] = comparison["rested_mean"] - comparison["b2b_mean"]
    comparison = comparison.sort_values("drop", ascending=False)
    sorted_goalies = comparison.index.tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Box(
            x=[g for g in sorted_goalies for _ in goalie_df[(goalie_df["player_name"] == g) & (goalie_df["is_back_to_back"] == 0)]["save_percentage"]],
            y=[v for g in sorted_goalies for v in goalie_df[(goalie_df["player_name"] == g) & (goalie_df["is_back_to_back"] == 0)]["save_percentage"]],
            name="Rested",
            marker_color="#5dade2",
            boxmean=True,
            hovertemplate="<b>%{x}</b><br>Rested Save%%: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Box(
            x=[g for g in sorted_goalies for _ in goalie_df[(goalie_df["player_name"] == g) & (goalie_df["is_back_to_back"] == 1)]["save_percentage"]],
            y=[v for g in sorted_goalies for v in goalie_df[(goalie_df["player_name"] == g) & (goalie_df["is_back_to_back"] == 1)]["save_percentage"]],
            name="Back-to-Back",
            marker_color="#e67e22",
            boxmean=True,
            hovertemplate="<b>%{x}</b><br>B2B Save%%: %{y:.3f}<extra></extra>",
        )
    )

    # Annotate drops
    for goalie in sorted_goalies:
        if goalie in comparison.index:
            drop = comparison.loc[goalie, "drop"]
            fig.add_annotation(
                x=goalie,
                y=0.843,
                text=f"-{drop:.3f}" if drop > 0 else f"+{abs(drop):.3f}",
                showarrow=False,
                font=dict(size=9, color="#e74c3c" if drop > 0 else "#2ecc71"),
                yref="y",
            )

    fig.update_layout(
        template="plotly_dark",
        title=dict(text="Save% Distribution: Rested vs Back-to-Back Games (sorted by performance drop)", font_size=14),
        xaxis=dict(title="Goalie", tickangle=-30, tickfont_size=11),
        yaxis=dict(title="Save Percentage", tickformat=".3f", range=[0.835, 0.985]),
        height=480,
        margin=dict(l=60, r=40, t=60, b=100),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        font_color="#e0e0e0",
        boxmode="group",
        legend=dict(x=0.01, y=0.99),
    )
    return fig


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

def build_layout(df: pd.DataFrame, team_df: pd.DataFrame) -> html.Div:
    goalie_options = [{"label": g, "value": g} for g in TOP_GOALIES]
    default_goalie = TOP_GOALIES[0]

    # Dark theme card style (fallback when dbc isn't used for cards)
    card_style = {
        "backgroundColor": "#16213e",
        "borderRadius": "8px",
        "padding": "16px",
        "marginBottom": "20px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.5)",
    }

    header = html.Div(
        [
            html.H1(
                "Kopitar — NHL Goaltender Fatigue Dashboard",
                style={
                    "textAlign": "center",
                    "color": "#e0e0e0",
                    "fontFamily": "Helvetica Neue, Arial, sans-serif",
                    "fontSize": "1.8rem",
                    "marginBottom": "4px",
                    "paddingTop": "16px",
                    "letterSpacing": "0.03em",
                },
            ),
            html.P(
                "2023-24 Regular Season  |  Composite Fatigue Analysis",
                style={"textAlign": "center", "color": "#a0a0b0", "marginTop": "0", "fontSize": "0.95rem"},
            ),
        ],
        style={"backgroundColor": "#0f3460", "paddingBottom": "12px", "marginBottom": "24px"},
    )

    # ---- Panel 1 ----
    panel1 = html.Div(
        [
            html.H3("League Fatigue Overview", style={"color": "#5dade2", "marginTop": 0, "fontSize": "1.05rem"}),
            dcc.Graph(id="chart-league-fatigue", figure=build_league_fatigue_chart(team_df), config={"displayModeBar": False}),
        ],
        style=card_style,
    )

    # ---- Panel 2 + 3 side by side ----
    panel2 = html.Div(
        [
            html.H3("Goalie Fatigue Radar", style={"color": "#5dade2", "marginTop": 0, "fontSize": "1.05rem"}),
            dcc.Dropdown(
                id="goalie-dropdown",
                options=goalie_options,
                value=default_goalie,
                clearable=False,
                style={"marginBottom": "12px", "backgroundColor": "#1a1a2e", "color": "#e0e0e0"},
                className="dash-dropdown-dark",
            ),
            dcc.Graph(id="chart-radar", figure=build_radar_chart(df, default_goalie), config={"displayModeBar": False}),
        ],
        style={**card_style, "flex": "1", "minWidth": "0"},
    )

    panel3 = html.Div(
        [
            html.H3("Save% vs Fatigue Index", style={"color": "#5dade2", "marginTop": 0, "fontSize": "1.05rem"}),
            dcc.Graph(id="chart-scatter", figure=build_scatter_chart(df), config={"displayModeBar": False}),
        ],
        style={**card_style, "flex": "1", "minWidth": "0"},
    )

    middle_row = html.Div(
        [panel2, panel3],
        style={"display": "flex", "gap": "20px", "marginBottom": "0"},
    )

    # ---- Panel 4 ----
    panel4 = html.Div(
        [
            html.H3("Back-to-Back Performance Drop", style={"color": "#5dade2", "marginTop": 0, "fontSize": "1.05rem"}),
            dcc.Graph(id="chart-b2b", figure=build_b2b_boxplot(df), config={"displayModeBar": False}),
        ],
        style=card_style,
    )

    layout = html.Div(
        [
            header,
            html.Div(
                [panel1, middle_row, panel4],
                style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 20px 40px"},
            ),
        ],
        style={"backgroundColor": "#1a1a2e", "minHeight": "100vh"},
    )
    return layout


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

# Load data at module level (needed before layout is built)
_df = load_data()
_team_df = build_team_fatigue(_df)

external_stylesheets = [dbc.themes.DARKLY] if _DBC else []
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
app.title = "Kopitar — NHL Goaltender Fatigue Dashboard"
app.layout = build_layout(_df, _team_df)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("chart-radar", "figure"),
    Input("goalie-dropdown", "value"),
)
def update_radar(selected_goalie: str) -> go.Figure:
    if not selected_goalie:
        return go.Figure()
    return build_radar_chart(_df, selected_goalie)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Kopitar Fatigue Dashboard on http://localhost:8050")
    app.run(debug=True, port=8050)
