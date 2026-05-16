export const DIVISION_COLORS: Record<string, string> = {
  Atlantic: '#4f9cf9',
  Metropolitan: '#a78bfa',
  Central: '#f5c842',
  Pacific: '#4caf7d',
};

export const TEAM_COLORS: Record<string, string> = {
  ANA: '#F47A38', ARI: '#8C2633', BOS: '#FCB514', BUF: '#003087',
  CAR: '#CE1126', CBJ: '#002654', CGY: '#C8102E', CHI: '#CF0A2C',
  COL: '#6F263D', DAL: '#006847', DET: '#CE1126', EDM: '#FF4C00',
  FLA: '#C8102E', LAK: '#A2AAAD', MIN: '#A6192E', MTL: '#AF1E2D',
  NSH: '#FFB81C', NJD: '#CE1126', NYI: '#00539B', NYR: '#0038A8',
  OTT: '#C2912C', PHI: '#F74902', PIT: '#FCB514', SEA: '#001628',
  SJS: '#006D75', STL: '#002F87', TBL: '#002868', TOR: '#00205B',
  UTA: '#6CAEDF', VAN: '#00843D', VGK: '#B4975A', WPG: '#041E42',
  WSH: '#041E42',
};

export const TEAM_NAMES: Record<string, string> = {
  ANA: 'Anaheim Ducks', ARI: 'Arizona Coyotes', BOS: 'Boston Bruins',
  BUF: 'Buffalo Sabres', CAR: 'Carolina Hurricanes', CBJ: 'Columbus Blue Jackets',
  CGY: 'Calgary Flames', CHI: 'Chicago Blackhawks', COL: 'Colorado Avalanche',
  DAL: 'Dallas Stars', DET: 'Detroit Red Wings', EDM: 'Edmonton Oilers',
  FLA: 'Florida Panthers', LAK: 'LA Kings', MIN: 'Minnesota Wild',
  MTL: 'Montreal Canadiens', NSH: 'Nashville Predators', NJD: 'New Jersey Devils',
  NYI: 'NY Islanders', NYR: 'NY Rangers', OTT: 'Ottawa Senators',
  PHI: 'Philadelphia Flyers', PIT: 'Pittsburgh Penguins', SEA: 'Seattle Kraken',
  SJS: 'San Jose Sharks', STL: 'St. Louis Blues', TBL: 'Tampa Bay Lightning',
  TOR: 'Toronto Maple Leafs', UTA: 'Utah Mammoth', VAN: 'Vancouver Canucks',
  VGK: 'Vegas Golden Knights', WPG: 'Winnipeg Jets', WSH: 'Washington Capitals',
};

export const fmt = {
  sv: (v: number | null): string => v == null ? '—' : (v * 100).toFixed(2) + '%',
  svRaw: (v: number | null): string => v == null ? '—' : v.toFixed(4),
  delta: (v: number | null): string => {
    if (v == null) return '—';
    return (v >= 0 ? '+' : '') + v.toFixed(4);
  },
  pct: (v: number): string => (v * 100).toFixed(1) + '%',
  miles: (v: number): string => Math.round(v).toLocaleString() + ' mi',
  num: (v: number): string => v.toLocaleString(),
  pValue: (v: number): string => v < 0.001 ? '<0.001' : v.toFixed(3),
};

/** Return a color on a red->gray->green scale for b2b_delta values */
export function deltaColor(delta: number | null): string {
  if (delta == null) return '#555c70';
  if (delta < -0.02) return '#ef5350';
  if (delta < -0.005) return '#ff8a65';
  if (delta > 0.01) return '#4caf7d';
  if (delta > 0.002) return '#81c784';
  return '#8b91a8';
}
