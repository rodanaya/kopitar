# Advanced Metrics Framework - NHL Analytics Enhancement

## Overview
**Objective**: Integrate sophisticated hockey analytics metrics to provide deeper insights into player performance, team dynamics, and fatigue impacts across all positions.

**Metric Categories**:
- **Possession Metrics**: Corsi, Fenwick, zone time
- **Expected Goals**: xG, xGA, GSAx, individual xG
- **Efficiency Metrics**: PDO, shooting%, save%, on-ice percentages
- **Context Metrics**: Quality of Competition, Quality of Teammates
- **Micro-stats**: Zone entries/exits, shot assists, screens
- **Fatigue-Adjusted**: All metrics normalized for fatigue state

---

## Core Advanced Metrics by Category

### 1. Possession and Shot Metrics

```python
POSSESSION_METRICS = {
    "corsi": {
        "definition": "All shot attempts for/against while player on ice",
        "calculation": "(Shots + Missed Shots + Blocked Shots) For vs Against",
        "positions": ["forwards", "defensemen"],
        "fatigue_sensitivity": "high",
        "interpretation": {
            "excellent": ">60%",
            "good": "55-60%",
            "average": "48-55%",
            "poor": "<48%"
        }
    },
    
    "fenwick": {
        "definition": "Unblocked shot attempts for/against while player on ice",
        "calculation": "(Shots + Missed Shots) For vs Against",
        "positions": ["forwards", "defensemen"],
        "fatigue_sensitivity": "high",
        "interpretation": {
            "excellent": ">58%",
            "good": "53-58%",
            "average": "47-53%",
            "poor": "<47%"
        }
    },
    
    "corsi_relative": {
        "definition": "Player's Corsi% minus team's Corsi% when player off ice",
        "calculation": "Player CF% - Team CF% (without player)",
        "positions": ["forwards", "defensemen"],
        "fatigue_sensitivity": "very_high",
        "interpretation": {
            "excellent": ">+5%",
            "good": "+2% to +5%",
            "average": "-2% to +2%",
            "poor": "<-2%"
        }
    },
    
    "shot_share": {
        "definition": "Percentage of all shots taken by team while player on ice",
        "calculation": "Shots For / (Shots For + Shots Against)",
        "positions": ["forwards", "defensemen"],
        "fatigue_sensitivity": "medium",
        "baseline": 0.50
    }
}
```

### 2. Expected Goals Framework

```python
class ExpectedGoalsCalculator:
    def __init__(self):
        self.xg_model = self.load_expected_goals_model()
        self.shot_quality_factors = {
            'distance': 0.25,
            'angle': 0.20,
            'shot_type': 0.15,
            'traffic': 0.10,
            'rebound': 0.15,
            'rush': 0.10,
            'one_timer': 0.05
        }
        
    def calculate_individual_expected_goals(self, shot_data: pd.DataFrame):
        """
        Calculate expected goals for individual shots
        """
        xg_values = []
        
        for _, shot in shot_data.iterrows():
            shot_xg = self.calculate_shot_xg({
                'distance_feet': shot['distance'],
                'angle_degrees': shot['angle'],
                'shot_type': shot['shot_type'],
                'is_rebound': shot['is_rebound'],
                'is_rush': shot['is_rush'],
                'is_one_timer': shot['is_one_timer'],
                'traffic_count': shot['players_in_front'],
                'shooter_fatigue': shot['shooter_fatigue_index']
            })
            
            xg_values.append(shot_xg)
            
        return xg_values
        
    def calculate_shot_xg(self, shot_features: dict):
        """
        Calculate expected goal probability for a single shot
        """
        # Base probability from distance and angle
        base_xg = self.distance_angle_xg(shot_features['distance_feet'], shot_features['angle_degrees'])
        
        # Shot type modifiers
        shot_type_multiplier = {
            'wrist': 1.0,
            'slap': 0.9,
            'snap': 1.1,
            'tip': 1.3,
            'deflection': 1.4,
            'wrap': 0.7,
            'backhand': 0.8
        }.get(shot_features['shot_type'], 1.0)
        
        # Situation modifiers
        rebound_multiplier = 1.6 if shot_features['is_rebound'] else 1.0
        rush_multiplier = 1.2 if shot_features['is_rush'] else 1.0
        one_timer_multiplier = 1.3 if shot_features['is_one_timer'] else 1.0
        
        # Traffic modifier (reduces xG due to screens but can deflect)
        traffic_modifier = max(0.8, 1.0 - (shot_features['traffic_count'] * 0.05))
        
        # Fatigue modifier (tired players less accurate)
        fatigue_modifier = max(0.7, 1.0 - (shot_features['shooter_fatigue'] / 100 * 0.3))
        
        final_xg = (base_xg * shot_type_multiplier * rebound_multiplier * 
                   rush_multiplier * one_timer_multiplier * traffic_modifier * fatigue_modifier)
        
        return min(final_xg, 0.95)  # Cap at 95% probability
        
    def distance_angle_xg(self, distance: float, angle: float):
        """
        Base xG calculation from distance and angle
        """
        # Logistic regression coefficients (simplified)
        # Real model would use more sophisticated ML
        distance_factor = -0.1 * distance + 8
        angle_factor = -0.05 * abs(angle) + 2
        
        logit = distance_factor + angle_factor - 3.5
        xg = 1 / (1 + np.exp(-logit))
        
        return max(0.01, min(xg, 0.95))
```

