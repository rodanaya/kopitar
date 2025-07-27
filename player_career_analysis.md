# Player Career Analysis - Longitudinal Fatigue Studies

## Overview
**Objective**: Conduct comprehensive longitudinal analysis of goaltender careers to understand fatigue accumulation, performance evolution, and career sustainability patterns across entire NHL careers.

**Scope**:
- **Career Spans**: Full career trajectories from debut to retirement
- **Timeframe**: 1980-2024 (40+ years of career data)
- **Players**: 1,200+ unique goaltenders
- **Career Games**: 500,000+ individual game performances
- **Analysis Depth**: Season-by-season, monthly, and game-by-game patterns

---

## Career Stage Framework

### Career Development Phases

```python
CAREER_PHASES = {
    "development": {
        "age_range": (18, 23),
        "nhl_experience": "0-2 seasons",
        "characteristics": [
            "Learning NHL pace",
            "Inconsistent performance",
            "High energy, quick recovery",
            "Limited game management"
        ],
        "fatigue_pattern": "Low baseline, high variance"
    },
    
    "emerging": {
        "age_range": (23, 26),
        "nhl_experience": "2-5 seasons",
        "characteristics": [
            "Establishing role",
            "Improved consistency",
            "Learning workload management",
            "Peak physical condition"
        ],
        "fatigue_pattern": "Moderate baseline, decreasing variance"
    },
    
    "prime": {
        "age_range": (26, 32),
        "nhl_experience": "5-12 seasons",
        "characteristics": [
            "Peak performance years",
            "Optimal experience-energy balance",
            "Sophisticated game management",
            "Leadership responsibilities"
        ],
        "fatigue_pattern": "Optimal baseline, controlled variance"
    },
    
    "veteran": {
        "age_range": (32, 37),
        "nhl_experience": "12-18 seasons",
        "characteristics": [
            "Experience compensates for physical decline",
            "Strategic rest management",
            "Mentorship role",
            "Injury management"
        ],
        "fatigue_pattern": "Elevated baseline, managed variance"
    },
    
    "twilight": {
        "age_range": (37, 45),
        "nhl_experience": "18+ seasons",
        "characteristics": [
            "Physical limitations increase",
            "Reduced workload tolerance",
            "Legacy preservation",
            "Selective competition"
        ],
        "fatigue_pattern": "High baseline, increasing variance"
    }
}
```

### Career Trajectory Modeling

```python
class CareerTrajectoryAnalyzer:
    def __init__(self):
        self.performance_metrics = [
            'save_percentage', 'goals_against_average', 'games_started',
            'quality_starts_pct', 'really_bad_starts_pct', 'fatigue_resistance'
        ]
        
    def model_career_trajectory(self, player_id: int):
        """
        Model complete career trajectory with fatigue analysis
        """
        career_data = self.load_career_data(player_id)
        
        trajectory = {
            'performance_curve': self.fit_performance_curve(career_data),
            'fatigue_evolution': self.analyze_fatigue_progression(career_data),
            'workload_tolerance': self.calculate_workload_capacity(career_data),
            'peak_identification': self.identify_peak_periods(career_data),
            'decline_analysis': self.analyze_performance_decline(career_data),
            'longevity_factors': self.identify_longevity_factors(career_data)
        }
        
        return trajectory
        
    def fit_performance_curve(self, career_data: pd.DataFrame):
        """
        Fit polynomial curve to career performance
        """
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        
        # Use career year as primary feature
        X = career_data[['career_year', 'age', 'cumulative_games']]
        y = career_data['save_percentage']
        
        # Polynomial features for curve fitting
        poly_features = PolynomialFeatures(degree=3)
        X_poly = poly_features.fit_transform(X)
        
        # Fit model
        model = LinearRegression()
        model.fit(X_poly, y)
        
        # Generate predictions for smooth curve
        career_years = range(1, max(career_data['career_year']) + 1)
        predictions = []
        
        for year in career_years:
            age = career_data[career_data['career_year'] == year]['age'].iloc[0] if year <= len(career_data) else None
            if age:
                pred_input = poly_features.transform([[year, age, year * 40]])
                prediction = model.predict(pred_input)[0]
                predictions.append(prediction)
                
        return {
            'model': model,
            'predictions': predictions,
            'career_years': career_years,
            'r_squared': model.score(X_poly, y)
        }
```

