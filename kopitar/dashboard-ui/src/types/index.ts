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
  career_gsax: number | null;
  career_hdsv_pct: number | null;
  resilience_z: number | null;
  quadrant: 'iron_man' | 'vulnerable_star' | 'workhorse' | 'high_risk' | null;
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

export interface GsaxSeasonPoint {
  season: string;
  label: string;
  gsax: number | null;
  gsax_per60: number | null;
  hdsv_pct: number | null;
  games: number;
}

export interface GsaxEntry {
  player_id: number;
  player_name: string;
  career_gsax: number;
  career_gsax_per60: number | null;
  career_hdsv_pct: number | null;
  seasons_with_gsax: number;
  seasons: GsaxSeasonPoint[];
}

export interface ScheduleStressMetric {
  label: string;
  mean_with: number;
  mean_without: number;
  delta: number;
  p_value: number;
  n_with: number;
  n_without: number;
  significant: boolean;
  goals_cost_per_game: number | null;
  total_extra_goals: number | null;
  extra_goals_per_team_season: number | null;
}

export interface RoadTripLeg {
  leg: number;
  label: string;
  mean_sv: number;
  count: number;
}

export interface AltitudeBin {
  label: string;
  mean_sv: number;
  count: number;
}

export interface SeasonPhaseStat {
  phase: string;
  label: string;
  mean_sv: number;
  count: number;
}

export interface ScheduleStress {
  four_in_six?: ScheduleStressMetric;
  three_in_four?: ScheduleStressMetric;
  road_trip_legs?: RoadTripLeg[];
  altitude?: AltitudeBin[];
  season_phase?: SeasonPhaseStat[];
}

export interface OtComparison {
  ot_sv: number;
  non_ot_sv: number;
  delta: number;
  n_ot: number;
  n_non_ot: number;
  p_value: number;
  significant: boolean;
}

export interface AfterOt {
  after_ot_sv: number;
  after_non_ot_sv: number;
  delta: number;
  n_after_ot: number;
  n_after_non_ot: number;
  p_value: number;
  significant: boolean;
}

export interface CompoundStress {
  ot_then_b2b_sv: number;
  regular_b2b_sv: number;
  delta: number;
  n_compound: number;
  n_regular_b2b: number;
  p_value: number;
  significant: boolean;
}

export interface ScoreDiffBin {
  label: string;
  mean_sv: number;
  count: number;
}

export interface MetroCorrection {
  b2b_all_sv: number | null;
  b2b_corrected_sv: number | null;
  same_metro_sv: number | null;
  rest_sv: number | null;
  delta_all: number | null;
  delta_corrected: number | null;
  n_b2b_all: number;
  n_b2b_corrected: number;
  n_same_metro: number;
  p_all: number | null;
  p_corrected: number | null;
}

export interface OtAnalysis {
  ot_vs_non_ot?: OtComparison;
  after_ot?: AfterOt;
  compound_stress?: CompoundStress;
  score_diff_bins?: ScoreDiffBin[];
  metro_correction?: MetroCorrection;
}

export interface SkaterToi {
  rest_days: number;
  mean_toi: number;
  count: number;
}

export interface SkaterB2bOverall {
  b2b_toi: number;
  rest_toi: number;
  delta: number;
  p_value: number;
  significant: boolean;
  n_b2b: number;
  n_rest: number;
}

export interface SkaterPositionB2b {
  position: string;
  b2b_toi: number;
  rest_toi: number;
  delta: number;
  p_value: number;
  n_b2b: number;
  n_rest: number;
}

export interface SkaterPlayerStat {
  player_id: number;
  player_name: string;
  position: string;
  avg_toi: number;
  b2b_toi: number | null;
  rest_toi: number | null;
  b2b_delta: number | null;
  games: number;
  b2b_games: number;
}

export interface SkaterFatigue {
  toi_by_rest?: SkaterToi[];
  b2b_overall?: SkaterB2bOverall;
  by_position?: SkaterPositionB2b[];
  top_players?: SkaterPlayerStat[];
}
