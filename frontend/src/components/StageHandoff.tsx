import Stage from './Stage'
import type { PipelineResult, QaoaResult, FoldResult } from '../api/client'

interface Props {
  run: PipelineResult | null
  qaoa: QaoaResult | null
  fold: FoldResult | null
}

function Row({ k, v, on }: { k: string; v: string; on: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-halos-line py-2 font-mono text-xs">
      <span className={on ? 'text-halos-text' : 'text-halos-muted'}>{k}</span>
      <span className={on ? 'text-halos-ok' : 'text-halos-muted'}>{v}</span>
    </div>
  )
}

export default function StageHandoff({ run, qaoa, fold }: Props) {
  const download = () => {
    if (!run) return
    const parsed = JSON.parse(run.handoff_json)
    if (qaoa) {
      parsed.qaoa_search = qaoa.handoff_block
      parsed.primary_recommendation = 'qaoa_search'
    }
    if (fold) {
      parsed.structure_prediction = {
        method: fold.source,
        mean_plddt: fold.mean_plddt,
        n_residues: fold.n_residues,
        sequence: fold.sequence,
        note: 'pLDDT is fold confidence, not binding or in-cell function.',
      }
    }
    const blob = new Blob([JSON.stringify(parsed, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `HALOS_handoff_${run.atom_id}_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Stage
      n="06"
      id="stage-handoff"
      title="Bio handoff payload"
      status={run ? 'READY' : 'WAITING ON SELECTION'}
      tone={run ? 'done' : 'idle'}
      guardrail="THE SINGLE JSON CONTRACT BETWEEN QC AND BIO · VERSIONED SCHEMA"
    >
      {!run && <div className="font-mono text-xs text-halos-muted">// awaiting peptide selection</div>}

      {run && (
        <div className="max-w-xl space-y-5">
          <p className="text-sm leading-relaxed text-halos-dim">
            The single JSON contract handed to the bio team. They consume it without further input
            from QC — FASTA, coordination geometry, the quantum-search recommendation, and the fold.
          </p>
          <div>
            <Row k="VQE energy + binding map" v="INCLUDED" on />
            <Row k="Designed FASTA candidate" v="INCLUDED" on />
            <Row k="QAOA recommendation (primary)" v={qaoa ? 'INCLUDED' : 'run stage 04'} on={!!qaoa} />
            <Row k="ESMFold structure + pLDDT" v={fold ? `pLDDT ${fold.mean_plddt}` : 'run stage 05'} on={!!fold} />
            <Row k="Prime-editing next steps" v="INCLUDED" on />
          </div>
          <button
            onClick={download}
            className="bg-halos-accent px-6 py-3 font-mono text-xs tracking-widest text-halos-bg transition-opacity hover:opacity-90"
          >
            DOWNLOAD HANDOFF PACKAGE ↓
          </button>
        </div>
      )}
    </Stage>
  )
}
