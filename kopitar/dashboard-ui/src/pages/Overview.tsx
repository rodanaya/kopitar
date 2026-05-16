import { useEffect, useState, useMemo } from 'react'
import {
  ComposedChart,
  Area,
  Line,
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
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip } from 'react-leaflet'
import type { Overview as OverviewData, TeamStat, RecoveryPoint } from '../types'
import { fmt, deltaColor, TEAM_NAMES } from '../utils'

// ── Tooltip styles shared across charts ──────────────────────────────────────
const tooltipStyle = {
  contentStyle: {
    background: '#141824',
    border: '1px solid #2a2f45',
    borderRadius: '8px',
    color: '#e8eaf0',
    fontSize: '0.85rem',
  },
  cursor: { fill: 'rgba(79,156,249,0.08)' },
}

// ── LeagueMap ────────────────────────────────────────────────────────────────
function LeagueMap({ teams }: { teams: TeamStat[] }) {
  return (
    <MapContainer
      center={[44, -96]}
      zoom={3}
      zoomControl={false}
      attributionControl={false}
      className="leaflet-map"
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      {teams.map((t) => {
        if (!t.lat || !t.lon) return null
        const radius = Math.min(14, 8 + t.avg_travel_miles / 200)
        const color = deltaColor(t.b2b_delta)
        return (
          <CircleMarker
            key={t.team}
            center={[t.lat, t.lon]}
            radius={radius}
            pathOptions={{
              fillColor: color,
              fillOpacity: 0.85,
              color: '#0b0e18',
              weight: 1.5,
            }}
          >
            <LeafletTooltip>
              <strong>{t.team}</strong> — {TEAM_NAMES[t.team] ?? t.team}<br />
              B2B Delta: {fmt.delta(t.b2b_delta)}<br />
              Avg Travel: {fmt.miles(t.avg_travel_miles)}<br />
              Avg SV%: {fmt.sv(t.avg_sv)}
            </LeafletTooltip>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}

// ── B2B Rankings ─────────────────────────────────────────────────────────────
interface B2BTooltipPayload {
  b2b_sv: number | null
  rest_sv: number
  b2b_delta: number | null
}

function B2BRankings({ teams }: { teams: TeamStat[] }) {
  const sorted = useMemo(() => {
    return [...teams]
      .filter((t) => t.b2b_sv != null)
      .sort((a, b) => (a.b2b_delta ?? 0) - (b.b2b_delta ?? 0))
      .slice(0, 20)
  }, [teams])

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 5, right: 20, bottom: 5, left: 40 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" horizontal={false} />
        <XAxis
          type="number"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)}
          domain={['auto', 'auto']}
        />
        <YAxis
          type="category"
          dataKey="team"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          width={36}
        />
        <Tooltip
          {...tooltipStyle}
          formatter={(_value: unknown, _name: unknown, props: { payload?: B2BTooltipPayload }) => {
            const d = props.payload
            if (!d) return ['—', '']
            return [
              <span key="info">
                B2B SV%: {fmt.sv(d.b2b_sv)}<br />
                Rest SV%: {fmt.sv(d.rest_sv)}<br />
                Delta: {fmt.delta(d.b2b_delta)}
              </span>,
              '',
            ]
          }}
          labelFormatter={(label: string) => TEAM_NAMES[label] ?? label}
        />
        <ReferenceLine x={0} stroke="#2a2f45" strokeWidth={2} />
        <Bar dataKey="b2b_delta" radius={[0, 3, 3, 0]}>
          {sorted.map((entry) => (
            <Cell
              key={entry.team}
              fill={(entry.b2b_delta ?? 0) < 0 ? '#ef5350' : '#4caf7d'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Recovery Curve ────────────────────────────────────────────────────────────
interface RecoveryTooltipProps {
  active?: boolean
  payload?: Array<{ payload: RecoveryPoint }>
  label?: number
}

function RecoveryTooltipContent({ active, payload }: RecoveryTooltipProps) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#e8eaf0' }}>
      <div><strong>{d.days_rest} day{d.days_rest !== 1 ? 's' : ''} rest</strong></div>
      <div>Mean SV%: <strong>{fmt.sv(d.mean_sv)}</strong></div>
      <div>95% CI: {fmt.sv(d.ci_lower)} – {fmt.sv(d.ci_upper)}</div>
      <div>Sample: {d.count} games</div>
    </div>
  )
}

function RecoveryCurve({ data }: { data: RecoveryPoint[] }) {
  const peakDay = useMemo(() => {
    if (!data.length) return 0
    return data.reduce((best, d) => (d.mean_sv > best.mean_sv ? d : best), data[0]).days_rest
  }, [data])

  const chartData = useMemo(() => data.map((d) => ({
    ...d,
    ci_band: [d.ci_lower, d.ci_upper] as [number, number],
  })), [data])

  const yMin = useMemo(() => {
    if (!data.length) return 0.88
    return Math.max(0.85, Math.min(...data.map((d) => d.ci_lower)) - 0.002)
  }, [data])

  const yMax = useMemo(() => {
    if (!data.length) return 0.935
    return Math.min(0.98, Math.max(...data.map((d) => d.ci_upper)) + 0.002)
  }, [data])

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          dataKey="days_rest"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 12 }}
          label={{ value: 'Days Rest', position: 'insideBottom', offset: -2, fill: '#555c70', fontSize: 12 }}
        />
        <YAxis
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 12 }}
          domain={[yMin, yMax]}
          tickFormatter={(v) => (v * 100).toFixed(1) + '%'}
        />
        <Tooltip content={<RecoveryTooltipContent />} />
        <ReferenceLine
          x={peakDay}
          stroke="#f5c842"
          strokeDasharray="4 3"
          label={{ value: `Peak: ${peakDay}d`, fill: '#f5c842', fontSize: 11, position: 'top' }}
        />
        <Area
          type="monotone"
          dataKey="ci_upper"
          fill="#4f9cf9"
          fillOpacity={0.12}
          stroke="none"
          legendType="none"
          name="CI Upper"
        />
        <Area
          type="monotone"
          dataKey="ci_lower"
          fill={`var(--bg-card)`}
          fillOpacity={1}
          stroke="none"
          legendType="none"
          name="CI Lower"
        />
        <Line
          type="monotone"
          dataKey="mean_sv"
          stroke="#4f9cf9"
          strokeWidth={2.5}
          dot={{ fill: '#4f9cf9', r: 4 }}
          activeDot={{ r: 6, fill: '#4f9cf9' }}
          name="Mean SV%"
        />
        <Legend wrapperStyle={{ color: '#8b91a8', fontSize: '0.85rem' }} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

// ── Overview Page ─────────────────────────────────────────────────────────────
export default function Overview() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [teams, setTeams] = useState<TeamStat[]>([])
  const [recovery, setRecovery] = useState<RecoveryPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [ov, tm, rc] = await Promise.all([
          fetch('/data/overview.json').then((r) => r.json()),
          fetch('/data/teams.json').then((r) => r.json()),
          fetch('/data/recovery.json').then((r) => r.json()),
        ])
        setOverview(ov as OverviewData)
        setTeams(tm as TeamStat[])
        setRecovery(rc as RecoveryPoint[])
      } catch {
        setError('Data not available — run the export script first.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className="loading-state">Loading...</div>
  if (error || !overview) return <div className="error-state">{error ?? 'Unknown error'}</div>

  const { kpis, league_b2b } = overview

  return (
    <main className="page">
      <h1 className="page-title">League Overview</h1>
      <p className="page-subtitle">
        {kpis.seasons} seasons · {kpis.total_games.toLocaleString()} game logs · {kpis.unique_goalies} goalies
      </p>

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-value">{kpis.total_games.toLocaleString()}</div>
          <div className="kpi-label">Total Game Logs</div>
          <div className="kpi-delta">{kpis.seasons} seasons analyzed</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{kpis.unique_goalies}</div>
          <div className="kpi-label">Unique Goalies</div>
          <div className="kpi-delta">All NHL starters & backups</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: 'var(--accent-gold)' }}>
            {fmt.pct(kpis.b2b_rate)}
          </div>
          <div className="kpi-label">B2B Game Rate</div>
          <div className="kpi-delta">{kpis.b2b_games.toLocaleString()} back-to-back starts</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: league_b2b.delta < 0 ? 'var(--danger)' : 'var(--success)' }}>
            {fmt.delta(league_b2b.delta)}
          </div>
          <div className="kpi-label">League B2B SV% Delta</div>
          <div className="kpi-delta">
            p={fmt.pValue(league_b2b.p_value)} · {league_b2b.significant ? 'significant' : 'not significant'}
          </div>
        </div>
      </div>

      {/* Map + B2B Rankings */}
      <div className="grid-6040">
        <div className="chart-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.5rem 1.5rem 0.75rem' }}>
            <div className="chart-title">Team Locations &amp; B2B Impact</div>
            <div className="chart-subtitle">
              Circle size = avg travel miles · Color = B2B delta (red = worse, green = better)
            </div>
          </div>
          {teams.length > 0 ? <LeagueMap teams={teams} /> : (
            <div className="loading-state">No team location data</div>
          )}
        </div>

        <div className="chart-card">
          <div className="chart-title">B2B Impact Rankings</div>
          <div className="chart-subtitle">Teams by save% delta on back-to-back nights</div>
          {teams.length > 0 ? <B2BRankings teams={teams} /> : (
            <div className="loading-state">No team data</div>
          )}
        </div>
      </div>

      {/* Recovery Curve */}
      <div className="chart-card">
        <div className="chart-title">Goalie Recovery Curve</div>
        <div className="chart-subtitle">
          Mean save percentage by days of rest (shaded area = 95% confidence interval)
        </div>
        {recovery.length > 0 ? <RecoveryCurve data={recovery} /> : (
          <div className="loading-state">No recovery data</div>
        )}
      </div>

      {/* League B2B summary */}
      <div className="chart-card">
        <div className="chart-title">League-Wide B2B Summary</div>
        <div className="chart-subtitle">Aggregate statistics across all teams and seasons</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginTop: '0.5rem' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>B2B SV%</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>{fmt.sv(league_b2b.b2b_sv)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>Rested SV%</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>{fmt.sv(league_b2b.rest_sv)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>Delta</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: league_b2b.delta < 0 ? 'var(--danger)' : 'var(--success)' }}>
              {fmt.delta(league_b2b.delta)}
            </div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>p-value</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>{fmt.pValue(league_b2b.p_value)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>Significant</div>
            <div>
              <span className={league_b2b.significant ? 'tag tag-negative' : 'tag tag-neutral'}>
                {league_b2b.significant ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
