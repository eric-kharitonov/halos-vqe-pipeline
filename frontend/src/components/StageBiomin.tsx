import Stage from './Stage'
import type { PipelineResult } from '../api/client'

export default function StageBiomin({ run }: { run: PipelineResult | null }) {
  return (
    <Stage
      n="08"
      id="stage-biomin"
      title="Biomineralization"
      status={run ? 'CONCEPTUAL' : 'WAITING ON CHASSIS'}
      tone="idle"
      guardrail="HALF-LIFE UNCHANGED · RADIOACTIVITY NOT NEUTRALIZED · MOBILITY & LEACHING RISK REDUCED"
    >
      <div className="max-w-2xl space-y-5">
        <p className="text-sm leading-relaxed text-halos-dim">
          The engineered cells capture the target ion with the designed protein and nucleate it into a
          solid mineral that precipitates out of solution and can be collected. This is the end goal of
          the pipeline — shown here as the concept it points to, not a measured result.
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div className="border border-halos-line bg-halos-surface p-3">
            <div className="label">INPUT</div>
            <div className="mt-1 font-mono text-sm text-halos-text">mobile ions</div>
          </div>
          <div className="border border-halos-line bg-halos-surface p-3">
            <div className="label">MECHANISM</div>
            <div className="mt-1 font-mono text-sm text-halos-text">bind → nucleate</div>
          </div>
          <div className="border border-halos-line bg-halos-surface p-3">
            <div className="label">OUTPUT</div>
            <div className="mt-1 font-mono text-sm text-halos-text">solid crystal</div>
          </div>
          <div className="border border-halos-line bg-halos-surface p-3">
            <div className="label">RADIOACTIVITY</div>
            <div className="mt-1 font-mono text-sm text-halos-warn">unchanged</div>
          </div>
        </div>
        <p className="text-xs leading-relaxed text-halos-muted">
          Biomineralization does not eliminate radioactivity — it converts mobile, leachable liquid waste
          into immobile solid crystals that are far safer to store, in smaller volumes, with negligible
          leaching. Be precise about this: the win is <span className="text-halos-dim">containment</span>, not decay.
        </p>
      </div>
    </Stage>
  )
}
