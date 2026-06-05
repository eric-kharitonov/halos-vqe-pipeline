import { useState } from 'react'
import Stage from './Stage'
import type { PipelineResult, QaoaResult } from '../api/client'
import type { Status } from '../lib/usePipeline'

interface Props {
  run: PipelineResult | null
  qaoa: QaoaResult | null
  qaoaStatus: Status
  onQaoa: () => void
}

export default function StageProtein({ run, qaoa, qaoaStatus, onQaoa }: Props) {
  const [copied, setCopied] = useState(false)
  const bindingSet = new Set(run?.binding_positions ?? [])
  const maxProb = qaoa ? Math.max(...qaoa.ranked_candidates.map(c => c.probability)) : 1

  const copy = () => {
    if (!run) return
    navigator.clipboard.writeText(run.fasta)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Stage
      n="04"
      id="stage-protein"
      title="Protein candidate search"
      status={run ? 'CANDIDATE READY' : 'WAITING ON MAP'}
      tone={run ? 'done' : 'idle'}
      guardrail="RULE-BASED RANKER + QAOA OVER A CURATED MOTIF POOL · STAND-IN FOR RFDIFFUSION + PROTEINMPNN"
    >
      {!run && <div className="font-mono text-xs text-halos-muted">// no candidates — generate map first</div>}

      {run && (
        <div className="space-y-7">
          {/* Deterministic designed candidate */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
              <div title="Mean fractional emptiness (1 − occupancy) of the binding orbitals — an electron-deficiency measure, not a binding probability.">
                <div className="label">{run.map_source === 'vqe' ? 'ELECTRON DEFICIENCY' : 'DEFICIENCY · LIT. EST.'}</div>
                <div className="font-mono text-2xl text-halos-accent">{(run.binding_confidence * 100).toFixed(0)}%</div>
              </div>
              <div>
                <div className="label">BINDING RESIDUES</div>
                <div className="font-mono text-sm text-halos-text">{run.binding_residues.join(' — ')}</div>
              </div>
              <div>
                <div className="label">HELIX POSITIONS</div>
                <div className="font-mono text-sm text-halos-text">{run.binding_positions.join(', ')}</div>
              </div>
            </div>
            <div className="border border-halos-line bg-halos-surface p-3 font-mono text-sm leading-loose tracking-wide">
              {run.sequence.split('').map((aa, i) => (
                <span key={i} className={bindingSet.has(i) ? 'font-bold text-halos-accent underline' : 'text-halos-muted'}>
                  {aa}
                </span>
              ))}
            </div>
            <button
              onClick={copy}
              className="border border-halos-border px-3 py-1.5 font-mono text-[10px] tracking-widest text-halos-dim transition-colors hover:border-halos-text hover:text-halos-text"
            >
              {copied ? 'COPIED' : 'COPY FASTA'}
            </button>
          </div>

          {/* QAOA quantum search */}
          <div className="border-t border-halos-line pt-6">
            <div className="mb-3 flex items-center justify-between">
              <div className="label">QUANTUM SEARCH · QAOA</div>
              {qaoa && (
                <span
                  className={`rounded-sm border px-2 py-0.5 font-mono text-[10px] tracking-widest ${
                    qaoa.found_optimum ? 'border-halos-ok/40 text-halos-ok' : 'border-halos-warn/40 text-halos-warn'
                  }`}
                >
                  {qaoa.found_optimum ? `✓ REACHED OPTIMUM · ${qaoa.brute_force_optimum}` : 'APPROXIMATE'}
                </span>
              )}
            </div>

            {!qaoa && (
              <button
                onClick={onQaoa}
                disabled={qaoaStatus === 'running'}
                className="border border-halos-accent px-4 py-2 font-mono text-[11px] tracking-widest text-halos-accent transition-colors hover:bg-halos-accent hover:text-halos-bg disabled:cursor-wait disabled:opacity-50"
              >
                {qaoaStatus === 'running' ? 'SEARCHING…' : `RUN QAOA SEARCH (${Math.pow(4, Math.min(run.coordination_number, 3))} CANDIDATES)`}
              </button>
            )}
            {qaoaStatus === 'error' && <div className="font-mono text-xs text-halos-error">QAOA search failed.</div>}

            {qaoa && (
              <div className="space-y-3">
                <div className="font-mono text-[10px] tracking-widest text-halos-muted">
                  {qaoa.n_qubits} QUBITS · REPS {qaoa.reps} · {qaoa.search_space_size} CANDIDATES
                </div>
                <div className="space-y-1.5">
                  {qaoa.ranked_candidates.map((c, i) => (
                    <div key={i} className="flex items-center gap-3 font-mono text-xs">
                      <span className={`w-16 ${i === 0 ? 'font-bold text-halos-accent' : 'text-halos-text'}`}>{c.sequence}</span>
                      <span className="w-20 text-halos-muted">{c.cost.toFixed(3)}</span>
                      <div className="h-2.5 max-w-[220px] flex-1 overflow-hidden bg-halos-line">
                        <div className={i === 0 ? 'h-full bg-halos-accent' : 'h-full bg-halos-muted'} style={{ width: `${(c.probability / maxProb) * 100}%` }} />
                      </div>
                      <span className="w-12 text-right text-halos-muted">{(c.probability * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </Stage>
  )
}
