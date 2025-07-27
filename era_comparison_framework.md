# Era Comparison Framework - Cross-Temporal Analysis

## Overview
**Objective**: Develop comprehensive framework for comparing goaltender fatigue patterns and performance across different eras of NHL history, accounting for rule changes, equipment evolution, and playing style shifts.

**Temporal Scope**: 1980-2024 (44 seasons)
**Era Boundaries**: Major rule changes, equipment innovations, strategic evolution
**Analysis Depth**: Statistical adjustment methods, contextual normalization, trend identification

---

## Era Definition Framework

### Historical Era Classifications

```python
NHL_ERAS = {
    "high_scoring_era": {
        "period": (1980, 1994),
        "characteristics": [
            "High offensive output (6+ goals/game)",
            "Limited goalie equipment restrictions",
            "Stand-up and hybrid styles dominant",
            "Shorter careers due to physical toll"
        ],
        "key_events": [
            "1980: Introduction of Gretzky era",
            "1986: Larger goal nets briefly tested",
            "1992: Video goal review introduced"
        ],
        "avg_stats": {
            "goals_per_game": 6.8,
            "avg_save_percentage": 0.876,
            "shots_per_game": 31.2,
            "goalie_games_avg": 42
        }
    },
    
    "dead_puck_era": {
        "period": (1994, 2005),
        "characteristics": [
            "Defensive systems dominant",
            "Neutral zone trap prevalent",
            "Butterfly style revolution",
            "Equipment size increases"
        ],
        "key_events": [
            "1994: Lockout, rule changes",
            "1998: Olympic break introduction",
            "2000: Equipment size restrictions begin",
            "2004-05: Lockout season"
        ],
        "avg_stats": {
            "goals_per_game": 5.2,
            "avg_save_percentage": 0.903,
            "shots_per_game": 28.8,
            "goalie_games_avg": 38
        }
    },
    
    "post_lockout_era": {
        "period": (2005, 2015),
        "characteristics": [
            "Obstruction rule enforcement",
            "Increased pace and skill",
            "Goalie equipment standardization",
            "Advanced analytics emergence"
        ],
        "key_events": [
            "2005: Obstruction crackdown",
            "2009: 4-on-4 overtime extended",
            "2013: Realignment to conferences",
            "2014: Coach's challenge introduced"
        ],
        "avg_stats": {
            "goals_per_game": 5.8,
            "avg_save_percentage": 0.911,
            "shots_per_game": 30.1,
            "goalie_games_avg": 41
        }
    },
    
    "modern_era": {
        "period": (2015, 2024),
        "characteristics": [
            "Speed and skill emphasis",
            "Advanced analytics integration",
            "Equipment size restrictions",
            "Increased shot volume and quality"
        ],
        "key_events": [
            "2015: 3-on-3 overtime introduced",
            "2018: Goalie equipment size reduced",
            "2019: Coach's challenge refined",
            "2020: COVID-19 adjustments"
        ],
        "avg_stats": {
            "goals_per_game": 6.0,
            "avg_save_percentage": 0.908,
            "shots_per_game": 31.7,
            "goalie_games_avg": 43
        }
    }
}
```

### Equipment Evolution Timeline

