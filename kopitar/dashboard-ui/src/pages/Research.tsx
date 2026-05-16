import { useEffect, useState, useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts'
import type {
  Overview as OverviewData,
  SeasonPoint,
  DivisionStat,
  RecoveryPoint,
  ScheduleStress,
  RoadTripLeg,
  AltitudeBin,
  SeasonPhaseStat,
  ScheduleStressMetric,
} from '../types'
import { fmt, DIVISION_COLORS } from '../utils'

// ── Shared chart style ────────────────────────────────────────────────────────
const tooltipStyle = {
  contentStyle: {
    background: '#141824',
    border: '1px solid #2a2f45',
    borderRadius: '8px',
    color: '#e8eaf0',
    fontSize: '0.85rem',
  },
}

// ── Season Trend Chart ────────────────────────────────────────────────────────
interface SeasonBarTooltipProps {
  active?: boolean
  payload?: Array<{ payload: SeasonPoint }>
}

function SeasonTooltip({ active, payload }: SeasonBarTooltipProps) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#e8eaf0' }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.label}</div>
      <div>B2B Delta: <strong style={{ color: d.delta < 0 ? '#ef5350' : '#4caf7d' }}>{fmt.delta(d.delta)}</strong></div>
      <div>B2B SV%: {fmt.sv(d.b2b_sv)}</div>
      <div>Rest SV%: {fmt.sv(d.rest_sv)}</div>
      <div>B2B Games: {d.b2b_n}</div>
      <div>p-value: {fmt.pValue(d.p_value)}</div>
      {d.significant && <div style={{ color: '#f5c842', marginTop: 4 }}>* Statistically significant</div>}
    </div>
  )
}

interface SeasonLabelProps { x?: number; y?: number; width?: number; value?: number; payload?: SeasonPoint }
function SeasonLabel({ x, y, width, value, payload }: SeasonLabelProps) {
  if (!payload?.significant || value == null || x == null || y == null || width == null) return null
  return (
    <text x={x + width / 2} y={value < 0 ? y + 16 : y - 6} textAnchor="middle" fill="#f5c842" fontSize={13} fontWeight={700}>*</text>
  )
}

function SeasonTrend({ seasons }: { seasons: SeasonPoint[] }) {
  const sorted = useMemo(() => [...seasons].sort((a, b) => a.season.localeCompare(b.season)), [seasons])
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sorted} margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis dataKey="label" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
        <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)} domain={['auto', 'auto']} />
        <Tooltip content={<SeasonTooltip />} />
        <ReferenceLine y={0} stroke="#555c70" strokeWidth={1.5} />
        <Bar dataKey="delta" name="B2B Delta" radius={[3, 3, 0, 0]} label={<SeasonLabel />}>
          {sorted.map((s) => <Cell key={s.season} fill={s.delta < 0 ? '#ef5350' : '#4caf7d'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Division Chart ────────────────────────────────────────────────────────────
function DivisionChart({ divisions }: { divisions: DivisionStat[] }) {
  const sorted = useMemo(() => {
    const order = ['Atlantic', 'Metropolitan', 'Central', 'Pacific']
    return [...divisions].sort((a, b) => order.indexOf(a.division) - order.indexOf(b.division))
  }, [divisions])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>Average Save % by Division</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis dataKey="division" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} />
            <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} domain={['auto', 'auto']} tickFormatter={(v) => (v * 100).toFixed(1) + '%'} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [fmt.sv(v), 'Avg SV%']} />
            <Bar dataKey="avg_sv" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>B2B Delta by Division</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis dataKey="division" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} />
            <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} domain={['auto', 'auto']} tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [(v >= 0 ? '+' : '') + v.toFixed(4), 'B2B Delta']} />
            <ReferenceLine y={0} stroke="#555c70" />
            <Bar dataKey="b2b_delta" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => <Cell key={d.division} fill={d.b2b_delta < 0 ? '#ef5350' : '#4caf7d'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>Average Travel Miles by Division</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis dataKey="division" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} />
            <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} tickFormatter={(v) => v.toLocaleString()} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [fmt.miles(v), 'Avg Travel']} />
            <Bar dataKey="avg_travel_miles" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} fillOpacity={0.7} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>B2B Game Rate by Division</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis dataKey="division" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} />
            <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} tickFormatter={(v) => (v * 100).toFixed(0) + '%'} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [fmt.pct(v), 'B2B Rate']} />
            <Bar dataKey="b2b_rate" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} fillOpacity={0.8} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Statistical Summary Table ─────────────────────────────────────────────────
