import Header from './components/Header'
import Hero from './components/Hero'
import PipelineNav from './components/PipelineNav'
import Stage from './components/Stage'
import TargetGrid from './components/TargetGrid'
import StageVqe from './components/StageVqe'
import { usePipeline } from './lib/usePipeline'

function Pending({ text }: { text: string }) {
  return <div className="font-mono text-xs text-halos-muted">{text}</div>
}

export default function App() {
  const p = usePipeline()
  const { atom, atomId, run, runStatus } = p

  const done = new Set<string>()
  if (atom) done.add('target')
  if (run) { done.add('vqe'); done.add('binding'); done.add('protein') }
  if (p.fold) done.add('fold')
  if (run) done.add('handoff')
  const activeKey = !atom ? 'target' : runStatus !== 'done' ? 'vqe' : 'protein'

  return (
    <div className="min-h-screen bg-halos-bg text-halos-text">
      <Header onReset={p.reset} />

      <div className="mx-auto max-w-[1400px] px-6">
        <Hero />

        <div className="flex gap-12 py-2">
          <main className="min-w-0 flex-1">
            {/* 01 — Target selection */}
            <Stage
              n="01"
              id="stage-target"
              title="Target selection"
              status={atom ? `LOCKED IN · ${atom.symbol}` : 'AWAITING INPUT'}
              tone={atom ? 'done' : 'active'}
            >
              <TargetGrid atoms={p.atoms} selectedId={atomId} onSelect={p.selectAtom} />
            </Stage>

            {/* 02 — VQE */}
            <StageVqe atom={atom} run={run} status={runStatus} error={p.runError} onRun={p.doRun} />

            {/* 03 — Binding hotspot map */}
            <Stage
              n="03"
              id="stage-binding"
              title="Binding hotspot map"
              status={run ? `${run.coordination_number} SITES · ${run.geometry.toUpperCase()}` : 'WAITING ON VQE'}
              tone={run ? 'done' : 'idle'}
              guardrail="SIMPLIFIED CHEMISTRY TRANSLATION · NOT A QM/MM ELECTRON-DENSITY EXTRACTION"
            >
              <Pending text="// no map yet — run stage 02" />
            </Stage>

            {/* 04 — Protein candidate search */}
            <Stage
              n="04"
              id="stage-protein"
              title="Protein candidate search"
              status={run ? 'CANDIDATE READY' : 'WAITING ON MAP'}
              tone={run ? 'done' : 'idle'}
              guardrail="RULE-BASED RANKER + QAOA OVER A CURATED MOTIF POOL · STAND-IN FOR RFDIFFUSION + PROTEINMPNN"
            >
              <Pending text="// no candidates — generate map first" />
            </Stage>

            {/* 05 — Structure prediction (ESMFold) */}
            <Stage
              n="05"
              id="stage-fold"
              title="Structure prediction"
              status="WAITING ON CANDIDATE"
              tone="idle"
              guardrail="REAL ESMFOLD PREDICTION · pLDDT IS FOLD CONFIDENCE, NOT BINDING OR IN-CELL FUNCTION"
            >
              <Pending text="// no structure — select a candidate first" />
            </Stage>

            {/* 06 — Bio handoff */}
            <Stage
              n="06"
              id="stage-handoff"
              title="Bio handoff payload"
              status={run ? 'READY' : 'WAITING ON SELECTION'}
              tone={run ? 'done' : 'idle'}
              guardrail="THE SINGLE JSON CONTRACT BETWEEN QC AND BIO · VERSIONED SCHEMA"
            >
              <Pending text="// awaiting peptide selection" />
            </Stage>

            {/* 07 — Chassis */}
            <Stage
              n="07"
              id="stage-chassis"
              title="Bacterial chassis design"
              status="CONCEPTUAL"
              tone="idle"
              guardrail="CONCEPTUAL STRAIN DESIGN · NO WET-LAB WORK · ACTINIDE WORK NEEDS A LICENSED BSL-2/RAM FACILITY"
            >
              <Pending text="// awaiting handoff payload" />
            </Stage>

            {/* 08 — Biomineralization */}
            <Stage
              n="08"
              id="stage-biomin"
              title="Biomineralization"
              status="CONCEPTUAL"
              tone="idle"
              guardrail="HALF-LIFE UNCHANGED · RADIOACTIVITY NOT NEUTRALIZED · MOBILITY & LEACHING RISK REDUCED"
            >
              <Pending text="// awaiting engineered chassis" />
            </Stage>

            {/* Event log */}
            <section className="border-b border-halos-line py-12">
              <div className="mb-5 flex items-baseline gap-4">
                <span className="font-mono text-[11px] tracking-widest text-halos-muted">CHANNELS</span>
                <h2 className="font-serif text-3xl font-light text-halos-text">Event log</h2>
              </div>
              <div className="space-y-1.5 font-mono text-xs">
                {p.log.length === 0 && <div className="text-halos-muted">// no events yet</div>}
                {p.log.map((e, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="text-halos-faint">{e.time}</span>
                    <span className="text-halos-dim">{e.text}</span>
                  </div>
                ))}
              </div>
            </section>
          </main>

          <PipelineNav doneKeys={done} activeKey={activeKey} />
        </div>

        <footer className="border-t border-halos-line py-8 font-mono text-[10px] tracking-widest text-halos-muted">
          HALOS · QUANTUM-ENHANCED MICROBIAL BIOREMEDIATION · TKS TORONTO 2025–2026 · ERIC KHARITONOV · DEMO TOOL
        </footer>
      </div>
    </div>
  )
}
