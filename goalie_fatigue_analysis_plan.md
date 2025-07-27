# NHL Goaltender Fatigue Analysis Project

## 1. Data Sources & APIs

### Primary NHL Data Sources:
- **NHL API (Unofficial)**: `https://statsapi.web.nhl.com/api/v1/`
  - Game data, player stats, schedule information
  - Real-time and historical data
  - No authentication required
  
- **NHL Stats API Endpoints**:
  - `/teams` - Team information and rosters
  - `/people/{id}/stats` - Player statistics
  - `/schedule` - Game schedules with dates/times
  - `/game/{id}/feed/live` - Detailed game data

- **Alternative Sources**:
  - **hockey-reference.com**: Web scraping for advanced stats
  - **naturalstattrick.com**: Advanced analytics
  - **moneypuck.com**: Expected goals data

## 2. Key Goaltender Metrics

### Core Performance Metrics:
- **Save Percentage (SV%)**: Shots saved / Total shots faced
- **Goals Against Average (GAA)**: (Goals against × 60) / Minutes played
- **Quality Start (QS)**: SV% > .917 or saves > league average
- **Really Bad Start (RBS)**: SV% < .850
- **Goals Saved Above Expected (GSAx)**: Actual saves - Expected saves

### Advanced Metrics:
- **High Danger Save Percentage**: Saves on high-danger chances
- **Rebound Control**: Secondary shot attempts allowed
- **Puck Freezing Rate**: Faceoffs forced vs shots faced
- **Cross-crease Save Rate**: Lateral movement effectiveness

### Fatigue Indicators:
- **Games in Last X Days**: 3, 5, 7, 10-day windows
- **Back-to-Back Games**: Performance in consecutive nights
- **Three-in-Four**: Three games in four nights
- **Minutes Played**: Recent workload
- **Shots Faced per Game**: Work intensity

## 3. Travel & Recovery Variables

### Travel Calculations:
```python
# Key factors to calculate:
- Distance between arenas (great circle distance)
- Time zone changes
- Travel time estimation:
  - Flight time (distance/500mph + 2hr buffer)
  - Bus trips for close cities (<200 miles)
- Direction of travel (east/west impacts)
```

### Recovery Time Factors:
- **Arrival Time**: Night before vs game day
- **Practice Schedule**: Morning skate participation
- **Consecutive Road Games**: Hotel stays vs home
- **Altitude Changes**: Impact on performance

## 4. Additional Variables to Consider

### Team Factors:
- **Defensive Quality**: Team's shots against/game
- **Penalty Kill Workload**: Short-handed minutes
- **Score Effects**: Leading vs trailing impacts
- **Backup Quality**: Pressure to play injured

### Game Context:
- **Opponent Strength**: Goals for/game
- **Game Importance**: Playoff race implications
- **Day of Week**: Weekend vs weekday
- **Month of Season**: Fatigue accumulation

### Physiological Factors:
- **Age**: Recovery time differences
- **Injury History**: Previous workload tolerance
- **Career Games Played**: Cumulative fatigue
- **Playing Style**: Athletic vs positional

## 5. Project Architecture

### Data Pipeline:
```python
# Recommended structure:
project/
├── data_collection/
│   ├── nhl_api_client.py
│   ├── travel_calculator.py
│   └── schedule_scraper.py
├── database/
│   ├── models.py
│   └── db_manager.py
├── analysis/
│   ├── fatigue_metrics.py
│   ├── performance_analyzer.py
│   └── visualization.py
└── notebooks/
    └── exploratory_analysis.ipynb
```

### Technology Stack:
- **Data Collection**: `requests`, `beautifulsoup4`
- **Data Storage**: `sqlite3` or `PostgreSQL`
- **Analysis**: `pandas`, `numpy`, `scipy`
- **Visualization**: `matplotlib`, `seaborn`, `plotly`
- **Machine Learning**: `scikit-learn`, `statsmodels`
- **Geographic**: `geopy`, `haversine`

## 6. Analysis Approach

### Statistical Methods:
1. **Correlation Analysis**: Travel distance vs performance
2. **Regression Models**: Multi-factor performance prediction
3. **Time Series**: Performance trends over season
4. **Clustering**: Identify goalie workload patterns
5. **Survival Analysis**: Time to performance decline

### Key Questions to Answer:
- What's the optimal rest between starts?
- How does travel distance impact save percentage?
- Which goalies handle heavy workloads best?
- Do east/west road trips affect differently?
- What's the cumulative effect of schedule density?

## 7. Implementation Steps

1. **Set up NHL API client** with rate limiting
2. **Build arena location database** with coordinates
3. **Create travel time calculator** using flight data
4. **Design database schema** for all metrics
5. **Implement data collection pipeline**
6. **Develop analysis notebooks**
7. **Create visualization dashboard**
8. **Build predictive models**

## 8. Sample Code Structure

```python
# Example: Goalie workload tracker
class GoalieWorkloadAnalyzer:
    def __init__(self):
        self.games_played = []
        self.travel_distances = []
        self.performance_metrics = {}
    
    def calculate_fatigue_index(self, goalie_id, date):
        recent_games = self.get_recent_games(goalie_id, date, days=7)
        travel_total = self.calculate_travel_distance(recent_games)
        rest_days = self.calculate_rest_days(recent_games)
        
        fatigue_index = (
            (len(recent_games) * 0.3) +
            (travel_total / 1000 * 0.2) +
            ((7 - rest_days) * 0.5)
        )
        return fatigue_index
```