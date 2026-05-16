# Fatigue Metric Validation Framework - Kopitar Platform

## Overview
Based on stakeholder interviews, this document establishes the validation framework for our fatigue metrics, ensuring they align with real-world NHL coaching needs and scientific validity.

## Stakeholder-Validated Metrics

### 🥇 **Tier 1: Primary Fatigue Indicators**

#### **1. Goals Saved Above Expected (GSAx) - Weighted Score**
**Stakeholder Consensus**: "Most sensitive metric to all types of fatigue"

**Calculation Enhancements**:
```python
def calculate_fatigue_adjusted_gsax(game_data, fatigue_context):
    base_gsax = calculate_standard_gsax(game_data)
    
    # Fatigue-specific adjustments based on stakeholder insights
    fatigue_multipliers = {
        'back_to_back': 1.15,           # 15% more sensitive in B2B
        'third_in_four': 1.25,          # 25% more sensitive 
        'extended_fatigue': 1.35,       # 35% more sensitive 4+ starts
        'travel_fatigue': 1.10          # 10% more sensitive after travel
    }
    
    context_weight = determine_fatigue_context(fatigue_context)
    adjusted_gsax = base_gsax * fatigue_multipliers.get(context_weight, 1.0)
    
    return adjusted_gsax
```

**Validation Criteria**:
- **Normal rest baseline**: GSAx ≥ +0.05 per game
- **Fatigue threshold**: GSAx < -0.15 per game for 2+ consecutive games
- **Recovery indicator**: Return to baseline within 48-72 hours

#### **2. Rebound Control Percentage**
**Stakeholder Quote**: *"First thing that goes when a goalie gets tired is rebound control"*

**Enhanced Calculation**:
```python
def calculate_rebound_control_fatigue_score(shot_data, rebounds):
    # Weight by shot danger level (stakeholder insight)
    danger_weights = {
        'high_danger': 3.0,     # High-danger rebounds most indicative
        'medium_danger': 2.0,
        'low_danger': 1.0
    }
    
    weighted_rebounds = sum(
        rebounds[danger] * danger_weights[danger] 
        for danger in danger_weights
    )
    
    total_weighted_shots = sum(
        shot_data[danger] * danger_weights[danger] 
        for danger in danger_weights
    )
    
    control_percentage = 1 - (weighted_rebounds / total_weighted_shots)
    
    return control_percentage
```

**Fatigue Thresholds** (Stakeholder-Validated):
- **Fresh**: 92%+ rebound control
- **Mild fatigue**: 88-92% rebound control
- **Moderate fatigue**: 82-88% rebound control
- **Severe fatigue**: <82% rebound control

#### **3. High-Danger Save Percentage**
**Stakeholder Insight**: *"Mental fatigue shows up first on high-danger chances"*

**Context-Aware Calculation**:
```python
def calculate_hd_save_percentage_with_context(saves, shots, game_context):
    base_percentage = saves / shots
    
    # Context adjustments based on stakeholder feedback
    context_adjustments = {
        'playoff_intensity': -0.02,     # 2% harder in playoff-style games
        'rivalry_game': -0.015,         # 1.5% harder in rivalry games
        'back_to_back': -0.025,         # 2.5% harder in B2B
        'overtime': -0.03               # 3% harder in OT
    }
    
    adjusted_baseline = base_percentage
    for context, adjustment in context_adjustments.items():
        if game_context.get(context, False):
            adjusted_baseline -= adjustment
    
    return max(0, adjusted_baseline)  # Floor at 0%
```

### 🥈 **Tier 2: Supporting Fatigue Indicators**

#### **4. Lateral Movement Efficiency Score**
**Stakeholder Validation**: *"Tired goalies move slower post-to-post and their pushoffs are weaker"*

**Biomechanical Tracking**:
```python
def calculate_lateral_movement_score(movement_data):
    # Based on video analysis insights from coaches
    movement_metrics = {
        'push_off_power': movement_data['velocity_change'],
        'recovery_time': 1 / movement_data['time_to_set'],
        'distance_efficiency': movement_data['direct_distance'] / movement_data['actual_distance'],
        'stance_maintenance': movement_data['stance_depth_consistency']
    }
    
    # Weights based on stakeholder importance ranking
    weights = {
        'push_off_power': 0.35,         # Most important per coaches
        'recovery_time': 0.30,          # Second most important
        'distance_efficiency': 0.20,    # Technique indicator
        'stance_maintenance': 0.15      # Fatigue-specific indicator
    }
    
    efficiency_score = sum(
        movement_metrics[metric] * weights[metric]
        for metric in weights
    )
    
    return efficiency_score
```

