# Multi-Position Analysis Framework - Comprehensive NHL Player Analytics

## Project Expansion Overview

**Enhanced Scope**: Extend Kopitar from goaltender-focused to comprehensive NHL player analysis across all positions

**Coverage**:
- **Goalies**: Fatigue, workload, performance (existing framework)
- **Forwards**: Offensive production, line chemistry, usage patterns
- **Defensemen**: Two-way play, defensive impact, usage in all situations
- **Cross-Position**: Team interactions, line combinations, situational deployment

**Dataset Scale**:
- **40+ years** of player data (1980-2024)
- **25,000+ unique players** across all positions
- **2+ million player-game records** 
- **500+ million individual statistics**

---

## Position-Specific Framework Structure

### Core Analysis Dimensions by Position

```python
POSITION_ANALYSIS_FRAMEWORK = {
    "goalies": {
        "primary_focus": "fatigue_and_workload",
        "key_metrics": [
            "save_percentage", "goals_against_average", "quality_starts",
            "fatigue_index", "workload_tolerance", "recovery_patterns"
        ],
        "unique_factors": [
            "back_to_back_performance", "travel_impact", "equipment_evolution",
            "playing_style_changes", "injury_recovery_patterns"
        ]
    },
    
    "forwards": {
        "primary_focus": "offensive_production_and_usage",
        "key_metrics": [
            "goals", "assists", "points", "shots", "shooting_percentage",
            "ice_time", "face_off_percentage", "plus_minus", "hits", "blocks"
        ],
        "unique_factors": [
            "line_chemistry", "power_play_usage", "penalty_kill_usage",
            "zone_starts", "quality_of_competition", "offensive_zone_time"
        ],
        "sub_positions": {
            "center": {
                "specialized_metrics": ["face_off_wins", "defensive_responsibility"],
                "roles": ["playmaker", "scorer", "two_way", "defensive_specialist"]
            },
            "winger": {
                "specialized_metrics": ["shooting_volume", "net_front_presence"],
                "roles": ["sniper", "power_forward", "speedster", "grinder"]
            }
        }
    },
    
    "defensemen": {
        "primary_focus": "two_way_impact_and_usage",
        "key_metrics": [
            "goals", "assists", "points", "plus_minus", "blocked_shots",
            "hits", "ice_time", "penalty_minutes", "takeaways", "giveaways"
        ],
        "unique_factors": [
            "power_play_quarterback", "penalty_kill_usage", "shutdown_role",
            "breakout_ability", "defensive_zone_coverage", "physicality"
        ],
        "sub_positions": {
            "offensive_defenseman": {
                "specialized_metrics": ["power_play_points", "shot_assists"],
                "roles": ["quarterback", "shooter", "rush_specialist"]
            },
            "defensive_defenseman": {
                "specialized_metrics": ["blocked_shots_per_60", "hits_per_60"],
                "roles": ["shutdown", "stay_at_home", "physical_presence"]
            }
        }
    }
}
```

### Unified Data Model Architecture

