import { useEffect, useState, useMemo } from 'react'
import {
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { GoalieStat } from '../types'
import { fmt } from '../utils'
import { TeamLogo } from '../components/TeamLogo'

// ── Helpers ───────────────────────────────────────────────────────────────────
type SortField =
  | 'total_games'
  | 'avg_sv'
  | 'b2b_delta'
  | 'avg_travel_miles'
  | 'avg_gaa'
  | 'career_gsax'
  | 'career_hdsv_pct'

function deltaColor(v: number | null): string {
  if (v == null) return '#8b91a8'
  if (v < -0.02) return '#ef5350'
  if (v < -0.005) return '#ff8a65'
  if (v > 0.01) return '#4caf7d'
  if (v > 0.002) return '#81c784'
  return '#8b91a8'
}

function gsaxColor(v: number | null): string {
  if (v == null) return '#8b91a8'
  if (v > 30) return '#4caf7d'
  if (v > 0) return '#81c784'
  if (v > -15) return '#ff8a65'
  return '#ef5350'
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
      <div>B2B Delta: <strong style={{ color: deltaColor(g.b2b_delta) }}>{fmt.delta(g.b2b_delta)}</strong></div>
      {g.career_gsax != null && <div>Career GSAx: <strong style={{ color: gsaxColor(g.career_gsax) }}>{g.career_gsax >= 0 ? '+' : ''}{g.career_gsax.toFixed(1)}</strong></div>}
      {g.career_hdsv_pct != null && <div>HDSV%: <strong>{fmt.sv(g.career_hdsv_pct)}</strong></div>}
    </div>
  )
}

// ── Custom Dot ────────────────────────────────────────────────────────────────
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
        <text x={cx + 8} y={cy + 4} fontSize={9} fill="#e8eaf0" style={{ pointerEvents: 'none', userSelect: 'none' }}>
          {initials(payload.player_name)}
        </text>
      )}
    </g>
  )
}

// ── HDSV% Scatter Dot ─────────────────────────────────────────────────────────
interface HdsvDotProps {
  cx?: number
  cy?: number
  payload?: GoalieStat
}

function HdsvDot({ cx, cy, payload }: HdsvDotProps) {
  if (!payload || cx == null || cy == null) return null
  const gsax = payload.career_gsax
  const color = gsaxColor(gsax)
  const isElite = gsax != null && gsax > 40
  return (
    <g>
      <circle cx={cx} cy={cy} r={isElite ? 7 : 4} fill={color} fillOpacity={0.85} stroke="#0b0e18" strokeWidth={1} />
      {isElite && (
        <text x={cx + 9} y={cy + 4} fontSize={9} fill="#e8eaf0" style={{ pointerEvents: 'none', userSelect: 'none' }}>
          {initials(payload.player_name)}
        </text>
      )}
    </g>
  )
}

// ── Quadrant Color Map ────────────────────────────────────────────────────────
const QUADRANT_COLOR: Record<string, string> = {
  iron_man: '#34d399',
  workhorse: '#38bdf8',
  vulnerable_star: '#f43f5e',
  high_risk: '#fbbf24',
}

const QUADRANT_META = [
  { key: 'iron_man',       label: 'Iron Man',       color: '#34d399', desc: 'Elite + resilient — the complete package' },
  { key: 'workhorse',      label: 'Workhorse',       color: '#38bdf8', desc: 'Average SV%, fatigue-resistant — ideal backup' },
  { key: 'vulnerable_star',label: 'Vulnerable Star', color: '#f43f5e', desc: 'Elite SV%, B2B fragile — protect the schedule' },
  { key: 'high_risk',      label: 'High Risk',       color: '#fbbf24', desc: 'Below average + fragile — avoid B2B entirely' },
]