```python
EQUIPMENT_EVOLUTION = {
    "1980s": {
        "pad_width": "9-10 inches",
        "chest_protector": "Minimal padding",
        "catching_glove": "Standard size",
        "blocker": "Small blocking surface",
        "mask": "Fiberglass, limited vision",
        "total_coverage": "Estimated 65% of net"
    },
    
    "1990s": {
        "pad_width": "10-11 inches",
        "chest_protector": "Increased shoulder protection",
        "catching_glove": "Enlarged catching area",
        "blocker": "Expanded blocking surface",
        "mask": "Improved visibility, cat-eye cages",
        "total_coverage": "Estimated 75% of net"
    },
    
    "2000s": {
        "pad_width": "11-12 inches (peak)",
        "chest_protector": "Maximum size allowed",
        "catching_glove": "Peak circumference",
        "blocker": "Maximum legal dimensions",
        "mask": "Advanced materials, better protection",
        "total_coverage": "Estimated 85% of net (peak)"
    },
    
    "2010s": {
        "pad_width": "11 inches (regulated)",
        "chest_protector": "Size restrictions implemented",
        "catching_glove": "Circumference limited",
        "blocker": "Standardized dimensions",
        "mask": "Safety improvements",
        "total_coverage": "Estimated 80% of net"
    },
    
    "2020s": {
        "pad_width": "10.5 inches (reduced 2018)",
        "chest_protector": "Further size reductions",
        "catching_glove": "Tighter restrictions",
        "blocker": "Reduced blocking area",
        "mask": "Lightweight, high-tech materials",
        "total_coverage": "Estimated 75% of net"
    }
}
```

---

## Statistical Adjustment Framework

### Era-Adjusted Performance Metrics

```python
class EraAdjustmentEngine:
    def __init__(self):
        self.era_baselines = self.calculate_era_baselines()
        self.equipment_factors = self.load_equipment_adjustment_factors()
        self.rule_impact_factors = self.load_rule_impact_factors()
        
    def calculate_era_adjusted_save_percentage(self, raw_save_pct: float, season: str, context: dict):
        """
        Adjust save percentage for era-specific factors
        """
        era = self.determine_era(season)
        
        # Base era adjustment
        era_baseline = self.era_baselines[era]['save_percentage']
        league_average = self.era_baselines[era]['league_average']
        
        # Calculate relative performance
        relative_performance = (raw_save_pct - era_baseline) / era_baseline
        
        # Apply equipment adjustment
        equipment_factor = self.equipment_factors[era]
        
        # Apply rule adjustment
        rule_factor = self.rule_impact_factors[era]
        
        # Modern era baseline (2015-2024)
        modern_baseline = self.era_baselines['modern_era']['save_percentage']
        
        # Adjusted save percentage
        adjusted_save_pct = modern_baseline * (1 + relative_performance) * equipment_factor * rule_factor
        
        return {
            'raw_save_pct': raw_save_pct,
            'era_adjusted_save_pct': adjusted_save_pct,
            'adjustment_factor': adjusted_save_pct / raw_save_pct,
            'era': era,
            'relative_to_era': relative_performance
        }
        
    def calculate_era_baselines(self):
        """
        Calculate baseline statistics for each era
        """
        baselines = {}
        
        for era_name, era_data in NHL_ERAS.items():
            baselines[era_name] = {
                'save_percentage': era_data['avg_stats']['avg_save_percentage'],
                'goals_per_game': era_data['avg_stats']['goals_per_game'],
                'shots_per_game': era_data['avg_stats']['shots_per_game'],
                'games_per_goalie': era_data['avg_stats']['goalie_games_avg']
            }
            
        return baselines
        
    def adjust_workload_metrics(self, games_played: int, minutes_played: int, season: str):
        """
        Adjust workload metrics for era-specific factors
        """
        era = self.determine_era(season)
        
        # Era-specific workload adjustments
        workload_adjustments = {
            'high_scoring_era': {
                'intensity_multiplier': 1.3,  # Higher shot volume, more intense
                'recovery_multiplier': 0.8,   # Less advanced recovery methods
                'travel_impact': 1.4          # More difficult travel conditions
            },
            'dead_puck_era': {
                'intensity_multiplier': 0.9,  # Lower shot volume
                'recovery_multiplier': 0.9,   # Improving recovery methods
                'travel_impact': 1.2          # Better travel conditions
            },
            'post_lockout_era': {
                'intensity_multiplier': 1.1,  # Increased pace
                'recovery_multiplier': 1.0,   # Modern recovery methods
                'travel_impact': 1.0          # Baseline travel
            },
            'modern_era': {
                'intensity_multiplier': 1.2,  # Highest skill level
                'recovery_multiplier': 1.1,   # Advanced recovery
                'travel_impact': 0.9          # Optimized travel
            }
        }
        
        adjustments = workload_adjustments[era]
        
        adjusted_workload = {
            'era_adjusted_games': games_played * adjustments['intensity_multiplier'],
            'era_adjusted_minutes': minutes_played * adjustments['intensity_multiplier'],
            'recovery_factor': adjustments['recovery_multiplier'],
            'travel_impact_factor': adjustments['travel_impact']
        }
        
        return adjusted_workload
```

