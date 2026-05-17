import { useEffect, useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, ReferenceLine, Legend,
} from 'recharts'
import { TeamLogo } from '../components/TeamLogo'
import { fmt, TEAM_NAMES } from '../utils'
import type { SkaterFatigue, SkaterPlayerStat } from '../types'

// ── Types ─────────────────────────────────────────────────────────────────────
interface PlayerSeason {
  player_id: number
  player_name: string
  position: string
  position_label: string
  team: string
  season: string
  season_label: string
  games_played: number
  goals: number
  assists: number
  points: number
  plus_minus: number
  pim: number
  shots: number
  toi_per_game: number | null
  pp_points: number
  sh_points: number
  points_per_game: number | null
}

type SortField = 'points' | 'goals' | 'assists' | 'toi_per_game' | 'plus_minus' | 'pp_points' | 'games_played' | 'shots'

const SEASONS = [
  '20242025', '20232024', '20222023', '20212022', '20202021',
  '20192020', '20182019', '20172018', '20162017', '20152016',
]

const SEASON_LABELS: Record<string, string> = {
  '20242025': '2024-25', '20232024': '2023-24', '20222023': '2022-23',
  '20212022': '2021-22', '20202021': '2020-21', '20192020': '2019-20',
  '20182019': '2018-19', '20172018': '2017-18', '20162017': '2016-17',
  '20152016': '2015-16',
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function plusMinusColor(v: number): string {
  if (v > 15) return '#4caf7d'
  if (v > 0) return '#81c784'
  if (v < -15) return '#ef5350'
  if (v < 0) return '#ff8a65'
  return '#8b91a8'
}

function formatToi(mins: number | null): string {
  if (mins == null) return '—'
  const m = Math.floor(mins)
  const s = Math.round((mins - m) * 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ── Top Points Card ───────────────────────────────────────────────────────────
function TopScorersCard({ players }: { players: PlayerSeason[] }) {
  const top5 = useMemo(
    () => [...players].sort((a, b) => b.points - a.points).slice(0, 5),
    [players]
  )
  return (
    <div>
      {top5.map((p, i) => (
        <div key={p.player_id} className="mini-table-row" style={{ alignItems: 'center' }}>
          <span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span>
          <TeamLogo team={p.team} size={22} style={{ flexShrink: 0 }} />
          <span className="mini-table-name" style={{ flex: 1 }}>{p.player_name}</span>
          <span className="mini-table-team" style={{ color: '#8b91a8', fontSize: '0.78rem' }}>
            {p.position}
          </span>
          <span className="mini-table-value" style={{ color: 'var(--accent-blue)', minWidth: 36, textAlign: 'right' }}>
            {p.points} pts
          </span>
        </div>
      ))}
    </div>
  )
}

function TopGoalsCard({ players }: { players: PlayerSeason[] }) {
  const top5 = useMemo(
    () => [...players].sort((a, b) => b.goals - a.goals).slice(0, 5),
    [players]
  )
  return (
    <div>
      {top5.map((p, i) => (
        <div key={p.player_id} className="mini-table-row" style={{ alignItems: 'center' }}>
          <span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span>
          <TeamLogo team={p.team} size={22} style={{ flexShrink: 0 }} />
          <span className="mini-table-name" style={{ flex: 1 }}>{p.player_name}</span>
          <span className="mini-table-value" style={{ color: '#f5c842', minWidth: 36, textAlign: 'right' }}>
            {p.goals} G
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Main Table ────────────────────────────────────────────────────────────────
interface TableProps {
  players: PlayerSeason[]
  sortField: SortField
  sortDir: 'asc' | 'desc'
  onSort: (f: SortField) => void
}

function PlayerTable({ players, sortField, sortDir, onSort }: TableProps) {
  const SortIcon = ({ f }: { f: SortField }) =>
    f !== sortField ? <span style={{ opacity: 0.3 }}>↕</span>
      : <span style={{ color: 'var(--accent-blue)' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>

  const Th = ({ f, label }: { f: SortField; label: string }) => (
    <th className={sortField === f ? 'sort-active' : ''} onClick={() => onSort(f)}>
      {label} <SortIcon f={f} />
    </th>
  )

  return (
    <div className="table-wrapper" style={{ maxHeight: 520, overflowY: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Player</th>
            <th>Pos</th>
            <th>Team</th>
            <Th f="games_played" label="GP" />
            <Th f="goals" label="G" />
            <Th f="assists" label="A" />
            <Th f="points" label="PTS" />
            <Th f="plus_minus" label="+/−" />
            <Th f="toi_per_game" label="TOI/G" />
            <Th f="pp_points" label="PP PTS" />
            <Th f="shots" label="SOG" />
          </tr>
        </thead>
        <tbody>
          {players.map((p, i) => (
            <tr key={`${p.player_id}-${p.season}`}>
              <td><span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span></td>
              <td style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>{p.player_name}</td>
              <td className="td-muted">{p.position}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <TeamLogo team={p.team} size={20} />
                  <span className="td-muted">{p.team}</span>
                </div>
              </td>
              <td>{p.games_played}</td>
              <td style={{ fontWeight: 600, color: p.goals >= 40 ? 'var(--accent-gold)' : undefined }}>{p.goals}</td>
              <td>{p.assists}</td>
              <td style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>{p.points}</td>
              <td style={{ color: plusMinusColor(p.plus_minus) }}>
                {p.plus_minus >= 0 ? '+' : ''}{p.plus_minus}
              </td>
              <td className="td-muted">{formatToi(p.toi_per_game)}</td>
              <td className="td-muted">{p.pp_points}</td>
              <td className="td-muted">{p.shots}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const TT_STYLE = {
  contentStyle: {
    background: '#0c1d33', border: '1px solid rgba(56,189,248,0.18)',
    borderRadius: '10px', color: '#eef4ff', fontSize: '0.83rem',
    boxShadow: '0 8px 28px rgba(0,0,0,0.5)',
  },
}

// ── TOI by Rest Days Chart ────────────────────────────────────────────────────
function ToiRestChart({ data }: { data: { rest_days: number; mean_toi: number; count: number }[] }) {
  if (!data.length) return null
  const refVal = data.find(d => d.rest_days === 1)?.mean_toi ?? data[0].mean_toi
  const minVal = Math.min(...data.map(d => d.mean_toi)) - 0.5
  const maxVal = Math.max(...data.map(d => d.mean_toi)) + 0.5
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="rest_days" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }}
          label={{ value: 'Days Rest', position: 'insideBottom', fill: '#7ea4c4', fontSize: 11, dy: 8 }} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={v => v.toFixed(1) + ' min'} />
        <Tooltip {...TT_STYLE} formatter={(v: number, _, p) => [
          `${v.toFixed(2)} min  (n=${(p.payload as { count: number }).count.toLocaleString()})`, 'Avg TOI'
        ]} />
        <ReferenceLine y={refVal} stroke="#38bdf8" strokeDasharray="4 3" />
        <Line dataKey="mean_toi" stroke="#38bdf8" strokeWidth={2} dot={{ fill: '#38bdf8', r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ── B2B TOI by Position Chart ─────────────────────────────────────────────────
function PositionB2bChart({ data }: { data: { position: string; b2b_toi: number; rest_toi: number; delta: number }[] }) {
  if (!data.length) return null
  const chartData = data.map(d => ({ ...d, label: d.position }))
  const allVals = chartData.flatMap(d => [d.b2b_toi, d.rest_toi])
  const minVal = Math.min(...allVals) - 0.3
  const maxVal = Math.max(...allVals) + 0.3
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="label" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 12 }} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={v => v.toFixed(1)} />
        <Tooltip {...TT_STYLE} formatter={(v: number) => [`${v.toFixed(2)} min`, '']} />
        <Legend wrapperStyle={{ color: '#7ea4c4', fontSize: '0.8rem' }} />
        <Bar dataKey="b2b_toi" name="B2B TOI" fill="#f43f5e" radius={[4, 4, 0, 0]} fillOpacity={0.85} />
        <Bar dataKey="rest_toi" name="Rested TOI" fill="#34d399" radius={[4, 4, 0, 0]} fillOpacity={0.85} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Skater B2B TOI Table ──────────────────────────────────────────────────────
function SkaterToiTable({ players }: { players: SkaterPlayerStat[] }) {
  const sorted = useMemo(() => [...players].sort((a, b) => (b.avg_toi ?? 0) - (a.avg_toi ?? 0)), [players])
  return (
    <div className="table-wrapper" style={{ maxHeight: 420, overflowY: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Player</th>
            <th>Pos</th>
            <th>Games</th>
            <th>Avg TOI</th>
            <th>Rested TOI</th>
            <th>B2B TOI</th>
            <th>B2B Delta</th>
            <th>B2B Games</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => {
            const delta = p.b2b_delta ?? 0
            return (
              <tr key={p.player_id}>
                <td><span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span></td>
                <td style={{ fontWeight: 500 }}>{p.player_name}</td>
                <td className="td-muted">{p.position}</td>
                <td className="td-muted">{p.games}</td>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--accent-ice)' }}>
                  {p.avg_toi != null ? p.avg_toi.toFixed(2) : '—'}
                </td>
                <td className="td-muted">{p.rest_toi != null ? p.rest_toi.toFixed(2) : '—'}</td>
                <td className="td-muted">{p.b2b_toi != null ? p.b2b_toi.toFixed(2) : '—'}</td>
                <td style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  color: delta < -0.3 ? '#f43f5e' : delta > 0.3 ? '#34d399' : 'var(--text-muted)',
                  fontWeight: Math.abs(delta) > 0.5 ? 700 : 400,
                }}>
                  {p.b2b_delta != null ? (delta >= 0 ? '+' : '') + delta.toFixed(2) : '—'}
                </td>
                <td className="td-muted">{p.b2b_games}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Players Page ──────────────────────────────────────────────────────────────
export default function Players() {
  const [allPlayers, setAllPlayers] = useState<PlayerSeason[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [season, setSeason] = useState('20242025')
  const [posFilter, setPosFilter] = useState<'ALL' | 'F' | 'D'>('ALL')
  const [teamFilter, setTeamFilter] = useState('ALL')
  const [sortField, setSortField] = useState<SortField>('points')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [fatigue, setFatigue] = useState<SkaterFatigue | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/data/players.json').then(r => r.json()),
      fetch('/data/skater_fatigue.json').then(r => r.json()).catch(() => null),
    ]).then(([players, fat]) => {
      setAllPlayers(players as PlayerSeason[])
      setFatigue(fat as SkaterFatigue | null)
    }).catch(() => setError('Data not available — run the export script first.'))
      .finally(() => setLoading(false))
  }, [])

  const handleSort = (f: SortField) => {
    if (f === sortField) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(f); setSortDir('desc') }
  }

  const seasonPlayers = useMemo(
    () => allPlayers.filter((p) => p.season === season),
    [allPlayers, season]
  )

  const teams = useMemo(
    () => ['ALL', ...Array.from(new Set(seasonPlayers.map((p) => p.team))).sort()],
    [seasonPlayers]
  )

  const filtered = useMemo(() => {
    return [...seasonPlayers]
      .filter((p) => {
        if (posFilter === 'F' && !['C', 'L', 'R'].includes(p.position)) return false
        if (posFilter === 'D' && p.position !== 'D') return false
        if (teamFilter !== 'ALL' && p.team !== teamFilter) return false
        return true
      })
      .sort((a, b) => {
        const av = (a[sortField] ?? (sortDir === 'asc' ? Infinity : -Infinity)) as number
        const bv = (b[sortField] ?? (sortDir === 'asc' ? Infinity : -Infinity)) as number
        return sortDir === 'asc' ? av - bv : bv - av
      })
  }, [seasonPlayers, posFilter, teamFilter, sortField, sortDir])

  if (loading) return <div className="loading-state">Loading...</div>
  if (error) return <div className="error-state">{error}</div>

  const totalGoals = seasonPlayers.reduce((s, p) => s + p.goals, 0)
  const totalPoints = seasonPlayers.reduce((s, p) => s + p.points, 0)
  const topScorer = seasonPlayers.reduce((best, p) => p.points > (best?.points ?? -1) ? p : best, seasonPlayers[0])

  return (
    <main className="page">
      <h1 className="page-title">Player Leaders</h1>
      <p className="page-subtitle">
        Top 100 skaters by points · forwards &amp; defensemen · regular season
      </p>

      {/* Season + Filter row */}
      <div className="filter-row" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <label className="filter-label">Season:</label>
        <select
          className="select-input"
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          style={{ width: 120 }}
        >
          {SEASONS.map((s) => (
            <option key={s} value={s}>{SEASON_LABELS[s]}</option>
          ))}
        </select>

        <label className="filter-label" style={{ marginLeft: '1rem' }}>Position:</label>
        {(['ALL', 'F', 'D'] as const).map((pos) => (
          <button
            key={pos}
            onClick={() => setPosFilter(pos)}
            style={{
              padding: '0.3rem 0.75rem',
              borderRadius: 6,
              border: `1px solid ${posFilter === pos ? 'var(--accent-blue)' : 'var(--border)'}`,
              background: posFilter === pos ? 'rgba(79,156,249,0.15)' : 'transparent',
              color: posFilter === pos ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            {pos === 'ALL' ? 'All' : pos === 'F' ? 'Forwards' : 'Defensemen'}
          </button>
        ))}

        <label className="filter-label" style={{ marginLeft: '1rem' }}>Team:</label>
        <select
          className="select-input"
          value={teamFilter}
          onChange={(e) => setTeamFilter(e.target.value)}
          style={{ width: 180 }}
        >
          {teams.map((t) => (
            <option key={t} value={t}>
              {t === 'ALL' ? 'All Teams' : `${TEAM_NAMES[t] ?? t}`}
            </option>
          ))}
        </select>

        <span className="filter-label" style={{ marginLeft: 'auto' }}>
          {filtered.length} players shown
        </span>
      </div>

      {/* KPI row */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="kpi-card">
          <div className="kpi-value">{SEASON_LABELS[season]}</div>
          <div className="kpi-label">Season</div>
        </div>
        <div className="kpi-card">
          {topScorer && (
            <>
              <div className="kpi-value" style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                <TeamLogo team={topScorer.team} size={28} />
                {topScorer.points} pts
              </div>
              <div className="kpi-label">{topScorer.player_name} — Points Leader</div>
            </>
          )}
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{totalGoals.toLocaleString()}</div>
          <div className="kpi-label">Total Goals (top 100)</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{totalPoints.toLocaleString()}</div>
          <div className="kpi-label">Total Points (top 100)</div>
        </div>
      </div>

      {/* Skater Fatigue Analysis — shown first, above leaderboard */}
      {fatigue && (
        <>
          <div style={{
            borderTop: '2px solid rgba(56,189,248,0.18)',
            paddingTop: '2rem',
            marginBottom: '0.5rem',
          }}>
            <h2 style={{
              fontFamily: '"Barlow Condensed", sans-serif',
              fontStyle: 'italic',
              fontSize: 'clamp(1.4rem, 3vw, 2rem)',
              color: 'var(--accent-ice)',
              margin: '0 0 0.25rem',
              letterSpacing: '0.02em',
            }}>
              Skater Fatigue — Ice Time Impact
            </h2>
            <p className="page-subtitle" style={{ marginTop: 0, marginBottom: '1.5rem' }}>
              How back-to-back games shrink skater ice time ·{' '}
              {(fatigue.b2b_overall
                ? (fatigue.b2b_overall.n_b2b + fatigue.b2b_overall.n_rest).toLocaleString()
                : '74k+')} game logs · forwards &amp; defensemen
            </p>
          </div>

          {/* Fatigue KPIs */}
          {fatigue.b2b_overall && (
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color: '#38bdf8', fontSize: '1.9rem' }}>
                  {fatigue.b2b_overall.rest_toi.toFixed(2)}
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginLeft: 4 }}>min</span>
                </div>
                <div className="kpi-label">Rested TOI / Game</div>
                <div className="kpi-delta">n={fatigue.b2b_overall.n_rest.toLocaleString()} starts</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color: '#f43f5e', fontSize: '1.9rem' }}>
                  {fatigue.b2b_overall.b2b_toi.toFixed(2)}
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginLeft: 4 }}>min</span>
                </div>
                <div className="kpi-label">B2B TOI / Game</div>
                <div className="kpi-delta">n={fatigue.b2b_overall.n_b2b.toLocaleString()} starts</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{
                  color: fatigue.b2b_overall.delta < 0 ? '#f43f5e' : '#34d399', fontSize: '1.9rem'
                }}>
                  {fatigue.b2b_overall.delta >= 0 ? '+' : ''}{(fatigue.b2b_overall.delta * 60).toFixed(0)}
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginLeft: 4 }}>sec</span>
                </div>
                <div className="kpi-label">TOI Drop on B2B</div>
                <div className="kpi-delta">{fatigue.b2b_overall.delta.toFixed(2)} min per B2B game</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{
                  color: fatigue.b2b_overall.significant ? '#fbbf24' : 'var(--text-muted)', fontSize: '1.9rem'
                }}>
                  p&lt;0.001
                </div>
                <div className="kpi-label">Statistical Significance</div>
                <div className="kpi-delta">{fatigue.b2b_overall.significant ? 'Highly significant' : 'Not significant'}</div>
              </div>
            </div>
          )}

          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            {fatigue.toi_by_rest && fatigue.toi_by_rest.length > 0 && (
              <div className="chart-card">
                <div className="chart-title">Avg TOI by Days of Rest</div>
                <div className="chart-subtitle">
                  More rest = more ice time · dashed line = 1-day rest baseline
                </div>
                <ToiRestChart data={fatigue.toi_by_rest} />
              </div>
            )}
            {fatigue.by_position && fatigue.by_position.length > 0 && (
              <div className="chart-card">
                <div className="chart-title">B2B TOI Impact by Position</div>
                <div className="chart-subtitle">
                  Forwards vs Defensemen — who absorbs more of the B2B load?
                </div>
                <PositionB2bChart data={fatigue.by_position} />
              </div>
            )}
          </div>

          {fatigue.top_players && fatigue.top_players.length > 0 && (
            <div className="chart-card" style={{ marginBottom: '2rem' }}>
              <div className="chart-title">Player TOI — B2B Impact Breakdown</div>
              <div className="chart-subtitle">
                Top 50 players by avg TOI · red delta = significant ice-time loss on back-to-backs
              </div>
              <SkaterToiTable players={fatigue.top_players} />
            </div>
          )}

          <div style={{ borderTop: '1px solid rgba(56,189,248,0.1)', marginBottom: '2rem' }} />
        </>
      )}

      {/* Top mini-tables */}
      <div className="grid-2">
        <div className="chart-card">
          <div className="chart-title">Points Leaders</div>
          <div className="chart-subtitle">{SEASON_LABELS[season]} — top 5 scorers</div>
          <TopScorersCard players={filtered} />
        </div>
        <div className="chart-card">
          <div className="chart-title">Goals Leaders</div>
          <div className="chart-subtitle">{SEASON_LABELS[season]} — top 5 goal scorers</div>
          <TopGoalsCard players={filtered} />
        </div>
      </div>

      {/* Full table */}
      <div className="chart-card">
        <div className="chart-title">Skater Leaderboard</div>
        <div className="chart-subtitle">
          Click column headers to sort · top 100 by points per season from NHL Stats API
        </div>
        <PlayerTable
          players={filtered}
          sortField={sortField}
          sortDir={sortDir}
          onSort={handleSort}
        />
      </div>
    </main>
  )
}
