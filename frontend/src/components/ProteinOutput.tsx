import { useState } from 'react'

interface Props {
  sequence: string
  fasta: string
  bindingResidues: string[]
  bindingPositions: number[]
  bindingConfidence: number
}

export default function ProteinOutput({ sequence, fasta, bindingResidues, bindingPositions, bindingConfidence }: Props) {
  const [copied, setCopied] = useState(false)
  const bindingSet = new Set(bindingPositions)

  const copy = () => {
    navigator.clipboard.writeText(fasta)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Designed Protein Sequence
      </h2>

      <div className="flex items-center gap-6 mb-4">
        <div>
          <div className="text-halos-muted text-xs mb-1">Binding confidence</div>
          <div className="font-mono text-2xl text-halos-accent">{(bindingConfidence * 100).toFixed(0)}%</div>
        </div>
        <div>
          <div className="text-halos-muted text-xs mb-1">Binding residues</div>
          <div className="font-mono text-halos-text">{bindingResidues.join(' — ')}</div>
        </div>
        <div>
          <div className="text-halos-muted text-xs mb-1">Positions (helix face)</div>
          <div className="font-mono text-halos-text">{bindingPositions.join(', ')}</div>
        </div>
      </div>

      <div className="bg-halos-surface border border-halos-border rounded p-4 mb-3 font-mono text-sm leading-loose">
        {sequence.split('').map((aa, i) => (
          <span
            key={i}
            className={bindingSet.has(i) ? 'text-halos-accent font-bold underline' : 'text-halos-muted'}
          >
            {aa}
          </span>
        ))}
      </div>

      <div className="bg-halos-surface border border-halos-border rounded p-4 mb-3">
        <pre className="font-mono text-xs text-halos-muted whitespace-pre-wrap break-all">{fasta}</pre>
      </div>

      <button
        onClick={copy}
        className="px-4 py-2 border border-halos-accent text-halos-accent font-mono text-sm hover:bg-halos-accent hover:text-halos-bg transition-colors rounded"
      >
        {copied ? 'Copied!' : 'Copy FASTA'}
      </button>
      <p className="text-halos-muted text-xs mt-2">
        Submit this FASTA to ColabFold (AlphaFold2). pLDDT &gt; 70 at binding residues required before wet lab synthesis.
      </p>
    </section>
  )
}
