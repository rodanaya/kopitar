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
  Cell,
} from 'recharts'
import type { GoalieStat } from '../types'
import { fmt } from '../utils'

// ── Helpers ───────────────────────────────────────────────────────────────────
type SortField = 'total_games' | 'avg_sv' | 'b2b_delta' | 'avg_travel_miles' | 'avg_gaa'

function deltaColor(v: number | null): string {
  if (v == null) return '#8b91a8'
  if (v < -0.02) return '#ef5350'
  if (v < -0.005) return '#ff8a65'
  if (v > 0.01) return '#4caf7d'
  if (v > 0.002) return '#81c784'
  return '#8b91a8'
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 3)
}

// ── Scatter Tooltip ───────────────────────────────────────────────────────────
interface ScatterTooltipProps {
  active?: boolean
  payload?: Array<{ payload: GoalieStat }>
}

function ScatterTooltip({ active, payload }: ScatterTooltipProps) {
  if (!active || !payload?.length) return null
  const g = payload[0].payload
  return (
    <div style={{
      background: '#141824',
      border: '1px solid #2a2f45',
      borderRadius: 8,
      padding: '0.75rem 1rem',
      fontSize: '0.85rem',
      color: '#e8eaf0',
      maxWidth: 220,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{g.player_name}</div>
      <div style={{ color: '#8b91a8', fontSize: '0.8rem', marginBottom: 8 }}>
        {g.teams.join(', ')} · {g.total_games} games
      </div>
      <div>Avg SV%: <strong>{fmt.sv(g.avg_sv)}</strong></div>
      <div>Avg GAA: <strong>{g.avg_gaa.toFixed(2)}</strong></div>
      <div>B2B Games: <strong>{g.b2b_games}</strong></div>
      <div>B2B Delta: <strong style={{ color: deltaColor(g.b2b_delta) }}>{fmt.delta(g.b2b_delta)}</strong></div>
      <div>Avg Travel: <strong>{fmt.miles(g.avg_travel_miles)}</strong></div>
    </div>
  )
}

// ── Custom Dot with label for outliers ────────────────────────────────────────
interface CustomDotProps {
  cx?: number
  cy?: number
  payload?: GoalieStat
}

function CustomDot({ cx, cy, payload }: CustomDotProps) {
  if (!payload || cx == null || cy == null) return null
  const delta = payload.b2b_delta
  const isOutlier = delta != null && Math.abs(delta) > 0.03
  const color = deltaColor(delta)
  return (
    <g>
      <circle cx={cx} cy={cy} r={isOutlier ? 6 : 4} fill={color} fillOpacity={0.85} stroke="#0b0e18" strokeWidth={1} />
      {isOutlier && (
        <text
          x={cx + 8}
          y={cy + 4}
          fontSize={9}
          fill="#e8eaf0"
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          {initials(payload.player_name)}
        </text>
      )}
    </g>
  )
}

// ── Goalie Scatter ────────────────────────────────────────────────────────────
function GoalieScatter({ goalies }: { goalies: GoalieStat[] }) {
  const hasB2B = useMemo(() => goalies.filter((g) => g.b2b_delta != null), [goalies])
  const leagueAvgSv = useMemo(() => {
    if (!goalies.length) return 0.910
    return goalies.reduce((s, g) => s + g.avg_sv, 0) / goalies.length
  }, [goalies])

  const xDomain = useMemo(() => {
    if (!goalies.length) return [0.87, 0.95]
    const vals = goalies.map((g) => g.avg_sv)
    return [Math.max(0.85, Math.min(...vals) - 0.005), Math.min(1.0, Math.max(...vals) + 0.005)]
  }, [goalies])

  const yDomain = useMemo(() => {
    if (!hasB2B.length) return [-0.08, 0.06]
    const vals = hasB2B.map((g) => g.b2b_delta as number)
    return [Math.min(-0.05, Math.min(...vals) - 0.005), Math.max(0.04, Math.max(...vals) + 0.005)]
  }, [hasB2B])

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          type="number"
          dataKey="avg_sv"
          domain={xDomain}
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
          name="Avg SV%"
          label={{ value: 'Avg Save %', position: 'insideBottom', offset: -10, fill: '#555c70', fontSize: 12 }}
        />
        <YAxis
          type="number"
          dataKey="b2b_delta"
          domain={yDomain}
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)}
          name="B2B Delta"
          label={{ value: 'B2B Delta', angle: -90, position: 'insideLeft', fill: '#555c70', fontSize: 12 }}
        />
        <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <ReferenceLine y={0} stroke="#555c70" strokeDasharray="4 3" label={{ value: 'B2B Neutral', fill: '#555c70', fontSize: 10, position: 'right' }} />
        <ReferenceLine x={leagueAvgSv} stroke="#4f9cf9" strokeDasharray="4 3" label={{ value: 'League Avg', fill: '#4f9cf9', fontSize: 10, position: 'top' }} />
        <Scatter
          data={hasB2B}
          shape={<CustomDot />}
          name="Goalies"
        >
          {hasB2B.map((g) => (
            <Cell key={g.player_id} fill={deltaColor(g.b2b_delta)} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}

// ── Mini Top/Bottom table ────────────────────────────────────────────────────
function TopBottomTable({ goalies }: { goalies: GoalieStat[] }) {
  const withDelta = useMemo(() =>
    goalies.filter((g) => g.b2b_delta != null && g.b2b_games >= 5),
    [goalies]
  )

  const top5 = useMemo(() =>
    [...withDelta].sort((a, b) => (b.b2b_delta as number) - (a.b2b_delta as number)).slice(0, 5),
    [withDelta]
  )

  const bottom5 = useMemo(() =>
    [...withDelta].sort((a, b) => (a.b2b_delta as number) - (b.b2b_delta as number)).slice(0, 5),
    [withDelta]
  )

  const Row = ({ g, rank, dir }: { g: GoalieStat; rank: number; dir: 'top' | 'bot' }) => (
    <div className="mini-table-row">
      <span className={`rank-badge ${rank <= 3 ? 'top3' : ''}`}>{rank}</span>
      <span className="mini-table-name">{g.player_name}</span>
      <span className="mini-table-team">{g.teams[0]}</span>
      <span
        className="mini-table-value"
        style={{ color: dir === 'top' ? 'var(--success)' : 'var(--danger)' }}
      >
        {fmt.delta(g.b2b_delta)}
      </span>
    </div>
  )

  return (
    <div>
      <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--success)', marginBottom: '0.5rem' }}>
        Best B2B Performance
      </h3>
      <div style={{ marginBottom: '1.5rem' }}>
        {top5.map((g, i) => <Row key={g.player_id} g={g} rank={i + 1} dir="top" />)}
      </div>
      <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--danger)', marginBottom: '0.5rem' }}>
        Most B2B Impacted
      </h3>
      <div>
        {bottom5.map((g, i) => <Row key={g.player_id} g={g} rank={i + 1} dir="bot" />)}
      </div>
    </div>
  )
}

// ── Data Table ────────────────────────────────────────────────────────────────
interface TableProps {
  goalies: GoalieStat[]
  sortField: SortField
  sortDir: 'asc' | 'desc'
  onSort: (field: SortField) => void
}

function GoalieTable({ goalies, sortField, sortDir, onSort }: TableProps) {
  const SortIcon = ({ field }: { field: SortField }) => {
    if (field !== sortField) return <span style={{ opacity: 0.3 }}>↕</span>
    return <span style={{ color: 'var(--accent-blue)' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  const Th = ({ field, label }: { field: SortField; label: string }) => (
    <th
      className={sortField === field ? 'sort-active' : ''}
      onClick={() => onSort(field)}
    >
      {label} <SortIcon field={field} />
    </th>
  )

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Name</th>
            <th>Teams</th>
            <Th field="total_games" label="Games" />
            <Th field="avg_sv" label="Avg SV%" />
            <Th field="avg_gaa" label="GAA" />
            <th>B2B Games</th>
            <th>B2B SV%</th>
            <th>Rest SV%</th>
            <Th field="b2b_delta" label="B2B Delta" />
            <Th field="avg_travel_miles" label="Avg Travel" />
          </tr>
        </thead>
        <tbody>
          {goalies.map((g, i) => (
            <tr key={g.player_id}>
              <td>
                <span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span>
              </td>
              <td style={{ fontWeight: 500 }}>{g.player_name}</td>
              <td className="td-muted">{g.teams.join(', ')}</td>
              <td>{g.total_games}</td>
              <td>{fmt.sv(g.avg_sv)}</td>
              <td>{g.avg_gaa.toFixed(2)}</td>
              <td className="td-muted">{g.b2b_games}</td>
              <td>{fmt.sv(g.b2b_sv)}</td>
              <td>{fmt.sv(g.rest_sv)}</td>
              <td
                className={
                  g.b2b_delta == null
                    ? 'td-muted'
                    : g.b2b_delta < -0.01
                    ? 'td-negative'
                    : g.b2b_delta > 0.01
                    ? 'td-positive'
                    : ''
                }
              >
                {fmt.delta(g.b2b_delta)}
              </td>
              <td className="td-muted">{fmt.miles(g.avg_travel_miles)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Goalies Page ──────────────────────────────────────────────────────────────
export default function Goalies() {
  const [allGoalies, setAllGoalies] = useState<GoalieStat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortField, setSortField] = useState<SortField>('total_games')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [minGames, setMinGames] = useState(50)

  useEffect(() => {
    fetch('/data/goalies.json')
      .then((r) => r.json())
      .then((data: GoalieStat[]) => setAllGoalies(data))
      .catch(() => setError('Data not available — run the export script first.'))
      .finally(() => setLoading(false))
  }, [])

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const filtered = useMemo(() => {
    return [...allGoalies]
      .filter((g) => g.total_games >= minGames)
      .sort((a, b) => {
        const aVal = a[sortField] ?? (sortDir === 'asc' ? Infinity : -Infinity)
        const bVal = b[sortField] ?? (sortDir === 'asc' ? Infinity : -Infinity)
        return sortDir === 'asc'
          ? (aVal as number) - (bVal as number)
          : (bVal as number) - (aVal as number)
      })
  }, [allGoalies, minGames, sortField, sortDir])

  if (loading) return <div className="loading-state">Loading...</div>
  if (error) return <div className="error-state">{error}</div>

  return (
    <main className="page">
      <h1 className="page-title">Goalie Rankings</h1>
      <p className="page-subtitle">
        {filtered.length} goalies · sorted by {sortField.replace('_', ' ')} · min {minGames} games
      </p>

      {/* Filters */}
      <div className="filter-row">
        <label className="filter-label">Min games:</label>
        <input
          type="number"
          className="number-input"
          value={minGames}
          min={1}
          max={500}
          onChange={(e) => setMinGames(Math.max(1, parseInt(e.target.value) || 1))}
        />
        <span className="filter-label" style={{ marginLeft: 'auto' }}>
          {allGoalies.length} total goalies in dataset
        </span>
      </div>

      {/* Scatter + Top/Bottom */}
      <div className="grid-5545">
        <div className="chart-card">
          <div className="chart-title">SV% vs B2B Impact</div>
          <div className="chart-subtitle">
            Each dot = one goalie · outlier labels = |delta| &gt; 0.03 · red line = B2B neutral
          </div>
          <GoalieScatter goalies={filtered} />
        </div>

        <div className="chart-card">
          <div className="chart-title">B2B Impact Extremes</div>
          <div className="chart-subtitle">Min 5 B2B games for inclusion</div>
          <TopBottomTable goalies={filtered} />
        </div>
      </div>

      {/* Data Table */}
      <div className="chart-card">
        <div className="chart-title">Goalie Data Table</div>
        <div className="chart-subtitle">
          Click column headers to sort · green/red = B2B delta impact
        </div>
        <GoalieTable
          goalies={filtered}
          sortField={sortField}
          sortDir={sortDir}
          onSort={handleSort}
        />
      </div>
    </main>
  )
}
