function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="border-l border-halos-line pl-3">
      <div className="label">{k}</div>
      <div className="mt-1 font-mono text-xs text-halos-dim">{v}</div>
    </div>
  )
}

export default function Hero() {
  return (
    <section className="border-b border-halos-line px-1 py-12">
      <div className="label mb-6">PIPELINE TOOL · ERIC KHARITONOV</div>
      <h1 className="max-w-3xl font-serif text-5xl font-light leading-[1.05] tracking-tight text-halos-text sm:text-6xl">
        Designing organisms
        <br />
        that lock away <span className="italic text-halos-gold">nuclear waste</span>,
        <br />
        computed atom-up.
      </h1>
      <p className="mt-7 max-w-2xl text-sm leading-relaxed text-halos-dim">
        An interactive simulator for the quantum-to-biology pipeline. Hydrogen runs a real VQE
        on a Qiskit backend; larger species are clearly-labelled proxies that run the downstream
        design and folding from literature chemistry; the heaviest actinides are locked until
        fault-tolerant hardware exists. Each stage produces an artifact the next stage consumes —
        <span className="text-halos-text"> VQE → binding map → protein candidate → fold → bio handoff.</span>
      </p>
      <div className="mt-9 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat k="STAGES" v="8" />
        <Stat k="REAL VQE" v="H₂ STO-3G · QISKIT" />
        <Stat k="FOLDING" v="ESMFOLD · LIVE" />
        <Stat k="HALF-LIFE" v="UNCHANGED · HONEST" />
      </div>
    </section>
  )
}