---

## Fatigue Accumulation Analysis

### Cumulative Fatigue Modeling

```python
class CumulativeFatigueAnalyzer:
    def __init__(self):
        self.fatigue_components = {
            'game_load': 0.3,      # Games played weight
            'minute_load': 0.25,   # Minutes played weight  
            'intensity_load': 0.2, # Shot volume and difficulty
            'travel_load': 0.15,   # Travel distance and frequency
            'recovery_deficit': 0.1 # Insufficient rest periods
        }
        
    def calculate_season_fatigue_load(self, season_data: pd.DataFrame):
        """
        Calculate cumulative fatigue load for a season
        """
        # Progressive fatigue accumulation
        season_data = season_data.sort_values('game_date')
        
        cumulative_fatigue = []
        carry_over_fatigue = 0
        
        for i, game in season_data.iterrows():
            # Game-specific fatigue
            game_fatigue = (
                self.fatigue_components['game_load'] * 1 +  # Each game = 1 unit
                self.fatigue_components['minute_load'] * (game['time_on_ice_seconds'] / 3600) +
                self.fatigue_components['intensity_load'] * (game['shots_against'] / 30) +
                self.fatigue_components['travel_load'] * (game['travel_distance'] / 1000) +
                self.fatigue_components['recovery_deficit'] * max(0, (3 - game['days_rest']) / 3)
            )
            
            # Fatigue recovery (exponential decay)
            recovery_rate = self.calculate_recovery_rate(game['age'], game['days_rest'])
            carry_over_fatigue = carry_over_fatigue * (1 - recovery_rate) + game_fatigue
            
            cumulative_fatigue.append(carry_over_fatigue)
            
        return cumulative_fatigue
        
    def calculate_recovery_rate(self, age: int, rest_days: int):
        """
        Calculate fatigue recovery rate based on age and rest
        """
        # Base recovery rate decreases with age
        base_recovery = max(0.1, 0.4 - (age - 25) * 0.02)
        
        # Rest days multiplier
        rest_multiplier = min(1.0, rest_days / 3)
        
        return base_recovery * rest_multiplier
        
    def analyze_career_fatigue_progression(self, career_data: pd.DataFrame):
        """
        Analyze how fatigue tolerance changes over career
        """
        fatigue_by_season = {}
        
        for season in career_data['season'].unique():
            season_data = career_data[career_data['season'] == season]
            season_fatigue = self.calculate_season_fatigue_load(season_data)
            
            fatigue_metrics = {
                'peak_fatigue': max(season_fatigue),
                'avg_fatigue': np.mean(season_fatigue),
                'fatigue_variance': np.var(season_fatigue),
                'late_season_fatigue': np.mean(season_fatigue[-20:]) if len(season_fatigue) >= 20 else np.mean(season_fatigue),
                'fatigue_resistance': self.calculate_fatigue_resistance(season_data, season_fatigue)
            }
            
            fatigue_by_season[season] = fatigue_metrics
            
        return fatigue_by_season
        
    def calculate_fatigue_resistance(self, season_data: pd.DataFrame, fatigue_levels: list):
        """
        Calculate how well performance is maintained under fatigue
        """
        # Correlate fatigue levels with performance
        correlation = np.corrcoef(fatigue_levels, season_data['save_percentage'])[0, 1]
        
        # Negative correlation means performance drops with fatigue
        # Convert to resistance score (0-1, higher is better)
        resistance_score = max(0, 1 + correlation)  # -1 correlation becomes 0, 0 becomes 1
        
        return resistance_score
```

### Age-Related Fatigue Changes