#### **5. Second-Chance Save Percentage**
**Expert Insight**: *"How a goalie handles second chances tells you everything about their current state"*

**Calculation with Fatigue Weighting**:
```python
def calculate_second_chance_performance(save_data):
    # Different weights for different second-chance types
    second_chance_types = {
        'immediate_rebound': 2.5,       # Most demanding
        'deflection_recovery': 2.0,     # High difficulty
        'scramble_sequence': 3.0,       # Highest fatigue indicator
        'cross_ice_pass': 1.5           # Positioning-dependent
    }
    
    weighted_performance = sum(
        save_data[sc_type]['saves'] / save_data[sc_type]['attempts'] * weight
        for sc_type, weight in second_chance_types.items()
        if save_data[sc_type]['attempts'] > 0
    )
    
    return weighted_performance / sum(second_chance_types.values())
```

### 🥉 **Tier 3: Contextual & Behavioral Indicators**

#### **6. Communication Frequency Index**
**Stakeholder Observation**: *"Tired goalies talk less to their D-men, and when they do, it's less helpful"*

**Audio Analysis Framework**:
```python
def calculate_communication_fatigue_score(audio_data, game_time):
    # Based on stakeholder-identified patterns
    communication_factors = {
        'frequency': count_verbal_communications(audio_data),
        'clarity': assess_speech_clarity(audio_data),
        'timing': assess_communication_timing(audio_data, game_time),
        'content_quality': assess_information_quality(audio_data)
    }
    
    # Fatigue-specific weights from coaching observations
    fatigue_weights = {
        'frequency': 0.40,      # Most obvious indicator
        'timing': 0.30,         # When they talk matters
        'clarity': 0.20,        # Physical fatigue indicator
        'content_quality': 0.10 # Mental fatigue indicator
    }
    
    communication_score = sum(
        communication_factors[factor] * fatigue_weights[factor]
        for factor in fatigue_weights
    )
    
    return communication_score
```

#### **7. Equipment Adjustment Frequency**
**Coach Insight**: *"When goalies start fiddling with their gear more during play, they're getting uncomfortable - usually means fatigue"*

**Behavioral Tracking**:
```python
def track_equipment_adjustments(video_data, game_periods):
    # Stakeholder-identified adjustment types
    adjustment_types = {
        'mask_adjustment': 1.0,         # Common fatigue behavior
        'pad_strap_adjustment': 1.5,    # More significant indicator
        'glove_adjustment': 2.0,        # High fatigue correlation
        'blocker_adjustment': 1.5,      # Equipment positioning issue
        'excessive_water_breaks': 2.5   # Strong fatigue indicator
    }
    
    period_adjustments = {}
    for period in game_periods:
        period_score = sum(
            count_adjustments(video_data, period, adj_type) * weight
            for adj_type, weight in adjustment_types.items()
        )
        period_adjustments[period] = period_score
    
    # Fatigue typically increases through game
    fatigue_progression = calculate_progression_score(period_adjustments)
    
    return fatigue_progression
```

## Validation Testing Framework

### 🧪 **Historical Data Validation**

#### **Retrospective Analysis Protocol**
```python
def validate_fatigue_metrics_historical(seasons_data, injury_data):
    """
    Validate fatigue metrics against historical known fatigue cases
    """
    validation_cases = {
        'confirmed_fatigue_games': extract_stakeholder_identified_cases(),
        'injury_preceded_games': extract_pre_injury_games(injury_data),
        'performance_decline_sequences': identify_known_decline_periods(),
        'recovery_confirmation_games': identify_post_rest_improvements()
    }
    
    metric_performance = {}
    for metric_name, metric_function in fatigue_metrics.items():
        performance_scores = test_metric_against_cases(
            metric_function, 
            validation_cases,
            seasons_data
        )
        metric_performance[metric_name] = performance_scores
    
    return metric_performance
```

#### **Validation Criteria**
- **Sensitivity**: 70%+ detection of stakeholder-confirmed fatigue cases
- **Specificity**: 80%+ correct identification of non-fatigue games  
- **Predictive Power**: 24-48 hour advance warning capability
- **False Positive Rate**: <15% for high-fatigue alerts

