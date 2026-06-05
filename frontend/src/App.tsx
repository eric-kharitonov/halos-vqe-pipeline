import { useState } from 'react'
import AtomSelector from './components/AtomSelector'
import PipelineRunner from './components/PipelineRunner'

export default function App() {
  const [selectedAtomId, setSelectedAtomId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-halos-bg text-halos-text">
      <header className="border-b border-halos-border px-8 py-5 flex items-center gap-4">
        <span className="font-serif text-2xl font-light tracking-widest text-halos-text">HALOS</span>
        <span className="text-halos-muted text-sm font-mono">Quantum Bioremediation Pipeline</span>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-10">
        {!selectedAtomId ? (
          <AtomSelector onSelect={setSelectedAtomId} />
        ) : (
          <PipelineRunner atomId={selectedAtomId} onReset={() => setSelectedAtomId(null)} />
        )}
      </main>
    </div>
  )
}
