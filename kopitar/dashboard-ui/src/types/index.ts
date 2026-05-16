export interface KPIs {
  total_games: number;
  unique_goalies: number;
  seasons: number;
  b2b_games: number;
  b2b_rate: number;
}

export interface LeagueB2B {
  b2b_sv: number;
  rest_sv: number;
  delta: number;
  p_value: number;
  significant: boolean;
}

export interface Overview {
  kpis: KPIs;
  league_b2b: LeagueB2B;
}

export interface TeamStat {
  team: string;
  division: string;
  conference: string;
  total_games: number;
  avg_sv: number;
  b2b_starts: number;
  b2b_sv: number | null;
  rest_sv: number;
  b2b_delta: number | null;
  avg_travel_miles: number;
  lat: number;
  lon: number;
}

export interface GoalieStat {
  player_id: number;
  player_name: string;
  teams: string[];
  total_games: number;
  avg_sv: number;
  avg_gaa: number;
  b2b_games: number;
  b2b_sv: number | null;
  rest_sv: number;
  b2b_delta: number | null;
  avg_travel_miles: number;
}

export interface RecoveryPoint {
  days_rest: number;
  mean_sv: number;
  count: number;
  std: number;
  ci_lower: number;
  ci_upper: number;
}

export interface SeasonPoint {
  season: string;
  label: string;
  total_games: number;
  b2b_n: number;
  b2b_sv: number;
  rest_sv: number;
  delta: number;
  p_value: number;
  significant: boolean;
}

export interface DivisionStat {
  division: string;
  total_games: number;
  b2b_rate: number;
  avg_sv: number;
  b2b_sv: number;
  rest_sv: number;
  b2b_delta: number;
  avg_travel_miles: number;
}

export interface GameLog {
  date: string;
  opponent: string;
  home_away: string;
  save_pct: number;
  shots_against: number;
  goals_against: number;
  days_rest: number;
  is_b2b: number;
  travel_miles: number;
  goalie: string;
  season: string;
  decision: string;
}
