import Stage from './Stage'
import type { PipelineResult } from '../api/client'

function CellSchematic() {
  return (
    <svg viewBox="0 0 420 240" className="w-full max-w-md" role="img" aria-label="Engineered cell schematic">
      {/* incoming ions */}
      {[40, 70, 100, 55, 85].map((y, i) => (
        <g key={i}>
          <circle cx={14 + (i % 2) * 10} cy={y} r="3" fill="#f5a623" />
        </g>
      ))}
      <text x="8" y="120" className="font-mono" fontSize="8" fill="#5c5c56">MOBILE IONS</text>
      <path d="M30 70 H120" stroke="#3a3a36" strokeWidth="1" strokeDasharray="3 3" />

      {/* cell body */}
      <ellipse cx="250" cy="120" rx="130" ry="90" fill="#0f0f0f" stroke="#6ad08f" strokeWidth="1.5" />
      <ellipse cx="250" cy="120" rx="130" ry="90" fill="none" stroke="#6ad08f" strokeWidth="6" opacity="0.08" />
      <text x="250" y="36" textAnchor="middle" className="font-mono italic" fontSize="9" fill="#6ad08f">D. radiodurans (engineered)</text>

      {/* inserted gene (DNA glyph) */}
      <g stroke="#48e3ea" strokeWidth="1.4" fill="none">
        <path d="M205 150 q10 -8 20 0 q10 8 20 0" />
        <path d="M205 158 q10 8 20 0 q10 -8 20 0" />
      </g>
      <text x="245" y="170" className="font-mono" fontSize="8" fill="#48e3ea">inserted gene</text>

      {/* surface binding proteins */}
      {[[140, 90], [150, 140], [360, 95], [355, 145]].map(([x, y], i) => (
        <g key={i}>
          <circle cx={x} cy={y} r="7" fill="none" stroke="#48e3ea" strokeWidth="1.3" />
          <circle cx={x} cy={y} r="2.5" fill="#f5a623" />
        </g>
      ))}
      <text x="250" y="205" textAnchor="middle" className="font-mono" fontSize="8" fill="#48e3ea">designed metal-binding protein → captures ion</text>

      {/* nucleated crystal */}
      <polygon points="300,110 316,119 316,137 300,146 284,137 284,119" fill="#48e3ea" opacity="0.25" stroke="#48e3ea" strokeWidth="1.2" />
      <text x="300" y="100" textAnchor="middle" className="font-mono" fontSize="8" fill="#48e3ea">solid crystal</text>
    </svg>
  )
}

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
      <div className="max-w-3xl space-y-6">
        <p className="text-sm leading-relaxed text-halos-dim">
          The engineered cells capture the target ion with the designed protein and nucleate it into a
          solid mineral that precipitates out of solution and can be collected — the end goal of the pipeline.
        </p>

        <div className="border border-halos-line bg-halos-surface p-4">
          <div className="label mb-3">SCHEMATIC · CONCEPT, NOT SIMULATION</div>
          <CellSchematic />
        </div>

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
          into immobile solid crystals, far safer to store in smaller volumes. The win is{' '}
          <span className="text-halos-dim">containment</span>, not decay.
        </p>
      </div>
    </Stage>
  )
}
