export interface StageMeta {
  n: string
  key: string
  title: string
  nav: string
}

// The vertical pipeline. Stage 05 (structure prediction / ESMFold) is the new,
// genuinely-simulatable bio step inserted between protein search and the handoff.
export const STAGES: StageMeta[] = [
  { n: '01', key: 'target', title: 'Target selection', nav: 'SELECT SPECIES' },
  { n: '02', key: 'vqe', title: 'Variational Quantum Eigensolver', nav: 'ELECTRONIC STRUCTURE' },
  { n: '03', key: 'binding', title: 'Binding hotspot map', nav: 'HOTSPOT INTERPRETATION' },
  { n: '04', key: 'protein', title: 'Protein candidate search', nav: 'RULE-BASED + QAOA' },
  { n: '05', key: 'fold', title: 'Structure prediction', nav: 'ESMFOLD · pLDDT' },
  { n: '06', key: 'handoff', title: 'Bio handoff payload', nav: 'QC → BIO JSON' },
  { n: '07', key: 'chassis', title: 'Bacterial chassis design', nav: 'D. RADIODURANS' },
  { n: '08', key: 'biomin', title: 'Biomineralization', nav: 'IMMOBILIZATION DEMO' },
]
