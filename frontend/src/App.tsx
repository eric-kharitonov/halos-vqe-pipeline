import Header from './components/Header'
import Hero from './components/Hero'
import PipelineNav from './components/PipelineNav'
import Stage from './components/Stage'
import TargetGrid from './components/TargetGrid'
import StageVqe from './components/StageVqe'
import StageBinding from './components/StageBinding'
import StageProtein from './components/StageProtein'
import StageFold from './components/StageFold'
import StageHandoff from './components/StageHandoff'
import StageChassis from './components/StageChassis'
import StageBiomin from './components/StageBiomin'
import { usePipeline } from './lib/usePipeline'

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
              <TargetGrid
                atoms={p.atoms}
                selectedId={atomId}
                onSelect={p.selectAtom}
                status={p.atomsStatus}
                error={p.atomsError}
                onRetry={p.reloadAtoms}
              />
            </Stage>

            {/* 02 — VQE */}
            <StageVqe atom={atom} run={run} status={runStatus} error={p.runError} onRun={p.doRun} />

            {/* 03 — Binding hotspot map */}
            <StageBinding run={run} />

            {/* 04 — Protein candidate search (design + QAOA) */}
            <StageProtein run={run} qaoa={p.qaoa} qaoaStatus={p.qaoaStatus} onQaoa={p.doQaoa} />

            {/* 05 — Structure prediction (ESMFold) */}
            <StageFold run={run} fold={p.fold} status={p.foldStatus} error={p.foldError} onFold={p.doFold} />

            {/* 06 — Bio handoff */}
            <StageHandoff run={run} qaoa={p.qaoa} fold={p.fold} />

            {/* 07 — Chassis (prime-edit design) */}
            <StageChassis run={run} edit={p.edit} editStatus={p.editStatus} onPrimeEdit={p.doPrimeEdit} />

            {/* 08 — Biomineralization */}
            <StageBiomin run={run} />

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
                    <span className="text-halos-muted">{e.time}</span>
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