### 3. PDO and Efficiency Metrics

```python
EFFICIENCY_METRICS = {
    "pdo": {
        "definition": "Shooting percentage + save percentage while player on ice",
        "calculation": "(Goals For / Shots For) + (Saves / Shots Against)",
        "baseline": 1.000,
        "positions": ["forwards", "defensemen"],
        "interpretation": {
            "unsustainably_high": ">1.025",
            "high": "1.010-1.025",
            "average": "0.990-1.010",
            "low": "0.975-0.990",
            "unsustainably_low": "<0.975"
        },
        "regression_tendency": "strong",
        "sample_size_stability": "~1000 minutes"
    },
    
    "individual_shooting_percentage": {
        "definition": "Goals scored / shots taken by individual player",
        "calculation": "Goals / Shots",
        "positions": ["forwards", "defensemen"],
        "career_averages": {
            "elite_scorer": 0.15,
            "good_scorer": 0.12,
            "average_forward": 0.09,
            "defensive_forward": 0.07,
            "offensive_defenseman": 0.06,
            "defensive_defenseman": 0.04
        }
    },
    
    "on_ice_shooting_percentage": {
        "definition": "Team shooting percentage while player on ice",
        "calculation": "Goals For / Shots For (while player on ice)",
        "baseline": 0.085,
        "positions": ["forwards", "defensemen"],
        "fatigue_impact": "high"
    },
    
    "on_ice_save_percentage": {
        "definition": "Team save percentage while player on ice",
        "calculation": "Saves / Shots Against (while player on ice)",
        "baseline": 0.915,
        "positions": ["forwards", "defensemen"],
        "fatigue_impact": "medium"
    }
}
```

### 4. Quality of Competition and Teammates

```python
class QualityMetricsCalculator:
    def __init__(self):
        self.player_ratings = self.load_player_quality_ratings()
        
    def calculate_quality_of_competition(self, player_data: pd.DataFrame):
        """
        Calculate average quality of opposition faced
        """
        opposition_ratings = []
        
        for _, game in player_data.iterrows():
            # Get opposing players who were on ice against this player
            opposing_players = self.get_opposing_players(game)
            
            # Weight by ice time faced against each opponent
            weighted_opposition = []
            for opp_player, time_against in opposing_players.items():
                player_rating = self.player_ratings.get(opp_player, 0.5)  # Default to average
                weighted_opposition.append(player_rating * time_against)
                
            if weighted_opposition:
                game_qoc = sum(weighted_opposition) / sum(time for _, time in opposing_players.items())
                opposition_ratings.append(game_qoc)
                
        return {
            'avg_quality_of_competition': np.mean(opposition_ratings),
            'qoc_variance': np.var(opposition_ratings),
            'hardest_competition_faced': max(opposition_ratings) if opposition_ratings else 0,
            'easiest_competition_faced': min(opposition_ratings) if opposition_ratings else 0
        }
        
    def calculate_quality_of_teammates(self, player_data: pd.DataFrame):
        """
        Calculate average quality of teammates played with
        """
        teammate_ratings = []
        
        for _, game in player_data.iterrows():
            teammates = self.get_teammates_on_ice(game)
            
            weighted_teammates = []
            for teammate, time_with in teammates.items():
                teammate_rating = self.player_ratings.get(teammate, 0.5)
                weighted_teammates.append(teammate_rating * time_with)
                
            if weighted_teammates:
                game_qot = sum(weighted_teammates) / sum(time for _, time in teammates.items())
                teammate_ratings.append(game_qot)
                
        return {
            'avg_quality_of_teammates': np.mean(teammate_ratings),
            'qot_variance': np.var(teammate_ratings),
            'best_teammates': max(teammate_ratings) if teammate_ratings else 0,
            'worst_teammates': min(teammate_ratings) if teammate_ratings else 0
        }
```

### 5. Micro-Statistics Framework

