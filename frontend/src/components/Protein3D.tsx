import { useEffect, useRef } from 'react'

declare global {
  interface Window {
    // 3Dmol.js is loaded from a CDN <script> in index.html.
    $3Dmol?: any
  }
}

// Colour each residue by pLDDT confidence. ESMFold writes pLDDT into the PDB B-factor on a
// 0-1 scale, so multiply by 100 to match the standard bands used elsewhere in the UI.
function plddtColor(atom: { b: number }): string {
  const v = atom.b * 100
  if (v >= 90) return '0x48e3ea'
  if (v >= 70) return '0x6ad08f'
  if (v >= 50) return '0xf5a623'
  return '0xe84848'
}

export default function Protein3D({ pdb }: { pdb: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    let viewer: any = null
    let cancelled = false

    // The CDN script may not have finished loading on first render — retry briefly.
    const start = (attempt = 0) => {
      if (cancelled) return
      const lib = window.$3Dmol
      if (!lib) {
        if (attempt < 20) setTimeout(() => start(attempt + 1), 150)
        return
      }
      viewer = lib.createViewer(el, { backgroundColor: '0x0a0a0a' })
      viewer.addModel(pdb, 'pdb')
      viewer.setStyle({}, { cartoon: { colorfunc: plddtColor } })
      viewer.zoomTo()
      viewer.spin('y', 0.5)
      viewer.render()
    }
    start()

    return () => {
      cancelled = true
      if (viewer) {
        try { viewer.clear() } catch { /* noop */ }
      }
    }
  }, [pdb])

  return (
    <div className="relative h-80 w-full overflow-hidden border border-halos-line bg-halos-bg">
      <div ref={ref} className="absolute inset-0" />
      <div className="pointer-events-none absolute bottom-2 left-2 font-mono text-[9px] tracking-widest text-halos-muted">
        DRAG TO ROTATE · SCROLL TO ZOOM · ESMFOLD STRUCTURE
      </div>
    </div>
  )
}
