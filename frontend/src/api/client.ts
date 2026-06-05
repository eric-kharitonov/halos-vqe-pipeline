export interface AtomMeta {
  id: string
  symbol: string
  name: string
  tier: string                 // real_vqe | precomputed | toy | proxy | locked
  badge: string                // REAL VQE | PRECOMPUTED | TOY | PROXY | LOCKED
  num_qubits: number
  qubits_are_estimate: boolean
  electrons: number
  coordination_class: string
  typical_coordination_number: number
  donor_preference: string[]
  known_ground_state_hartree: number | null
  runs_vqe: boolean
  is_downstream_only: boolean
  is_locked: boolean
  notes: string
}

export interface PipelineResult {
  atom_id: string
  tier: string
  map_source: string           // "vqe" | "literature"
  ground_state_energy: number | null
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
  foldable_construct: string
  foldable_binding_positions: number[]
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

export interface FoldResult {
  sequence: string
  n_residues: number
  mean_plddt: number
  per_residue_plddt: number[]
  pdb: string
  source: string
}

export interface PrimeEditResult {
  locus_name: string
  protein: string
  gene_dna: string
  gene_length_bp: number
  gc_content: number
  spacer: string
  pam: string
  pbs: string
  rtt: string
  before: string
  after: string
  insert_index: number
}

const BASE = '/api'

// Default request budget. ESMFold can legitimately take minutes (server retries a flaky
// public endpoint), so folding overrides this with a much larger ceiling.
const DEFAULT_TIMEOUT_MS = 30_000

async function getJson<T>(path: string, timeoutMs: number = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const r = await fetch(`${BASE}${path}`, { signal: controller.signal })
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(err.detail ?? `Request failed (${r.status})`)
    }
    return await r.json()
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s — is the backend running?`)
    }
    throw e
  } finally {
    clearTimeout(timer)
  }
}

export function fetchAtoms(): Promise<AtomMeta[]> {
  return getJson<AtomMeta[]>('/atoms')
}

export function runPipeline(atomId: string): Promise<PipelineResult> {
  return getJson<PipelineResult>(`/pipeline/run/${atomId}`)
}

export function runQaoaSearch(
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
  return getJson<QaoaResult>(`/pipeline/qaoa-search?${params}`)
}

export function foldSequence(sequence: string): Promise<FoldResult> {
  const params = new URLSearchParams({ sequence })
  // ESMFold's public endpoint retries server-side and can run several minutes on a novel
  // (uncached) sequence; give it a generous ceiling rather than hanging forever.
  return getJson<FoldResult>(`/pipeline/fold?${params}`, 300_000)
}

export function primeEdit(protein: string): Promise<PrimeEditResult> {
  const params = new URLSearchParams({ protein })
  return getJson<PrimeEditResult>(`/pipeline/prime-edit?${params}`)
}
