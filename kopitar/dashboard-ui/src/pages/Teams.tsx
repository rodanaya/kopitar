import { useEffect, useState, useMemo } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend,
} from 'recharts'
import type { TeamStat, GameLog } from '../types'
import { fmt, TEAM_NAMES, DIVISION_COLORS } from '../utils'

// ── Recharts shared style ─────────────────────────────────────────────────────
const tooltipStyle = {
  contentStyle: {
    background: '#141824',
    border: '1px solid #2a2f45',
    borderRadius: '8px',
    color: '#e8eaf0',
    fontSize: '0.85rem',
  },
}

// ── Season Timeline (Scatter) ─────────────────────────────────────────────────
interface TimelinePoint {
  ts: number
  date: string
  save_pct: number
  opponent: string
  shots_against: number
  days_rest: number
  travel_miles: number
  is_b2b: number
  decision: string
  goalie: string
}

interface TimelineTooltipProps {
  active?: boolean
  payload?: Array<{ payload: TimelinePoint }>
}

function TimelineTooltip({ active, payload }: TimelineTooltipProps) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#e8eaf0' }}>
      <div><strong>{d.date}</strong> vs {d.opponent}</div>
      <div>SV%: <strong>{fmt.sv(d.save_pct)}</strong></div>
      <div>Shots: {d.shots_against} · Rest: {d.days_rest}d</div>
      <div>Travel: {fmt.miles(d.travel_miles)}</div>
      {d.is_b2b === 1 && <div style={{ color: '#f5c842', marginTop: 4 }}>Back-to-back game</div>}
    </div>
  )
}

