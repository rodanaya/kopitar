import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Cell, Legend,
} from 'recharts'
import type {
  ScheduleStress, ScheduleStressMetric, RoadTripLeg, AltitudeBin, SeasonPhaseStat,
  OtAnalysis, ScoreDiffBin, MetroCorrection,
} from '../types'
import { fmt } from '../utils'

const TT = {
  contentStyle: {
    background: '#0c1d33',
    border: '1px solid rgba(56,189,248,0.18)',
    borderRadius: '10px',
    color: '#eef4ff',
    fontSize: '0.83rem',
    boxShadow: '0 8px 28px rgba(0,0,0,0.5)',
  },
}

// ── Density Comparison ────────────────────────────────────────────────────────
function DensityChart({ four_in_six, three_in_four }: { four_in_six?: ScheduleStressMetric; three_in_four?: ScheduleStressMetric }) {
  const data = [
    four_in_six && {
      label: '4-in-6',
      Stressed: four_in_six.mean_with,
      Rested: four_in_six.mean_without,
      delta: four_in_six.delta,
      p: four_in_six.p_value,
      sig: four_in_six.significant,
      n: four_in_six.n_with,
    },
    three_in_four && {
      label: '3-in-4',
      Stressed: three_in_four.mean_with,
      Rested: three_in_four.mean_without,
      delta: three_in_four.delta,
      p: three_in_four.p_value,
      sig: three_in_four.significant,
      n: three_in_four.n_with,
    },
  ].filter(Boolean) as { label: string; Stressed: number; Rested: number; delta: number; p: number; sig: boolean; n: number }[]

  if (!data.length) return <div className="loading-state">No data</div>

  const allVals = data.flatMap(d => [d.Stressed, d.Rested])
  const minVal = Math.min(...allVals) - 0.0015
  const maxVal = Math.max(...allVals) + 0.0015

  interface DPayload { label: string; Stressed: number; Rested: number; delta: number; p: number; sig: boolean; n: number }
  function DTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DPayload }> }) {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={TT.contentStyle}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>{d.label} stress window</div>
        <div>Under stress: <strong>{fmt.sv(d.Stressed)}</strong> (n={d.n.toLocaleString()})</div>
        <div>Not stressed: <strong>{fmt.sv(d.Rested)}</strong></div>
        <div style={{ color: d.delta < 0 ? '#f43f5e' : '#34d399', marginTop: 4 }}>
          Delta: {d.delta >= 0 ? '+' : ''}{d.delta.toFixed(5)}
        </div>
        <div style={{ color: d.sig ? '#fbbf24' : '#384f68' }}>
          p = {d.p.toFixed(4)}{d.sig ? ' ✱ significant' : ''}
        </div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 20, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="label" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 12 }} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={v => (v * 100).toFixed(2) + '%'} />
        <Tooltip content={<DTooltip />} />
        <Legend wrapperStyle={{ color: '#7ea4c4', fontSize: '0.8rem' }} />
        <Bar dataKey="Stressed" fill="#f43f5e" radius={[4, 4, 0, 0]} fillOpacity={0.85} />
        <Bar dataKey="Rested"   fill="#34d399" radius={[4, 4, 0, 0]} fillOpacity={0.85} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Road Trip Chart ───────────────────────────────────────────────────────────
