import { STAGES } from '../lib/stages'

interface Props {
  doneKeys: Set<string>
  activeKey: string | null
}

export default function PipelineNav({ doneKeys, activeKey }: Props) {
  return (
    <aside className="hidden w-60 shrink-0 lg:block">
      <div className="sticky top-20 space-y-6">
        <div>
          <div className="label mb-3">// PIPELINE</div>
          <ol className="space-y-2.5">
            {STAGES.map(s => {
              const done = doneKeys.has(s.key)
              const active = activeKey === s.key
              return (
                <li key={s.key}>
                  <a href={`#stage-${s.key}`} className="group flex items-start gap-3">
                    <span
                      className={`mt-0.5 font-mono text-[10px] ${
                        done ? 'text-halos-ok' : active ? 'text-halos-accent' : 'text-halos-faint'
                      }`}
                    >
                      {done ? '●' : active ? '◆' : '○'} {s.n}
                    </span>
                    <span className="flex-1">
                      <span
                        className={`block text-xs ${
                          active ? 'text-halos-text' : 'text-halos-dim'
                        } group-hover:text-halos-text`}
                      >
                        {s.title}
                      </span>
                      <span className="label block">{s.nav}</span>
                    </span>
                  </a>
                </li>
              )
            })}
          </ol>
        </div>

        <div className="border-t border-halos-line pt-5">
          <div className="label mb-2 text-halos-gold/70">SCIENTIFIC GUARDRAIL</div>
          <p className="text-[11px] leading-relaxed text-halos-muted">
            Ion chemistry &amp; oxidation state govern binding, not radioactivity itself. Protein
            design here is a rule-based + QAOA stand-in; AlphaFold/RFdiffusion are downstream.
            Folding is real (ESMFold); chassis &amp; biomineralization are conceptual, not wet-lab.
          </p>
        </div>
      </div>
    </aside>
  )
}
