# Research Questions & Hypotheses - Kopitar Project

## Primary Research Questions

### 1. Core Fatigue Impact
**RQ1.1**: How does consecutive game frequency affect goaltender save percentage?

**Hypotheses**:
- H1a: Goaltenders playing back-to-back games experience a statistically significant decrease in save percentage (expected: -0.008 to -0.012)
- H1b: The performance degradation is more pronounced in the second period of back-to-back games
- H1c: Goaltenders over age 32 show 50% greater performance decline in back-to-back scenarios

**Methodology**: 
- Paired t-tests comparing same goalie performance
- Mixed-effects regression controlling for opponent strength
- Age-stratified analysis with interaction terms

**Success Metrics**:
- Statistical significance: p < 0.05
- Effect size: Cohen's d > 0.3
- Model R² > 0.15

---

### 2. Travel Distance Effects
**RQ2.1**: What is the relationship between travel distance and goaltender performance?

**Hypotheses**:
- H2a: Every 1000 miles of travel in the previous 5 days decreases save percentage by 0.003-0.005
- H2b: Eastward travel has 1.5x greater negative impact than westward travel
- H2c: Travel impact is mitigated by arrival timing (2+ days before game)

**Methodology**:
- Linear regression with travel distance as continuous variable
- Directional analysis with timezone adjustments
- Survival analysis for performance threshold maintenance

**Variables to Control**:
- Team defensive quality
- Opponent offensive strength  
- Game importance (playoff race)
- Day of week

---

### 3. Cumulative Workload
**RQ3.1**: How does season-long workload accumulation affect late-season performance?

**Hypotheses**:
- H3a: Goaltenders with >65 games show progressive save percentage decline after game 50
- H3b: High-workload goalies (>70% of team games) have 2x injury risk
- H3c: Optimal workload is 55-60 games for sustained performance

**Methodology**:
- Time series analysis with changepoint detection
- Cox proportional hazards for injury risk
- Performance curve modeling with polynomial regression

**Key Indicators**:
- Rolling 10-game save percentage
- Days missed due to injury
- Quality start percentage trend

---

### 4. Recovery Patterns
**RQ4.1**: What is the optimal rest period between starts for peak performance?

**Hypotheses**:
- H4a: Performance peaks with 2-3 days rest between starts
- H4b: Rest beyond 7 days shows performance decline ("rust effect")
- H4c: Younger goalies (<27) require 25% less recovery time

**Methodology**:
- Non-linear regression for rest-performance curve
- Segmented analysis by age groups
- Bayesian modeling for individual optimization

---

### 5. Three-in-Four Nights
**RQ5.1**: How do compressed schedules (3 games in 4 nights) impact goaltender metrics?

**Hypotheses**:
- H5a: Third game shows -0.015 save percentage decline vs. first game
- H5b: High-danger save percentage drops by >5% in third game
- H5c: Recovery time needed post-3-in-4 is 4+ days for baseline return

**Methodology**:
- Repeated measures ANOVA
- Shot quality adjusted analysis
- Recovery curve modeling

---

## Secondary Research Questions

### 6. Altitude Effects
**RQ6.1**: Does altitude change affect goaltender performance?

**Hypotheses**:
- H6a: Games in Denver/Calgary show -0.005 save percentage for visiting goalies
- H6b: Altitude impact is amplified when combined with back-to-backs
- H6c: Acclimatization requires 48+ hours

### 7. Playoff Intensity
**RQ7.1**: How do playoff games differ in fatigue accumulation?

**Hypotheses**:
- H7a: Playoff games create 1.5x fatigue load vs regular season
- H7b: Consecutive playoff games show steeper performance decline
- H7c: Recovery time increases by 40% in playoffs

### 8. Backup Goalie Patterns
**RQ8.1**: Do backup goalies show different fatigue patterns?

**Hypotheses**:
- H8a: Irregular playing patterns create higher variance in performance
- H8b: "Rust" effect is 2x stronger for backups (>10 days between games)
- H8c: Back-to-back performance penalty is 50% higher for backups

### 9. Team System Effects  
**RQ9.1**: How do defensive systems moderate fatigue impact?

**Hypotheses**:
- H9a: High-shot-blocking teams reduce goalie fatigue by 20%
- H9b: Teams allowing fewer high-danger chances show less goalie performance variance
- H9c: System changes mid-season increase fatigue impact for 10-15 games

