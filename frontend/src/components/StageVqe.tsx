import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import Stage from './Stage'
import type { AtomMeta, PipelineResult } from '../api/client'
import type { Status } from '../lib/usePipeline'

interface Props {
  atom: AtomMeta | undefined
  run: PipelineResult | null
  status: Status
  error: string | null
  onRun: () => void
}

function Metric({ k, v }: { k: string; v: string }) {
  return (
    <div className="border border-halos-line bg-halos-surface p-3">
      <div className="label">{k}</div>
      <div className="mt-1 font-mono text-sm text-halos-text">{v}</div>
    </div>
  )
}

export default function StageVqe({ atom, run, status, error, onRun }: Props) {
  const isProxy = atom?.is_downstream_only
  const vqeDone = run && run.map_source === 'vqe'

  let statusText = 'WAITING ON TARGET'
  let tone: 'idle' | 'active' | 'running' | 'done' = 'idle'
  if (atom && status === 'idle') { statusText = isProxy ? 'NO VQE · PROXY' : 'READY'; tone = 'active' }
  if (status === 'running') { statusText = isProxy ? 'ESTIMATING' : 'RUNNING'; tone = 'running' }
  if (status === 'done') { statusText = isProxy ? 'LITERATURE MAP' : 'CONVERGED'; tone = 'done' }
  if (status === 'error') { statusText = 'ERROR'; tone = 'idle' }

  const chartData = (run?.convergence_history ?? []).map((e, i) => ({ i: i + 1, e }))

  return (
    <Stage n="02" id="stage-vqe" title="Variational Quantum Eigensolver" status={statusText} tone={tone}>
      {!atom && <div className="font-mono text-xs text-halos-muted">// select a target above</div>}

      {atom && (
        <div className="space-y-5">
          <p className="max-w-2xl text-sm leading-relaxed text-halos-dim">
            {isProxy
              ? `${atom.symbol} has ${atom.electrons} electrons — far beyond classical or current quantum simulation. We skip VQE and estimate the binding map from known coordination chemistry, then run the same downstream design + folding.`
              : `Hybrid quantum-classical ground-state search on a Qiskit StatevectorEstimator + EfficientSU2 ansatz + COBYLA. ${atom.id === 'lih' ? 'Verified precomputed Hamiltonian.' : atom.id === 't' ? 'Toy 2-qubit hydrogenic system.' : 'Real 4-qubit Jordan-Wigner Hamiltonian.'}`}
          </p>

          {status !== 'done' && (
            <button
              onClick={onRun}
              disabled={status === 'running'}
              className="border border-halos-accent px-5 py-2.5 font-mono text-xs tracking-widest text-halos-accent transition-colors hover:bg-halos-accent hover:text-halos-bg disabled:cursor-wait disabled:opacity-50"
            >
              {status === 'running' ? (isProxy ? 'ESTIMATING…' : 'RUNNING VQE…') : isProxy ? 'BUILD LITERATURE MAP →' : 'RUN VQE →'}
            </button>
          )}

          {status === 'running' && (
            <div className="h-1 w-full max-w-md overflow-hidden bg-halos-line">
              <div className="h-full w-1/2 animate-pulse bg-halos-accent" />
            </div>
          )}

          {status === 'error' && (
            <div className="border border-halos-error/50 p-3 font-mono text-xs text-halos-error">{error}</div>
          )}

          {run && (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Metric k="FINAL E" v={vqeDone ? `${run.ground_state_energy!.toFixed(5)} Ha` : '— (no VQE)'} />
              <Metric k="REFERENCE" v={run.known_ground_state != null ? `${run.known_ground_state.toFixed(4)} Ha` : '—'} />
              <Metric
                k="RESIDUAL"
                v={vqeDone && run.known_ground_state != null ? `${Math.abs(run.ground_state_energy! - run.known_ground_state).toFixed(4)} Ha` : '—'}
              />
              <Metric k="ITERS" v={vqeDone ? String(run.num_iterations) : 'literature'} />
            </div>
          )}

          {vqeDone && chartData.length > 1 && (
            <div className="h-44 border border-halos-line bg-halos-surface p-3">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="i" tick={{ fill: '#5c5c56', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                  <YAxis tick={{ fill: '#5c5c56', fontSize: 10, fontFamily: 'JetBrains Mono' }} tickFormatter={(v: number) => v.toFixed(2)} width={48} />
                  <Tooltip contentStyle={{ background: '#0f0f0f', border: '1px solid #222', fontFamily: 'JetBrains Mono', fontSize: 11 }} formatter={(v: number) => [`${v.toFixed(6)} Ha`, 'E']} />
                  {run.known_ground_state != null && <ReferenceLine y={run.known_ground_state} stroke="#48e3ea" strokeDasharray="4 4" strokeWidth={1} />}
                  <Line type="monotone" dataKey="e" stroke="#48e3ea" dot={false} strokeWidth={1.5} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </Stage>
  )
}
