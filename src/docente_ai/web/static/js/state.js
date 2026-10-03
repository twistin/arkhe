// Módulo local: responsabilidad separada sin alterar el contenido.

export const store = {
  state: null,
  modelStatus: null,
  selected: localStorage.getItem('enjambre-subject') || '',
  selectedPeriod: '',
  tab: 'all',
  query: '',
  currentRun: null,
  drafts: {},
  chosenFiles: [],
  knownJobs: new Map(),
  polling: false,
  toastTimer: null,
  monitorTimer: null,
  connectionLost: false,
  isClosed: false,
  selectedRunStats: null
};
export const view = () => ['biblioteca', 'asistente', 'propuestas', 'diario', 'ajustes'].includes(location
  .hash.slice(1)) ? location.hash.slice(1) : 'biblioteca';
export const subjectName = id => store.state.config.subjects.find(s => s.id === id)?.name || 'Sin materia';
export const readyDocs = subject => store.state.documents.filter(d => d.enabled && d.indexed && (!subject || d
  .shared || d.subjects.includes(subject)));
export const draft = (form, key, fallback = '') => store.drafts[form]?.[key] ?? fallback;
