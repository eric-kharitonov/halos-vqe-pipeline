import Stage from './Stage'
import type { PipelineResult } from '../api/client'

export default function StageBinding({ run }: { run: PipelineResult | null }) {
  const status = run ? `${run.coordination_number} SITES · ${run.geometry.replace(/_/g, ' ').toUpperCase()}` : 'WAITING ON VQE'

  return (
    <Stage
      n="03"
      id="stage-binding"
      title="Binding hotspot map"
      status={status}
      tone={run ? 'done' : 'idle'}
      guardrail="SIMPLIFIED CHEMISTRY TRANSLATION · NOT A QM/MM ELECTRON-DENSITY EXTRACTION"
    >
      {!run && <div className="font-mono text-xs text-halos-muted">// no map yet — run stage 02</div>}

      {run && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className="font-mono text-2xl text-halos-text">{run.coordination_number}</span>
            <span className="text-sm text-halos-muted">empty orbitals →</span>
            <span className="font-mono text-lg capitalize text-halos-accent">{run.geometry.replace(/_/g, ' ')}</span>
            <span
              className={`ml-2 rounded-sm border px-2 py-0.5 font-mono text-[10px] tracking-widest ${
                run.map_source === 'vqe' ? 'border-halos-accent/40 text-halos-accent' : 'border-halos-warn/40 text-halos-warn'
              }`}
            >
              {run.map_source === 'vqe' ? 'QUANTUM-COMPUTED' : 'LITERATURE ESTIMATE'}
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {run.orbital_occupancies.map((occ, i) => {
              const isSite = run.empty_orbital_indices.includes(i)
              return (
                <div
                  key={i}
                  className={`border px-3 py-2 text-center font-mono text-xs ${
                    isSite ? 'border-halos-accent bg-halos-accent/5 text-halos-accent' : 'border-halos-line text-halos-muted'
                  }`}
                >
                  <div>ψ{i}</div>
                  <div className="mt-0.5">{occ.toFixed(3)}</div>
                  {isSite && <div className="mt-1 text-[8px] tracking-widest">SITE</div>}
                </div>
              )
            })}
          </div>

          <p className="max-w-2xl text-xs leading-relaxed text-halos-muted">
            {run.map_source === 'vqe'
              ? 'Orbitals with occupancy < 0.3 are electron-deficient — where protein donor groups coordinate. Occupancies come straight from the VQE 1-RDM.'
              : 'This species is too large for VQE; the coordination number and geometry are taken from the literature, not a quantum-computed density. The downstream design is identical.'}
          </p>
        </div>
      )}
    </Stage>
  )
}