```python
class AgeFatigueAnalysis:
    def __init__(self):
        self.age_cohorts = {
            'young': (18, 25),
            'prime': (25, 30), 
            'veteran': (30, 35),
            'elder': (35, 45)
        }
        
    def analyze_age_fatigue_patterns(self, all_players_data: pd.DataFrame):
        """
        Analyze fatigue patterns across age groups
        """
        age_analysis = {}
        
        for cohort, (min_age, max_age) in self.age_cohorts.items():
            cohort_data = all_players_data[
                (all_players_data['age'] >= min_age) & 
                (all_players_data['age'] < max_age)
            ]
            
            age_analysis[cohort] = {
                'recovery_time': self.calculate_avg_recovery_time(cohort_data),
                'fatigue_threshold': self.calculate_fatigue_threshold(cohort_data),
                'workload_capacity': self.calculate_workload_capacity(cohort_data),
                'performance_volatility': self.calculate_performance_volatility(cohort_data)
            }
            
        return age_analysis
        
    def calculate_avg_recovery_time(self, cohort_data: pd.DataFrame):
        """
        Calculate average recovery time to baseline performance
        """
        recovery_times = []
        
        for player_id in cohort_data['player_id'].unique():
            player_data = cohort_data[cohort_data['player_id'] == player_id]
            
            # Find periods of high fatigue followed by recovery
            high_fatigue_games = player_data[player_data['fatigue_index'] > 70]
            
            for _, fatigue_game in high_fatigue_games.iterrows():
                recovery_time = self.find_recovery_time(player_data, fatigue_game)
                if recovery_time:
                    recovery_times.append(recovery_time)
                    
        return np.mean(recovery_times) if recovery_times else None
        
    def find_recovery_time(self, player_data: pd.DataFrame, fatigue_game: pd.Series):
        """
        Find how many days until player returns to baseline performance
        """
        baseline_performance = player_data['save_percentage'].quantile(0.5)  # Median
        
        subsequent_games = player_data[
            player_data['game_date'] > fatigue_game['game_date']
        ].head(10)  # Look at next 10 games
        
        for i, game in subsequent_games.iterrows():
            if game['save_percentage'] >= baseline_performance:
                days_to_recovery = (game['game_date'] - fatigue_game['game_date']).days
                return days_to_recovery
                
        return None
```

---

## Career Milestone Analysis

### Performance Peak Identification

```python
class CareerMilestoneAnalyzer:
    def __init__(self):
        self.milestone_thresholds = {
            'games_played': [100, 200, 300, 400, 500, 600, 700],
            'seasons': [5, 10, 15, 20],
            'cumulative_minutes': [10000, 20000, 30000, 40000],
            'career_saves': [10000, 15000, 20000, 25000, 30000]
        }
        
    def identify_career_peaks(self, career_data: pd.DataFrame):
        """
        Identify peak performance periods in career
        """
        # Rolling performance windows
        career_data = career_data.sort_values('game_date')
        
        # Calculate rolling averages
        rolling_windows = [10, 20, 41]  # 10-game, 20-game, half-season
        
        peak_analysis = {}
        
        for window in rolling_windows:
            rolling_save_pct = career_data['save_percentage'].rolling(window=window).mean()
            
            # Find peak periods
            peak_idx = rolling_save_pct.idxmax()
            peak_period = career_data.loc[peak_idx-window+1:peak_idx]
            
            peak_analysis[f'{window}_game_peak'] = {
                'period': (peak_period['game_date'].min(), peak_period['game_date'].max()),
                'save_percentage': rolling_save_pct.loc[peak_idx],
                'age_range': (peak_period['age'].min(), peak_period['age'].max()),
                'career_year': peak_period['career_year'].iloc[-1],
                'context': self.analyze_peak_context(peak_period)
            }
            
        return peak_analysis
        
    def analyze_peak_context(self, peak_period: pd.DataFrame):
        """
        Analyze context around peak performance periods
        """
        context = {
            'avg_rest_days': peak_period['days_rest'].mean(),
            'avg_travel': peak_period['travel_distance'].mean(),
            'workload': {
                'games': len(peak_period),
                'avg_minutes': peak_period['time_on_ice_seconds'].mean() / 60,
                'total_shots': peak_period['shots_against'].sum()
            },
            'team_performance': {
                'wins': len(peak_period[peak_period['decision'] == 'W']),
                'losses': len(peak_period[peak_period['decision'] == 'L']),
                'avg_goals_support': peak_period['team_goals_for'].mean()
            },
            'fatigue_levels': {
                'avg_fatigue_index': peak_period['fatigue_index'].mean(),
                'peak_fatigue': peak_period['fatigue_index'].max()
            }
        }
        
        return context
        
    def analyze_milestone_impact(self, career_data: pd.DataFrame):
        """
        Analyze performance around career milestones
        """
        milestone_analysis = {}
        
        for milestone_type, thresholds in self.milestone_thresholds.items():
            milestone_analysis[milestone_type] = {}
            
            for threshold in thresholds:
                milestone_game = self.find_milestone_game(career_data, milestone_type, threshold)
                
                if milestone_game is not None:
                    pre_milestone = self.get_games_around_milestone(career_data, milestone_game, -10, 0)
                    post_milestone = self.get_games_around_milestone(career_data, milestone_game, 1, 11)
                    
                    milestone_analysis[milestone_type][threshold] = {
                        'milestone_date': milestone_game['game_date'],
                        'age_at_milestone': milestone_game['age'],
                        'pre_performance': pre_milestone['save_percentage'].mean(),
                        'post_performance': post_milestone['save_percentage'].mean(),
                        'performance_change': post_milestone['save_percentage'].mean() - pre_milestone['save_percentage'].mean(),
                        'psychological_impact': self.assess_psychological_impact(pre_milestone, post_milestone)
                    }
                    
        return milestone_analysis
```

