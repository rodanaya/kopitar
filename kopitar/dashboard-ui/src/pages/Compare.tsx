import { useEffect, useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, BarChart, Bar,
} from 'recharts'
import type { GoalieStat, GsaxEntry } from '../types'
import { TeamLogo } from '../components/TeamLogo'
import { fmt } from '../utils'

const A_COLOR = '#38bdf8'  // ice blue
const B_COLOR = '#f43f5e'  // crimson

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

// ── Head-to-Head stat table ───────────────────────────────────────────────────
function HeadToHead({ a, b }: { a: GoalieStat; b: GoalieStat }) {
  const rows: { label: string; va: string; vb: string; aWins: boolean; noWinner?: boolean }[] = [
    {
      label: 'Career SV%',
      va: fmt.sv(a.avg_sv),
      vb: fmt.sv(b.avg_sv),
      aWins: a.avg_sv > b.avg_sv,
    },
    {
      label: 'Career GAA',
      va: a.avg_gaa.toFixed(2),
      vb: b.avg_gaa.toFixed(2),
      aWins: a.avg_gaa < b.avg_gaa,
    },
    {
      label: 'Career GSAx',
      va: a.career_gsax != null ? (a.career_gsax >= 0 ? '+' : '') + a.career_gsax.toFixed(1) : '—',
      vb: b.career_gsax != null ? (b.career_gsax >= 0 ? '+' : '') + b.career_gsax.toFixed(1) : '—',
      aWins: (a.career_gsax ?? -9999) > (b.career_gsax ?? -9999),
    },
    {
      label: 'HD SV%',
      va: a.career_hdsv_pct != null ? fmt.sv(a.career_hdsv_pct) : '—',
      vb: b.career_hdsv_pct != null ? fmt.sv(b.career_hdsv_pct) : '—',
      aWins: (a.career_hdsv_pct ?? 0) > (b.career_hdsv_pct ?? 0),
    },
    {
      label: 'B2B Delta',
      va: a.b2b_delta != null ? fmt.delta(a.b2b_delta) : '—',
      vb: b.b2b_delta != null ? fmt.delta(b.b2b_delta) : '—',
      aWins: (a.b2b_delta ?? -1) > (b.b2b_delta ?? -1),
    },
    {
      label: 'B2B Starts',
      va: String(a.b2b_games),
      vb: String(b.b2b_games),
      aWins: false,
      noWinner: true,
    },
    {
      label: 'Total Starts',
      va: String(a.total_games),
      vb: String(b.total_games),
      aWins: false,
      noWinner: true,
    },
  ]

  return (
    <div className="chart-card">
      <div className="chart-title">Head-to-Head Career Stats</div>
      <div className="chart-subtitle">Bold = statistical edge in that category</div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, marginTop: '0.5rem' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'right', padding: '0.5rem 1rem 0.5rem 0', fontSize: '0.82rem', color: A_COLOR, borderBottom: '1px solid rgba(56,189,248,0.12)', fontWeight: 700 }}>
                {a.player_name}
              </th>
              <th style={{ textAlign: 'center', padding: '0.5rem', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', borderBottom: '1px solid rgba(56,189,248,0.12)' }}>
                Metric
              </th>
              <th style={{ textAlign: 'left', padding: '0.5rem 0 0.5rem 1rem', fontSize: '0.82rem', color: B_COLOR, borderBottom: '1px solid rgba(56,189,248,0.12)', fontWeight: 700 }}>
                {b.player_name}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ label, va, vb, aWins, noWinner }) => (
              <tr key={label}>
                <td style={{
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontWeight: !noWinner && aWins ? 700 : 400,
                  color: !noWinner && aWins ? A_COLOR : 'var(--text-primary)',
                  padding: '0.6rem 1rem 0.6rem 0',
                  borderBottom: '1px solid rgba(56,189,248,0.04)',
                  fontSize: '0.875rem',
                }}>{va}</td>
                <td style={{
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '0.76rem',
                  borderBottom: '1px solid rgba(56,189,248,0.04)',
                  padding: '0.6rem 0.5rem',
                  whiteSpace: 'nowrap',
                }}>{label}</td>
                <td style={{
                  textAlign: 'left',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontWeight: !noWinner && !aWins ? 700 : 400,
                  color: !noWinner && !aWins ? B_COLOR : 'var(--text-primary)',
                  padding: '0.6rem 0 0.6rem 1rem',
                  borderBottom: '1px solid rgba(56,189,248,0.04)',
                  fontSize: '0.875rem',
                }}>{vb}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── GSAx Season Trend ─────────────────────────────────────────────────────────
function GsaxTrend({ gsaxA, gsaxB, nameA, nameB }: { gsaxA: GsaxEntry | null; gsaxB: GsaxEntry | null; nameA: string; nameB: string }) {
  const chartData = useMemo(() => {
    const labels = new Set<string>()
    gsaxA?.seasons.forEach(s => labels.add(s.label))
    gsaxB?.seasons.forEach(s => labels.add(s.label))
    return [...labels].sort().map(label => ({
      label,
      [nameA]: gsaxA?.seasons.find(s => s.label === label)?.gsax ?? null,
      [nameB]: gsaxB?.seasons.find(s => s.label === label)?.gsax ?? null,
    }))
  }, [gsaxA, gsaxB, nameA, nameB])

  if (!gsaxA && !gsaxB) return <div className="loading-state">No GSAx data available</div>

  return (
    <div className="chart-card">
      <div className="chart-title">Goals Saved Above Expected — Season by Season</div>
      <div className="chart-subtitle">
        Positive GSAx = outperforming shot quality expectations · Source: MoneyPuck
      </div>
      <ResponsiveContainer width="100%" height={290}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
          <XAxis dataKey="label" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }} angle={-15} textAnchor="end" height={42} />
          <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }}
            tickFormatter={v => (v >= 0 ? '+' : '') + v.toFixed(0)} />
          <Tooltip {...TT} formatter={(v: number, name: string) => [(v >= 0 ? '+' : '') + v.toFixed(2) + ' GSAx', name]} />
          <Legend wrapperStyle={{ color: '#7ea4c4', fontSize: '0.82rem', paddingTop: '0.5rem' }} />
          <Line type="monotone" dataKey={nameA} stroke={A_COLOR} strokeWidth={2.5}
            dot={{ r: 4, fill: A_COLOR, strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
          <Line type="monotone" dataKey={nameB} stroke={B_COLOR} strokeWidth={2.5}
            dot={{ r: 4, fill: B_COLOR, strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── B2B Comparison ────────────────────────────────────────────────────────────
function B2BComparison({ a, b }: { a: GoalieStat; b: GoalieStat }) {
  const hasData = a.b2b_sv != null || b.b2b_sv != null
  if (!hasData) return null

  const data = [
    { name: 'B2B SV%', [a.player_name]: a.b2b_sv, [b.player_name]: b.b2b_sv },
    { name: 'Rested SV%', [a.player_name]: a.rest_sv, [b.player_name]: b.rest_sv },
  ]

  const allVals = [a.b2b_sv, b.b2b_sv, a.rest_sv, b.rest_sv].filter(v => v != null) as number[]
  const minVal = Math.min(...allVals) - 0.002
  const maxVal = Math.max(...allVals) + 0.002

  return (
    <div className="chart-card">
      <div className="chart-title">B2B Fatigue Impact</div>
      <div className="chart-subtitle">Back-to-back SV% vs rested — who handles fatigue better?</div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.07)" />
          <XAxis dataKey="name" stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 11 }} />
          <YAxis stroke="rgba(56,189,248,0.2)" tick={{ fill: '#7ea4c4', fontSize: 10 }}
            domain={[minVal, maxVal]} tickFormatter={v => (v * 100).toFixed(1) + '%'} />
          <Tooltip {...TT} formatter={(v: number) => [fmt.sv(v), '']} />
          <Legend wrapperStyle={{ color: '#7ea4c4', fontSize: '0.82rem' }} />
          <Bar dataKey={a.player_name} fill={A_COLOR} radius={[4, 4, 0, 0]} fillOpacity={0.85} />
          <Bar dataKey={b.player_name} fill={B_COLOR} radius={[4, 4, 0, 0]} fillOpacity={0.85} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Goalie Profile Card ───────────────────────────────────────────────────────
function ProfileCard({ g, color }: { g: GoalieStat; color: string }) {
  return (
    <div className="chart-card" style={{ borderColor: `${color}40`, boxShadow: `0 0 32px ${color}0f` }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {g.teams.slice(0, 4).map(t => <TeamLogo key={t} team={t} size={28} />)}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color }}>{g.player_name}</div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: 2 }}>
            {g.total_games} career starts · {g.teams.slice(0, 3).join(', ')}
          </div>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        {[
          { label: 'Career SV%', val: fmt.sv(g.avg_sv), highlight: true },
          { label: 'Career GAA', val: g.avg_gaa.toFixed(2) },
          { label: 'Career GSAx', val: g.career_gsax != null ? (g.career_gsax >= 0 ? '+' : '') + g.career_gsax.toFixed(1) : '—' },
          { label: 'HD SV%', val: g.career_hdsv_pct != null ? fmt.sv(g.career_hdsv_pct) : '—' },
          { label: 'B2B Delta', val: g.b2b_delta != null ? fmt.delta(g.b2b_delta) : '—' },
          { label: 'B2B Starts', val: String(g.b2b_games) },
        ].map(({ label, val, highlight }) => (
          <div key={label} style={{
            background: 'var(--bg-surface)',
            borderRadius: 8,
            padding: '0.65rem 0.85rem',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.2rem' }}>{label}</div>
            <div style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontWeight: highlight ? 700 : 500,
              fontSize: highlight ? '1.2rem' : '1rem',
              color: highlight ? color : 'var(--text-primary)',
            }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Compare() {
  const [goalies, setGoalies] = useState<GoalieStat[]>([])
  const [gsax, setGsax] = useState<GsaxEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [idA, setIdA] = useState<number | null>(null)
  const [idB, setIdB] = useState<number | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/data/goalies.json').then(r => r.json()),
      fetch('/data/gsax.json').then(r => r.json()),
    ]).then(([g, x]) => {
      setGoalies(g as GoalieStat[])
      setGsax(x as GsaxEntry[])
    }).finally(() => setLoading(false))
  }, [])

  const sorted = useMemo(
    () => [...goalies].sort((a, b) => a.player_name.localeCompare(b.player_name)),
    [goalies]
  )

  const statA = useMemo(() => goalies.find(g => g.player_id === idA) ?? null, [goalies, idA])
  const statB = useMemo(() => goalies.find(g => g.player_id === idB) ?? null, [goalies, idB])
  const gsaxA = useMemo(() => gsax.find(g => g.player_id === idA) ?? null, [gsax, idA])
  const gsaxB = useMemo(() => gsax.find(g => g.player_id === idB) ?? null, [gsax, idB])

  if (loading) return <div className="loading-state">Loading goalie data…</div>

  return (
    <main className="page">
      <h1 className="page-title">Compare Goalies</h1>
      <p className="page-subtitle">
        Head-to-head career analysis · GSAx trends · B2B fatigue resilience · {goalies.length} goalies available
      </p>

      {/* Selectors */}
      <div className="filter-row" style={{ gap: '1.5rem', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
          <div className="filter-label" style={{ color: A_COLOR }}>Goalie A</div>
          <select
            className="select-input"
            value={idA ?? ''}
            onChange={e => setIdA(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Choose a goalie…</option>
            {sorted.map(g => (
              <option key={g.player_id} value={g.player_id}>{g.player_name}</option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.12em', paddingBottom: '0.1rem', fontFamily: 'Barlow Condensed, sans-serif' }}>
          VS
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
          <div className="filter-label" style={{ color: B_COLOR }}>Goalie B</div>
          <select
            className="select-input"
            value={idB ?? ''}
            onChange={e => setIdB(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Choose a goalie…</option>
            {sorted.map(g => (
              <option key={g.player_id} value={g.player_id}>{g.player_name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Empty state */}
      {(!statA || !statB) && (
        <div className="chart-card" style={{ textAlign: 'center', padding: '5rem 2rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem', opacity: 0.2, fontFamily: 'Barlow Condensed, sans-serif', fontStyle: 'italic', letterSpacing: '0.1em' }}>
            VS
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Select two goalies above to compare
          </div>
          <div style={{ fontSize: '0.82rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
            {goalies.length} goalies · 10 seasons · career stats, GSAx, B2B fatigue
          </div>
        </div>
      )}

      {/* Content */}
      {statA && statB && (
        <>
          {/* Profile cards */}
          <div className="grid-2" style={{ marginBottom: 0 }}>
            <ProfileCard g={statA} color={A_COLOR} />
            <ProfileCard g={statB} color={B_COLOR} />
          </div>

          {/* Head-to-head table */}
          <HeadToHead a={statA} b={statB} />

          {/* GSAx trend */}
          <GsaxTrend gsaxA={gsaxA} gsaxB={gsaxB} nameA={statA.player_name} nameB={statB.player_name} />

          {/* B2B comparison */}
          <B2BComparison a={statA} b={statB} />
        </>
      )}
    </main>
  )
}
