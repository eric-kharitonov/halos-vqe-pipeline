interface Props {
  onReset: () => void
}

// HALOS wordmark: the O is the orbital (ring + electron), with a halo arcing over the word.
function HalosWordmark() {
  return (
    <span className="relative inline-flex items-center">
      <svg
        viewBox="0 0 262 46"
        className="pointer-events-none absolute -top-[5px] left-0 w-full"
        fill="none"
        aria-hidden="true"
      >
        <ellipse cx="124" cy="30" rx="118" ry="12" stroke="#48e3ea" strokeWidth="1.6" transform="rotate(-6 124 30)" opacity="0.85" />
        <circle cx="241" cy="18" r="4" fill="#48e3ea" />
      </svg>
      <span className="inline-flex items-center font-mono text-[15px] font-medium tracking-[0.16em] text-halos-text">
        HAL
        <svg viewBox="0 0 100 100" className="mx-[0.1em]" style={{ width: '0.66em', height: '0.66em' }} fill="none" aria-hidden="true">
          <circle cx="50" cy="50" r="42" stroke="#48e3ea" strokeWidth="8" />
          <circle cx="79.7" cy="20.3" r="8" fill="#e8e6df" />
        </svg>
        S
      </span>
    </span>
  )
}

export default function Header({ onReset }: Props) {
  return (
    <header className="sticky top-0 z-30 border-b border-halos-line bg-halos-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <HalosWordmark />
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
