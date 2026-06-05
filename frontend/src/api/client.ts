export interface AtomMeta {
  id: string
  symbol: string
  name: string
  num_qubits: number
  coordination_class: string
  typical_coordination_number: number
  donor_preference: string[]
  is_placeholder: boolean
  notes: string
}

export interface PipelineResult {
  atom_id: string
  ground_state_energy: number
  known_ground_state: number | null
  convergence_history: number[]
  num_iterations: number
  orbital_occupancies: number[]
  empty_orbital_indices: number[]
  coordination_number: number
  geometry: string
  binding_residues: string[]
  binding_positions: number[]
  sequence: string
  fasta: string
  binding_confidence: number
  handoff_json: string
}

export interface QaoaCandidate {
  sequence: string
  cost: number
  probability: number
}

export interface QaoaResult {
  n_residues: number
  n_qubits: number
  reps: number
  search_space_size: number
  alphabet: string[]
  ranked_candidates: QaoaCandidate[]
  best_sequence: string
  best_cost: number
  brute_force_optimum: string
  brute_force_cost: number
  found_optimum: boolean
  convergence_history: number[]
  recommended_sequence: string
  recommended_fasta: string
  handoff_block: Record<string, unknown>
}

const BASE = '/api'

export async function fetchAtoms(): Promise<AtomMeta[]> {
  const r = await fetch(`${BASE}/atoms`)
  if (!r.ok) throw new Error('Failed to load atoms')
  return r.json()
}

export async function runPipeline(atomId: string): Promise<PipelineResult> {
  const r = await fetch(`${BASE}/pipeline/run/${atomId}`)
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? 'Pipeline failed')
  }
  return r.json()
}

export async function runQaoaSearch(
  bindingStrength: number,
  nResidues: number,
  atomId: string,
  geometry: string,
): Promise<QaoaResult> {
  const params = new URLSearchParams({
    binding_strength: String(bindingStrength),
    n_residues: String(nResidues),
    atom_id: atomId,
    geometry,
  })
  const r = await fetch(`${BASE}/pipeline/qaoa-search?${params}`)
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? 'QAOA search failed')
  }
  return r.json()
}
