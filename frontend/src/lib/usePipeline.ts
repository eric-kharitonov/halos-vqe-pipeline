import { useCallback, useEffect, useState } from 'react'
import {
  fetchAtoms,
  runPipeline,
  runQaoaSearch,
  foldSequence,
  primeEdit,
  type AtomMeta,
  type PipelineResult,
  type QaoaResult,
  type FoldResult,
  type PrimeEditResult,
} from '../api/client'

export type Status = 'idle' | 'running' | 'done' | 'error'

export interface LogEntry {
  time: string
  text: string
}

function now(): string {
  return new Date().toLocaleTimeString('en-GB')
}

export function usePipeline() {
  const [atoms, setAtoms] = useState<AtomMeta[]>([])
  const [atomId, setAtomId] = useState<string | null>(null)

  const [run, setRun] = useState<PipelineResult | null>(null)
  const [runStatus, setRunStatus] = useState<Status>('idle')
  const [runError, setRunError] = useState<string | null>(null)

  const [qaoa, setQaoa] = useState<QaoaResult | null>(null)
  const [qaoaStatus, setQaoaStatus] = useState<Status>('idle')

  const [fold, setFold] = useState<FoldResult | null>(null)
  const [foldStatus, setFoldStatus] = useState<Status>('idle')
  const [foldError, setFoldError] = useState<string | null>(null)

  const [edit, setEdit] = useState<PrimeEditResult | null>(null)
  const [editStatus, setEditStatus] = useState<Status>('idle')

  const [log, setLog] = useState<LogEntry[]>([])
  const addLog = useCallback((text: string) => {
    setLog(prev => [{ time: now(), text }, ...prev].slice(0, 40))
  }, [])

  useEffect(() => {
    fetchAtoms().then(setAtoms).catch(() => setAtoms([]))
  }, [])

  const atom = atoms.find(a => a.id === atomId)

  const selectAtom = useCallback((id: string) => {
    const a = atoms.find(x => x.id === id)
    if (!a || a.is_locked) return
    setAtomId(id)
    setRun(null); setRunStatus('idle'); setRunError(null)
    setQaoa(null); setQaoaStatus('idle')
    setFold(null); setFoldStatus('idle'); setFoldError(null)
    addLog(`target selected · ${a.symbol} (${a.badge})`)
  }, [atoms, addLog])

  const doRun = useCallback(() => {
    if (!atom) return
    setRunStatus('running'); setRunError(null)
    addLog(atom.runs_vqe ? `VQE started · ${atom.symbol}` : `downstream design · ${atom.symbol} (literature map)`)
    runPipeline(atom.id)
      .then(r => {
        setRun(r); setRunStatus('done')
        addLog(
          r.map_source === 'vqe'
            ? `VQE converged · E=${r.ground_state_energy?.toFixed(5)} Ha · ${r.coordination_number} sites`
            : `literature map · ${r.coordination_number} sites · ${r.geometry}`,
        )
      })
      .catch(e => { setRunError(e.message); setRunStatus('error'); addLog(`error · ${e.message}`) })
  }, [atom, addLog])

  const doQaoa = useCallback(() => {
    if (!run) return
    setQaoaStatus('running')
    addLog('QAOA search started')
    const nRes = Math.min(run.coordination_number, 3)
    runQaoaSearch(run.binding_confidence, nRes, run.atom_id, run.geometry)
      .then(r => {
        setQaoa(r); setQaoaStatus('done')
        addLog(`QAOA done · ${r.best_sequence} · ${r.found_optimum ? 'reached optimum' : 'approximate'}`)
      })
      .catch(() => setQaoaStatus('error'))
  }, [run, addLog])

  const doFold = useCallback(() => {
    if (!run) return
    setFoldStatus('running'); setFoldError(null)
    addLog('ESMFold structure prediction started')
    foldSequence(run.foldable_construct)
      .then(r => { setFold(r); setFoldStatus('done'); addLog(`fold complete · mean pLDDT ${r.mean_plddt}`) })
      .catch(e => { setFoldError(e.message); setFoldStatus('error'); addLog(`fold failed · ${e.message}`) })
  }, [run, addLog])

  const doPrimeEdit = useCallback(() => {
    if (!run) return
    setEditStatus('running')
    addLog('prime-edit design started')
    // Edit the gene for the deployable construct (the same protein we folded).
    primeEdit(run.foldable_construct)
      .then(r => { setEdit(r); setEditStatus('done'); addLog(`pegRNA designed · ${r.gene_length_bp} bp gene · ${r.gc_content}% GC`) })
      .catch(() => setEditStatus('error'))
  }, [run, addLog])

  const reset = useCallback(() => {
    setAtomId(null)
    setRun(null); setRunStatus('idle'); setRunError(null)
    setQaoa(null); setQaoaStatus('idle')
    setFold(null); setFoldStatus('idle'); setFoldError(null)
    setEdit(null); setEditStatus('idle')
    addLog('pipeline reset')
  }, [addLog])

  return {
    atoms, atom, atomId, selectAtom,
    run, runStatus, runError, doRun,
    qaoa, qaoaStatus, doQaoa,
    fold, foldStatus, foldError, doFold,
    edit, editStatus, doPrimeEdit,
    log, reset,
  }
}