function StatTable({ seasons }: { seasons: SeasonPoint[] }) {
  const sorted = useMemo(() => [...seasons].sort((a, b) => a.season.localeCompare(b.season)), [seasons])
  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Season</th>
            <th>Total Games</th>
            <th>B2B Games</th>
            <th>B2B SV%</th>
            <th>Rested SV%</th>
            <th>Delta</th>
            <th>p-value</th>
            <th>Significant?</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr key={s.season}>
              <td style={{ fontWeight: 500 }}>{s.label}</td>
              <td>{s.total_games.toLocaleString()}</td>
              <td>{s.b2b_n}</td>
              <td>{fmt.sv(s.b2b_sv)}</td>
              <td>{fmt.sv(s.rest_sv)}</td>
              <td className={s.delta < -0.01 ? 'td-negative' : s.delta > 0.01 ? 'td-positive' : ''}>{fmt.delta(s.delta)}</td>
              <td className={s.p_value < 0.05 ? 'td-positive' : 'td-muted'}>{fmt.pValue(s.p_value)}</td>
              <td>
                {s.significant ? <span className="tag tag-gold">Yes *</span> : <span className="tag tag-neutral">No</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Recovery Summary ──────────────────────────────────────────────────────────
function RecoverySummary({ data }: { data: RecoveryPoint[] }) {
  const peak = useMemo(() => {
    if (!data.length) return null
    return data.reduce((best, d) => (d.mean_sv > best.mean_sv ? d : best), data[0])
  }, [data])
  if (!peak) return null

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
      {data.slice(0, 10).map((d) => (
        <div key={d.days_rest} style={{
          background: 'var(--bg-primary)',
          border: `1px solid ${d.days_rest === peak.days_rest ? 'var(--accent-gold)' : 'var(--border)'}`,
          borderRadius: 8,
          padding: '0.75rem 1rem',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>
            {d.days_rest} day{d.days_rest !== 1 ? 's' : ''} rest{d.days_rest === peak.days_rest && ' ★'}
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: d.days_rest === peak.days_rest ? 'var(--accent-gold)' : 'var(--text-primary)' }}>
            {fmt.sv(d.mean_sv)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>n={d.count}</div>
        </div>
      ))}
    </div>
  )
}

// ── Schedule Stress Components ────────────────────────────────────────────────

function DensityComparisonChart({ four_in_six, three_in_four }: { four_in_six?: ScheduleStressMetric; three_in_four?: ScheduleStressMetric }) {
  const data = [
    four_in_six && {
      label: '4-in-6',
      'With Flag': four_in_six.mean_with,
      'Without Flag': four_in_six.mean_without,
      delta: four_in_six.delta,
      p: four_in_six.p_value,
      sig: four_in_six.significant,
      n: four_in_six.n_with,
    },
    three_in_four && {
      label: '3-in-4',
      'With Flag': three_in_four.mean_with,
      'Without Flag': three_in_four.mean_without,
      delta: three_in_four.delta,
      p: three_in_four.p_value,
      sig: three_in_four.significant,
      n: three_in_four.n_with,
    },
  ].filter(Boolean)

  if (!data.length) return <div className="loading-state">No density data</div>

  const allVals = data.flatMap((d) => [d!['With Flag' as keyof typeof d] as number, d!['Without Flag' as keyof typeof d] as number])
  const minVal = Math.min(...allVals) - 0.001
  const maxVal = Math.max(...allVals) + 0.001

  interface DensityTooltipProps { active?: boolean; payload?: Array<{ name: string; value: number; payload: typeof data[0] }> }
  function DensityTooltip({ active, payload }: DensityTooltipProps) {
    if (!active || !payload?.length) return null
    const d = payload[0].payload!
    return (
      <div style={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#e8eaf0' }}>
        <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.label} Schedule Stress</div>
        <div>With flag: <strong>{fmt.sv(d['With Flag'])}</strong> (n={d.n?.toLocaleString()})</div>
        <div>Without: <strong>{fmt.sv(d['Without Flag'])}</strong></div>
        <div style={{ color: d.delta < 0 ? '#ef5350' : '#4caf7d', marginTop: 4 }}>
          Delta: {d.delta >= 0 ? '+' : ''}{d.delta?.toFixed(5)}
        </div>
        <div style={{ color: d.sig ? '#f5c842' : '#8b91a8' }}>
          p = {d.p?.toFixed(4)}{d.sig ? ' *' : ''}
        </div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 20, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis dataKey="label" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 12 }} />
        <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={(v) => (v * 100).toFixed(2) + '%'} />
        <Tooltip content={<DensityTooltip />} />
        <Legend wrapperStyle={{ color: '#8b91a8', fontSize: '0.8rem' }} />
        <Bar dataKey="With Flag" fill="#ef5350" radius={[3, 3, 0, 0]} />
        <Bar dataKey="Without Flag" fill="#4caf7d" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function RoadTripChart({ legs }: { legs: RoadTripLeg[] }) {
  if (!legs.length) return <div className="loading-state">No road trip data</div>
  const homeVal = legs.find((l) => l.leg === 0)?.mean_sv ?? 0.9
  const minVal = Math.min(...legs.map((l) => l.mean_sv)) - 0.001
  const maxVal = Math.max(...legs.map((l) => l.mean_sv)) + 0.001

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={legs} margin={{ top: 20, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis dataKey="label" stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 11 }} />
        <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={(v) => (v * 100).toFixed(2) + '%'} />
        <Tooltip
          contentStyle={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, color: '#e8eaf0', fontSize: '0.85rem' }}
          formatter={(v: number) => [fmt.sv(v), 'Mean SV%']}
        />
        <ReferenceLine y={homeVal} stroke="#4f9cf9" strokeDasharray="4 3"
          label={{ value: 'Home Avg', fill: '#4f9cf9', fontSize: 10, position: 'right' }} />
        <Bar dataKey="mean_sv" name="Mean SV%" radius={[3, 3, 0, 0]}>
          {legs.map((l) => (
            <Cell key={l.leg} fill={l.leg === 0 ? '#4f9cf9' : l.mean_sv < homeVal ? '#ef5350' : '#4caf7d'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function SimpleBarChart({ data, dataKey, labelKey, title }: {
  data: (AltitudeBin | SeasonPhaseStat)[]
  dataKey: string
  labelKey: string
  title: string
}) {
  if (!data.length) return null
  const vals = data.map((d) => (d as unknown as Record<string, number>)[dataKey])
  const minVal = Math.min(...vals) - 0.001
  const maxVal = Math.max(...vals) + 0.001
  const refVal = vals[0]

  return (
    <div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{title}</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
          <XAxis dataKey={labelKey} stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }} />
          <YAxis stroke="#555c70" tick={{ fill: '#8b91a8', fontSize: 10 }}
            domain={[minVal, maxVal]} tickFormatter={(v) => (v * 100).toFixed(2) + '%'} />
          <Tooltip
            contentStyle={{ background: '#141824', border: '1px solid #2a2f45', borderRadius: 8, color: '#e8eaf0', fontSize: '0.85rem' }}
            formatter={(v: number) => [fmt.sv(v), 'Mean SV%']}
          />
          <ReferenceLine y={refVal} stroke="#555c70" strokeDasharray="4 3" />
          <Bar dataKey={dataKey} radius={[3, 3, 0, 0]}>
            {data.map((d, i) => {
              const v = (d as unknown as Record<string, number>)[dataKey]
              return <Cell key={i} fill={v >= refVal ? '#4caf7d' : '#ef5350'} />
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Research Page ─────────────────────────────────────────────────────────────
export default function Research() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [seasons, setSeasons] = useState<SeasonPoint[]>([])
  const [divisions, setDivisions] = useState<DivisionStat[]>([])
  const [recovery, setRecovery] = useState<RecoveryPoint[]>([])
  const [stress, setStress] = useState<ScheduleStress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [ov, se, di, rc, st] = await Promise.all([
          fetch('/data/overview.json').then((r) => r.json()),
          fetch('/data/seasons.json').then((r) => r.json()),
          fetch('/data/divisions.json').then((r) => r.json()),
          fetch('/data/recovery.json').then((r) => r.json()),
          fetch('/data/schedule_stress.json').then((r) => r.json()).catch(() => null),
        ])
        setOverview(ov as OverviewData)
        setSeasons(se as SeasonPoint[])
        setDivisions(di as DivisionStat[])
        setRecovery(rc as RecoveryPoint[])
        if (st) setStress(st as ScheduleStress)
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

  const { league_b2b } = overview

  return (
    <main className="page">
      <h1 className="page-title">Research Findings</h1>
      <p className="page-subtitle">
        Statistical analysis of NHL goaltender fatigue · back-to-back game effects · schedule stress · recovery patterns
      </p>

      {/* Key Findings */}
      <h2 className="section-header">Key Findings</h2>

      <div className="finding-box">
        <div className="finding-box-title">Selection Bias Explains Near-Zero League B2B Effect</div>
        <p>
          League-wide B2B effect is near zero ({fmt.delta(league_b2b.delta)} SV%, p={fmt.pValue(league_b2b.p_value)})
          due to selection bias — coaches systematically avoid starting their #1 goalie on back-to-back nights
          when feasible. The goalies who do start B2B are disproportionately fresher or in must-win situations,
          masking the true fatigue signal at the aggregate level.
        </p>
      </div>

      <div className="finding-box warning">
        <div className="finding-box-title">4-in-6 Schedule Stress Is the Real Fatigue Signal (p=0.035)</div>
        <p>
          While 3-in-4 scheduling shows no significant effect (p=0.56 — coaches protect starters), the
          4-in-6 scenario is statistically significant: goalies starting their 4th game within 6 days
          show a {stress?.four_in_six ? fmt.delta(stress.four_in_six.delta) : '−0.007'} SV% drop (p=0.035).
          Road trip leg degradation is also consistent — away-leg performance declines progressively
          from Leg 1 through Leg 5, independent of opponent quality.
        </p>
      </div>

      <div className="finding-box danger">
        <div className="finding-box-title">2023-24 Was the Most Significant B2B Season · Recovery Peaks at 8 Days</div>
        <p>
          Seasonal analysis reveals meaningful year-to-year variance in B2B impact, potentially driven by
          schedule format changes and roster depth trends. The recovery curve peaks at approximately 8 days
          of rest ({recovery.find((r) => r.days_rest === 8) ? fmt.sv(recovery.find((r) => r.days_rest === 8)!.mean_sv) : '—'})
          before declining — consistent with sports science literature on cumulative fatigue in elite athletes.
        </p>
      </div>

      {/* Schedule Stress */}
      {stress && (
        <>
          <h2 className="section-header" style={{ marginTop: '2rem' }}>Schedule Stress Analysis</h2>

          <div className="grid-5545">
            <div className="chart-card">
              <div className="chart-title">Schedule Density: 3-in-4 vs 4-in-6</div>
              <div className="chart-subtitle">
                Red = under stress · Green = without flag · * p&lt;0.05 significant
              </div>
              <DensityComparisonChart four_in_six={stress.four_in_six} three_in_four={stress.three_in_four} />
              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.82rem' }}>
                {stress.four_in_six && (
                  <div style={{ color: stress.four_in_six.significant ? '#f5c842' : '#8b91a8' }}>
                    4-in-6: p={stress.four_in_six.p_value.toFixed(4)}{stress.four_in_six.significant ? ' ✱' : ''} (n={stress.four_in_six.n_with.toLocaleString()})
                  </div>
                )}
                {stress.three_in_four && (
                  <div style={{ color: '#8b91a8' }}>
                    3-in-4: p={stress.three_in_four.p_value.toFixed(4)} (n={stress.three_in_four.n_with.toLocaleString()})
                  </div>
                )}
              </div>
            </div>

            <div className="chart-card">
              <div className="chart-title">Road Trip Leg Degradation</div>
              <div className="chart-subtitle">
                Leg 0 = home games · Legs 1–5 = consecutive road games · blue reference = home baseline
              </div>
              {stress.road_trip_legs && <RoadTripChart legs={stress.road_trip_legs} />}
            </div>
          </div>

          {(stress.altitude || stress.season_phase) && (
            <div className="chart-card" style={{ marginTop: '1.5rem' }}>
              <div className="chart-title">Altitude &amp; Season Phase Effects</div>
              <div className="chart-subtitle">
                Altitude = venue elevation above sea level · Phase = games played in season so far
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1rem' }}>
                {stress.altitude && (
                  <SimpleBarChart
                    data={stress.altitude}
                    dataKey="mean_sv"
                    labelKey="label"
                    title="Mean SV% by Venue Altitude"
                  />
                )}
                {stress.season_phase && (
                  <SimpleBarChart
                    data={stress.season_phase}
                    dataKey="mean_sv"
                    labelKey="label"
                    title="Mean SV% by Season Phase"
                  />
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Season Trend */}
      <h2 className="section-header" style={{ marginTop: '2rem' }}>Season-by-Season B2B Trend</h2>
      <div className="chart-card">
        <div className="chart-title">B2B Save% Delta by Season</div>
        <div className="chart-subtitle">
          Red = negative B2B effect · Green = positive · * = statistically significant (p &lt; 0.05)
        </div>
        {seasons.length > 0 ? <SeasonTrend seasons={seasons} /> : <div className="loading-state">No season data</div>}
      </div>

      {/* Division Analysis */}
      <h2 className="section-header">Division Analysis</h2>
      <div className="chart-card">
        <div className="chart-title">Division-Level Comparisons</div>
        <div className="chart-subtitle">
          Atlantic · Metropolitan · Central · Pacific — save %, B2B delta, travel, and schedule density
        </div>
        {divisions.length > 0 ? <DivisionChart divisions={divisions} /> : <div className="loading-state">No division data</div>}
      </div>

      {/* Statistical Summary Table */}
      <h2 className="section-header">Statistical Summary by Season</h2>
      <div className="chart-card">
        <div className="chart-title">t-Test Results: B2B vs Rested Performance</div>
        <div className="chart-subtitle">Independent samples t-test per season · p &lt; 0.05 = significant</div>
        {seasons.length > 0 ? <StatTable seasons={seasons} /> : <div className="loading-state">No season data</div>}
      </div>

      {/* Recovery Summary */}
      {recovery.length > 0 && (
        <>
          <h2 className="section-header">Recovery Curve Summary</h2>
          <div className="chart-card">
            <div className="chart-title">Mean SV% by Days of Rest</div>
            <div className="chart-subtitle">Gold highlight = peak recovery day</div>
            <RecoverySummary data={recovery} />
          </div>
        </>
      )}

      {/* Methodology */}
      <h2 className="section-header" style={{ marginTop: '2rem' }}>Methodology</h2>
      <div className="methodology">
        <h3>Data Sources</h3>
        <ul>
          <li>NHL Stats API (<code>api-web.nhle.com/v1/</code>) — 10 seasons (2015–2025), 28,069 game logs</li>
          <li>MoneyPuck (<code>moneypuck.com</code>) — season-level GSAx, HDSV%, MDSV%, LDSV% for 973 goalie-seasons</li>
          <li>Arena coordinates &amp; altitude data (hardcoded, manually verified)</li>
          <li>Great-circle distance calculation for travel miles</li>
        </ul>
      </div>
      <div className="methodology">
        <h3>Advanced Metrics (MoneyPuck)</h3>
        <ul>
          <li><strong>GSAx</strong> (Goals Saved Above Expected) = xGoals − actual goals allowed</li>
          <li><strong>HDSV%</strong> = High-Danger Save % = (HD shots − HD goals) ÷ HD shots</li>
          <li><strong>MDSV%</strong> = Medium-Danger Save % (same formula)</li>
          <li>Season-level only — game-level GSAx not publicly available from MoneyPuck</li>
        </ul>
      </div>
      <div className="methodology">
        <h3>Schedule Stress Variables</h3>
        <ul>
          <li><strong>3-in-4</strong>: goalie started their 3rd game within 4 consecutive days</li>
          <li><strong>4-in-6</strong>: goalie started their 4th game within 6 consecutive days</li>
          <li><strong>Road trip leg</strong>: consecutive away games on current road trip (resets on home game)</li>
          <li><strong>Venue altitude</strong>: arena elevation above sea level (ft) — COL=5280ft, UTA=4226ft are highest</li>
          <li><strong>Season phase</strong>: early (Gm 1–20), mid (21–60), stretch (61+) based on goalie's starts</li>
        </ul>
      </div>
      <div className="methodology">
        <h3>Statistical Methods</h3>
        <ul>
          <li>Independent samples t-test for all group comparisons</li>
          <li>95% confidence intervals for recovery curve</li>
          <li>Welch's t-test (unequal variance) for season-level B2B analysis</li>
          <li>Minimum sample threshold: n≥50 for stress variable groups</li>
        </ul>
      </div>
      <div className="methodology">
        <h3>Caveats &amp; Limitations</h3>
        <ul>
          <li>3-in-4 shows no effect (p=0.56) due to coach protection — only strongest goalies play 3-in-4</li>
          <li>Emergency callups from AHL may have untracked prior travel</li>
          <li>Altitude effect not significant league-wide (p=0.31) but may interact with travel direction</li>
          <li>Stretch phase sample is small (n=202) — treat with caution</li>
          <li>Backup goalies (&lt;20 starts) have high variance</li>
        </ul>
      </div>
    </main>
  )
}