```python
class MultiPositionDataModel:
    def __init__(self):
        self.position_schemas = {
            'base_player': self.create_base_player_schema(),
            'goalie_specific': self.create_goalie_schema(),
            'skater_specific': self.create_skater_schema(),
            'forward_specific': self.create_forward_schema(),
            'defenseman_specific': self.create_defenseman_schema()
        }
        
    def create_base_player_schema(self):
        """
        Common fields for all player positions
        """
        return {
            'player_id': 'INTEGER PRIMARY KEY',
            'game_id': 'INTEGER REFERENCES games(id)',
            'team_id': 'INTEGER REFERENCES teams(id)',
            'position': 'VARCHAR(2) CHECK (position IN ("G", "D", "F"))',
            'age': 'INTEGER',
            'height_cm': 'INTEGER',
            'weight_kg': 'INTEGER',
            'handedness': 'VARCHAR(1) CHECK (handedness IN ("L", "R"))',
            'time_on_ice_seconds': 'INTEGER',
            'shifts': 'INTEGER',
            'penalty_minutes': 'INTEGER',
            'plus_minus': 'INTEGER',
            'is_home': 'BOOLEAN',
            'game_date': 'DATE',
            'season': 'VARCHAR(8)',
            'fatigue_index': 'DECIMAL(5,2)',
            'days_rest': 'INTEGER',
            'travel_distance': 'DECIMAL(8,2)',
            'injury_status': 'VARCHAR(20)'
        }
        
    def create_skater_schema(self):
        """
        Common fields for forwards and defensemen
        """
        return {
            'goals': 'INTEGER DEFAULT 0',
            'assists': 'INTEGER DEFAULT 0',
            'points': 'INTEGER GENERATED ALWAYS AS (goals + assists)',
            'shots': 'INTEGER DEFAULT 0',
            'shooting_percentage': 'DECIMAL(5,2)',
            'hits': 'INTEGER DEFAULT 0',
            'blocked_shots': 'INTEGER DEFAULT 0',
            'takeaways': 'INTEGER DEFAULT 0',
            'giveaways': 'INTEGER DEFAULT 0',
            'face_off_wins': 'INTEGER DEFAULT 0',
            'face_off_attempts': 'INTEGER DEFAULT 0',
            'face_off_percentage': 'DECIMAL(5,2)',
            'power_play_goals': 'INTEGER DEFAULT 0',
            'power_play_assists': 'INTEGER DEFAULT 0',
            'power_play_points': 'INTEGER GENERATED ALWAYS AS (power_play_goals + power_play_assists)',
            'power_play_time_seconds': 'INTEGER DEFAULT 0',
            'short_handed_goals': 'INTEGER DEFAULT 0',
            'short_handed_assists': 'INTEGER DEFAULT 0',
            'penalty_kill_time_seconds': 'INTEGER DEFAULT 0',
            'even_strength_goals': 'INTEGER DEFAULT 0',
            'even_strength_assists': 'INTEGER DEFAULT 0',
            'even_strength_time_seconds': 'INTEGER',
            'corsi_for': 'INTEGER',
            'corsi_against': 'INTEGER',
            'corsi_percentage': 'DECIMAL(5,2)',
            'fenwick_for': 'INTEGER',
            'fenwick_against': 'INTEGER',
            'fenwick_percentage': 'DECIMAL(5,2)',
            'zone_start_offensive_pct': 'DECIMAL(5,2)',
            'quality_of_competition': 'DECIMAL(5,2)',
            'quality_of_teammates': 'DECIMAL(5,2)'
        }
```

---

## Cross-Position Analysis Framework

### Team Chemistry and Line Analysis

```python
class TeamChemistryAnalyzer:
    def __init__(self):
        self.line_combinations = LineComboTracker()
        self.chemistry_metrics = ChemistryMetrics()
        
    def analyze_line_performance(self, game_data: pd.DataFrame, line_combo: dict):
        """
        Analyze performance of specific line combinations
        """
        line_players = [line_combo['left_wing'], line_combo['center'], line_combo['right_wing']]
        
        # Filter data for when these players were on ice together
        line_shifts = self.identify_common_shifts(game_data, line_players)
        
        line_performance = {
            'goals_for': line_shifts['goals_for'].sum(),
            'goals_against': line_shifts['goals_against'].sum(),
            'shots_for': line_shifts['shots_for'].sum(),
            'shots_against': line_shifts['shots_against'].sum(),
            'corsi_percentage': self.calculate_corsi_percentage(line_shifts),
            'expected_goals_for': line_shifts['expected_goals_for'].sum(),
            'expected_goals_against': line_shifts['expected_goals_against'].sum(),
            'chemistry_score': self.calculate_chemistry_score(line_shifts),
            'zone_time_offensive_pct': self.calculate_offensive_zone_time(line_shifts)
        }
        
        return line_performance
        
    def calculate_chemistry_score(self, line_shifts: pd.DataFrame):
        """
        Calculate line chemistry based on multiple factors
        """
        chemistry_factors = {
            'passing_accuracy': self.calculate_line_passing_accuracy(line_shifts),
            'scoring_sequence_involvement': self.analyze_scoring_sequences(line_shifts),
            'defensive_coordination': self.analyze_defensive_coordination(line_shifts),
            'sustained_pressure': self.calculate_sustained_pressure(line_shifts),
            'turnover_recovery': self.analyze_turnover_recovery(line_shifts)
        }
        
        # Weighted chemistry score
        chemistry_score = (
            chemistry_factors['passing_accuracy'] * 0.25 +
            chemistry_factors['scoring_sequence_involvement'] * 0.25 +
            chemistry_factors['defensive_coordination'] * 0.20 +
            chemistry_factors['sustained_pressure'] * 0.15 +
            chemistry_factors['turnover_recovery'] * 0.15
        )
        
        return chemistry_score
        
    def analyze_defensive_pairings(self, game_data: pd.DataFrame):
        """
        Analyze defensive pairing effectiveness
        """
        defensive_pairings = self.identify_defensive_pairings(game_data)
        
        pairing_analysis = {}
        
        for pairing in defensive_pairings:
            d1, d2 = pairing['defenseman_1'], pairing['defenseman_2']
            
            pairing_shifts = self.identify_common_shifts(game_data, [d1, d2])
            
            pairing_performance = {
                'goals_against_per_60': self.calculate_goals_against_per_60(pairing_shifts),
                'shots_against_per_60': self.calculate_shots_against_per_60(pairing_shifts),
                'corsi_percentage': self.calculate_corsi_percentage(pairing_shifts),
                'zone_exits_successful_pct': self.calculate_zone_exit_success(pairing_shifts),
                'neutral_zone_regroups': self.count_neutral_zone_regroups(pairing_shifts),
                'complementary_skills_score': self.analyze_skill_complementarity(d1, d2)
            }
            
            pairing_analysis[f"{d1}_{d2}"] = pairing_performance
            
        return pairing_analysis
```

