interface Props {
  handoffJson: string
  atomId: string
}

export default function HandoffExport({ handoffJson, atomId }: Props) {
  const download = () => {
    const blob = new Blob([handoffJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `HALOS_handoff_${atomId}_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="border-t border-halos-border pt-6">
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Bio Team Handoff Package
      </h2>
      <p className="text-halos-muted text-sm mb-4">
        Download the complete handoff JSON. Contains: FASTA sequence, coordination geometry,
        binding confidence, orbital data, and lab instructions for prime editing into D. radiodurans.
      </p>
      <button
        onClick={download}
        className="px-6 py-3 bg-halos-accent text-halos-bg font-mono text-sm font-medium hover:bg-halos-accent/90 transition-colors rounded"
      >
        Download Handoff Package
      </button>
    </section>
  )
}
