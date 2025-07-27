#!/usr/bin/env python
# coding: utf-8

# # NHL Goaltender Performance Analysis
# 
# This notebook analyzes how NHL goaltenders perform in various conditions, with a focus on:
# - Back-to-back games
# - High-workload periods
# - Travel impact (distance, time zones)

# Import required libraries
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pickle

# Set plotting style
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# ## 1. Data Loading and Preparation

# Choose a season to analyze
SEASON = '20222023'

# Function to load data
def load_data(season):
    """Load NHL goalie data for a specific season"""
    try:
        # Try loading from pickle first (faster)
        with open(f'../data/goalie_analysis_dataset_{season}.pkl', 'rb') as f:
            df = pickle.load(f)
        print(f"Loaded existing data for season {season}")
    except FileNotFoundError:
        # Fall back to CSV if pickle not available
        try:
            df = pd.read_csv(f'../data/goalie_analysis_dataset_{season}.csv')
            print(f"Loaded CSV data for season {season}")
        except FileNotFoundError:
            print(f"No data found for season {season}. Run data collection first.")
            return None
    
    # Convert date to datetime if it's not already
    if 'date' in df.columns and not pd.api.types.is_datetime64_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    return df

# Load data
df = load_data(SEASON)

if df is not None:
    # Display basic info
    print(f"Dataset shape: {df.shape}")
    print(f"Number of unique goalies: {df['player_name'].nunique()}")
    if 'date' in df.columns:
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Display first few rows
    print("\nFirst few rows of the dataset:")
    display(df.head())
else:
    print("Exiting due to missing data.")
    sys.exit(1)

# ## 2. Back-to-Back Games Analysis

# Filter out rows with missing save percentage
df_filtered = df.dropna(subset=['savePercentage'])

if 'is_back_to_back' in df_filtered.columns:
    # Save percentage by back-to-back status
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='is_back_to_back', y='savePercentage', data=df_filtered)
    plt.title('Save Percentage by Back-to-Back Status', fontsize=16)
    plt.xlabel('Back-to-Back Game (1 = Yes, 0 = No)', fontsize=14)
    plt.ylabel('Save Percentage', fontsize=14)
    plt.show()
    
    # T-test for statistical significance
    b2b_games = df_filtered[df_filtered['is_back_to_back'] == 1]['savePercentage']
    rested_games = df_filtered[df_filtered['is_back_to_back'] == 0]['savePercentage']
    
    if len(b2b_games) > 0 and len(rested_games) > 0:
        t_stat, p_value = stats.ttest_ind(b2b_games, rested_games, equal_var=False)
        
        print("\nT-test: Back-to-back vs. Rested Games")
        print(f"Back-to-back mean save %: {b2b_games.mean():.4f} (n={len(b2b_games)})")
        print(f"Rested games mean save %: {rested_games.mean():.4f} (n={len(rested_games)})")
        print(f"Difference: {b2b_games.mean() - rested_games.mean():.4f}")
        print(f"t-statistic: {t_stat:.4f}")
        print(f"p-value: {p_value:.4f}")
        if p_value < 0.05:
            print("The difference is statistically significant (p < 0.05)")
        else:
            print("The difference is not statistically significant (p >= 0.05)")
else:
    print("Back-to-back information not available in the dataset")

# ## 3. Travel Impact Analysis

if 'distance_traveled' in df_filtered.columns:
    # Create distance categories for easier analysis
    df_filtered['distance_category'] = pd.cut(
        df_filtered['distance_traveled'],
        bins=[0, 500, 1500, 3000, float('inf')],
        labels=['Short (<500km)', 'Medium (500-1500km)', 'Long (1500-3000km)', 'Very Long (>3000km)']
    )
    
    # Save percentage by distance category
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='distance_category', y='savePercentage', data=df_filtered)
    plt.title('Save Percentage by Travel Distance', fontsize=16)
    plt.xlabel('Distance Traveled', fontsize=14)
    plt.ylabel('Save Percentage', fontsize=14)
    plt.show()
    
    # Average save % by distance category
    distance_avg = df_filtered.groupby('distance_category')['savePercentage'].agg(['mean', 'count']).reset_index()
    distance_avg.columns = ['Distance Category', 'Average Save %', 'Number of Games']
    
    print("\nAverage Save Percentage by Travel Distance:")
    print(distance_avg)
    
    # Correlation between distance and save percentage
    corr = df_filtered['distance_traveled'].corr(df_filtered['savePercentage'])
    print(f"\nCorrelation between travel distance and save percentage: {corr:.4f}")