---

## Injury and Recovery Analysis

### Injury Impact on Career Trajectory

```python
class InjuryCareerAnalysis:
    def __init__(self):
        self.injury_types = {
            'lower_body': ['groin', 'hip', 'knee', 'ankle'],
            'upper_body': ['shoulder', 'arm', 'wrist', 'hand'],
            'core': ['back', 'abdomen', 'core'],
            'head': ['concussion', 'head', 'neck']
        }
        
    def analyze_injury_patterns(self, career_data: pd.DataFrame, injury_data: pd.DataFrame):
        """
        Analyze injury patterns throughout career
        """
        injury_analysis = {
            'injury_frequency_by_age': self.calculate_injury_frequency_by_age(injury_data),
            'fatigue_injury_correlation': self.analyze_fatigue_injury_correlation(career_data, injury_data),
            'recovery_patterns': self.analyze_recovery_patterns(career_data, injury_data),
            'long_term_impact': self.assess_long_term_injury_impact(career_data, injury_data)
        }
        
        return injury_analysis
        
    def analyze_fatigue_injury_correlation(self, career_data: pd.DataFrame, injury_data: pd.DataFrame):
        """
        Correlate fatigue levels with injury occurrence
        """
        correlations = {}
        
        for _, injury in injury_data.iterrows():
            # Find games in 30 days before injury
            pre_injury_period = career_data[
                (career_data['game_date'] >= injury['injury_date'] - pd.Timedelta(days=30)) &
                (career_data['game_date'] < injury['injury_date'])
            ]
            
            if len(pre_injury_period) > 0:
                injury_risk_factors = {
                    'avg_fatigue_index': pre_injury_period['fatigue_index'].mean(),
                    'peak_fatigue': pre_injury_period['fatigue_index'].max(),
                    'games_played': len(pre_injury_period),
                    'total_minutes': pre_injury_period['time_on_ice_seconds'].sum() / 60,
                    'travel_distance': pre_injury_period['travel_distance'].sum(),
                    'back_to_backs': len(pre_injury_period[pre_injury_period['is_back_to_back']])
                }
                
                correlations[injury['injury_date']] = injury_risk_factors
                
        return correlations
        
    def analyze_recovery_patterns(self, career_data: pd.DataFrame, injury_data: pd.DataFrame):
        """
        Analyze performance recovery after injuries
        """
        recovery_analysis = {}
        
        for _, injury in injury_data.iterrows():
            return_date = injury['return_date']
            
            # Performance before injury (last 20 games)
            pre_injury = career_data[
                career_data['game_date'] < injury['injury_date']
            ].tail(20)
            
            # Performance after return (first 20 games)
            post_injury = career_data[
                career_data['game_date'] >= return_date
            ].head(20)
            
            if len(pre_injury) > 0 and len(post_injury) > 0:
                recovery_metrics = {
                    'time_missed_days': (return_date - injury['injury_date']).days,
                    'pre_injury_save_pct': pre_injury['save_percentage'].mean(),
                    'post_injury_save_pct': post_injury['save_percentage'].mean(),
                    'performance_recovery_pct': (post_injury['save_percentage'].mean() / pre_injury['save_percentage'].mean()) * 100,
                    'games_to_baseline': self.calculate_games_to_baseline(post_injury, pre_injury['save_percentage'].mean()),
                    'full_recovery_achieved': post_injury['save_percentage'].mean() >= pre_injury['save_percentage'].mean() * 0.98
                }
                
                recovery_analysis[injury['injury_date']] = recovery_metrics
                
        return recovery_analysis
```