### 10. Injury Prediction
**RQ10.1**: Can fatigue metrics predict injury probability?

**Hypotheses**:
- H10a: Fatigue index >75 for 3+ consecutive games increases injury risk by 300%
- H10b: Specific movement patterns change 2-3 games before injury
- H10c: Workload spikes (>20% increase) are strongest injury predictor

---

## Advanced Analytics Questions

### 11. Machine Learning Applications
**RQ11.1**: Can ensemble models predict next-game performance better than traditional statistics?

**Target Metrics**:
- Prediction accuracy: >75% for performance categories
- AUC-ROC: >0.85 for binary outcomes
- RMSE: <0.015 for save percentage predictions

**Model Comparison**:
1. Baseline: Historical average
2. Linear: Multiple regression
3. Tree-based: Random Forest, XGBoost
4. Neural: LSTM for sequence modeling
5. Ensemble: Weighted combination

### 12. Individual Variation
**RQ12.1**: How much do fatigue responses vary between individual goalies?

**Clustering Approach**:
- Group goalies by fatigue response patterns
- Identify "workhorses" vs "rhythm" goalies
- Personalized fatigue thresholds

### 13. Real-time Adjustments
**RQ13.1**: Can in-game metrics predict fatigue-related performance drops?

**Live Indicators**:
- Lateral movement speed decline
- Rebound control degradation
- Positioning drift from optimal

---

## Validation Framework

### Statistical Requirements
1. **Sample Size**: Minimum 1000 goalie-games per analysis
2. **Significance Level**: α = 0.05 (Bonferroni adjusted for multiple comparisons)
3. **Power Analysis**: 80% power to detect medium effect sizes
4. **Cross-validation**: 5-fold for all predictive models

### External Validation
1. **Expert Review**: NHL goalie coaches validate findings
2. **Case Studies**: Deep dive on 5 specific goalies
3. **A/B Testing**: Live testing with partner teams
4. **Longitudinal**: Track predictions over full season

### Robustness Checks
1. **Sensitivity Analysis**: Vary fatigue weights ±20%
2. **Outlier Impact**: With/without extreme performances
3. **Era Effects**: Test on different seasons
4. **Team Effects**: Fixed effects models

---

## Expected Outcomes & Impact

### Academic Contributions
1. **Publication Targets**:
   - Journal of Sports Analytics
   - MIT Sloan Sports Analytics Conference
   - International Journal of Performance Analysis in Sport

2. **Novel Findings Expected**:
   - Quantified fatigue accumulation rates
   - Optimal rest algorithms
   - Personalized workload management

### Practical Applications
1. **Team Strategy**:
   - Goalie rotation optimization
   - Travel planning adjustments
   - Practice intensity modulation

2. **Player Health**:
   - Injury prevention protocols
   - Career longevity strategies
   - Recovery optimization

3. **Performance Enhancement**:
   - Peak performance timing
   - Playoff preparation strategies
   - In-season adjustments

### Industry Impact
1. **Adoption Metrics**:
   - 10+ NHL teams using system
   - Integration with team analytics
   - Media coverage and citations

2. **Financial Value**:
   - Reduced injury costs
   - Optimized contract values
   - Competitive advantages

---

## Research Timeline

### Phase 1 (Weeks 1-4): Data Collection & Cleaning
- Gather 3 seasons of comprehensive data
- Validate data quality
- Create analysis datasets

### Phase 2 (Weeks 5-8): Initial Analysis
- Test primary hypotheses
- Identify significant relationships
- Refine research questions

### Phase 3 (Weeks 9-12): Advanced Modeling
- Build predictive models
- Conduct robustness checks
- Validate with experts

### Phase 4 (Weeks 13-16): Publication & Implementation
- Draft research papers
- Create team presentations
- Develop implementation guides

---

## Ethical Considerations

1. **Player Privacy**: 
   - No personal health data
   - Aggregate reporting only
   - Opt-in for detailed analysis

2. **Competitive Fairness**:
   - Equal access to findings
   - No real-time gambling applications
   - Transparent methodology

3. **Player Welfare**:
   - Focus on health and longevity
   - Injury prevention priority
   - Player association collaboration