// ── Resilience Quadrant Scatter ───────────────────────────────────────────────
function QuadrantScatter({ goalies }: { goalies: GoalieStat[] }) {
  const qualified = useMemo(
    () => goalies.filter(g => g.b2b_delta != null && g.b2b_games >= 5),
    [goalies]
  )

  const leagueMedianSv = useMemo(() => {
    if (!qualified.length) return 0.910
    const sorted = [...qualified].sort((a, b) => a.avg_sv - b.avg_sv)
    const mid = Math.floor(sorted.length / 2)
    return sorted.length % 2 === 0
      ? (sorted[mid - 1].avg_sv + sorted[mid].avg_sv) / 2
      : sorted[mid].avg_sv
  }, [qualified])

  const xDomain = useMemo(() => {
    if (!qualified.length) return [0.88, 0.940]
    const vals = qualified.map(g => g.avg_sv)
    return [Math.max(0.875, Math.min(...vals) - 0.004), Math.min(0.948, Math.max(...vals) + 0.004)]
  }, [qualified])

  const yDomain = useMemo(() => {
    if (!qualified.length) return [-0.07, 0.06]
    const vals = qualified.map(g => g.b2b_delta as number)
    return [Math.min(-0.055, Math.min(...vals) - 0.005), Math.max(0.04, Math.max(...vals) + 0.005)]
  }, [qualified])

  // Dot: size by career games, color by quadrant, label for top starters
  function QDot({ cx, cy, payload }: { cx?: number; cy?: number; payload?: GoalieStat }) {
    if (!payload || cx == null || cy == null) return null
    const q = payload.quadrant
    const color = q ? QUADRANT_COLOR[q] : '#7ea4c4'
    const r = Math.min(10, Math.max(4, 4 + Math.sqrt(payload.total_games / 25)))
    const showName = payload.total_games >= 120
    const lastName = payload.player_name.split(' ').slice(1).join(' ') || payload.player_name
    return (
      <g>
        <circle cx={cx} cy={cy} r={r} fill={color} fillOpacity={0.88}
          stroke={q === 'iron_man' ? 'rgba(52,211,153,0.4)' : '#060c18'}
          strokeWidth={q === 'iron_man' ? 2 : 1} />
        {showName && (
          <text x={cx + r + 3} y={cy + 4} fontSize={8.5} fill="rgba(238,244,255,0.65)"
            style={{ pointerEvents: 'none', userSelect: 'none' }}>
            {lastName}
          </text>
        )}
      </g>
    )
  }

  return (
    <>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 15, right: 30, bottom: 30, left: 15 }}>
          {/* Quadrant backgrounds */}
          <ReferenceArea x1={xDomain[0]} x2={leagueMedianSv} y1={0} y2={yDomain[1]}
            fill="rgba(56,189,248,0.04)"
            label={{ value: 'WORKHORSE', position: 'insideTopLeft', fill: 'rgba(56,189,248,0.22)', fontSize: 9, fontWeight: 700 }} />
          <ReferenceArea x1={leagueMedianSv} x2={xDomain[1]} y1={0} y2={yDomain[1]}
            fill="rgba(52,211,153,0.04)"
            label={{ value: 'IRON MAN', position: 'insideTopRight', fill: 'rgba(52,211,153,0.22)', fontSize: 9, fontWeight: 700 }} />
          <ReferenceArea x1={xDomain[0]} x2={leagueMedianSv} y1={yDomain[0]} y2={0}
            fill="rgba(251,191,36,0.04)"
            label={{ value: 'HIGH RISK', position: 'insideBottomLeft', fill: 'rgba(251,191,36,0.22)', fontSize: 9, fontWeight: 700 }} />
          <ReferenceArea x1={leagueMedianSv} x2={xDomain[1]} y1={yDomain[0]} y2={0}
            fill="rgba(244,63,94,0.04)"
            label={{ value: 'VULNERABLE STAR', position: 'insideBottomRight', fill: 'rgba(244,63,94,0.22)', fontSize: 9, fontWeight: 700 }} />

          <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
          <XAxis type="number" dataKey="avg_sv" domain={xDomain}
            stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }}
            tickFormatter={v => (v * 100).toFixed(1) + '%'}
            label={{ value: 'Career Avg SV%  ← weaker · stronger →', position: 'insideBottom', offset: -15, fill: '#7ea4c4', fontSize: 10 }} />
          <YAxis type="number" dataKey="b2b_delta" domain={yDomain}
            stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
            tickFormatter={v => (v >= 0 ? '+' : '') + v.toFixed(3)}
            label={{ value: 'B2B Delta  ↑ resilient · fragile ↓', angle: -90, position: 'insideLeft', dy: 60, fill: '#7ea4c4', fontSize: 10 }} />
          <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '3 3' }} />

          {/* Dividing lines */}
          <ReferenceLine y={0} stroke="rgba(56,189,248,0.35)" strokeWidth={1.5} />
          <ReferenceLine x={leagueMedianSv} stroke="rgba(56,189,248,0.35)" strokeWidth={1.5}
            label={{ value: 'Median SV%', fill: 'rgba(56,189,248,0.4)', fontSize: 9, position: 'top' }} />

          <Scatter data={qualified} shape={<QDot />} name="Goalies" />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Quadrant legend */}
      <div className="quadrant-legend">
        {QUADRANT_META.map(q => (
          <div key={q.key} className="quadrant-chip">
            <div className="qc-dot" style={{ background: q.color }} />
            <div>
              <div className="qc-name" style={{ color: q.color }}>{q.label}</div>
              <div className="qc-desc">{q.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

// ── HDSV% vs SV% Scatter ──────────────────────────────────────────────────────
function HdsvScatter({ goalies }: { goalies: GoalieStat[] }) {
  const hasHdsv = useMemo(
    () => goalies.filter((g) => g.career_hdsv_pct != null && g.avg_sv != null),
    [goalies]
  )
  const xDomain = useMemo(() => {
    if (!hasHdsv.length) return [0.80, 0.92]
    const vals = hasHdsv.map((g) => g.career_hdsv_pct as number)
    return [Math.max(0.78, Math.min(...vals) - 0.005), Math.min(1.0, Math.max(...vals) + 0.005)]
  }, [hasHdsv])
  const yDomain = useMemo(() => {
    if (!hasHdsv.length) return [0.88, 0.94]
    const vals = hasHdsv.map((g) => g.avg_sv)
    return [Math.max(0.87, Math.min(...vals) - 0.003), Math.min(1.0, Math.max(...vals) + 0.003)]
  }, [hasHdsv])

  if (!hasHdsv.length) return <div className="loading-state">No HDSV% data</div>

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis type="number" dataKey="career_hdsv_pct" domain={xDomain} stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }} tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
          label={{ value: 'Career HDSV%', position: 'insideBottom', offset: -10, fill: '#555c70', fontSize: 12 }} />
        <YAxis type="number" dataKey="avg_sv" domain={yDomain} stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }} tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
          label={{ value: 'Avg SV%', angle: -90, position: 'insideLeft', fill: '#555c70', fontSize: 12 }} />
        <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={hasHdsv} shape={<HdsvDot />} name="Goalies">
          {hasHdsv.map((g) => <Cell key={g.player_id} fill={gsaxColor(g.career_gsax)} />)}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}

