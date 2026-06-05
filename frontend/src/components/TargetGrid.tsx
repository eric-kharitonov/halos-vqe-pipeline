import type { AtomMeta } from '../api/client'
import type { AtomsStatus } from '../lib/usePipeline'

const TIER_STYLE: Record<string, { badge: string; ring: string }> = {
  real_vqe: { badge: 'text-halos-accent border-halos-accent/40', ring: 'hover:border-halos-accent' },
  precomputed: { badge: 'text-halos-ok border-halos-ok/40', ring: 'hover:border-halos-ok' },
  toy: { badge: 'text-halos-gold border-halos-gold/40', ring: 'hover:border-halos-gold' },
  proxy: { badge: 'text-halos-warn border-halos-warn/40', ring: 'hover:border-halos-warn' },
  locked: { badge: 'text-halos-muted border-halos-faint', ring: '' },
}

interface Props {
  atoms: AtomMeta[]
  selectedId: string | null
  onSelect: (id: string) => void
  status: AtomsStatus
  error: string | null
  onRetry: () => void
}

function Tile({ atom, selected, onSelect }: { atom: AtomMeta; selected: boolean; onSelect: (id: string) => void }) {
  const style = TIER_STYLE[atom.tier] ?? TIER_STYLE.locked
  const locked = atom.is_locked
  const qubitLabel = `${atom.qubits_are_estimate ? '~' : ''}${atom.num_qubits}${atom.qubits_are_estimate ? ' (FT)' : 'q'} · ${atom.electrons} e⁻`

  return (
    <button
      disabled={locked}
      onClick={() => onSelect(atom.id)}
      title={atom.notes}
      className={`group relative flex aspect-[5/6] flex-col justify-between border p-3 text-left transition-colors ${
        locked
          ? 'cursor-not-allowed border-halos-faint opacity-45'
          : `border-halos-border bg-halos-surface ${style.ring} ${selected ? 'border-halos-text bg-halos-panel' : ''}`
      }`}
    >
      <div className="flex items-start justify-between">
        <span className="font-mono text-[10px] tracking-wider text-halos-muted">{atom.id.toUpperCase()}</span>
        <span className={`rounded-sm border px-1 py-0.5 font-mono text-[8px] tracking-widest ${style.badge}`}>
          {atom.badge}
        </span>
      </div>
      <div className="font-serif text-3xl font-light leading-none text-halos-text">{atom.symbol}</div>
      <div>
        <div className="truncate text-[11px] text-halos-dim">{atom.name}</div>
        <div className="label mt-1 normal-case tracking-wider">{qubitLabel}</div>
      </div>
    </button>
  )
}

export default function TargetGrid({ atoms, selectedId, onSelect, status, error, onRetry }: Props) {
  return (
    <div>
      <p className="mb-5 max-w-2xl text-sm leading-relaxed text-halos-dim">
        Select a target. <span className="text-halos-text">H₂</span> runs a real VQE; LiH is a
        verified precomputed Hamiltonian; tritium is a toy. <span className="text-halos-warn">Proxies</span>{' '}
        (Cs⁺, Sr²⁺) skip VQE and run the downstream design + folding from literature chemistry.
        <span className="text-halos-muted"> Locked</span> actinides await fault-tolerant hardware.
      </p>

      {status === 'loading' && (
        <div className="font-mono text-xs text-halos-muted">// loading targets…</div>
      )}

      {status === 'error' && (
        <div className="flex flex-col items-start gap-2 border border-halos-error/50 p-4">
          <div className="font-mono text-xs text-halos-error">
            Could not reach the backend{error ? ` — ${error}` : ''}. Start it with{' '}
            <span className="text-halos-text">uvicorn main:app</span> on port 8000.
          </div>
          <button
            onClick={onRetry}
            className="border border-halos-border px-3 py-1.5 font-mono text-[10px] tracking-widest text-halos-dim transition-colors hover:border-halos-text hover:text-halos-text"
          >
            RETRY
          </button>
        </div>
      )}

      {status === 'ready' && (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-9">
          {atoms.map(a => (
            <Tile key={a.id} atom={a} selected={a.id === selectedId} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  )
}
