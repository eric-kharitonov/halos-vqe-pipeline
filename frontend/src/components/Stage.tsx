import type { ReactNode } from 'react'

type Tone = 'idle' | 'active' | 'running' | 'done' | 'blocked'

const TONE: Record<Tone, string> = {
  idle: 'text-halos-muted border-halos-faint',
  active: 'text-halos-accent border-halos-accent/40',
  running: 'text-halos-warn border-halos-warn/40',
  done: 'text-halos-ok border-halos-ok/40',
  blocked: 'text-halos-error border-halos-error/40',
}

interface Props {
  n: string
  title: string
  status: string
  tone?: Tone
  guardrail?: string
  id?: string
  children: ReactNode
}

export default function Stage({ n, title, status, tone = 'idle', guardrail, id, children }: Props) {
  return (
    <section id={id} className="scroll-mt-20 border-b border-halos-line py-12">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-baseline gap-4">
          <span className="font-mono text-[11px] tracking-widest text-halos-muted">STAGE / {n}</span>
          <h2 className="font-serif text-3xl font-light text-halos-text">{title}</h2>
        </div>
        <span className={`shrink-0 rounded-sm border px-2 py-1 font-mono text-[10px] tracking-widest ${TONE[tone]}`}>
          {status}
        </span>
      </div>
      {guardrail && (
        <div className="mb-6 border-l-2 border-halos-gold/40 pl-3 font-mono text-[10px] uppercase leading-relaxed tracking-wider text-halos-muted">
          {guardrail}
        </div>
      )}
      {children}
    </section>
  )
}