### 🎯 **Real-Time Validation Protocol**

#### **Live Game Testing**
```python
def real_time_validation_protocol(live_game_data, stakeholder_observers):
    """
    Real-time validation with stakeholder observers during live games
    """
    real_time_scores = calculate_all_fatigue_metrics(live_game_data)
    
    # Stakeholder assessment (coaches watching)
    stakeholder_fatigue_assessment = {
        'period_1': stakeholder_observers.assess_period(1),
        'period_2': stakeholder_observers.assess_period(2),
        'period_3': stakeholder_observers.assess_period(3)
    }
    
    # Compare algorithmic vs. human expert assessment
    correlation_scores = calculate_correlation(
        real_time_scores,
        stakeholder_fatigue_assessment
    )
    
    return {
        'algorithm_scores': real_time_scores,
        'expert_scores': stakeholder_fatigue_assessment,
        'correlation': correlation_scores,
        'validation_timestamp': datetime.now()
    }
```

### 📊 **Cross-Validation with External Data**

#### **Sports Science Validation**
```python
def validate_against_sports_science_data(fatigue_scores, physiological_data):
    """
    Validate fatigue metrics against objective physiological measures
    """
    physiological_indicators = {
        'heart_rate_variability': physiological_data['hrv'],
        'lactate_levels': physiological_data['lactate'],
        'hydration_status': physiological_data['urine_specific_gravity'],
        'sleep_quality': physiological_data['sleep_metrics'],
        'reaction_time': physiological_data['cognitive_tests']
    }
    
    correlation_matrix = calculate_correlations(
        fatigue_scores,
        physiological_indicators
    )
    
    return correlation_matrix
```

## Stakeholder Feedback Integration

### 🔄 **Continuous Validation Loop**

#### **Weekly Coach Feedback Protocol**
```python
def weekly_stakeholder_validation(week_fatigue_predictions, actual_outcomes):
    """
    Weekly validation sessions with coaching staff
    """
    feedback_categories = {
        'prediction_accuracy': compare_predictions_to_outcomes(),
        'actionability': assess_recommendation_utility(),
        'false_positives': identify_incorrect_alerts(),
        'missed_fatigue': identify_undetected_cases(),
        'recovery_timing': validate_recovery_predictions()
    }
    
    adjustment_recommendations = generate_algorithm_adjustments(
        feedback_categories
    )
    
    return adjustment_recommendations
```

### 📈 **Performance Improvement Tracking**

#### **Season-Long Validation**
- **Monthly accuracy assessments** with participating teams
- **Quarterly algorithm refinements** based on feedback
- **End-of-season comprehensive review** with all stakeholders
- **Off-season model retraining** incorporating lessons learned

## Implementation Validation Phases

### **Phase 1: Offline Validation** (Months 1-2)
- Historical data testing against stakeholder-confirmed cases
- Algorithm calibration using expert-labeled fatigue instances
- Cross-validation with sports science research findings

### **Phase 2: Controlled Testing** (Months 3-4)
- Partnership with 1-2 NHL teams for controlled validation
- Real-time testing during practice sessions
- Comparison with existing team assessment methods

### **Phase 3: Live Deployment** (Months 5-6)
- Full game testing with stakeholder observation
- Real-time feedback collection during games
- Continuous algorithm adjustment based on expert input

### **Phase 4: League Validation** (Months 7-12)
- Expansion to multiple teams across different playing styles
- Season-long performance tracking and validation
- Comprehensive accuracy and utility assessment

## Success Metrics

### **Technical Validation**
- **Accuracy**: 75%+ prediction accuracy vs. stakeholder assessment
- **Precision**: 80%+ for high-fatigue alerts
- **Recall**: 70%+ for actual fatigue detection
- **Lead Time**: 24-48 hours advance warning capability

### **Stakeholder Adoption**
- **Daily Usage**: Active use by coaching staff during season
- **Decision Impact**: Influence on actual rest/rotation decisions
- **Satisfaction**: 8/10+ rating from coaching staff
- **Retention**: Continued use season-over-season

This validation framework ensures our fatigue metrics are not just statistically sound, but practically useful for NHL coaching staff and grounded in real-world hockey expertise.