### Cross-Era Fatigue Comparison

```python
class CrossEraFatigueAnalyzer:
    def __init__(self):
        self.era_adjustment_engine = EraAdjustmentEngine()
        
    def compare_fatigue_patterns_across_eras(self, historical_data: pd.DataFrame):
        """
        Compare fatigue patterns across different eras
        """
        era_comparisons = {}
        
        for era_name in NHL_ERAS.keys():
            era_data = self.filter_data_by_era(historical_data, era_name)
            
            era_fatigue_analysis = {
                'average_fatigue_resistance': self.calculate_era_fatigue_resistance(era_data),
                'back_to_back_impact': self.analyze_back_to_back_impact(era_data),
                'workload_tolerance': self.calculate_workload_tolerance(era_data),
                'recovery_patterns': self.analyze_recovery_patterns(era_data),
                'career_longevity': self.calculate_career_longevity_stats(era_data)
            }
            
            era_comparisons[era_name] = era_fatigue_analysis
            
        return era_comparisons
        
    def calculate_era_fatigue_resistance(self, era_data: pd.DataFrame):
        """
        Calculate fatigue resistance for an era
        """
        # Group by player and calculate individual fatigue resistance
        player_resistance = []
        
        for player_id in era_data['player_id'].unique():
            player_data = era_data[era_data['player_id'] == player_id]
            
            if len(player_data) >= 20:  # Minimum games for analysis
                # Calculate correlation between fatigue index and performance
                correlation = player_data['fatigue_index'].corr(player_data['save_percentage'])
                
                # Convert to resistance score (higher is better)
                resistance_score = 1 + correlation  # Range: 0-2, where 1 is neutral
                player_resistance.append(resistance_score)
                
        return {
            'mean_resistance': np.mean(player_resistance),
            'median_resistance': np.median(player_resistance),
            'std_resistance': np.std(player_resistance),
            'sample_size': len(player_resistance)
        }
        
    def analyze_back_to_back_impact(self, era_data: pd.DataFrame):
        """
        Analyze back-to-back game impact within an era
        """
        b2b_games = era_data[era_data['is_back_to_back'] == True]
        regular_games = era_data[era_data['is_back_to_back'] == False]
        
        b2b_analysis = {
            'b2b_save_pct': b2b_games['save_percentage'].mean(),
            'regular_save_pct': regular_games['save_percentage'].mean(),
            'performance_drop': regular_games['save_percentage'].mean() - b2b_games['save_percentage'].mean(),
            'b2b_frequency': len(b2b_games) / len(era_data),
            'statistical_significance': self.calculate_significance(b2b_games['save_percentage'], regular_games['save_percentage'])
        }
        
        return b2b_analysis
        
    def calculate_workload_tolerance(self, era_data: pd.DataFrame):
        """
        Calculate workload tolerance patterns for an era
        """
        # Group by season and player
        season_workloads = era_data.groupby(['player_id', 'season']).agg({
            'games_played': 'count',
            'time_on_ice_seconds': 'sum',
            'save_percentage': 'mean',
            'fatigue_index': 'mean'
        }).reset_index()
        
        # Analyze relationship between workload and performance
        high_workload = season_workloads[season_workloads['games_played'] >= 60]
        medium_workload = season_workloads[(season_workloads['games_played'] >= 40) & (season_workloads['games_played'] < 60)]
        low_workload = season_workloads[season_workloads['games_played'] < 40]
        
        workload_tolerance = {
            'high_workload_performance': high_workload['save_percentage'].mean(),
            'medium_workload_performance': medium_workload['save_percentage'].mean(),
            'low_workload_performance': low_workload['save_percentage'].mean(),
            'workload_performance_correlation': season_workloads['games_played'].corr(season_workloads['save_percentage']),
            'optimal_games_range': self.find_optimal_workload_range(season_workloads)
        }
        
        return workload_tolerance
```

