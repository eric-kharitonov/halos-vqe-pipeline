interface Props {
  handoffJson: string
  atomId: string
  qaoaBlock: Record<string, unknown> | null
}

export default function HandoffExport({ handoffJson, atomId, qaoaBlock }: Props) {
  const download = () => {
    // If a QAOA search has been run, merge its recommendation into the package and
    // mark it the primary recommendation. The block's schema is defined by the backend.
    let payload = handoffJson
    if (qaoaBlock) {
      const parsed = JSON.parse(handoffJson)
      parsed.qaoa_search = qaoaBlock
      parsed.primary_recommendation = 'qaoa_search'
      payload = JSON.stringify(parsed, null, 2)
    }

    const blob = new Blob([payload], { type: 'application/json' })
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
      {qaoaBlock && (
        <p className="text-halos-accent text-xs font-mono mb-4">
          ✓ QAOA recommendation included — it will be set as the primary candidate in the package.
        </p>
      )}
      <button
        onClick={download}
        className="px-6 py-3 bg-halos-accent text-halos-bg font-mono text-sm font-medium hover:bg-halos-accent/90 transition-colors rounded"
      >
        Download Handoff Package
      </button>
    </section>
  )
}