---

## Career Longevity Factors

### Longevity Prediction Modeling

```python
class CareerLongevityAnalyzer:
    def __init__(self):
        self.longevity_factors = [
            'early_career_workload',
            'injury_history',
            'fatigue_resistance',
            'performance_consistency',
            'playing_style',
            'team_support_quality'
        ]
        
    def build_longevity_model(self, historical_careers: pd.DataFrame):
        """
        Build model to predict career longevity
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score
        
        # Feature engineering for longevity factors
        features = self.engineer_longevity_features(historical_careers)
        
        # Target: career length in seasons
        target = historical_careers['career_seasons']
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        model.fit(features, target)
        
        # Validate model
        cv_scores = cross_val_score(model, features, target, cv=5)
        
        longevity_model = {
            'model': model,
            'features': features.columns.tolist(),
            'cv_score_mean': cv_scores.mean(),
            'cv_score_std': cv_scores.std(),
            'feature_importance': dict(zip(features.columns, model.feature_importances_))
        }
        
        return longevity_model
        
    def engineer_longevity_features(self, careers_data: pd.DataFrame):
        """
        Engineer features predictive of career longevity
        """
        features = pd.DataFrame()
        
        # Early career metrics (first 3 seasons)
        features['early_games_per_season'] = careers_data['games_seasons_1_3'].mean()
        features['early_save_pct'] = careers_data['save_pct_seasons_1_3'].mean()
        features['early_fatigue_resistance'] = careers_data['fatigue_resistance_seasons_1_3'].mean()
        
        # Physical and style factors
        features['height_cm'] = careers_data['height_cm']
        features['weight_kg'] = careers_data['weight_kg']
        features['playing_style_butterfly'] = careers_data['style_butterfly_pct']
        features['debut_age'] = careers_data['debut_age']
        
        # Performance consistency
        features['performance_variance'] = careers_data['save_pct_variance']
        features['quality_start_pct'] = careers_data['quality_starts_pct']
        features['really_bad_start_pct'] = careers_data['really_bad_starts_pct']
        
        # Workload management
        features['avg_games_per_season'] = careers_data['total_games'] / careers_data['career_seasons']
        features['back_to_back_frequency'] = careers_data['back_to_back_games'] / careers_data['total_games']
        features['travel_load_avg'] = careers_data['total_travel_miles'] / careers_data['total_games']
        
        # Team and era factors
        features['team_defensive_quality'] = careers_data['avg_team_defense_rating']
        features['era_scoring_environment'] = careers_data['era_goals_per_game']
        
        return features
        
    def predict_remaining_career(self, current_player_data: pd.DataFrame, longevity_model: dict):
        """
        Predict remaining career length for active player
        """
        current_features = self.engineer_current_player_features(current_player_data)
        
        predicted_total_seasons = longevity_model['model'].predict(current_features.values.reshape(1, -1))[0]
        current_seasons = current_player_data['career_seasons'].iloc[-1]
        
        remaining_seasons = max(0, predicted_total_seasons - current_seasons)
        
        # Calculate confidence intervals
        predictions = []
        for estimator in longevity_model['model'].estimators_:
            pred = estimator.predict(current_features.values.reshape(1, -1))[0]
            predictions.append(pred)
            
        prediction_std = np.std(predictions)
        
        return {
            'predicted_total_seasons': predicted_total_seasons,
            'predicted_remaining_seasons': remaining_seasons,
            'confidence_interval_low': predicted_total_seasons - 1.96 * prediction_std,
            'confidence_interval_high': predicted_total_seasons + 1.96 * prediction_std,
            'retirement_probability_by_age': self.calculate_retirement_probabilities(current_player_data)
        }
```

