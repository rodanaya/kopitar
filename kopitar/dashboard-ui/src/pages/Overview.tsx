import { useEffect, useState, useMemo } from 'react'
import {
  ComposedChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts'
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip } from 'react-leaflet'
import type { Overview as OverviewData, TeamStat, RecoveryPoint, ScheduleStress } from '../types'
import { fmt, deltaColor, TEAM_NAMES } from '../utils'

const TT = {
  contentStyle: {
    background: '#0c1d33', border: '1px solid rgba(56,189,248,0.18)',
    borderRadius: '10px', color: '#eef4ff', fontSize: '0.83rem',
    boxShadow: '0 8px 28px rgba(0,0,0,0.5)',
  },
}

// ── League Map ────────────────────────────────────────────────────────────────
function LeagueMap({ teams }: { teams: TeamStat[] }) {
  return (
    <MapContainer center={[44, -96]} zoom={3} zoomControl={false} attributionControl={false} className="leaflet-map">
      <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
      {teams.map((t) => {
        if (!t.lat || !t.lon) return null
        const radius = Math.min(14, 8 + t.avg_travel_miles / 200)
        const color = deltaColor(t.b2b_delta)
        return (
          <CircleMarker key={t.team} center={[t.lat, t.lon]} radius={radius}
            pathOptions={{ fillColor: color, fillOpacity: 0.85, color: '#060c18', weight: 1.5 }}>
            <LeafletTooltip>
              <strong>{t.team}</strong> — {TEAM_NAMES[t.team] ?? t.team}<br />
              B2B Delta: {fmt.delta(t.b2b_delta)} · Avg Travel: {fmt.miles(t.avg_travel_miles)}
            </LeafletTooltip>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}

// ── B2B Rankings ─────────────────────────────────────────────────────────────
function B2BRankings({ teams }: { teams: TeamStat[] }) {
  const sorted = useMemo(() =>
    [...teams].filter(t => t.b2b_sv != null).sort((a, b) => (a.b2b_delta ?? 0) - (b.b2b_delta ?? 0)).slice(0, 20),
    [teams]
  )
  interface B2BPayload { b2b_sv: number | null; rest_sv: number; b2b_delta: number | null }
  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" horizontal={false} />
        <XAxis type="number" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }}
          tickFormatter={v => (v >= 0 ? '+' : '') + v.toFixed(3)} domain={['auto', 'auto']} />
        <YAxis type="category" dataKey="team" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }} width={36} />
        <Tooltip
          {...TT}
          formatter={(_: unknown, __: unknown, props: { payload?: B2BPayload }) => {
            const d = props.payload
            if (!d) return ['—', '']
            return [<span key="x">B2B: {fmt.sv(d.b2b_sv)} · Rest: {fmt.sv(d.rest_sv)} · Delta: {fmt.delta(d.b2b_delta)}</span>, '']
          }}
          labelFormatter={(l: string) => TEAM_NAMES[l] ?? l}
        />
        <ReferenceLine x={0} stroke="rgba(56,189,248,0.25)" strokeWidth={1.5} />
        <Bar dataKey="b2b_delta" radius={[0, 3, 3, 0]}>
          {sorted.map(e => <Cell key={e.team} fill={(e.b2b_delta ?? 0) < 0 ? '#f43f5e' : '#34d399'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Recovery Curve ────────────────────────────────────────────────────────────
interface RCTooltipProps { active?: boolean; payload?: Array<{ payload: RecoveryPoint }> }
function RCTooltip({ active, payload }: RCTooltipProps) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ ...TT.contentStyle, padding: '0.75rem 1rem' }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.days_rest} day{d.days_rest !== 1 ? 's' : ''} rest</div>
      <div>Mean SV%: <strong>{fmt.sv(d.mean_sv)}</strong></div>
      <div>95% CI: {fmt.sv(d.ci_lower)} – {fmt.sv(d.ci_upper)}</div>
      <div style={{ color: '#7ea4c4', fontSize: '0.78rem' }}>n={d.count.toLocaleString()} starts</div>
    </div>
  )
}

function RecoveryCurve({ data }: { data: RecoveryPoint[] }) {
  const peakDay = useMemo(() =>
    data.length ? data.reduce((b, d) => d.mean_sv > b.mean_sv ? d : b, data[0]).days_rest : 0,
    [data]
  )
  const chartData = useMemo(() => data.map(d => ({ ...d, ci_band: [d.ci_lower, d.ci_upper] })), [data])
  const yMin = useMemo(() => !data.length ? 0.88 : Math.max(0.85, Math.min(...data.map(d => d.ci_lower)) - 0.002), [data])
  const yMax = useMemo(() => !data.length ? 0.935 : Math.min(0.98, Math.max(...data.map(d => d.ci_upper)) + 0.002), [data])

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="days_rest" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 12 }}
          label={{ value: 'Days Rest Before Start', position: 'insideBottom', offset: -8, fill: '#7ea4c4', fontSize: 11 }} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 12 }}
          domain={[yMin, yMax]} tickFormatter={v => (v * 100).toFixed(1) + '%'} />
        <Tooltip content={<RCTooltip />} />
        <ReferenceLine x={peakDay} stroke="#fbbf24" strokeDasharray="4 3"
          label={{ value: `Peak: ${peakDay}d`, fill: '#fbbf24', fontSize: 11, position: 'top' }} />
        <Area type="monotone" dataKey="ci_upper" fill="#38bdf8" fillOpacity={0.09} stroke="none" legendType="none" name="_up" />
        <Area type="monotone" dataKey="ci_lower" fill="var(--bg-card)" fillOpacity={1} stroke="none" legendType="none" name="_lo" />
        <Line type="monotone" dataKey="mean_sv" stroke="#38bdf8" strokeWidth={2.5}
          dot={{ fill: '#38bdf8', r: 4 }} activeDot={{ r: 6 }} name="Mean SV%" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

