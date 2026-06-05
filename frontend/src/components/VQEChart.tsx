import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

interface Props {
  history: number[]
  groundStateEnergy: number
  knownGroundState: number | null
}

export default function VQEChart({ history, groundStateEnergy, knownGroundState }: Props) {
  const data = history.map((e, i) => ({ iteration: i + 1, energy: e }))

  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-1">
        VQE Convergence
      </h2>
      <div className="text-halos-text font-mono text-sm mb-3">
        Ground state energy:{' '}
        <span className="text-halos-accent">{groundStateEnergy.toFixed(6)} Ha</span>
        {knownGroundState && (
          <span className="text-halos-muted ml-3">
            (reference: {knownGroundState.toFixed(6)} Ha,{' '}
            error: {Math.abs(groundStateEnergy - knownGroundState).toFixed(4)} Ha)
          </span>
        )}
      </div>
      <div className="bg-halos-surface border border-halos-border rounded p-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="iteration"
              tick={{ fill: '#666', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              label={{ value: 'Iteration', position: 'insideBottom', offset: -4, fill: '#666', fontSize: 11 }}
            />
            <YAxis
              tick={{ fill: '#666', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickFormatter={(v: number) => v.toFixed(3)}
            />
            <Tooltip
              contentStyle={{ background: '#111', border: '1px solid #1e1e1e', color: '#e8e6df', fontFamily: 'JetBrains Mono', fontSize: 12 }}
              formatter={(v: number) => [v.toFixed(6) + ' Ha', 'Energy']}
            />
            {knownGroundState && (
              <ReferenceLine y={knownGroundState} stroke="#48e3ea" strokeDasharray="4 4" strokeWidth={1} />
            )}
            <Line type="monotone" dataKey="energy" stroke="#48e3ea" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