### Fatigue Analysis Across Positions

```python
class MultiPositionFatigueAnalyzer:
    def __init__(self):
        self.position_fatigue_models = {
            'goalies': GoalieFatigueModel(),
            'forwards': ForwardFatigueModel(),
            'defensemen': DefensemanFatigueModel()
        }
        
    def calculate_position_specific_fatigue(self, player_data: pd.DataFrame, position: str):
        """
        Calculate fatigue using position-specific models
        """
        fatigue_model = self.position_fatigue_models[position]
        
        if position == 'goalies':
            return self.calculate_goalie_fatigue(player_data, fatigue_model)
        elif position == 'forwards':
            return self.calculate_forward_fatigue(player_data, fatigue_model)
        elif position == 'defensemen':
            return self.calculate_defenseman_fatigue(player_data, fatigue_model)
            
    def calculate_forward_fatigue(self, player_data: pd.DataFrame, model):
        """
        Forward-specific fatigue calculation
        """
        fatigue_components = {
            'ice_time_load': 0.35,      # Ice time per game
            'shift_intensity': 0.25,    # Number and length of shifts
            'physical_play': 0.20,      # Hits given/taken, battles won
            'special_teams': 0.10,      # PP/PK time
            'travel_recovery': 0.10     # Travel and rest patterns
        }
        
        # Calculate each component
        recent_games = player_data.tail(10)  # Last 10 games
        
        ice_time_factor = recent_games['time_on_ice_seconds'].mean() / 1200  # Normalize to 20 min
        shift_intensity_factor = (recent_games['shifts'].mean() * recent_games['avg_shift_length'].mean()) / 1200
        physical_factor = (recent_games['hits'].mean() + recent_games['hits_taken'].mean()) / 10
        special_teams_factor = (recent_games['power_play_time_seconds'].mean() + 
                               recent_games['penalty_kill_time_seconds'].mean()) / 300
        travel_factor = recent_games['travel_distance'].sum() / 5000  # 5000 miles baseline
        
        # Weighted fatigue index
        fatigue_index = (
            ice_time_factor * fatigue_components['ice_time_load'] +
            shift_intensity_factor * fatigue_components['shift_intensity'] +
            physical_factor * fatigue_components['physical_play'] +
            special_teams_factor * fatigue_components['special_teams'] +
            travel_factor * fatigue_components['travel_recovery']
        ) * 100  # Scale to 0-100
        
        return min(fatigue_index, 100)
        
    def calculate_defenseman_fatigue(self, player_data: pd.DataFrame, model):
        """
        Defenseman-specific fatigue calculation
        """
        fatigue_components = {
            'ice_time_load': 0.40,      # Higher weight due to higher TOI
            'defensive_actions': 0.25,  # Blocks, hits, defensive plays
            'special_teams': 0.15,      # PP/PK time (often high for D)
            'zone_coverage': 0.10,      # Defensive zone time
            'travel_recovery': 0.10     # Travel and rest patterns
        }
        
        recent_games = player_data.tail(10)
        
        ice_time_factor = recent_games['time_on_ice_seconds'].mean() / 1500  # 25 min baseline for D
        defensive_factor = (recent_games['blocked_shots'].mean() + 
                           recent_games['hits'].mean() + 
                           recent_games['defensive_plays'].mean()) / 15
        special_teams_factor = (recent_games['power_play_time_seconds'].mean() + 
                               recent_games['penalty_kill_time_seconds'].mean()) / 400
        zone_coverage_factor = recent_games['defensive_zone_time_pct'].mean() / 50  # 50% baseline
        travel_factor = recent_games['travel_distance'].sum() / 5000
        
        fatigue_index = (
            ice_time_factor * fatigue_components['ice_time_load'] +
            defensive_factor * fatigue_components['defensive_actions'] +
            special_teams_factor * fatigue_components['special_teams'] +
            zone_coverage_factor * fatigue_components['zone_coverage'] +
            travel_factor * fatigue_components['travel_recovery']
        ) * 100
        
        return min(fatigue_index, 100)
```