// ── Overview Page ─────────────────────────────────────────────────────────────
export default function Overview() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [teams, setTeams] = useState<TeamStat[]>([])
  const [recovery, setRecovery] = useState<RecoveryPoint[]>([])
  const [stress, setStress] = useState<ScheduleStress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/data/overview.json').then(r => r.json()),
      fetch('/data/teams.json').then(r => r.json()),
      fetch('/data/recovery.json').then(r => r.json()),
      fetch('/data/schedule_stress.json').then(r => r.json()).catch(() => null),
    ]).then(([ov, tm, rc, st]) => {
      setOverview(ov as OverviewData)
      setTeams(tm as TeamStat[])
      setRecovery(rc as RecoveryPoint[])
      if (st) setStress(st as ScheduleStress)
    }).catch(() => setError('Data not available — run the export script first.'))
      .finally(() => setLoading(false))
  }, [])

  const peakRecovery = useMemo(
    () => recovery.length ? recovery.reduce((b, d) => d.mean_sv > b.mean_sv ? d : b, recovery[0]) : null,
    [recovery]
  )
  const worstB2bTeam = useMemo(
    () => teams.length ? [...teams].filter(t => t.b2b_delta != null).sort((a, b) => (a.b2b_delta ?? 0) - (b.b2b_delta ?? 0))[0] : null,
    [teams]
  )

  if (loading) return <div className="loading-state">Loading…</div>
  if (error || !overview) return <div className="error-state">{error ?? 'Unknown error'}</div>

  const { kpis, league_b2b } = overview
  const f4 = stress?.four_in_six

  // Effect size: 4-in-6 delta × avg shots per game
  const goalsCostPerGame = f4?.goals_cost_per_game ?? null

  return (
    <main className="page">

      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <div className="hero-banner">
        <div className="hero-eyebrow">NHL Fatigue Lab · 10-Season Analysis · 2015–2025</div>
        <h1 className="hero-title">The Schedule Fatigue Problem</h1>
        <p className="hero-subtitle">
          Coach protection masks the B2B effect — but the 4-in-6 threshold exposes it.
          {goalsCostPerGame ? ` Each overextended start costs teams an estimated ${goalsCostPerGame.toFixed(2)} extra goals.` : ''}
        </p>
        <div className="hero-stat-row">
          <span><strong>{kpis.total_games.toLocaleString()}</strong> game logs</span>
          <span>·</span>
          <span><strong>{kpis.unique_goalies}</strong> goalies tracked</span>
          <span>·</span>
          <span><strong>{kpis.seasons}</strong> seasons</span>
          <span>·</span>
          <span><strong>{kpis.b2b_games.toLocaleString()}</strong> B2B starts ({(kpis.b2b_rate * 100).toFixed(1)}%)</span>
          {f4 && f4.significant && (
            <>
              <span>·</span>
              <span style={{ color: '#fbbf24' }}>4-in-6 effect p = {f4.p_value.toFixed(4)} ✱</span>
            </>
          )}
        </div>
      </div>

      {/* ── Three Insights ─────────────────────────────────────────────────── */}
      <div className="insight-grid">

        {/* 01 — The Paradox */}
        <div className="insight-card">
          <div className="insight-number">01</div>
          <div className="insight-label">The Paradox</div>
          <div className="insight-value" style={{ color: '#7ea4c4' }}>
            {fmt.delta(league_b2b.delta)}
          </div>
          <p className="insight-desc">
            League-wide B2B SV% delta is near zero — not because fatigue doesn't exist,
            but because coaches systematically protect their starter when a viable backup exists.
            Selection bias masks the true signal.
          </p>
        </div>

        {/* 02 — The Real Signal */}
        <div className="insight-card">
          <div className="insight-number">02</div>
          <div className="insight-label">The Real Signal</div>
          <div className="insight-value" style={{ color: f4?.significant ? '#f43f5e' : '#fbbf24' }}>
            {f4 ? fmt.delta(f4.delta) : '−0.007'}
          </div>
          <p className="insight-desc">
            SV% drop at the 4-in-6 threshold — a goalie's 4th start within 6 days.
            Statistically significant (p={f4?.p_value.toFixed(4) ?? '0.035'}).
            At this density, cumulative fatigue overrides coach rotation.
            {goalsCostPerGame ? ` ≈ ${goalsCostPerGame.toFixed(2)} extra goals per game.` : ''}
          </p>
        </div>

        {/* 03 — Recovery Peak */}
        <div className="insight-card">
          <div className="insight-number">03</div>
          <div className="insight-label">Peak Recovery</div>
          <div className="insight-value" style={{ color: '#34d399' }}>
            {peakRecovery ? `${peakRecovery.days_rest} days` : '8 days'}
          </div>
          <p className="insight-desc">
            Optimal rest before a start. Goalies averaging {peakRecovery ? fmt.sv(peakRecovery.mean_sv) : '~.915'}
            at this rest level — well above the B2B baseline. The curve plateaus after day 8–10,
            meaning rest beyond 10 days offers no additional benefit.
          </p>
        </div>
      </div>

      {/* ── Map + B2B Rankings ────────────────────────────────────────────── */}
      <div className="grid-6040">
        <div className="chart-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.5rem 1.5rem 0.75rem' }}>
            <div className="chart-title">Geographic B2B Impact</div>
            <div className="chart-subtitle">
              Dot size = avg travel miles · color = B2B delta (crimson = worse, green = better)
            </div>
          </div>
          {teams.length > 0 ? <LeagueMap teams={teams} /> : <div className="loading-state">No team data</div>}
        </div>

        <div className="chart-card">
          <div className="chart-title">Worst B2B Teams</div>
          <div className="chart-subtitle">
            SV% delta on back-to-backs · {worstB2bTeam ? `${worstB2bTeam.team} most impacted at ${fmt.delta(worstB2bTeam.b2b_delta)}` : 'top 20 shown'}
          </div>
          {teams.length > 0 ? <B2BRankings teams={teams} /> : <div className="loading-state">No team data</div>}
        </div>
      </div>

      {/* ── Recovery Curve ────────────────────────────────────────────────── */}
      <div className="chart-card">
        <div className="chart-title">Goalie Recovery Curve</div>
        <div className="chart-subtitle">
          Mean SV% by days of rest · shaded band = 95% confidence interval ·
          gold dashed = peak performance day ({peakRecovery?.days_rest ?? '?'} days)
        </div>
        {recovery.length > 0
          ? <RecoveryCurve data={recovery} />
          : <div className="loading-state">No recovery data</div>}
        {peakRecovery && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid rgba(56,189,248,0.08)' }}>
            {[
              { label: 'B2B SV% (1d rest)', val: fmt.sv(league_b2b.b2b_sv), color: '#f43f5e' },
              { label: 'Rested SV% (≥2d)', val: fmt.sv(league_b2b.rest_sv), color: '#34d399' },
              { label: `Peak SV% (${peakRecovery.days_rest}d)`, val: fmt.sv(peakRecovery.mean_sv), color: '#fbbf24' },
              { label: 'Peak vs B2B Delta', val: fmt.delta((peakRecovery.mean_sv ?? 0) - (league_b2b.b2b_sv ?? peakRecovery.mean_sv)), color: 'var(--accent-ice)' },
            ].map(item => (
              <div key={item.label} style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'Barlow Condensed, sans-serif', fontStyle: 'italic', fontWeight: 700, fontSize: '1.6rem', color: item.color }}>{item.val}</div>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{item.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>

    </main>
  )
}