function SeasonTimeline({ logs, avgSv }: { logs: GameLog[]; avgSv: number }) {
  const points = useMemo<TimelinePoint[]>(() =>
    logs.map((g) => ({
      ts: new Date(g.date).getTime(),
      date: g.date,
      save_pct: g.save_pct,
      opponent: g.opponent,
      shots_against: g.shots_against,
      days_rest: g.days_rest,
      travel_miles: g.travel_miles,
      is_b2b: g.is_b2b,
      decision: g.decision,
      goalie: g.goalie,
    })), [logs])

  const b2bPoints = points.filter((p) => p.is_b2b === 1)
  const restedPoints = points.filter((p) => p.is_b2b === 0)

  const yDomain = useMemo(() => {
    const vals = points.map((p) => p.save_pct)
    return [Math.max(0.82, Math.min(...vals) - 0.01), Math.min(1.0, Math.max(...vals) + 0.005)]
  }, [points])

  const xDomain = useMemo(() => {
    if (!points.length) return [0, 1]
    return [Math.min(...points.map((p) => p.ts)), Math.max(...points.map((p) => p.ts))]
  }, [points])

  const formatDate = (ts: number) => {
    const d = new Date(ts)
    return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ScatterChart margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          type="number"
          dataKey="ts"
          domain={xDomain}
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={formatDate}
          scale="time"
          name="Date"
        />
        <YAxis
          type="number"
          dataKey="save_pct"
          domain={yDomain}
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
          name="SV%"
        />
        <Tooltip content={<TimelineTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <ReferenceLine
          y={avgSv}
          stroke="#4f9cf9"
          strokeDasharray="4 3"
          label={{ value: `Avg ${fmt.sv(avgSv)}`, fill: '#4f9cf9', fontSize: 11, position: 'right' }}
        />
        <Scatter
          name="Rested"
          data={restedPoints}
          fill="#4f9cf9"
          fillOpacity={0.7}
          r={3}
        />
        <Scatter
          name="Back-to-Back"
          data={b2bPoints}
          fill="#f5c842"
          fillOpacity={0.85}
          r={4}
        />
        <Legend wrapperStyle={{ color: '#8b91a8', fontSize: '0.85rem', paddingTop: '8px' }} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}

// ── SV% Distribution ──────────────────────────────────────────────────────────
interface SvBin {
  label: string
  b2b: number
  rested: number
  center: number
}

function SvDistribution({ logs }: { logs: GameLog[] }) {
  const bins = useMemo<SvBin[]>(() => {
    const edges = [0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.01]
    const data: SvBin[] = []
    for (let i = 0; i < edges.length - 1; i++) {
      const lo = edges[i], hi = edges[i + 1]
      const b2b = logs.filter((g) => g.is_b2b === 1 && g.save_pct >= lo && g.save_pct < hi).length
      const rested = logs.filter((g) => g.is_b2b === 0 && g.save_pct >= lo && g.save_pct < hi).length
      data.push({
        label: (lo * 100).toFixed(0) + '–' + (hi * 100).toFixed(0),
        b2b,
        rested,
        center: (lo + hi) / 2,
      })
    }
    return data
  }, [logs])

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={bins} margin={{ top: 5, right: 10, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          dataKey="label"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 10 }}
          label={{ value: 'SV% Range', position: 'insideBottom', offset: -12, fill: '#555c70', fontSize: 11 }}
          interval={0}
          angle={-30}
          textAnchor="end"
        />
        <YAxis
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          label={{ value: 'Games', angle: -90, position: 'insideLeft', fill: '#555c70', fontSize: 11 }}
        />
        <Tooltip
          {...tooltipStyle}
          formatter={(val: number, name: string) => [val, name === 'b2b' ? 'B2B' : 'Rested']}
        />
        <Legend
          wrapperStyle={{ color: '#8b91a8', fontSize: '0.85rem' }}
          formatter={(val) => val === 'b2b' ? 'Back-to-Back' : 'Rested'}
        />
        <Bar dataKey="rested" name="rested" fill="#4f9cf9" fillOpacity={0.75} radius={[3, 3, 0, 0]} />
        <Bar dataKey="b2b" name="b2b" fill="#f5c842" fillOpacity={0.85} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Stats by Season ───────────────────────────────────────────────────────────
interface SeasonAvg {
  season: string
  avg_sv: number
  games: number
}

const SEASON_PALETTE = ['#4f9cf9', '#a78bfa', '#f5c842', '#4caf7d', '#f47a38', '#ef5350', '#81c784', '#7986cb', '#4dd0e1', '#ff8a65']

function StatsBySeason({ logs }: { logs: GameLog[] }) {
  const seasons = useMemo<SeasonAvg[]>(() => {
    const map: Record<string, { sum: number; count: number }> = {}
    logs.forEach((g) => {
      if (!map[g.season]) map[g.season] = { sum: 0, count: 0 }
      map[g.season].sum += g.save_pct
      map[g.season].count++
    })
    return Object.entries(map)
      .map(([season, { sum, count }]) => ({ season, avg_sv: sum / count, games: count }))
      .sort((a, b) => a.season.localeCompare(b.season))
  }, [logs])

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={seasons} margin={{ top: 5, right: 10, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          dataKey="season"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 10 }}
          angle={-30}
          textAnchor="end"
        />
        <YAxis
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 10 }}
          domain={['auto', 'auto']}
          tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
        />
        <Tooltip
          {...tooltipStyle}
          formatter={(v: number) => [fmt.sv(v), 'Avg SV%']}
        />
        <Bar dataKey="avg_sv" name="Avg SV%" radius={[3, 3, 0, 0]}>
          {seasons.map((_, i) => (
            <Cell key={i} fill={SEASON_PALETTE[i % SEASON_PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Teams Page ────────────────────────────────────────────────────────────────
export default function Teams() {
  const [teamStats, setTeamStats] = useState<TeamStat[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [logs, setLogs] = useState<GameLog[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsError, setLogsError] = useState<string | null>(null)
  const [pageLoading, setPageLoading] = useState(true)

  // Load team list on mount
  useEffect(() => {
    fetch('/data/teams.json')
      .then((r) => r.json())
      .then((data: TeamStat[]) => {
        setTeamStats(data)
        // Sort by division then team name, pick first
        const sorted = [...data].sort((a, b) => {
          if (a.division !== b.division) return a.division.localeCompare(b.division)
          return a.team.localeCompare(b.team)
        })
        if (sorted.length > 0) setSelectedTeam(sorted[0].team)
      })
      .catch(() => {/* silently ignore — shown via logsError */})
      .finally(() => setPageLoading(false))
  }, [])

  // Load team logs when selection changes
  useEffect(() => {
    if (!selectedTeam) return
    setLogsLoading(true)
    setLogsError(null)
    fetch(`/data/team_logs/${selectedTeam}.json`)
      .then((r) => {
        if (!r.ok) throw new Error('not found')
        return r.json()
      })
      .then((data: GameLog[]) => setLogs(data))
      .catch(() => setLogsError('Data not available — run the export script first.'))
      .finally(() => setLogsLoading(false))
  }, [selectedTeam])

  const currentTeamStat = useMemo(
    () => teamStats.find((t) => t.team === selectedTeam),
    [teamStats, selectedTeam]
  )

  const sortedTeams = useMemo(() => {
    return [...teamStats].sort((a, b) => {
      if (a.division !== b.division) return a.division.localeCompare(b.division)
      return a.team.localeCompare(b.team)
    })
  }, [teamStats])

  if (pageLoading) return <div className="loading-state">Loading...</div>

  return (
    <main className="page">
      <h1 className="page-title">Team Analysis</h1>
      <p className="page-subtitle">Per-team back-to-back game performance and season trends</p>

      {/* Team Selector */}
      <div className="filter-row" style={{ marginBottom: '1.5rem' }}>
        <label className="filter-label">Select Team:</label>
        <div style={{ width: 260 }}>
          <select
            className="select-input"
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
          >
            {sortedTeams.map((t) => (
              <option key={t.team} value={t.team}>
                {t.team} — {TEAM_NAMES[t.team] ?? t.team} ({t.division})
              </option>
            ))}
          </select>
        </div>
        {currentTeamStat && (
          <span
            className="tag tag-neutral"
            style={{ color: DIVISION_COLORS[currentTeamStat.division] ?? undefined }}
          >
            {currentTeamStat.division}
          </span>
        )}
      </div>

      {/* KPI Cards */}
      {currentTeamStat && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-value">{currentTeamStat.total_games.toLocaleString()}</div>
            <div className="kpi-label">Total Games</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{fmt.sv(currentTeamStat.avg_sv)}</div>
            <div className="kpi-label">Avg Save %</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value" style={{ color: 'var(--accent-gold)' }}>
              {currentTeamStat.b2b_starts}
            </div>
            <div className="kpi-label">B2B Starts</div>
            <div className="kpi-delta">B2B SV%: {fmt.sv(currentTeamStat.b2b_sv)}</div>
          </div>
          <div className="kpi-card">
            <div
              className="kpi-value"
              style={{
                color: currentTeamStat.b2b_delta == null
                  ? 'var(--text-muted)'
                  : (currentTeamStat.b2b_delta < 0 ? 'var(--danger)' : 'var(--success)'),
              }}
            >
              {fmt.delta(currentTeamStat.b2b_delta)}
            </div>
            <div className="kpi-label">B2B Delta</div>
            <div className="kpi-delta">Avg Travel: {fmt.miles(currentTeamStat.avg_travel_miles)}</div>
          </div>
        </div>
      )}

      {/* Game Log charts */}
      {logsLoading && <div className="loading-state">Loading game logs...</div>}
      {logsError && <div className="error-state">{logsError}</div>}

      {!logsLoading && !logsError && logs.length > 0 && (
        <>
          {/* Season Timeline */}
          <div className="chart-card">
            <div className="chart-title">Season Timeline</div>
            <div className="chart-subtitle">
              Save % per game — blue = rested, gold = back-to-back
            </div>
            <SeasonTimeline logs={logs} avgSv={currentTeamStat?.avg_sv ?? 0.910} />
          </div>

          {/* Distribution + By Season */}
          <div className="grid-2">
            <div className="chart-card">
              <div className="chart-title">SV% Distribution</div>
              <div className="chart-subtitle">B2B vs rested games histogram</div>
              <SvDistribution logs={logs} />
            </div>
            <div className="chart-card">
              <div className="chart-title">Average SV% by Season</div>
              <div className="chart-subtitle">Season-by-season goalie performance</div>
              <StatsBySeason logs={logs} />
            </div>
          </div>

          {/* Game log table */}
          <div className="chart-card">
            <div className="chart-title">Recent Game Log</div>
            <div className="chart-subtitle">Last 50 games (most recent first)</div>
            <div className="table-wrapper" style={{ maxHeight: 360, overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Goalie</th>
                    <th>Opp</th>
                    <th>H/A</th>
                    <th>SV%</th>
                    <th>SA</th>
                    <th>GA</th>
                    <th>Rest</th>
                    <th>Travel</th>
                    <th>B2B</th>
                  </tr>
                </thead>
                <tbody>
                  {[...logs]
                    .sort((a, b) => b.date.localeCompare(a.date))
                    .slice(0, 50)
                    .map((g, i) => (
                      <tr key={i}>
                        <td className="td-muted">{g.date}</td>
                        <td>{g.goalie}</td>
                        <td>{g.opponent}</td>
                        <td className="td-muted">{g.home_away}</td>
                        <td
                          className={
                            g.save_pct >= 0.93
                              ? 'td-positive'
                              : g.save_pct < 0.88
                              ? 'td-negative'
                              : ''
                          }
                        >
                          {fmt.sv(g.save_pct)}
                        </td>
                        <td>{g.shots_against}</td>
                        <td>{g.goals_against}</td>
                        <td>{g.days_rest}d</td>
                        <td>{Math.round(g.travel_miles).toLocaleString()}</td>
                        <td>
                          {g.is_b2b === 1 ? (
                            <span className="tag tag-gold">B2B</span>
                          ) : (
                            <span className="td-muted">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </main>
  )
}