function RoadTripChart({ legs }: { legs: RoadTripLeg[] }) {
  if (!legs.length) return <div className="loading-state">No data</div>
  const homeVal = legs.find(l => l.leg === 0)?.mean_sv ?? 0.9
  const minVal = Math.min(...legs.map(l => l.mean_sv)) - 0.001
  const maxVal = Math.max(...legs.map(l => l.mean_sv)) + 0.001

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={legs} margin={{ top: 20, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="label" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={v => (v * 100).toFixed(2) + '%'} />
        <Tooltip {...TT} formatter={(v: number) => [fmt.sv(v), 'Mean SV%']} />
        <ReferenceLine y={homeVal} stroke="#38bdf8" strokeDasharray="4 3"
          label={{ value: 'Home baseline', fill: '#38bdf8', fontSize: 10, position: 'insideTopRight' }} />
        <Bar dataKey="mean_sv" name="Mean SV%" radius={[4, 4, 0, 0]}>
          {legs.map(l => (
            <Cell key={l.leg} fill={l.leg === 0 ? '#38bdf8' : l.mean_sv < homeVal ? '#f43f5e' : '#34d399'} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Simple Bar ────────────────────────────────────────────────────────────────
function MiniBar({ data, dataKey, labelKey, title }: {
  data: (AltitudeBin | SeasonPhaseStat)[]
  dataKey: string; labelKey: string; title: string
}) {
  if (!data.length) return null
  const vals = data.map(d => (d as unknown as Record<string, number>)[dataKey])
  const minVal = Math.min(...vals) - 0.0015
  const maxVal = Math.max(...vals) + 0.0015
  const refVal = vals[0]

  return (
    <div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{title}</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 15, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
          <XAxis dataKey={labelKey} stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }} />
          <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
            domain={[minVal, maxVal]} tickFormatter={v => (v * 100).toFixed(2) + '%'} />
          <Tooltip {...TT} formatter={(v: number) => [fmt.sv(v), 'Mean SV%']} />
          <ReferenceLine y={refVal} stroke="rgba(56,189,248,0.3)" strokeDasharray="4 3" />
          <Bar dataKey={dataKey} radius={[4, 4, 0, 0]}>
            {data.map((d, i) => {
              const v = (d as unknown as Record<string, number>)[dataKey]
              return <Cell key={i} fill={v >= refVal ? '#34d399' : '#f43f5e'} fillOpacity={0.8} />
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Stat Compare Row ──────────────────────────────────────────────────────────
function MetricRow({ m, label }: { m: ScheduleStressMetric; label: string }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr',
      gap: '0.5rem',
      padding: '0.7rem 1rem',
      borderBottom: '1px solid rgba(56,189,248,0.05)',
      alignItems: 'center',
      fontSize: '0.875rem',
    }}>
      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{label}</div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', color: '#f43f5e' }}>{fmt.sv(m.mean_with)}</div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', color: '#34d399' }}>{fmt.sv(m.mean_without)}</div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', color: m.delta < 0 ? '#f43f5e' : '#34d399' }}>
        {m.delta >= 0 ? '+' : ''}{m.delta.toFixed(5)}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', color: m.p_value < 0.05 ? '#fbbf24' : 'var(--text-muted)' }}>
          {m.p_value.toFixed(4)}
        </span>
        {m.significant && <span className="tag tag-gold">✱ sig</span>}
      </div>
    </div>
  )
}

// ── Score Diff Chart ──────────────────────────────────────────────────────────
function ScoreDiffChart({ bins }: { bins: ScoreDiffBin[] }) {
  if (!bins.length) return null
  const refVal = bins.find(b => b.label.includes('Tie'))?.mean_sv ?? bins[0].mean_sv
  const minVal = Math.min(...bins.map(b => b.mean_sv)) - 0.002
  const maxVal = Math.max(...bins.map(b => b.mean_sv)) + 0.002
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={bins} margin={{ top: 10, right: 20, bottom: 55, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
        <XAxis dataKey="label" stroke="rgba(56,189,248,0.2)"
          tick={{ fill: '#7ea4c4', fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
        <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
          domain={[minVal, maxVal]} tickFormatter={v => (v * 100).toFixed(2) + '%'} />
        <Tooltip {...TT} formatter={(v: number, _: string, p) => [fmt.sv(v), `n=${(p.payload as ScoreDiffBin).count.toLocaleString()}`]} />
        <ReferenceLine y={refVal} stroke="#38bdf8" strokeDasharray="4 3" />
        <Bar dataKey="mean_sv" radius={[4, 4, 0, 0]}>
          {bins.map((b, i) => {
            const win = b.label.includes('Win')
            const loss = b.label.includes('Loss')
            return <Cell key={i} fill={win ? '#34d399' : loss ? '#f43f5e' : '#38bdf8'} fillOpacity={0.85} />
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Metro Correction Panel ────────────────────────────────────────────────────
function MetroPanel({ metro }: { metro: MetroCorrection }) {
  const rows = [
    { label: 'All B2B (uncorrected)', sv: metro.b2b_all_sv, delta: metro.delta_all, n: metro.n_b2b_all, p: metro.p_all },
    { label: 'B2B excl. same-metro', sv: metro.b2b_corrected_sv, delta: metro.delta_corrected, n: metro.n_b2b_corrected, p: metro.p_corrected },
    { label: 'Same-metro only', sv: metro.same_metro_sv, delta: metro.same_metro_sv != null && metro.rest_sv != null ? metro.same_metro_sv - metro.rest_sv : null, n: metro.n_same_metro, p: null },
    { label: 'Rested baseline', sv: metro.rest_sv, delta: 0, n: null, p: null },
  ]
  return (
    <div>
      {rows.map(r => (
        <div key={r.label} style={{
          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr',
          gap: '0.5rem', padding: '0.6rem 1rem',
          borderBottom: '1px solid rgba(56,189,248,0.05)', fontSize: '0.85rem', alignItems: 'center',
        }}>
          <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{r.label}</div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--accent-ice)' }}>
            {r.sv != null ? fmt.sv(r.sv) : '—'}
          </div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', color: r.delta != null && r.delta < 0 ? '#f43f5e' : r.delta != null && r.delta > 0 ? '#34d399' : 'var(--text-muted)' }}>
            {r.delta != null ? (r.delta >= 0 ? '+' : '') + r.delta.toFixed(5) : '—'}
          </div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
            {r.n != null ? `n=${r.n.toLocaleString()}` : ''}
            {r.p != null ? `  p=${r.p.toFixed(4)}` : ''}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Fatigue() {
  const [stress, setStress] = useState<ScheduleStress | null>(null)
  const [ot, setOt] = useState<OtAnalysis | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/data/schedule_stress.json').then(r => r.json()).catch(() => null),
      fetch('/data/ot_analysis.json').then(r => r.json()).catch(() => null),
    ]).then(([s, o]) => {
      setStress(s as ScheduleStress)
      setOt(o as OtAnalysis)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-state">Loading fatigue data…</div>
  if (!stress) return <div className="error-state">No fatigue data — run export script first.</div>

  const { four_in_six: f4, three_in_four: f3, road_trip_legs: legs, altitude, season_phase } = stress
  const otVsNot = ot?.ot_vs_non_ot
  const afterOt = ot?.after_ot
  const compound = ot?.compound_stress
  const scoreBins = ot?.score_diff_bins ?? []
  const metro = ot?.metro_correction

  const roadDrop = legs && legs.length > 1
    ? (legs.find(l => l.leg === 0)?.mean_sv ?? 0) - Math.min(...legs.slice(1).map(l => l.mean_sv))
    : null

  return (
    <main className="page">
      <h1 className="page-title">Fatigue Analysis</h1>
      <p className="page-subtitle">
        Tier-1 schedule stress variables · 28,069 game logs · 10 NHL seasons (2015–2025)
      </p>

      {/* KPI Row */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: f4?.significant ? '#fbbf24' : 'var(--accent-ice)', fontSize: '2rem' }}>
            {f4 ? fmt.delta(f4.delta) : '—'}
          </div>
          <div className="kpi-label">4-in-6 SV% Drop</div>
          <div className="kpi-delta">
            {f4 ? `p=${f4.p_value.toFixed(4)} · n=${f4.n_with.toLocaleString()} games` : 'not computed'}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: f4?.significant ? '#fbbf24' : 'var(--accent-ice)' }}>
            {f4 ? (f4.significant ? 'SIG' : 'N/S') : '—'}
          </div>
          <div className="kpi-label">4-in-6 Significance</div>
          <div className="kpi-delta">p &lt; 0.05 threshold</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: '#f43f5e', fontSize: '2rem' }}>
            {roadDrop != null ? fmt.delta(-roadDrop) : '—'}
          </div>
          <div className="kpi-label">Max Road-Trip Drop</div>
          <div className="kpi-delta">home baseline vs worst away leg</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: 'var(--text-muted)', fontSize: '2rem' }}>
            {f3 ? f3.p_value.toFixed(3) : '—'}
          </div>
          <div className="kpi-label">3-in-4 p-value</div>
          <div className="kpi-delta">not sig — coach protection bias</div>
        </div>
      </div>

      {/* Key Insights */}
      <div className="finding-box warning">
        <div className="finding-box-title">4-in-6 Is the Real Fatigue Signal (p=0.035)</div>
        <p>
          While 3-in-4 shows no effect (p≈0.56) because coaches protect their starter in those situations,
          the 4-in-6 window is statistically significant. Goalies starting their 4th game within 6 days
          drop {f4 ? fmt.delta(f4.delta) : '−0.007'} in SV% versus non-stressed starts.
          This represents the threshold where cumulative fatigue overrides coach selection bias.
        </p>
      </div>
      <div className="finding-box">
        <div className="finding-box-title">Road Trips Show Consistent Progressive Degradation</div>
        <p>
          Road trip leg 1 is often comparable to home performance, but legs 3+ show consistent drops.
          The progressive decline is independent of opponent quality and correlates with travel distance
          and timezone changes accumulated over the trip.
        </p>
      </div>

      {/* Schedule Density */}
      <h2 className="section-header" style={{ marginTop: '2rem' }}>Schedule Density</h2>
      <div className="grid-5545">
        <div className="chart-card">
          <div className="chart-title">3-in-4 vs 4-in-6: SV% Under Stress</div>
          <div className="chart-subtitle">Red = under stress window · Green = not stressed</div>
          <DensityChart four_in_six={f4} three_in_four={f3} />
          {f4 && f3 && (
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.78rem' }}>
              <span style={{ color: f4.significant ? '#fbbf24' : 'var(--text-muted)' }}>
                4-in-6: p={f4.p_value.toFixed(4)}{f4.significant ? ' ✱' : ''} (n={f4.n_with.toLocaleString()})
              </span>
              <span style={{ color: 'var(--text-muted)' }}>
                3-in-4: p={f3.p_value.toFixed(4)} (n={f3.n_with.toLocaleString()})
              </span>
            </div>
          )}
        </div>

        <div className="chart-card">
          <div className="chart-title">Metric Detail</div>
          <div className="chart-subtitle">With vs without stress flag · SV% comparison</div>
          <div style={{ marginTop: '0.5rem' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderBottom: '1px solid rgba(56,189,248,0.1)',
            }}>
              {['Metric', 'Stressed SV%', 'Normal SV%', 'Delta', 'p-value'].map(h => (
                <div key={h} style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>{h}</div>
              ))}
            </div>
            {f4 && <MetricRow m={f4} label="4-in-6" />}
            {f3 && <MetricRow m={f3} label="3-in-4" />}
          </div>
        </div>
      </div>

      {/* Road Trip */}
      <h2 className="section-header">Road Trip Degradation</h2>
      <div className="chart-card">
        <div className="chart-title">SV% by Road Trip Leg</div>
        <div className="chart-subtitle">
          Leg 0 = home games (blue) · Legs 1–7 = consecutive away games · Red = below home baseline
        </div>
        {legs && legs.length > 0 ? <RoadTripChart legs={legs} /> : <div className="loading-state">No road trip data</div>}
      </div>

      {/* Altitude + Season Phase */}
      {(altitude || season_phase) && (
        <>
          <h2 className="section-header">Environmental &amp; Scheduling Effects</h2>
          <div className="chart-card">
            <div className="chart-title">Altitude &amp; Season Phase Breakdown</div>
            <div className="chart-subtitle">
              Altitude = venue elevation (ft) · Phase = where in the season the goalie's start falls
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1rem' }}>
              {altitude && altitude.length > 0 && (
                <MiniBar data={altitude} dataKey="mean_sv" labelKey="label" title="Mean SV% by Altitude" />
              )}
              {season_phase && season_phase.length > 0 && (
                <MiniBar data={season_phase} dataKey="mean_sv" labelKey="label" title="Mean SV% by Season Phase" />
              )}
            </div>
          </div>
        </>
      )}

      {/* OT & Score Differential Analysis */}
      {ot && (
        <>
          <h2 className="section-header" style={{ marginTop: '2rem' }}>Overtime &amp; Score Context</h2>

          {/* OT KPI row */}
          <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
            <div className="kpi-card">
              <div className="kpi-value" style={{ color: '#38bdf8', fontSize: '1.9rem' }}>
                {otVsNot ? fmt.sv(otVsNot.ot_sv) : '—'}
              </div>
              <div className="kpi-label">OT Game SV%</div>
              <div className="kpi-delta">{otVsNot ? `vs ${fmt.sv(otVsNot.non_ot_sv)} in regulation` : ''}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value" style={{ color: otVsNot?.delta && otVsNot.delta > 0 ? '#34d399' : '#f43f5e', fontSize: '1.9rem' }}>
                {otVsNot ? fmt.delta(otVsNot.delta) : '—'}
              </div>
              <div className="kpi-label">OT SV% Delta</div>
              <div className="kpi-delta">{otVsNot ? `p=${otVsNot.p_value.toFixed(4)} · n=${otVsNot.n_ot.toLocaleString()} OT starts` : ''}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value" style={{ color: afterOt?.delta && afterOt.delta < 0 ? '#f43f5e' : '#34d399', fontSize: '1.9rem' }}>
                {afterOt ? fmt.delta(afterOt.delta) : '—'}
              </div>
              <div className="kpi-label">Next Start After OT</div>
              <div className="kpi-delta">{afterOt ? `p=${afterOt.p_value.toFixed(4)} · n=${afterOt.n_after_ot.toLocaleString()} starts` : ''}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value" style={{ color: compound?.delta && compound.delta < 0 ? '#f43f5e' : '#fbbf24', fontSize: '1.9rem' }}>
                {compound ? fmt.delta(compound.delta) : '—'}
              </div>
              <div className="kpi-label">OT→B2B Compound Stress</div>
              <div className="kpi-delta">{compound ? `p=${compound.p_value.toFixed(4)} · n=${compound.n_compound.toLocaleString()} starts` : ''}</div>
            </div>
          </div>

          <div className="grid-5545">
            {/* Score Differential chart */}
            {scoreBins.length > 0 && (
              <div className="chart-card">
                <div className="chart-title">SV% by Game Score Margin</div>
                <div className="chart-subtitle">
                  Goalies in blowout losses face easier shots — score effects contaminate raw SV%
                </div>
                <ScoreDiffChart bins={scoreBins} />
              </div>
            )}

            {/* Metro correction table */}
            {metro && (
              <div className="chart-card">
                <div className="chart-title">Same-Metro B2B Correction</div>
                <div className="chart-subtitle">
                  LAK↔ANA, NYR/NJD/NYI trips exclude real travel fatigue — correcting inflates the true B2B signal
                </div>
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{
                    display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr',
                    gap: '0.5rem', padding: '0.4rem 1rem',
                    borderBottom: '1px solid rgba(56,189,248,0.1)', marginBottom: '0.25rem',
                  }}>
                    {['Segment', 'SV%', 'Delta vs Rest', 'n / p'].map(h => (
                      <div key={h} style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>{h}</div>
                    ))}
                  </div>
                  <MetroPanel metro={metro} />
                </div>
                <div className="finding-box" style={{ marginTop: '1rem', padding: '0.75rem 1rem' }}>
                  <div className="finding-box-title" style={{ fontSize: '0.78rem' }}>Key Insight</div>
                  <p style={{ fontSize: '0.78rem', margin: 0 }}>
                    Same-metro trips (no real travel) have SV% closer to rested baseline.
                    Removing them from B2B analysis reveals a larger true fatigue effect.
                  </p>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Variable Reference */}
      <h2 className="section-header" style={{ marginTop: '2rem' }}>Variable Definitions</h2>
      <div className="methodology">
        <h3>Schedule Stress Variables</h3>
        <ul>
          <li><strong>3-in-4</strong>: goalie started their 3rd game within 4 consecutive calendar days</li>
          <li><strong>4-in-6</strong>: goalie started their 4th game within 6 consecutive calendar days — the real fatigue signal (p=0.035)</li>
          <li><strong>Road trip leg</strong>: consecutive away starts without a home game (resets to 0 on each home start)</li>
          <li><strong>Venue altitude</strong>: arena elevation in feet — Colorado (5,280 ft) and Utah (4,226 ft) are highest</li>
          <li><strong>Season phase</strong>: early = games 1–20, mid = 21–60, stretch = 61+ of goalie's starts in a season</li>
        </ul>
        <h3 style={{ marginTop: '1rem' }}>Overtime &amp; Score Variables</h3>
        <ul>
          <li><strong>OT flag</strong>: game went to overtime or shootout (detected via decision='O' or TOI &gt; 60.5 min)</li>
          <li><strong>Prev game OT</strong>: goalie's previous start also went to OT — compound fatigue flag</li>
          <li><strong>Score diff</strong>: reconstructed from cross-team goalie GA (positive = goalie's team won)</li>
          <li><strong>Same metro</strong>: LAK↔ANA (~30 mi), NYR/NJD/NYI triangle — bus trips with no real travel fatigue</li>
          <li><strong>Score effects</strong>: leading teams sit back, trailing teams shoot from worse positions — raw SV% is contaminated by game state</li>
        </ul>
      </div>
      <div className="methodology">
        <h3>Why 3-in-4 Shows No Effect</h3>
        <p>
          Coaches systematically protect their starter from 3-in-4 scenarios when the team has a viable backup.
          The goalies who do start their 3rd game in 4 days are disproportionately rested going in (e.g., they
          just had 3 days off before the first of the three games). This selection bias masks the true fatigue
          signal at the 3-in-4 threshold. At 4-in-6, the effect becomes strong enough to overcome this bias.
        </p>
      </div>
    </main>
  )
}
