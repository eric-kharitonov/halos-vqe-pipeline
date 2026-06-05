interface Props {
  onReset: () => void
}

export default function Header({ onReset }: Props) {
  return (
    <header className="sticky top-0 z-30 border-b border-halos-line bg-halos-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-3">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-sm tracking-widest text-halos-text">HALOS</span>
          <span className="font-mono text-[10px] tracking-widest text-halos-muted">· V0.4</span>
          <span className="ml-3 hidden font-mono text-[10px] tracking-widest text-halos-dim sm:inline">
            QUANTUM-ENHANCED BIOREMEDIATION · TKS MOONSHOT 2025
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-sm border border-halos-ok/40 px-2 py-1 font-mono text-[10px] tracking-widest text-halos-ok">
            REAL COMPUTE
          </span>
          <button
            onClick={onReset}
            className="rounded-sm border border-halos-border px-2 py-1 font-mono text-[10px] tracking-widest text-halos-dim transition-colors hover:border-halos-text hover:text-halos-text"
          >
            RESET
          </button>
        </div>
      </div>
    </header>
  )
}
