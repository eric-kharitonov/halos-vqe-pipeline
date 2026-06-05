import Stage from './Stage'
import type { PipelineResult, PrimeEditResult } from '../api/client'
import type { Status } from '../lib/usePipeline'

interface Props {
  run: PipelineResult | null
  edit: PrimeEditResult | null
  editStatus: Status
  onPrimeEdit: () => void
}

const EDITS = [
  { gene: 'neutral locus', edit: 'INSERT', detail: 'quantum-designed metal-binding protein gene' },
  { gene: 'PprI', edit: 'UPREGULATE', detail: 'radiation-resistance master regulator' },
  { gene: 'katA', edit: 'ENHANCE', detail: 'catalase — clears radiation-generated ROS' },
]

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="min-w-0">
      <div className="label">{k}</div>
      <div className="mt-0.5 truncate font-mono text-xs text-halos-text" title={v}>{v}</div>
    </div>
  )
}

export default function StageChassis({ run, edit, editStatus, onPrimeEdit }: Props) {
  return (
    <Stage
      n="07"
      id="stage-chassis"
      title="Bacterial chassis design"
      status={edit ? 'EDIT DESIGNED' : run ? 'READY' : 'WAITING ON HANDOFF'}
      tone={edit ? 'done' : 'idle'}
      guardrail="EDIT DESIGN IS REAL (CODON-OPTIMIZED GENE + pegRNA) · WHETHER THE CELL SURVIVES/EXPRESSES IS WET-LAB, NOT SIMULATED"
    >
      <div className="max-w-3xl space-y-6">
        <p className="text-sm leading-relaxed text-halos-dim">
          Prime-edit the designed gene into <span className="italic">Deinococcus radiodurans</span> —
          the most radiation-resistant organism known. The edit <span className="text-halos-text">design</span> below
          is computed (codon optimization + pegRNA); the radiation-hardening edits are the conceptual plan.
        </p>

        {/* Computed prime edit */}
        {run && !edit && (
          <button
            onClick={onPrimeEdit}
            disabled={editStatus === 'running'}
            className="border border-halos-accent px-5 py-2.5 font-mono text-xs tracking-widest text-halos-accent transition-colors hover:bg-halos-accent hover:text-halos-bg disabled:cursor-wait disabled:opacity-50"
          >
            {editStatus === 'running' ? 'DESIGNING EDIT…' : 'DESIGN PRIME EDIT →'}
          </button>
        )}
        {editStatus === 'error' && <div className="font-mono text-xs text-halos-error">Edit design failed.</div>}

        {edit && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Field k="LOCUS" v={edit.locus_name.split(' ')[0]} />
              <Field k="GENE LENGTH" v={`${edit.gene_length_bp} bp`} />
              <Field k="GC CONTENT" v={`${edit.gc_content}%`} />
              <Field k="PAM" v={edit.pam} />
            </div>

            <div>
              <div className="label mb-1">CODON-OPTIMIZED GENE (D. RADIODURANS)</div>
              <div className="break-all border border-halos-line bg-halos-surface p-3 font-mono text-[11px] leading-relaxed text-halos-ok">
                {edit.gene_dna}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="label mb-1">pegRNA SPACER + PAM</div>
                <div className="border border-halos-line bg-halos-surface p-2 font-mono text-[11px] text-halos-text">
                  {edit.spacer}<span className="text-halos-accent">{edit.pam}</span>
                </div>
              </div>
              <div>
                <div className="label mb-1">PBS · RT TEMPLATE</div>
                <div className="border border-halos-line bg-halos-surface p-2 font-mono text-[11px] text-halos-dim">
                  <span className="text-halos-warn">{edit.pbs}</span> · {edit.rtt.slice(0, 18)}…
                </div>
              </div>
            </div>

            <div>
              <div className="label mb-1">GENOMIC EDIT · BEFORE → AFTER</div>
              <div className="space-y-1 border border-halos-line bg-halos-surface p-3 font-mono text-[11px] leading-relaxed">
                <div className="break-all text-halos-muted">{edit.before}</div>
                <div className="break-all text-halos-dim">
                  {edit.after.slice(0, edit.insert_index)}
                  <span className="bg-halos-accent/15 text-halos-accent">{edit.gene_dna}</span>
                  {edit.after.slice(edit.insert_index + edit.gene_dna.length)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conceptual radiation-hardening edits */}
        <div className="border border-halos-line">
          {EDITS.map((e, i) => (
            <div key={i} className="flex items-center gap-4 border-b border-halos-line px-4 py-2.5 font-mono text-xs last:border-b-0">
              <span className="w-28 text-halos-text">{e.gene}</span>
              <span className="w-24 tracking-widest text-halos-accent">{e.edit}</span>
              <span className="flex-1 text-halos-muted">{e.detail}</span>
            </div>
          ))}
        </div>
      </div>
    </Stage>
  )
}