---

## Playing Style Evolution Analysis

### Style Classification Framework

```python
class PlayingStyleEvolution:
    def __init__(self):
        self.style_indicators = {
            'butterfly_percentage': 'Time spent in butterfly position',
            'lateral_movement_frequency': 'Side-to-side movements per game',
            'aggressive_positioning': 'Distance from goal line',
            'rebound_control_style': 'Rebound direction control',
            'puck_handling_frequency': 'Puck plays per game'
        }
        
    def analyze_style_evolution_by_era(self, historical_data: pd.DataFrame):
        """
        Analyze how playing styles evolved across eras
        """
        style_evolution = {}
        
        for era_name in NHL_ERAS.keys():
            era_data = self.filter_data_by_era(historical_data, era_name)
            
            style_analysis = {
                'dominant_styles': self.identify_dominant_styles(era_data),
                'style_distribution': self.calculate_style_distribution(era_data),
                'fatigue_by_style': self.analyze_fatigue_by_style(era_data),
                'performance_by_style': self.analyze_performance_by_style(era_data),
                'innovation_indicators': self.identify_style_innovations(era_data)
            }
            
            style_evolution[era_name] = style_analysis
            
        return style_evolution
        
    def identify_dominant_styles(self, era_data: pd.DataFrame):
        """
        Identify dominant playing styles in an era
        """
        # Cluster players by style characteristics
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        style_features = era_data[[
            'butterfly_percentage',
            'lateral_movement_frequency', 
            'aggressive_positioning',
            'rebound_control_rating',
            'puck_handling_frequency'
        ]].fillna(era_data.mean())
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(style_features)
        
        # Cluster into style groups
        kmeans = KMeans(n_clusters=4, random_state=42)
        style_clusters = kmeans.fit_predict(scaled_features)
        
        # Analyze cluster characteristics
        era_data['style_cluster'] = style_clusters
        
        cluster_analysis = {}
        for cluster in range(4):
            cluster_data = era_data[era_data['style_cluster'] == cluster]
            
            cluster_analysis[f'style_{cluster}'] = {
                'prevalence': len(cluster_data) / len(era_data),
                'characteristics': {
                    'butterfly_pct': cluster_data['butterfly_percentage'].mean(),
                    'lateral_movement': cluster_data['lateral_movement_frequency'].mean(),
                    'positioning': cluster_data['aggressive_positioning'].mean()
                },
                'performance': {
                    'avg_save_pct': cluster_data['save_percentage'].mean(),
                    'fatigue_resistance': self.calculate_cluster_fatigue_resistance(cluster_data)
                },
                'representative_players': self.identify_representative_players(cluster_data)
            }
            
        return cluster_analysis
        
    def analyze_fatigue_by_style(self, era_data: pd.DataFrame):
        """
        Analyze how different playing styles affect fatigue
        """
        style_fatigue_analysis = {}
        
        # Categorize players by primary style
        style_categories = {
            'butterfly': era_data[era_data['butterfly_percentage'] > 75],
            'hybrid': era_data[(era_data['butterfly_percentage'] >= 40) & (era_data['butterfly_percentage'] <= 75)],
            'stand_up': era_data[era_data['butterfly_percentage'] < 40],
            'aggressive': era_data[era_data['aggressive_positioning'] > era_data['aggressive_positioning'].quantile(0.75)],
            'conservative': era_data[era_data['aggressive_positioning'] < era_data['aggressive_positioning'].quantile(0.25)]
        }
        
        for style_name, style_data in style_categories.items():
            if len(style_data) > 10:  # Minimum sample size
                style_fatigue_analysis[style_name] = {
                    'avg_fatigue_index': style_data['fatigue_index'].mean(),
                    'fatigue_variance': style_data['fatigue_index'].var(),
                    'recovery_rate': self.calculate_style_recovery_rate(style_data),
                    'workload_tolerance': self.calculate_style_workload_tolerance(style_data),
                    'injury_rate': self.calculate_style_injury_rate(style_data)
                }
                
        return style_fatigue_analysis
```

