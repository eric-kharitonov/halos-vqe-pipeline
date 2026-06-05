import { useEffect, useState } from 'react'
import { fetchAtoms, type AtomMeta } from '../api/client'

const CLASS_COLORS: Record<string, string> = {
  diatomic: 'text-sky-400',
  alkali: 'text-emerald-400',
  lanthanide: 'text-violet-400',
  actinide: 'text-orange-400',
}

interface Props {
  onSelect: (atomId: string) => void
}

export default function AtomSelector({ onSelect }: Props) {
  const [atoms, setAtoms] = useState<AtomMeta[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAtoms().then(setAtoms).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-halos-muted font-mono text-sm">Loading atoms...</p>

  const runnable = atoms.filter(a => !a.is_placeholder)
  const placeholders = atoms.filter(a => a.is_placeholder)

  return (
    <div>
      <h1 className="font-serif text-4xl font-light mb-2">Select Target Atom</h1>
      <p className="text-halos-muted text-sm mb-8">
        VQE identifies coordination sites. The pipeline designs a protein to bind them — deterministically.
      </p>

      <section className="mb-8">
        <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
          Runnable Now
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {runnable.map(atom => (
            <button
              key={atom.id}
              onClick={() => onSelect(atom.id)}
              className="text-left p-4 rounded border border-halos-border bg-halos-surface hover:border-halos-accent transition-colors group"
            >
              <div className="flex items-baseline gap-2 mb-1">
                <span className={`font-mono text-lg font-medium ${CLASS_COLORS[atom.coordination_class] ?? 'text-halos-text'}`}>
                  {atom.symbol}
                </span>
                <span className="text-halos-muted text-xs">{atom.num_qubits} qubits</span>
              </div>
              <div className="text-halos-text text-sm mb-1">{atom.name}</div>
              <div className="text-halos-muted text-xs">{atom.notes}</div>
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
          Actinide Targets — Awaiting Fault-Tolerant Hardware
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {placeholders.map(atom => (
            <div
              key={atom.id}
              className="p-4 rounded border border-halos-border opacity-50 cursor-not-allowed"
            >
              <div className="flex items-baseline gap-2 mb-1">
                <span className={`font-mono text-lg font-medium ${CLASS_COLORS[atom.coordination_class] ?? 'text-halos-muted'}`}>
                  {atom.symbol}
                </span>
                <span className="text-halos-muted text-xs">{atom.num_qubits} electrons</span>
              </div>
              <div className="text-halos-muted text-sm">{atom.name}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
