import { useEffect, useState } from 'react'
import { runPipeline, type PipelineResult, type QaoaResult } from '../api/client'
import VQEChart from './VQEChart'
import BindingSites from './BindingSites'
import ProteinOutput from './ProteinOutput'
import QaoaSearch from './QaoaSearch'
import HandoffExport from './HandoffExport'

type Stage = 'running' | 'done' | 'error'

interface Props {
  atomId: string
  onReset: () => void
}

export default function PipelineRunner({ atomId, onReset }: Props) {
  const [stage, setStage] = useState<Stage>('running')
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [qaoaResult, setQaoaResult] = useState<QaoaResult | null>(null)

  useEffect(() => {
    runPipeline(atomId)
      .then(r => { setResult(r); setStage('done') })
      .catch(e => { setError(e.message); setStage('error') })
  }, [atomId])

  return (
    <div>
      <div className="flex items-center gap-4 mb-8">
        <button onClick={onReset} className="text-halos-muted hover:text-halos-text text-sm font-mono">
          ← Back
        </button>
        <h1 className="font-serif text-3xl font-light">
          Pipeline: <span className="text-halos-accent">{atomId.toUpperCase()}</span>
        </h1>
      </div>

      {stage === 'running' && (
        <div className="space-y-2">
          <div className="text-halos-muted text-sm font-mono">Running VQE...</div>
          <div className="text-xs text-halos-muted">
            Qiskit StatevectorEstimator + COBYLA optimizer. H2 takes ~20s. LiH takes ~30s.
          </div>
          <div className="h-1 bg-halos-border rounded overflow-hidden">
            <div className="h-full bg-halos-accent animate-pulse w-1/2" />
          </div>
        </div>
      )}

      {stage === 'error' && (
        <div className="text-halos-error font-mono text-sm border border-halos-error rounded p-4">
          Error: {error}
        </div>
      )}

      {stage === 'done' && result && (
        <div className="space-y-8">
          <VQEChart
            history={result.convergence_history}
            groundStateEnergy={result.ground_state_energy}
            knownGroundState={result.known_ground_state}
          />
          <BindingSites
            geometry={result.geometry}
            coordinationNumber={result.coordination_number}
            orbitalOccupancies={result.orbital_occupancies}
            emptyOrbitalIndices={result.empty_orbital_indices}
          />
          <ProteinOutput
            sequence={result.sequence}
            fasta={result.fasta}
            bindingResidues={result.binding_residues}
            bindingPositions={result.binding_positions}
            bindingConfidence={result.binding_confidence}
          />
          <QaoaSearch
            bindingStrength={result.binding_confidence}
            coordinationNumber={result.coordination_number}
            atomId={result.atom_id}
            geometry={result.geometry}
            onResult={setQaoaResult}
          />
          <HandoffExport
            handoffJson={result.handoff_json}
            atomId={result.atom_id}
            qaoaBlock={qaoaResult?.handoff_block ?? null}
          />
        </div>
      )}
    </div>
  )
}