// ── GSAx Leaders Bar Chart ────────────────────────────────────────────────────
function GsaxLeaders({ goalies }: { goalies: GoalieStat[] }) {
  const top15 = useMemo(
    () =>
      [...goalies]
        .filter((g) => g.career_gsax != null)
        .sort((a, b) => (b.career_gsax as number) - (a.career_gsax as number))
        .slice(0, 15),
    [goalies]
  )

  if (!top15.length) return <div className="loading-state">No GSAx data</div>

  interface LabelProps { x?: number; y?: number; width?: number; value?: number }
  const ValueLabel = ({ x, y, width, value }: LabelProps) => {
    if (value == null || x == null || y == null || width == null) return null
    return (
      <text x={x + width + 4} y={y + 12} fontSize={10} fill="#8b91a8" textAnchor="start">
        {value >= 0 ? '+' : ''}{value.toFixed(1)}
      </text>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={420}>
      <BarChart data={top15} layout="vertical" margin={{ top: 5, right: 60, bottom: 5, left: 140 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" horizontal={false} />
        <XAxis type="number" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }}
          tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(0)} />
        <YAxis type="category" dataKey="player_name" stroke="#555c70"
          tick={{ fill: '#e8eaf0', fontSize: 11 }} width={135} />
        <Tooltip
          contentStyle={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, color: '#e8eaf0', fontSize: '0.85rem' }}
          formatter={(v: number) => [(v >= 0 ? '+' : '') + v.toFixed(1), 'Career GSAx']}
        />
        <ReferenceLine x={0} stroke="#555c70" strokeWidth={1.5} />
        <Bar dataKey="career_gsax" name="Career GSAx" radius={[0, 3, 3, 0]} label={<ValueLabel />}>
          {top15.map((g) => <Cell key={g.player_id} fill={gsaxColor(g.career_gsax)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Mini Top/Bottom table ─────────────────────────────────────────────────────
function TopBottomTable({ goalies }: { goalies: GoalieStat[] }) {
  const withDelta = useMemo(
    () => goalies.filter((g) => g.b2b_delta != null && g.b2b_games >= 5),
    [goalies]
  )
  const top5 = useMemo(
    () => [...withDelta].sort((a, b) => (b.b2b_delta as number) - (a.b2b_delta as number)).slice(0, 5),
    [withDelta]
  )
  const bottom5 = useMemo(
    () => [...withDelta].sort((a, b) => (a.b2b_delta as number) - (b.b2b_delta as number)).slice(0, 5),
    [withDelta]
  )

  const Row = ({ g, rank, dir }: { g: GoalieStat; rank: number; dir: 'top' | 'bot' }) => (
    <div className="mini-table-row">
      <span className={`rank-badge ${rank <= 3 ? 'top3' : ''}`}>{rank}</span>
      <span className="mini-table-name">{g.player_name}</span>
      <span className="mini-table-team">{g.teams[0]}</span>
      <span className="mini-table-value" style={{ color: dir === 'top' ? 'var(--success)' : 'var(--danger)' }}>
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
    <th className={sortField === field ? 'sort-active' : ''} onClick={() => onSort(field)}>
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
            <Th field="career_gsax" label="Career GSAx" />
            <Th field="career_hdsv_pct" label="HDSV%" />
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
              <td><span className={`rank-badge ${i < 3 ? 'top3' : ''}`}>{i + 1}</span></td>
              <td style={{ fontWeight: 500 }}>{g.player_name}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                  {g.teams.slice(0, 3).map((t) => (
                    <TeamLogo key={t} team={t} size={20} />
                  ))}
                  {g.teams.length > 3 && <span className="td-muted">+{g.teams.length - 3}</span>}
                </div>
              </td>
              <td>{g.total_games}</td>
              <td>{fmt.sv(g.avg_sv)}</td>
              <td>{g.avg_gaa?.toFixed(2) ?? '—'}</td>
              <td style={{ color: gsaxColor(g.career_gsax), fontWeight: g.career_gsax != null ? 600 : 400 }}>
                {g.career_gsax != null ? (g.career_gsax >= 0 ? '+' : '') + g.career_gsax.toFixed(1) : '—'}
              </td>
              <td className={g.career_hdsv_pct == null ? 'td-muted' : ''}>
                {g.career_hdsv_pct != null ? fmt.sv(g.career_hdsv_pct) : '—'}
              </td>
              <td className="td-muted">{g.b2b_games}</td>
              <td>{fmt.sv(g.b2b_sv)}</td>
              <td>{fmt.sv(g.rest_sv)}</td>
              <td className={
                g.b2b_delta == null ? 'td-muted' : g.b2b_delta < -0.01 ? 'td-negative' : g.b2b_delta > 0.01 ? 'td-positive' : ''
              }>
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

  const hasGsax = useMemo(() => filtered.some((g) => g.career_gsax != null), [filtered])
  const hasHdsv = useMemo(() => filtered.some((g) => g.career_hdsv_pct != null), [filtered])

  if (loading) return <div className="loading-state">Loading...</div>
  if (error) return <div className="error-state">{error}</div>

  const qualified = useMemo(
    () => filtered.filter(g => g.quadrant != null),
    [filtered]
  )
  const quadrantCounts = useMemo(() => {
    const c: Record<string, number> = {}
    qualified.forEach(g => { if (g.quadrant) c[g.quadrant] = (c[g.quadrant] ?? 0) + 1 })
    return c
  }, [qualified])

  return (
    <main className="page">
      <h1 className="page-title">Goalie Resilience Lab</h1>
      <p className="page-subtitle">
        {filtered.length} goalies · fatigue resilience quadrant · min {minGames} games
      </p>

      {/* Quadrant KPI summary */}
      {qualified.length > 0 && (
        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
          {QUADRANT_META.map(q => (
            <div key={q.key} className="kpi-card">
              <div className="kpi-value" style={{ color: q.color, fontSize: '2rem' }}>
                {quadrantCounts[q.key] ?? 0}
              </div>
              <div className="kpi-label">{q.label}</div>
              <div className="kpi-delta">{q.desc}</div>
            </div>
          ))}
        </div>
      )}

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

      {/* Resilience Quadrant */}
      <div className="chart-card">
        <div className="chart-title">Goalie Resilience Quadrant</div>
        <div className="chart-subtitle">
          X = career average SV% (skill) · Y = B2B SV% delta (resilience) ·
          Dot size = career starts · labels shown for goalies with ≥120 starts
        </div>
        <QuadrantScatter goalies={filtered} />
      </div>

      {/* B2B Extremes */}
      <div className="chart-card">
        <div className="chart-title">B2B Impact Extremes</div>
        <div className="chart-subtitle">Min 5 B2B games for inclusion · most and least resilient goalies</div>
        <TopBottomTable goalies={filtered} />
      </div>

      {/* GSAx Leaders */}
      {hasGsax && (
        <div className="grid-5545">
          <div className="chart-card">
            <div className="chart-title">Career GSAx Leaders</div>
            <div className="chart-subtitle">
              Goals Saved Above Expected (MoneyPuck) · green = elite, red = below average
            </div>
            <GsaxLeaders goalies={filtered} />
          </div>
          {hasHdsv && (
            <div className="chart-card">
              <div className="chart-title">HDSV% vs Overall SV%</div>
              <div className="chart-subtitle">
                High-Danger Save % vs career average · dot color = career GSAx tier
              </div>
              <HdsvScatter goalies={filtered} />
            </div>
          )}
        </div>
      )}

      {/* Data Table */}
      <div className="chart-card">
        <div className="chart-title">Goalie Data Table</div>
        <div className="chart-subtitle">
          Click column headers to sort · GSAx &amp; HDSV% from MoneyPuck season data
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
