interface Props {
  geometry: string
  coordinationNumber: number
  orbitalOccupancies: number[]
  emptyOrbitalIndices: number[]
}

export default function BindingSites({ geometry, coordinationNumber, orbitalOccupancies, emptyOrbitalIndices }: Props) {
  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Binding Sites (Coordination Sites)
      </h2>
      <div className="flex items-baseline gap-4 mb-4">
        <span className="font-mono text-2xl text-halos-text">{coordinationNumber}</span>
        <span className="text-halos-muted text-sm">empty orbitals →</span>
        <span className="font-mono text-halos-accent text-lg capitalize">{geometry.replace(/_/g, ' ')}</span>
        <span className="text-halos-muted text-sm">coordination</span>
      </div>
      <div className="flex gap-2 flex-wrap">
        {orbitalOccupancies.map((occ, i) => {
          const isEmpty = emptyOrbitalIndices.includes(i)
          return (
            <div
              key={i}
              className={`px-3 py-2 rounded border font-mono text-xs ${
                isEmpty
                  ? 'border-halos-accent text-halos-accent bg-halos-accent/5'
                  : 'border-halos-border text-halos-muted'
              }`}
            >
              <div>ψ{i}</div>
              <div>{occ.toFixed(3)}</div>
              {isEmpty && <div className="text-[10px] mt-1">SITE</div>}
            </div>
          )
        })}
      </div>
      <p className="text-halos-muted text-xs mt-3">
        Orbitals with occupancy &lt; 0.3 are electron-deficient — these are where protein donor groups coordinate.
        The geometry determines the spatial arrangement of binding residues in the designed protein.
      </p>
    </section>
  )
}
