import Stage from './Stage'
import type { PipelineResult } from '../api/client'

const EDITS = [
  { gene: 'neutral locus', edit: 'INSERT', detail: 'quantum-designed metal-binding protein gene' },
  { gene: 'PprI', edit: 'UPREGULATE', detail: 'radiation-resistance master regulator' },
  { gene: 'katA', edit: 'ENHANCE', detail: 'catalase — clears radiation-generated ROS' },
  { gene: 'recA', edit: 'PRESERVE', detail: 'homologous-recombination DNA repair' },
]

export default function StageChassis({ run }: { run: PipelineResult | null }) {
  return (
    <Stage
      n="07"
      id="stage-chassis"
      title="Bacterial chassis design"
      status={run ? 'CONCEPTUAL' : 'WAITING ON HANDOFF'}
      tone="idle"
      guardrail="CONCEPTUAL STRAIN DESIGN · NO WET-LAB WORK · ACTINIDE WORK NEEDS A LICENSED BSL-2/RAM FACILITY"
    >
      <div className="max-w-2xl space-y-4">
        <p className="text-sm leading-relaxed text-halos-dim">
          The bio team prime-edits the designed gene into <span className="italic">Deinococcus radiodurans</span> —
          the most radiation-resistant organism known (survives ~1.5M rads). This is a paper design, not
          executed: the edits below show what the handoff would drive in a licensed lab.
        </p>
        <div className="border border-halos-line">
          {EDITS.map((e, i) => (
            <div key={i} className="flex items-center gap-4 border-b border-halos-line px-4 py-2.5 font-mono text-xs last:border-b-0">
              <span className="w-28 text-halos-text">{e.gene}</span>
              <span className="w-24 tracking-widest text-halos-accent">{e.edit}</span>
              <span className="flex-1 text-halos-muted">{e.detail}</span>
            </div>
          ))}
        </div>
        <p className="font-mono text-[10px] uppercase tracking-wider text-halos-muted">
          Prime editing (find-and-replace) over CRISPR · single off-target in an essential gene is lethal
        </p>
      </div>
    </Stage>
  )
}
