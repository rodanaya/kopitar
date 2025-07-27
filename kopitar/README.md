# NHL Goaltender Performance Analysis

This project analyzes how NHL goaltenders perform in various conditions, with a focus on:
- Back-to-back games
- High-workload periods
- Travel impact (distance, time zones, direction)

## Project Structure

- `/data`: Raw and processed data files
- `/analysis`: Python scripts for data analysis
- `/notebooks`: Jupyter notebooks for exploration and visualization
- `/utils`: Helper functions for API access, data processing, etc.

## Features Analyzed

- **Goaltender Metrics**: Save percentage (SV%), goals against average (GAA), high-danger saves
- **Workload Variables**: Days between games, games played in last 7/14 days
- **Travel Factors**: Distance traveled, timezone changes, travel direction
- **Game Context**: Home/away, opponent strength, back-to-back status

## Data Sources

- NHL Official API
- Hockey Reference / MoneyPuck (advanced stats)
- Geographical data for NHL cities

## Requirements

See `requirements.txt` for all dependencies.

## Getting Started

1. Install the required packages:

```
pip install -r requirements.txt
```

2. Collect the data for a specific season:

```
python analysis/data_collection.py --season 20222023 --output_dir data
```

3. Run the analysis script:

```
python analysis/goalie_performance_analysis.py --data_file data/goalie_analysis_dataset_20222023.csv --output_dir notebooks/figures
```

4. For interactive analysis, open the Jupyter notebook:

```
jupyter notebook notebooks/goalie_analysis.py
```

## Analysis Workflow

1. **Data Collection**: Gather game-by-game stats for all goalies using the NHL API
2. **Feature Engineering**: Calculate rest days, travel metrics, workload variables
3. **Exploratory Analysis**: Visualize performance by various conditions
4. **Statistical Testing**: Identify significant factors affecting performance
5. **Regression Modeling**: Quantify the impact of each factor

## Key Questions Addressed

1. How does save percentage change in back-to-back games?
2. What is the impact of long-distance travel on performance?
3. Is there a relationship between workload (games played recently) and performance?
4. Which goalies perform best in high-workload situations?
5. Can we predict goalie performance based on rest and travel factors? 