---

## Cross-Career Comparative Analysis

### Cohort Comparison Framework

```python
class CareerCohortAnalysis:
    def __init__(self):
        self.comparison_dimensions = [
            'debut_era',
            'draft_position', 
            'playing_style',
            'team_context',
            'physical_attributes'
        ]
        
    def compare_career_cohorts(self, all_careers: pd.DataFrame):
        """
        Compare career patterns across different player cohorts
        """
        cohort_analysis = {}
        
        # Era-based cohorts
        era_cohorts = {
            'dead_puck_era': (1995, 2005),
            'modern_era': (2005, 2015),
            'current_era': (2015, 2024)
        }
        
        for era_name, (start_year, end_year) in era_cohorts.items():
            era_players = all_careers[
                (all_careers['debut_year'] >= start_year) & 
                (all_careers['debut_year'] < end_year)
            ]
            
            cohort_analysis[era_name] = self.analyze_cohort_patterns(era_players)
            
        # Style-based cohorts
        style_cohorts = {
            'butterfly': all_careers[all_careers['style_butterfly_pct'] > 80],
            'hybrid': all_careers[(all_careers['style_butterfly_pct'] >= 40) & (all_careers['style_butterfly_pct'] <= 80)],
            'stand_up': all_careers[all_careers['style_butterfly_pct'] < 40]
        }
        
        for style_name, style_players in style_cohorts.items():
            cohort_analysis[f"style_{style_name}"] = self.analyze_cohort_patterns(style_players)
            
        return cohort_analysis
        
    def analyze_cohort_patterns(self, cohort_data: pd.DataFrame):
        """
        Analyze patterns within a player cohort
        """
        if len(cohort_data) == 0:
            return None
            
        patterns = {
            'career_length': {
                'mean': cohort_data['career_seasons'].mean(),
                'median': cohort_data['career_seasons'].median(),
                'std': cohort_data['career_seasons'].std()
            },
            'peak_performance': {
                'avg_peak_save_pct': cohort_data['peak_save_percentage'].mean(),
                'avg_peak_age': cohort_data['peak_age'].mean(),
                'peak_duration_seasons': cohort_data['peak_duration'].mean()
            },
            'fatigue_patterns': {
                'avg_fatigue_resistance': cohort_data['fatigue_resistance'].mean(),
                'workload_tolerance': cohort_data['max_games_season'].mean(),
                'recovery_efficiency': cohort_data['recovery_rate'].mean()
            },
            'injury_rates': {
                'injuries_per_season': cohort_data['total_injuries'] / cohort_data['career_seasons'],
                'games_missed_per_injury': cohort_data['games_missed'] / cohort_data['total_injuries'],
                'career_ending_injury_rate': (cohort_data['retirement_reason'] == 'injury').mean()
            },
            'performance_evolution': {
                'improvement_rate_early': cohort_data['save_pct_improvement_seasons_1_5'].mean(),
                'decline_rate_late': cohort_data['save_pct_decline_final_seasons'].mean(),
                'consistency_score': cohort_data['performance_consistency'].mean()
            }
        }
        
        return patterns
```

This comprehensive player career analysis framework enables deep longitudinal studies of goaltender fatigue patterns, performance evolution, and career sustainability across the entire span of NHL history, providing unprecedented insights into the factors that determine career success and longevity in professional hockey.