---

## Performance Metrics by Position

### Advanced Statistics Framework

```python
class AdvancedStatsCalculator:
    def __init__(self):
        self.position_weights = self.load_position_weights()
        
    def calculate_war_by_position(self, player_data: pd.DataFrame, position: str):
        """
        Calculate Wins Above Replacement for each position
        """
        if position == 'goalies':
            return self.calculate_goalie_war(player_data)
        elif position == 'forwards':
            return self.calculate_forward_war(player_data)
        elif position == 'defensemen':
            return self.calculate_defenseman_war(player_data)
            
    def calculate_forward_war(self, player_data: pd.DataFrame):
        """
        Forward WAR calculation
        """
        war_components = {
            'offensive_war': self.calculate_offensive_war(player_data),
            'defensive_war': self.calculate_forward_defensive_war(player_data),
            'special_teams_war': self.calculate_special_teams_war(player_data),
            'durability_war': self.calculate_durability_war(player_data)
        }
        
        total_war = sum(war_components.values())
        
        return {
            'total_war': total_war,
            'components': war_components,
            'war_per_game': total_war / player_data['games_played'].iloc[0],
            'war_percentile': self.calculate_war_percentile(total_war, 'forwards')
        }
        
    def calculate_offensive_war(self, player_data: pd.DataFrame):
        """
        Offensive component of WAR
        """
        # Goals above replacement
        replacement_goals_per_game = 0.08  # Replacement level
        actual_goals_per_game = player_data['goals'].sum() / player_data['games_played'].iloc[0]
        goals_above_replacement = (actual_goals_per_game - replacement_goals_per_game) * player_data['games_played'].iloc[0]
        
        # Assists above replacement
        replacement_assists_per_game = 0.12
        actual_assists_per_game = player_data['assists'].sum() / player_data['games_played'].iloc[0]
        assists_above_replacement = (actual_assists_per_game - replacement_assists_per_game) * player_data['games_played'].iloc[0]
        
        # Expected goals impact
        expected_goals_impact = player_data['individual_expected_goals'].sum() - (replacement_goals_per_game * player_data['games_played'].iloc[0])
        
        # Convert to WAR (roughly 6 goals = 1 win)
        offensive_war = (goals_above_replacement * 1.5 + assists_above_replacement + expected_goals_impact) / 6
        
        return offensive_war
        
    def calculate_defenseman_war(self, player_data: pd.DataFrame):
        """
        Defenseman WAR calculation
        """
        war_components = {
            'offensive_war': self.calculate_defenseman_offensive_war(player_data),
            'defensive_war': self.calculate_defenseman_defensive_war(player_data),
            'special_teams_war': self.calculate_special_teams_war(player_data),
            'ice_time_war': self.calculate_ice_time_war(player_data)
        }
        
        total_war = sum(war_components.values())
        
        return {
            'total_war': total_war,
            'components': war_components,
            'war_per_game': total_war / player_data['games_played'].iloc[0],
            'war_percentile': self.calculate_war_percentile(total_war, 'defensemen')
        }
```

---

## Injury Analysis Framework

### Cross-Position Injury Impact

