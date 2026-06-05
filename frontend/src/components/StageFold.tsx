import Stage from './Stage'
import type { PipelineResult, FoldResult } from '../api/client'
import type { Status } from '../lib/usePipeline'

interface Props {
  run: PipelineResult | null
  fold: FoldResult | null
  status: Status
  error: string | null
  onFold: () => void
}

function plddtColor(v: number): string {
  if (v >= 90) return '#48e3ea'   // very high
  if (v >= 70) return '#6ad08f'   // confident
  if (v >= 50) return '#f5a623'   // low
  return '#e84848'                // very low
}

export default function StageFold({ run, fold, status, error, onFold }: Props) {
  let statusText = 'WAITING ON CANDIDATE'
  let tone: 'idle' | 'active' | 'running' | 'done' = 'idle'
  if (run && status === 'idle') { statusText = 'READY'; tone = 'active' }
  if (status === 'running') { statusText = 'FOLDING'; tone = 'running' }
  if (fold) { statusText = `MEAN pLDDT ${fold.mean_plddt}`; tone = 'done' }
  if (status === 'error') { statusText = 'SERVICE BUSY'; tone = 'idle' }

  return (
    <Stage
      n="05"
      id="stage-fold"
      title="Structure prediction"
      status={statusText}
      tone={tone}
      guardrail="REAL ESMFOLD PREDICTION · pLDDT IS FOLD CONFIDENCE, NOT BINDING OR IN-CELL FUNCTION"
    >
      {!run && <div className="font-mono text-xs text-halos-muted">// no structure — run the pipeline first</div>}

      {run && (
        <div className="space-y-5">
          <p className="max-w-2xl text-sm leading-relaxed text-halos-dim">
            Fold the designed construct with ESMFold (real structure prediction, no MSA). The
            motif is embedded in a longer α-helical scaffold so the fold is meaningful.
            <span className="text-halos-muted"> High pLDDT means the sequence folds confidently — not that the protein binds the metal or works in a cell.</span>
          </p>

          {!fold && (
            <button
              onClick={onFold}
              disabled={status === 'running'}
              className="border border-halos-accent px-5 py-2.5 font-mono text-xs tracking-widest text-halos-accent transition-colors hover:bg-halos-accent hover:text-halos-bg disabled:cursor-wait disabled:opacity-50"
            >
              {status === 'running' ? 'PREDICTING STRUCTURE…' : `PREDICT FOLD · ${run.foldable_construct.length} RESIDUES →`}
            </button>
          )}

          {status === 'running' && (
            <div className="h-1 w-full max-w-md overflow-hidden bg-halos-line">
              <div className="h-full w-1/2 animate-pulse bg-halos-accent" />
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-2">
              <div className="border border-halos-warn/50 p-3 font-mono text-xs text-halos-warn">
                ESMFold is busy right now ({error}). The public endpoint is intermittent — try again in a moment.
              </div>
              <button onClick={onFold} className="border border-halos-border px-3 py-1.5 font-mono text-[10px] tracking-widest text-halos-dim hover:border-halos-text hover:text-halos-text">
                RETRY
              </button>
            </div>
          )}

          {fold && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <div className="border border-halos-line bg-halos-surface p-3">
                  <div className="label">MEAN pLDDT</div>
                  <div className="mt-1 font-mono text-2xl" style={{ color: plddtColor(fold.mean_plddt) }}>{fold.mean_plddt}</div>
                </div>
                <div className="border border-halos-line bg-halos-surface p-3">
                  <div className="label">CONFIDENCE</div>
                  <div className="mt-1 font-mono text-sm text-halos-text">{fold.mean_plddt >= 70 ? 'CONFIDENT' : 'LOW'}</div>
                </div>
                <div className="border border-halos-line bg-halos-surface p-3">
                  <div className="label">RESIDUES</div>
                  <div className="mt-1 font-mono text-sm text-halos-text">{fold.n_residues}</div>
                </div>
                <div className="border border-halos-line bg-halos-surface p-3">
                  <div className="label">SOURCE</div>
                  <div className="mt-1 font-mono text-[11px] text-halos-dim">ESMFold v1</div>
                </div>
              </div>

              <div>
                <div className="label mb-2">PER-RESIDUE pLDDT</div>
                <div className="flex h-12 items-end gap-px">
                  {fold.per_residue_plddt.map((v, i) => (
                    <div key={i} className="flex-1" style={{ height: `${v}%`, backgroundColor: plddtColor(v), minWidth: '2px' }} title={`res ${i + 1}: ${v}`} />
                  ))}
                </div>
                <div className="mt-2 flex gap-4 font-mono text-[9px] tracking-widest text-halos-muted">
                  <span><span style={{ color: '#48e3ea' }}>■</span> ≥90</span>
                  <span><span style={{ color: '#6ad08f' }}>■</span> 70–90</span>
                  <span><span style={{ color: '#f5a623' }}>■</span> 50–70</span>
                  <span><span style={{ color: '#e84848' }}>■</span> &lt;50</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </Stage>
  )
}