else:
    print("\nTravel distance information not available in the dataset")

# ## 4. Goaltender Workload Analysis

if 'games_last_7d' in df_filtered.columns:
    # Save percentage vs. games in last 7 days
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='games_last_7d', y='savePercentage', data=df_filtered)
    plt.title('Save Percentage vs. Games in Last 7 Days', fontsize=16)
    plt.xlabel('Games in Last 7 Days', fontsize=14)
    plt.ylabel('Save Percentage', fontsize=14)
    plt.show()
    
    # Average save % by games in last 7 days
    games_7d_avg = df_filtered.groupby('games_last_7d')['savePercentage'].agg(['mean', 'count']).reset_index()
    games_7d_avg.columns = ['Games in Last 7 Days', 'Average Save %', 'Number of Games']
    
    print("\nAverage Save Percentage by Games in Last 7 Days:")
    print(games_7d_avg)
    
    # Correlation
    corr = df_filtered['games_last_7d'].corr(df_filtered['savePercentage'])
    print(f"\nCorrelation between games in last 7 days and save percentage: {corr:.4f}")
else:
    print("\nRecent workload information not available in the dataset")

# ## 5. Individual Goalie Analysis

# Filter for goalies with sufficient games
min_games = 20
goalie_counts = df_filtered['player_name'].value_counts()
qualified_goalies = goalie_counts[goalie_counts >= min_games].index.tolist()

df_qualified = df_filtered[df_filtered['player_name'].isin(qualified_goalies)]

# Calculate average save percentage for each goalie
goalie_overall = df_qualified.groupby('player_name')['savePercentage'].mean().sort_values(ascending=False).reset_index()
goalie_overall.columns = ['Goalie', 'Average Save %']

print(f"\nTop Goalies by Overall Save Percentage (min {min_games} games):")
print(goalie_overall.head(10))

# Calculate back-to-back vs. rested performance
if 'is_back_to_back' in df_qualified.columns:
    b2b_performance = df_qualified.pivot_table(
        index='player_name',
        columns='is_back_to_back',
        values='savePercentage',
        aggfunc='mean'
    ).reset_index()
    
    # Rename columns for clarity
    b2b_performance.columns = ['Goalie', 'Rested', 'Back-to-Back']
    
    # Calculate difference
    b2b_performance['Difference'] = b2b_performance['Back-to-Back'] - b2b_performance['Rested']
    
    # Sort by difference (most improved in back-to-back)
    b2b_best = b2b_performance.sort_values('Difference', ascending=False)
    b2b_worst = b2b_performance.sort_values('Difference', ascending=True)
    
    print("\nGoalies Who Perform Best in Back-to-Back Games (vs. Rested):")
    print(b2b_best.head(5))
    
    print("\nGoalies Who Struggle Most in Back-to-Back Games (vs. Rested):")
    print(b2b_worst.head(5))

# ## 6. Regression Analysis

# Prepare data for regression
reg_df = df_filtered.copy()

# Create dummy variables for categorical features
if 'home_road' in reg_df.columns:
    reg_df['is_home'] = (reg_df['home_road'] == 'home').astype(int)

# Select features for the model
features = []

if 'is_back_to_back' in reg_df.columns:
    features.append('is_back_to_back')
    
if 'distance_traveled' in reg_df.columns:
    features.append('distance_traveled')
    
if 'days_since_last_game' in reg_df.columns:
    features.append('days_since_last_game')
    
if 'is_home' in reg_df.columns:
    features.append('is_home')
    
if 'games_last_7d' in reg_df.columns:
    features.append('games_last_7d')
    
if 'timezone_diff' in reg_df.columns:
    features.append('timezone_diff')

if len(features) > 0:
    # Create formula for statsmodels
    formula = 'savePercentage ~ ' + ' + '.join(features)
    
    try:
        # Fit linear regression model
        model = ols(formula, data=reg_df).fit()
        
        # Display model summary
        print("\nRegression Analysis Results:")
        print(model.summary())
        
    except Exception as e:
        print(f"\nError fitting regression model: {e}")
else:
    print("\nNot enough features available for regression analysis")
