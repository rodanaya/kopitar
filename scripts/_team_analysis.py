import sqlite3, pandas as pd, scipy.stats as stats

DIVISIONS = {
    'Atlantic':   ['BOS','BUF','DET','FLA','MTL','OTT','TBL','TOR'],
    'Metropolitan': ['CAR','CBJ','NJD','NYI','NYR','PHI','PIT','WSH'],
    'Central':    ['CHI','COL','DAL','MIN','NSH','STL','WPG','UTA','ARI'],
    'Pacific':    ['ANA','CGY','EDM','LAK','SJS','SEA','VGK','VAN'],
}
TEAM_DIV = {t:d for d, ts in DIVISIONS.items() for t in ts}

conn = sqlite3.connect('data/scraped/kopitar.db')
df = pd.read_sql('SELECT * FROM goalie_game_logs', conn)
ss = pd.read_sql('SELECT DISTINCT player_id, player_name FROM goalie_season_stats', conn)
conn.close()
df = df.merge(ss, on='player_id', how='left')
df['division'] = df['team'].map(TEAM_DIV).fillna('Unknown')
reg = df[df['game_type']==2]

print('=== DIVISION ANALYSIS ===')
for div in ['Pacific','Central','Metropolitan','Atlantic']:
    d = reg[reg['division']==div]
    b2b = d[d['is_back_to_back']==1]['save_pct'].dropna()
    rest = d[d['is_back_to_back']==0]['save_pct'].dropna()
    avg_travel = d['travel_miles'].mean()
    delta = b2b.mean()-rest.mean() if len(b2b) > 0 else float('nan')
    print(f"{div:15s} games={len(d):5d} avg_SV={d['save_pct'].mean():.4f} B2B_n={len(b2b):3d} delta={delta:+.4f} avg_travel={avg_travel:.0f}mi")

print()
print('=== TEAM B2B IMPACT (top 10 most-impacted) ===')
teams = []
for team, g in reg.groupby('team'):
    b2b = g[g['is_back_to_back']==1]['save_pct'].dropna()
    rest = g[g['is_back_to_back']==0]['save_pct'].dropna()
    if len(b2b) >= 5:
        teams.append({
            'team': team,
            'div': TEAM_DIV.get(team,'?'),
            'b2b_n': len(b2b),
            'b2b_sv': b2b.mean(),
            'rest_sv': rest.mean(),
            'delta': b2b.mean()-rest.mean(),
            'avg_travel': g['travel_miles'].mean()
        })
teams.sort(key=lambda x: x['delta'])
print(f"  {'Team':<5} {'Division':<15} {'B2B SV%':<10} {'Rest SV%':<10} {'Delta':<9} {'n B2B':<7} {'Avg travel'}")
for t in teams[:10]:
    print(f"  {t['team']:<5} {t['div']:<15} {t['b2b_sv']:.4f}     {t['rest_sv']:.4f}     {t['delta']:+.4f}   {t['b2b_n']:<7} {t['avg_travel']:.0f}mi")

print()
print('=== TOP 10 MOST RESILIENT TEAMS ===')
for t in sorted(teams, key=lambda x: x['delta'], reverse=True)[:10]:
    print(f"  {t['team']:<5} {t['div']:<15} {t['b2b_sv']:.4f}     {t['rest_sv']:.4f}     {t['delta']:+.4f}   {t['b2b_n']}")

print()
print('=== SEASON-BY-SEASON B2B TREND ===')
for season, g in sorted(reg.groupby('season')):
    b2b = g[g['is_back_to_back']==1]['save_pct'].dropna()
    rest = g[g['is_back_to_back']==0]['save_pct'].dropna()
    delta = b2b.mean()-rest.mean() if len(b2b) > 5 else float('nan')
    t_stat, p = stats.ttest_ind(b2b, rest) if len(b2b) > 5 else (0, 1)
    print(f"  {season}  B2B={len(b2b):3d}  delta={delta:+.4f}  p={p:.3f}")

print()
print('=== TOP 15 GOALIES by GAMES PLAYED ===')
top = df.groupby(['player_id','player_name'])['game_id'].count().reset_index()
top = top.rename(columns={'game_id':'games'}).sort_values('games',ascending=False).head(15)
for _,r in top.iterrows():
    g = reg[reg['player_id']==r['player_id']]
    b2b = g[g['is_back_to_back']==1]['save_pct'].dropna()
    rest = g[g['is_back_to_back']==0]['save_pct'].dropna()
    delta = b2b.mean()-rest.mean() if len(b2b) >= 3 else float('nan')
    print(f"  {r['player_name']:<25} {int(r['games']):3d} games  SV%={g['save_pct'].mean():.4f}  B2B_delta={delta:+.4f} (n={len(b2b)})")