```python
class CrossPositionInjuryAnalyzer:
    def __init__(self):
        self.injury_databases = {
            'primary': 'NHL injury reports',
            'secondary': 'Media injury tracking',
            'tertiary': 'Performance-based injury inference'
        }
        
    def analyze_injury_patterns_by_position(self, historical_data: pd.DataFrame):
        """
        Analyze injury patterns across all positions
        """
        position_injury_analysis = {}
        
        for position in ['goalies', 'forwards', 'defensemen']:
            position_data = historical_data[historical_data['position_group'] == position]
            
            injury_analysis = {
                'injury_frequency': self.calculate_injury_frequency(position_data),
                'injury_types': self.analyze_injury_types(position_data),
                'recovery_patterns': self.analyze_recovery_patterns(position_data),
                'fatigue_injury_correlation': self.analyze_fatigue_injury_correlation(position_data),
                'age_injury_relationship': self.analyze_age_injury_patterns(position_data),
                'workload_injury_threshold': self.identify_injury_thresholds(position_data)
            }
            
            position_injury_analysis[position] = injury_analysis
            
        return position_injury_analysis
        
    def calculate_injury_frequency(self, position_data: pd.DataFrame):
        """
        Calculate injury frequency metrics by position
        """
        injury_metrics = {
            'injuries_per_season': position_data.groupby(['player_id', 'season'])['injury_events'].sum().mean(),
            'games_missed_per_injury': position_data['games_missed'].sum() / position_data['injury_events'].sum(),
            'injury_rate_per_1000_games': (position_data['injury_events'].sum() / position_data['games_played'].sum()) * 1000,
            'career_ending_injury_rate': self.calculate_career_ending_rate(position_data),
            'recurring_injury_rate': self.calculate_recurring_injury_rate(position_data)
        }
        
        return injury_metrics
        
    def analyze_injury_types(self, position_data: pd.DataFrame):
        """
        Analyze types of injuries by position
        """
        injury_type_analysis = position_data.groupby('injury_type').agg({
            'injury_events': 'sum',
            'games_missed': 'sum',
            'return_performance_impact': 'mean',
            'recovery_time_days': 'mean'
        }).to_dict('index')
        
        # Calculate injury type percentages
        total_injuries = position_data['injury_events'].sum()
        
        for injury_type in injury_type_analysis:
            injury_type_analysis[injury_type]['percentage_of_total'] = \
                (injury_type_analysis[injury_type]['injury_events'] / total_injuries) * 100
                
        return injury_type_analysis
```

---

## Usage Patterns and Role Analysis

### Situational Usage Framework

```python
class SituationalUsageAnalyzer:
    def __init__(self):
        self.game_situations = {
            'even_strength': {'players_on_ice': 6, 'baseline': True},
            'power_play': {'players_on_ice': 6, 'advantage': True},
            'penalty_kill': {'players_on_ice': 5, 'disadvantage': True},
            'empty_net': {'players_on_ice': 6, 'special': True},
            'overtime_3v3': {'players_on_ice': 4, 'special': True},
            'shootout': {'players_on_ice': 2, 'special': True}
        }
        
    def analyze_player_usage_patterns(self, player_data: pd.DataFrame, position: str):
        """
        Analyze how players are used in different situations
        """
        usage_analysis = {
            'ice_time_distribution': self.analyze_ice_time_distribution(player_data),
            'situational_deployment': self.analyze_situational_deployment(player_data, position),
            'quality_of_competition': self.analyze_competition_quality(player_data),
            'zone_start_tendencies': self.analyze_zone_starts(player_data),
            'role_evolution': self.analyze_role_evolution(player_data)
        }
        
        return usage_analysis
        
    def analyze_situational_deployment(self, player_data: pd.DataFrame, position: str):
        """
        Analyze deployment in different game situations
        """
        situational_usage = {}
        
        for situation in self.game_situations.keys():
            situation_data = player_data[player_data['game_situation'] == situation]
            
            if len(situation_data) > 0:
                situational_usage[situation] = {
                    'ice_time_percentage': situation_data['time_on_ice_seconds'].sum() / player_data['time_on_ice_seconds'].sum(),
                    'points_per_60': (situation_data['points'].sum() / situation_data['time_on_ice_seconds'].sum()) * 3600,
                    'usage_rate': len(situation_data) / len(player_data),
                    'performance_vs_average': self.calculate_situational_performance_vs_average(situation_data, situation, position)
                }
                
        return situational_usage
        
    def analyze_role_evolution(self, player_data: pd.DataFrame):
        """
        Track how player roles evolve over career
        """
        career_seasons = player_data['season'].unique()
        role_evolution = {}
        
        for season in sorted(career_seasons):
            season_data = player_data[player_data['season'] == season]
            
            role_metrics = {
                'primary_role': self.identify_primary_role(season_data),
                'ice_time_rank_on_team': self.calculate_ice_time_rank(season_data),
                'offensive_role_score': self.calculate_offensive_role_score(season_data),
                'defensive_role_score': self.calculate_defensive_role_score(season_data),
                'special_teams_importance': self.calculate_special_teams_importance(season_data)
            }
            
            role_evolution[season] = role_metrics
            
        return role_evolution
```

This comprehensive multi-position framework expands the Kopitar project to analyze forwards, defensemen, and goalies with position-specific metrics, cross-position interactions, and unified injury/fatigue analysis across all NHL players.