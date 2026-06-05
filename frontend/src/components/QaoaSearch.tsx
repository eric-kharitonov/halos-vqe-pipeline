import { useState } from 'react'
import { runQaoaSearch, type QaoaResult } from '../api/client'

interface Props {
  bindingStrength: number
  coordinationNumber: number
}

type Stage = 'idle' | 'running' | 'done' | 'error'

export default function QaoaSearch({ bindingStrength, coordinationNumber }: Props) {
  const [stage, setStage] = useState<Stage>('idle')
  const [result, setResult] = useState<QaoaResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Search a peptide as long as the coordination number, capped at 3 (<= 6 qubits).
  const nResidues = Math.min(coordinationNumber, 3)

  const run = () => {
    setStage('running')
    runQaoaSearch(bindingStrength, nResidues)
      .then(r => { setResult(r); setStage('done') })
      .catch(e => { setError(e.message); setStage('error') })
  }

  const maxProb = result ? Math.max(...result.ranked_candidates.map(c => c.probability)) : 1

  return (
    <section className="border-t border-halos-border pt-6">
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        QAOA Sequence Search <span className="text-halos-muted normal-case">(quantum optimization)</span>
      </h2>
      <p className="text-halos-muted text-sm mb-4">
        Instead of placing residues deterministically, search the whole peptide space with the
        Quantum Approximate Optimization Algorithm. Each candidate is a basis state; the cost
        Hamiltonian encodes binding strength vs. this site's electron deficiency.
      </p>

      {stage === 'idle' && (
        <button
          onClick={run}
          className="px-6 py-3 border border-halos-accent text-halos-accent font-mono text-sm hover:bg-halos-accent hover:text-halos-bg transition-colors rounded"
        >
          Run QAOA Search ({nResidues}-mer, {Math.pow(4, nResidues)} candidates)
        </button>
      )}

      {stage === 'running' && (
        <div className="space-y-2">
          <div className="text-halos-muted text-sm font-mono">Running QAOA...</div>
          <div className="text-xs text-halos-muted">
            QAOAAnsatz over a diagonal cost Hamiltonian + COBYLA. {nResidues}-mer takes ~{nResidues === 2 ? 20 : 60}s.
          </div>
          <div className="h-1 bg-halos-border rounded overflow-hidden">
            <div className="h-full bg-halos-accent animate-pulse w-1/2" />
          </div>
        </div>
      )}

      {stage === 'error' && (
        <div className="text-halos-error font-mono text-sm border border-halos-error rounded p-4">
          Error: {error}
        </div>
      )}

      {stage === 'done' && result && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-4 text-sm font-mono">
            <span className="text-halos-muted">{result.n_qubits} qubits · reps {result.reps} · {result.search_space_size} candidates</span>
            {result.found_optimum ? (
              <span className="text-emerald-400 border border-emerald-400/40 rounded px-2 py-0.5 text-xs">
                ✓ reached brute-force optimum ({result.brute_force_optimum})
              </span>
            ) : (
              <span className="text-halos-warn border border-halos-warn/40 rounded px-2 py-0.5 text-xs">
                approximate — brute-force optimum is {result.brute_force_optimum} ({result.brute_force_cost.toFixed(3)})
              </span>
            )}
          </div>

          <div className="space-y-1">
            {result.ranked_candidates.map((c, i) => (
              <div key={i} className="flex items-center gap-3 font-mono text-sm">
                <span className={`w-14 ${i === 0 ? 'text-halos-accent font-bold' : 'text-halos-text'}`}>{c.sequence}</span>
                <span className="text-halos-muted text-xs w-20">cost {c.cost.toFixed(3)}</span>
                <div className="flex-1 h-3 bg-halos-border rounded overflow-hidden max-w-xs">
                  <div
                    className={i === 0 ? 'h-full bg-halos-accent' : 'h-full bg-halos-muted'}
                    style={{ width: `${(c.probability / maxProb) * 100}%` }}
                  />
                </div>
                <span className="text-halos-muted text-xs w-14 text-right">{(c.probability * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>

          <p className="text-halos-muted text-xs">
            Bars show measurement probability of each peptide in the optimized QAOA state. The
            top candidate ({result.best_sequence}) is the recommended binder for this site.
          </p>
        </div>
      )}
    </section>
  )
}
