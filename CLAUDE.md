# CLAUDE.md - AI Assistant Context for Kopitar Project

## Project Overview
**Project Name**: Kopitar - NHL Goaltender Fatigue Analysis System  
**Objective**: Analyze NHL goaltender performance degradation due to fatigue factors including back-to-back games, travel distance, schedule density, and recovery time.

## Key Project Goals
1. **Quantify Fatigue Impact**: Establish statistical relationships between workload/travel and goaltender performance metrics
2. **Predictive Modeling**: Build ML models to predict goalie performance based on fatigue indicators
3. **Optimization Insights**: Provide actionable recommendations for goalie rotation and rest strategies
4. **Real-time Analysis**: Create dashboard for live tracking of goalie fatigue levels across the league

## Team Structure (6 Specialists)
1. **Data Engineer** (Alex): API integration, ETL pipelines, data quality
2. **Data Scientist** (Maria): Statistical analysis, ML models, feature engineering  
3. **Sports Analytics Specialist** (Jordan): Domain expertise, metric validation, hypothesis testing
4. **Backend Developer** (Chen): Database architecture, API development, system integration
5. **Frontend Developer** (Sarah): Dashboard UI/UX, data visualization, interactive reports
6. **DevOps Engineer** (Raj): Infrastructure, deployment, monitoring, performance optimization

## Technical Stack
- **Languages**: Python 3.11+, TypeScript, SQL
- **Data Pipeline**: Apache Airflow, Pandas, NumPy
- **Database**: PostgreSQL (primary), Redis (caching), InfluxDB (time-series)
- **ML/Stats**: Scikit-learn, StatsModels, XGBoost, PyTorch
- **API Framework**: FastAPI, Pydantic
- **Frontend**: React, D3.js, Plotly Dash
- **Infrastructure**: Docker, Kubernetes, AWS/GCP
- **Monitoring**: Prometheus, Grafana, Sentry

## Critical Domain Knowledge

### Goaltender-Specific Factors
- **Starter vs Backup**: Different fatigue patterns and expectations
- **Playing Style**: Butterfly vs hybrid affects energy expenditure
- **Age Curves**: Recovery time increases with age (typically 2-3% per year after 30)
- **Injury History**: Previous injuries affect fatigue resistance

### NHL Schedule Nuances
- **Back-to-Back Games**: ~13-15 per team per season
- **Three-in-Four Nights**: High fatigue scenario
- **Circus Trips**: Extended road trips during events
- **Time Zones**: East/West travel has asymmetric effects
- **Division Play**: More frequent travel to same cities

### Performance Metrics Hierarchy
1. **Primary**: Save %, GAA, GSAx (Goals Saved Above Expected)
2. **Secondary**: QS%, RBS%, HDSV% (High Danger Save %)
3. **Advanced**: Rebound control, lateral movement efficiency
4. **Workload**: Shots faced, minutes played, games started

## Key Algorithms & Models

### Fatigue Index Calculation
```python
Fatigue_Index = w1*(Games_Last_7d) + w2*(Minutes_Last_10d) + 
                w3*(Travel_Miles_Last_5d) + w4*(Timezone_Changes) + 
                w5*(Consecutive_Games) + w6*(Shot_Volume)
# Weights determined through regression analysis
```

### Performance Prediction Model
- **Features**: Fatigue index, opponent strength, home/away, rest days, altitude change
- **Target**: Next game save percentage
- **Model Types**: Random Forest, XGBoost, Neural Network ensemble

### Travel Impact Algorithm
- Calculate great circle distance between arenas
- Estimate flight time (distance/500mph + 2hr buffer)
- Account for timezone changes (1.5x penalty for eastward travel)
- Consider arrival time (night before vs game day)

## Data Sources & APIs

### Primary Sources
1. **NHL Stats API**: `https://statsapi.web.nhl.com/api/v1/`
   - No auth required, rate limit: 100 req/min
   - Endpoints: /teams, /people, /schedule, /game

2. **Supporting Data**:
   - Arena coordinates (hardcoded, verified)
   - Flight schedules (estimated)
   - Practice schedules (team websites)

### Data Update Frequency
- **Game Data**: Real-time during games, final stats within 1 hour
- **Schedule**: Daily updates at 6 AM ET
- **Travel Calculations**: Pre-computed weekly
- **Model Retraining**: Weekly with rolling 2-season window

## Important Caveats & Edge Cases

### Data Quality Issues
- **Emergency Recalls**: Backup goalies may have AHL travel not tracked
- **Injured Reserve**: Games missed due to injury vs rest
- **Tandem Systems**: Some teams rotate goalies equally
- **Playoff Differences**: Compressed schedule, higher intensity

### Statistical Considerations
- **Sample Size**: Backup goalies may have <20 games/season
- **Survivorship Bias**: Poor performing goalies get benched
- **Score Effects**: Trailing teams pull goalies, affecting GAA
- **Strength of Schedule**: Must adjust for opponent quality

## Code Style Guidelines
- **Python**: PEP 8, type hints required, docstrings for all functions
- **SQL**: Uppercase keywords, meaningful table aliases
- **Git**: Conventional commits, PR requires 2 reviews
- **Testing**: Minimum 80% coverage, integration tests required

## Security & Privacy
- No PII collected (only public performance data)
- API keys in environment variables
- Rate limiting on all endpoints
- Data retention: 3 seasons rolling window

## Performance Requirements
- Dashboard load time: <2 seconds
- API response time: <200ms for cached, <1s for computed
- Model inference: <50ms per prediction
- Data pipeline: Complete daily update in <30 minutes

## Common Commands
```bash
# Run data pipeline
python -m kopitar.pipeline.daily_update

# Start API server
uvicorn kopitar.api.main:app --reload

# Run tests
pytest tests/ --cov=kopitar --cov-report=html

# Update model
python -m kopitar.models.train --model fatigue_predictor

# Generate reports
python -m kopitar.reports.weekly_analysis
```

## Debugging Tips
1. **Missing Games**: Check if game was postponed/rescheduled
2. **Anomalous Stats**: Verify goalie didn't leave game early (injury)
3. **Travel Calculations**: Some teams have practice facilities != arena
4. **Performance Spikes**: Check for scoring changes/corrections

## Future Enhancements
- Real-time fatigue alerts during games
- Integration with sports betting APIs
- Biomechanical data from player tracking
- Social media sentiment analysis
- Weather data for travel impact

## Key Decisions Made
1. **PostgreSQL over MongoDB**: Better for time-series queries
2. **Fatigue window**: 10 days chosen based on literature
3. **Travel threshold**: 200 miles for bus vs flight
4. **Model update frequency**: Weekly to balance accuracy/stability

## Success Metrics
- Model accuracy: >75% for performance prediction
- Dashboard adoption: Used by 10+ NHL teams
- API reliability: 99.9% uptime
- Research impact: Published findings in sports analytics conference