---

## Rule Change Impact Analysis

### Major Rule Change Timeline

```python
RULE_CHANGES = {
    "1994_lockout_changes": {
        "date": "1994-10-01",
        "changes": [
            "Minor penalty for diving/embellishment",
            "Instigator rule modification",
            "Regular season overtime introduced"
        ],
        "goalie_impact": "Moderate - more penalties, slight pace increase"
    },
    
    "2005_obstruction_crackdown": {
        "date": "2005-10-05",
        "changes": [
            "Strict obstruction enforcement",
            "Shootout introduction",
            "Goal line moved to 11 feet",
            "No line changes on icing"
        ],
        "goalie_impact": "High - increased offensive opportunities, more breakaways"
    },
    
    "2015_3on3_overtime": {
        "date": "2015-10-07",
        "changes": [
            "3-on-3 overtime period",
            "Shootout reduced frequency"
        ],
        "goalie_impact": "Moderate - more high-danger chances in OT"
    },
    
    "2018_equipment_reduction": {
        "date": "2018-08-01",
        "changes": [
            "Goalie pad width reduced to 10.5 inches",
            "Chest protector size restrictions",
            "Catching glove circumference limits"
        ],
        "goalie_impact": "High - direct equipment limitations"
    }
}

class RuleChangeImpactAnalyzer:
    def __init__(self):
        self.rule_changes = RULE_CHANGES
        
    def analyze_rule_change_impact(self, historical_data: pd.DataFrame, rule_change_key: str):
        """
        Analyze impact of specific rule change on goalie performance and fatigue
        """
        rule_change = self.rule_changes[rule_change_key]
        change_date = pd.to_datetime(rule_change['date'])
        
        # Define pre/post periods (2 seasons each for stability)
        pre_period_start = change_date - pd.DateOffset(years=2)
        pre_period_end = change_date - pd.DateOffset(days=1)
        post_period_start = change_date
        post_period_end = change_date + pd.DateOffset(years=2)
        
        pre_change_data = historical_data[
            (historical_data['game_date'] >= pre_period_start) &
            (historical_data['game_date'] <= pre_period_end)
        ]
        
        post_change_data = historical_data[
            (historical_data['game_date'] >= post_period_start) &
            (historical_data['game_date'] <= post_period_end)
        ]
        
        impact_analysis = {
            'performance_impact': self.calculate_performance_impact(pre_change_data, post_change_data),
            'fatigue_impact': self.calculate_fatigue_impact(pre_change_data, post_change_data),
            'workload_impact': self.calculate_workload_impact(pre_change_data, post_change_data),
            'style_adaptation': self.analyze_style_adaptation(pre_change_data, post_change_data),
            'statistical_significance': self.test_statistical_significance(pre_change_data, post_change_data)
        }
        
        return impact_analysis
        
    def calculate_performance_impact(self, pre_data: pd.DataFrame, post_data: pd.DataFrame):
        """
        Calculate performance changes before/after rule change
        """
        performance_metrics = {
            'save_percentage': {
                'pre_avg': pre_data['save_percentage'].mean(),
                'post_avg': post_data['save_percentage'].mean(),
                'change': post_data['save_percentage'].mean() - pre_data['save_percentage'].mean(),
                'pct_change': ((post_data['save_percentage'].mean() / pre_data['save_percentage'].mean()) - 1) * 100
            },
            'goals_against_avg': {
                'pre_avg': pre_data['goals_against_average'].mean(),
                'post_avg': post_data['goals_against_average'].mean(),
                'change': post_data['goals_against_average'].mean() - pre_data['goals_against_average'].mean()
            },
            'quality_starts_pct': {
                'pre_avg': pre_data['quality_start'].mean(),
                'post_avg': post_data['quality_start'].mean(),
                'change': post_data['quality_start'].mean() - pre_data['quality_start'].mean()
            },
            'shots_faced_per_game': {
                'pre_avg': pre_data['shots_against'].mean(),
                'post_avg': post_data['shots_against'].mean(),
                'change': post_data['shots_against'].mean() - pre_data['shots_against'].mean()
            }
        }
        
        return performance_metrics
```