```python
MICRO_STATS = {
    "zone_entries": {
        "controlled_entries": "Entries with possession retained",
        "dump_ins": "Entries without possession",
        "carry_ins": "Skating puck across blue line",
        "pass_ins": "Passing puck across blue line",
        "success_rate": "Controlled entries / total entries"
    },
    
    "zone_exits": {
        "controlled_exits": "Exits with possession retained",
        "clearing_attempts": "Exits without possession",
        "success_rate": "Controlled exits / total exit attempts",
        "under_pressure": "Exits while being forechecked"
    },
    
    "shot_contributions": {
        "shot_assists": "Passes leading directly to shots",
        "screen_assists": "Screens leading to goals",
        "deflection_attempts": "Attempts to deflect shots",
        "rebound_creation": "Shots creating rebound opportunities"
    },
    
    "defensive_actions": {
        "stick_checks": "Successful stick-on-puck checks",
        "body_checks": "Successful body checks",
        "poke_checks": "Successful poke checks",
        "shot_blocks": "Shots blocked by player",
        "pass_breakups": "Passes intercepted or broken up"
    }
}

class MicroStatsCalculator:
    def __init__(self):
        self.tracking_data = self.load_player_tracking_data()
        
    def calculate_zone_entry_metrics(self, player_data: pd.DataFrame):
        """
        Calculate zone entry success and methods
        """
        zone_entries = player_data[player_data['event_type'] == 'zone_entry']
        
        entry_metrics = {
            'total_entries': len(zone_entries),
            'controlled_entries': len(zone_entries[zone_entries['controlled'] == True]),
            'controlled_entry_rate': len(zone_entries[zone_entries['controlled'] == True]) / len(zone_entries) if len(zone_entries) > 0 else 0,
            'carry_in_rate': len(zone_entries[zone_entries['method'] == 'carry']) / len(zone_entries) if len(zone_entries) > 0 else 0,
            'pass_in_rate': len(zone_entries[zone_entries['method'] == 'pass']) / len(zone_entries) if len(zone_entries) > 0 else 0,
            'dump_in_rate': len(zone_entries[zone_entries['method'] == 'dump']) / len(zone_entries) if len(zone_entries) > 0 else 0
        }
        
        return entry_metrics
        
    def calculate_shot_assist_metrics(self, player_data: pd.DataFrame):
        """
        Calculate shot creation and assistance metrics
        """
        shot_events = player_data[player_data['event_type'].isin(['shot', 'goal'])]
        
        # Find plays where player created shot opportunity
        shot_assists = shot_events[
            (shot_events['primary_assist'] == player_data['player_id'].iloc[0]) |
            (shot_events['secondary_assist'] == player_data['player_id'].iloc[0]) |
            (shot_events['screen_by'] == player_data['player_id'].iloc[0])
        ]
        
        assist_metrics = {
            'shot_assists': len(shot_assists[shot_assists['resulted_in_shot'] == True]),
            'goal_assists': len(shot_assists[shot_assists['resulted_in_goal'] == True]),
            'screen_assists': len(shot_assists[shot_assists['screen_by'] == player_data['player_id'].iloc[0]]),
            'shot_assist_rate': len(shot_assists) / len(shot_events) if len(shot_events) > 0 else 0
        }
        
        return assist_metrics
```

### 6. Fatigue-Adjusted Advanced Metrics

