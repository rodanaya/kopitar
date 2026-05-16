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
import type { Overview as OverviewData, SeasonPoint, DivisionStat, RecoveryPoint } from '../types'
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
  label?: string
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

interface SeasonLabelProps {
  x?: number
  y?: number
  width?: number
  value?: number
  payload?: SeasonPoint
}

function SeasonLabel({ x, y, width, value, payload }: SeasonLabelProps) {
  if (!payload?.significant || value == null || x == null || y == null || width == null) return null
  const cx = x + width / 2
  const cy = value < 0 ? y + 16 : y - 6
  return (
    <text x={cx} y={cy} textAnchor="middle" fill="#f5c842" fontSize={13} fontWeight={700}>
      *
    </text>
  )
}

function SeasonTrend({ seasons }: { seasons: SeasonPoint[] }) {
  const sorted = useMemo(() => [...seasons].sort((a, b) => a.season.localeCompare(b.season)), [seasons])

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sorted} margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
        <XAxis
          dataKey="label"
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 10 }}
          angle={-20}
          textAnchor="end"
          height={50}
        />
        <YAxis
          stroke="#555c70"
          tick={{ fill: '#8b91a8', fontSize: 11 }}
          tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<SeasonTooltip />} />
        <ReferenceLine y={0} stroke="#555c70" strokeWidth={1.5} />
        <Bar dataKey="delta" name="B2B Delta" radius={[3, 3, 0, 0]} label={<SeasonLabel />}>
          {sorted.map((s) => (
            <Cell key={s.season} fill={s.delta < 0 ? '#ef5350' : '#4caf7d'} />
          ))}
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
      {/* Avg SV% by Division */}
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          Average Save % by Division
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis
              dataKey="division"
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 11 }}
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
              {sorted.map((d) => (
                <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* B2B Delta by Division */}
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          B2B Delta by Division
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis
              dataKey="division"
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 11 }}
            />
            <YAxis
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 10 }}
              domain={['auto', 'auto']}
              tickFormatter={(v) => (v >= 0 ? '+' : '') + v.toFixed(3)}
            />
            <Tooltip
              {...tooltipStyle}
              formatter={(v: number) => [(v >= 0 ? '+' : '') + v.toFixed(4), 'B2B Delta']}
            />
            <ReferenceLine y={0} stroke="#555c70" />
            <Bar dataKey="b2b_delta" name="B2B Delta" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => (
                <Cell key={d.division} fill={d.b2b_delta < 0 ? '#ef5350' : '#4caf7d'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Avg Travel Miles by Division */}
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          Average Travel Miles by Division
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis
              dataKey="division"
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 11 }}
            />
            <YAxis
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 10 }}
              tickFormatter={(v) => v.toLocaleString()}
            />
            <Tooltip
              {...tooltipStyle}
              formatter={(v: number) => [fmt.miles(v), 'Avg Travel']}
            />
            <Bar dataKey="avg_travel_miles" name="Avg Travel" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => (
                <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} fillOpacity={0.7} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* B2B Rate by Division */}
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          B2B Game Rate by Division
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
            <XAxis
              dataKey="division"
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 11 }}
            />
            <YAxis
              stroke="#555c70"
              tick={{ fill: '#8b91a8', fontSize: 10 }}
              tickFormatter={(v) => (v * 100).toFixed(0) + '%'}
            />
            <Tooltip
              {...tooltipStyle}
              formatter={(v: number) => [fmt.pct(v), 'B2B Rate']}
            />
            <Bar dataKey="b2b_rate" name="B2B Rate" radius={[3, 3, 0, 0]}>
              {sorted.map((d) => (
                <Cell key={d.division} fill={DIVISION_COLORS[d.division] ?? '#8b91a8'} fillOpacity={0.8} />
              ))}
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
              <td
                className={
                  s.delta < -0.01 ? 'td-negative' : s.delta > 0.01 ? 'td-positive' : ''
                }
              >
                {fmt.delta(s.delta)}
              </td>
              <td className={s.p_value < 0.05 ? 'td-positive' : 'td-muted'}>
                {fmt.pValue(s.p_value)}
              </td>
              <td>
                {s.significant ? (
                  <span className="tag tag-gold">Yes *</span>
                ) : (
                  <span className="tag tag-neutral">No</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Recovery Summary (compact) ────────────────────────────────────────────────
function RecoverySummary({ data }: { data: RecoveryPoint[] }) {
  const peak = useMemo(() => {
    if (!data.length) return null
    return data.reduce((best, d) => (d.mean_sv > best.mean_sv ? d : best), data[0])
  }, [data])

  if (!peak) return null

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
      {data.slice(0, 10).map((d) => (
        <div
          key={d.days_rest}
          style={{
            background: 'var(--bg-primary)',
            border: `1px solid ${d.days_rest === peak.days_rest ? 'var(--accent-gold)' : 'var(--border)'}`,
            borderRadius: 8,
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>
            {d.days_rest} day{d.days_rest !== 1 ? 's' : ''} rest
            {d.days_rest === peak.days_rest && ' ★'}
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: d.days_rest === peak.days_rest ? 'var(--accent-gold)' : 'var(--text-primary)' }}>
            {fmt.sv(d.mean_sv)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            n={d.count}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Research Page ─────────────────────────────────────────────────────────────
export default function Research() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [seasons, setSeasons] = useState<SeasonPoint[]>([])
  const [divisions, setDivisions] = useState<DivisionStat[]>([])
  const [recovery, setRecovery] = useState<RecoveryPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [ov, se, di, rc] = await Promise.all([
          fetch('/data/overview.json').then((r) => r.json()),
          fetch('/data/seasons.json').then((r) => r.json()),
          fetch('/data/divisions.json').then((r) => r.json()),
          fetch('/data/recovery.json').then((r) => r.json()),
        ])
        setOverview(ov as OverviewData)
        setSeasons(se as SeasonPoint[])
        setDivisions(di as DivisionStat[])
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

  const { league_b2b } = overview

  return (
    <main className="page">
      <h1 className="page-title">Research Findings</h1>
      <p className="page-subtitle">
        Statistical analysis of NHL goaltender fatigue · back-to-back game effects · recovery patterns
      </p>

      {/* Key Findings */}
      <h2 className="section-header">Key Findings</h2>

      <div className="finding-box">
        <div className="finding-box-title">Selection Bias Explains Near-Zero League Effect</div>
        <p>
          League-wide B2B effect is near zero ({fmt.delta(league_b2b.delta)} SV%, p={fmt.pValue(league_b2b.p_value)})
          due to selection bias — coaches systematically avoid starting their #1 goalie on back-to-back nights
          when feasible. The goalies who do start B2B are disproportionately fresher or in must-win situations,
          masking the true fatigue signal at the aggregate level.
        </p>
      </div>

      <div className="finding-box warning">
        <div className="finding-box-title">Team-Level Effects Are Real and Clinically Significant</div>
        <p>
          Individual team effects are large and actionable. High-travel teams and those with limited backup
          depth show the most pronounced drops. Division structure creates systematic travel asymmetries:
          Pacific division teams average the highest miles-per-game, while Metropolitan teams benefit from
          geographic clustering. Teams with strong backup options show attenuated B2B effects.
        </p>
      </div>

      <div className="finding-box danger">
        <div className="finding-box-title">2023-24 Was the Most Significant B2B Season · Recovery Peaks at 8 Days</div>
        <p>
          Seasonal analysis reveals meaningful year-to-year variance in B2B impact, potentially driven by
          schedule format changes and roster depth trends. The recovery curve peaks at approximately 8 days
          of rest ({recovery.find((r) => r.days_rest === 8) ? fmt.sv(recovery.find((r) => r.days_rest === 8)!.mean_sv) : '—'})
          before declining — consistent with the sports science literature on cumulative fatigue in elite athletes.
          Goalies with fewer than 2 days rest show statistically lower performance regardless of physical condition.
        </p>
      </div>

      {/* Season Trend */}
      <h2 className="section-header" style={{ marginTop: '2rem' }}>Season-by-Season B2B Trend</h2>
      <div className="chart-card">
        <div className="chart-title">B2B Save% Delta by Season</div>
        <div className="chart-subtitle">
          Red = negative B2B effect · Green = positive · * = statistically significant (p &lt; 0.05)
        </div>
        {seasons.length > 0 ? <SeasonTrend seasons={seasons} /> : (
          <div className="loading-state">No season data</div>
        )}
      </div>

      {/* Division Analysis */}
      <h2 className="section-header">Division Analysis</h2>
      <div className="chart-card">
        <div className="chart-title">Division-Level Comparisons</div>
        <div className="chart-subtitle">
          Atlantic · Metropolitan · Central · Pacific — save %, B2B delta, travel, and schedule density
        </div>
        {divisions.length > 0 ? <DivisionChart divisions={divisions} /> : (
          <div className="loading-state">No division data</div>
        )}
      </div>

      {/* Statistical Summary Table */}
      <h2 className="section-header">Statistical Summary by Season</h2>
      <div className="chart-card">
        <div className="chart-title">t-Test Results: B2B vs Rested Performance</div>
        <div className="chart-subtitle">
          Independent samples t-test per season · p &lt; 0.05 = significant
        </div>
        {seasons.length > 0 ? <StatTable seasons={seasons} /> : (
          <div className="loading-state">No season data</div>
        )}
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
          <li>NHL Stats API (<code>statsapi.web.nhl.com/api/v1/</code>) — game logs, goalie stats, schedule</li>
          <li>Arena coordinates (hardcoded, manually verified)</li>
          <li>Great-circle distance calculation for travel miles</li>
        </ul>
      </div>

      <div className="methodology">
        <h3>B2B Game Definition</h3>
        <p>
          A game is classified as a back-to-back start if the goalie started the previous calendar night.
          Days of rest = calendar days between starts (0 = same day, 1 = one day gap, etc.).
        </p>
      </div>

      <div className="methodology">
        <h3>Statistical Methods</h3>
        <ul>
          <li>Independent samples t-test for B2B vs rested save percentage</li>
          <li>95% confidence intervals computed via bootstrap (n=1000) for recovery curve</li>
          <li>Minimum sample threshold: 10 B2B games for team-level analysis, 5 for goalie-level</li>
          <li>Season-level analysis uses Welch's t-test (unequal variance assumed)</li>
        </ul>
      </div>

      <div className="methodology">
        <h3>Travel Calculation</h3>
        <p>
          Travel miles are computed as great-circle distance between arena coordinates.
          The fatigue index incorporates:
        </p>
        <ol>
          <li>Raw distance (miles)</li>
          <li>Estimated flight time (distance ÷ 500 mph + 2 hr buffer)</li>
          <li>Timezone changes (1.5× penalty for eastward travel)</li>
          <li>Arrival time penalty (game-day arrival vs. prior night)</li>
        </ol>
      </div>

      <div className="methodology">
        <h3>Caveats &amp; Limitations</h3>
        <ul>
          <li>Emergency callups from AHL may have untracked prior travel</li>
          <li>Injury-related absences can inflate apparent rest-day performance</li>
          <li>Score effects: teams trailing may pull goalies, distorting GAA but not SV%</li>
          <li>Survivorship bias: goalies who perform poorly on B2B may get fewer future starts</li>
          <li>Backup goalies (&lt;20 starts) have high variance — treat with caution</li>
        </ul>
      </div>
    </main>
  )
}
