/**
 * Global Application State
 */
export const state = {
  currentUser: null,
  cy: null,
  selectedNodes: new Set(),
  selectedEdges: new Set(),
  manualEdgeNodes: { node1: null, node2: null },
  graphInitialized: false,
  indexVisible: false,
  activeDocuments: new Set(),
  indexData: { nodes: [], edges: [], documents: [] },
  viewportMode: false,
  isLoading: false,
  loadedNodes: new Set(),
  documents: [],
  // Filter states to persist across tabs
  filterStates: {
    viewFilter: 'all',
    typeFilter: '',
    searchTerm: '',
    verifiedOnly: false
  }
};