```python
class FatigueAdjustedMetrics:
    def __init__(self):
        self.fatigue_adjustments = self.load_fatigue_adjustment_factors()
        
    def calculate_fatigue_adjusted_corsi(self, player_data: pd.DataFrame):
        """
        Adjust Corsi metrics for player fatigue levels
        """
        fatigue_adjusted_corsi = []
        
        for _, game in player_data.iterrows():
            raw_corsi = game['corsi_for'] / (game['corsi_for'] + game['corsi_against'])
            fatigue_index = game['fatigue_index']
            
            # Fatigue impact on possession (tired players lose more battles)
            fatigue_penalty = self.calculate_fatigue_penalty(fatigue_index, 'possession')
            adjusted_corsi = raw_corsi * (1 - fatigue_penalty)
            
            fatigue_adjusted_corsi.append({
                'game_date': game['game_date'],
                'raw_corsi': raw_corsi,
                'fatigue_index': fatigue_index,
                'fatigue_penalty': fatigue_penalty,
                'adjusted_corsi': adjusted_corsi
            })
            
        return pd.DataFrame(fatigue_adjusted_corsi)
        
    def calculate_fatigue_penalty(self, fatigue_index: float, metric_type: str):
        """
        Calculate performance penalty based on fatigue level
        """
        penalty_rates = {
            'possession': 0.002,    # 0.2% penalty per fatigue point
            'shooting': 0.003,      # 0.3% penalty per fatigue point
            'defensive': 0.0025,    # 0.25% penalty per fatigue point
            'speed': 0.004,         # 0.4% penalty per fatigue point
            'decision_making': 0.0035  # 0.35% penalty per fatigue point
        }
        
        base_penalty_rate = penalty_rates.get(metric_type, 0.003)
        
        # Non-linear fatigue impact (accelerates at high fatigue)
        if fatigue_index < 60:
            penalty = fatigue_index * base_penalty_rate * 0.5
        elif fatigue_index < 80:
            penalty = 30 * base_penalty_rate * 0.5 + (fatigue_index - 60) * base_penalty_rate
        else:
            penalty = 30 * base_penalty_rate * 0.5 + 20 * base_penalty_rate + (fatigue_index - 80) * base_penalty_rate * 2
            
        return min(penalty, 0.4)  # Cap penalty at 40%
        
    def calculate_expected_fatigue_impact(self, player_data: pd.DataFrame, upcoming_games: int):
        """
        Predict performance impact of upcoming schedule
        """
        current_fatigue = player_data['fatigue_index'].iloc[-1]
        
        # Model fatigue accumulation over upcoming games
        projected_fatigue = current_fatigue
        fatigue_projections = []
        
        for game_num in range(upcoming_games):
            # Fatigue accumulation per game (varies by position)
            position = player_data['position'].iloc[0]
            base_accumulation = {
                'G': 8,   # Goalies accumulate fatigue differently
                'D': 6,   # Defensemen play more minutes
                'F': 5    # Forwards
            }.get(position, 5)
            
            projected_fatigue += base_accumulation
            
            # Expected performance impact
            performance_impact = {
                'game_number': game_num + 1,
                'projected_fatigue': projected_fatigue,
                'corsi_impact': self.calculate_fatigue_penalty(projected_fatigue, 'possession'),
                'shooting_impact': self.calculate_fatigue_penalty(projected_fatigue, 'shooting'),
                'overall_performance': self.calculate_overall_performance_impact(projected_fatigue)
            }
            
            fatigue_projections.append(performance_impact)
            
        return fatigue_projections
```

### 7. Advanced Goalie Metrics

```python
ADVANCED_GOALIE_METRICS = {
    "goals_saved_above_expected": {
        "definition": "Goals prevented beyond what expected based on shot quality",
        "calculation": "Expected Goals Against - Actual Goals Against",
        "elite_threshold": ">+10 per season",
        "fatigue_sensitivity": "very_high"
    },
    
    "high_danger_save_percentage": {
        "definition": "Save percentage on high-danger scoring chances",
        "high_danger_areas": ["slot", "crease", "backdoor"],
        "elite_threshold": ">0.850",
        "average": "0.800-0.830"
    },
    
    "rebound_control_percentage": {
        "definition": "Percentage of saves that don't create rebound opportunities",
        "calculation": "Saves without rebounds / Total saves",
        "elite_threshold": ">75%",
        "fatigue_impact": "high"
    },
    
    "cross_crease_save_percentage": {
        "definition": "Save percentage on cross-crease passes and lateral plays",
        "elite_threshold": ">0.750",
        "fatigue_sensitivity": "extreme"
    }
}
```

### 8. Team Context Metrics

```python
class TeamContextAnalyzer:
    def __init__(self):
        self.team_systems = self.load_team_system_data()
        
    def calculate_system_adjusted_metrics(self, player_data: pd.DataFrame):
        """
        Adjust player metrics based on team system
        """
        team_id = player_data['team_id'].iloc[0]
        season = player_data['season'].iloc[0]
        
        team_system = self.team_systems.get((team_id, season), 'balanced')
        
        system_adjustments = {
            'defensive_trap': {
                'corsi_adjustment': -0.03,  # Lower possession in trap system
                'goals_for_adjustment': -0.15,  # Fewer goals scored
                'goals_against_adjustment': -0.20  # Fewer goals allowed
            },
            'run_and_gun': {
                'corsi_adjustment': +0.02,
                'goals_for_adjustment': +0.10,
                'goals_against_adjustment': +0.15
            },
            'balanced': {
                'corsi_adjustment': 0,
                'goals_for_adjustment': 0,
                'goals_against_adjustment': 0
            }
        }
        
        adjustments = system_adjustments.get(team_system, system_adjustments['balanced'])
        
        return {
            'system_type': team_system,
            'adjusted_metrics': self.apply_system_adjustments(player_data, adjustments)
        }
```

This comprehensive advanced metrics framework provides sophisticated analytics tools including PDO, expected goals, possession metrics, and fatigue-adjusted statistics to deeply analyze player performance across all positions in the Kopitar project.