---

## Cohort Comparison Analytics

### Generation-Based Analysis

```python
class GenerationalAnalyzer:
    def __init__(self):
        self.generations = {
            'pre_expansion': {'birth_years': (1950, 1965), 'peak_years': (1975, 1990)},
            'expansion_era': {'birth_years': (1965, 1975), 'peak_years': (1990, 2005)},
            'modern_generation': {'birth_years': (1975, 1985), 'peak_years': (2005, 2015)},
            'current_generation': {'birth_years': (1985, 2000), 'peak_years': (2015, 2025)}
        }
        
    def compare_generational_fatigue_patterns(self, historical_data: pd.DataFrame):
        """
        Compare fatigue patterns across generational cohorts
        """
        generational_analysis = {}
        
        for gen_name, gen_data in self.generations.items():
            birth_start, birth_end = gen_data['birth_years']
            
            generation_players = historical_data[
                (historical_data['birth_year'] >= birth_start) &
                (historical_data['birth_year'] < birth_end)
            ]
            
            if len(generation_players) > 50:  # Minimum sample size
                generational_analysis[gen_name] = {
                    'sample_size': len(generation_players['player_id'].unique()),
                    'career_patterns': self.analyze_generational_career_patterns(generation_players),
                    'fatigue_characteristics': self.analyze_generational_fatigue(generation_players),
                    'adaptation_strategies': self.identify_generational_adaptations(generation_players),
                    'performance_evolution': self.track_generational_performance(generation_players)
                }
                
        return generational_analysis
        
    def analyze_generational_career_patterns(self, generation_data: pd.DataFrame):
        """
        Analyze career patterns specific to a generation
        """
        career_patterns = {
            'avg_career_length': generation_data.groupby('player_id')['season'].nunique().mean(),
            'avg_peak_age': generation_data.groupby('player_id').apply(
                lambda x: x.loc[x['save_percentage'].idxmax(), 'age']
            ).mean(),
            'games_per_season': generation_data.groupby(['player_id', 'season']).size().mean(),
            'workload_distribution': {
                'heavy_workload_pct': (generation_data.groupby(['player_id', 'season']).size() >= 60).mean(),
                'moderate_workload_pct': ((generation_data.groupby(['player_id', 'season']).size() >= 30) & 
                                         (generation_data.groupby(['player_id', 'season']).size() < 60)).mean(),
                'light_workload_pct': (generation_data.groupby(['player_id', 'season']).size() < 30).mean()
            },
            'specialization_trends': self.analyze_role_specialization(generation_data)
        }
        
        return career_patterns
```

This comprehensive era comparison framework enables sophisticated analysis of how goaltender fatigue patterns, performance metrics, and career trajectories have evolved across different periods of NHL history, accounting for equipment changes, rule modifications, and playing style evolution.