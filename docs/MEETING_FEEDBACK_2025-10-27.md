# Meeting Feedback and Implementation Plan - October 27, 2025

## Meeting Summary

This document captures feedback from the October 27, 2025 meeting regarding the Knowledge Synthesis platform, focusing on ingestion improvements and user interface enhancements.

## Key Feedback Points

### 1. Domain-Agnostic Extraction (CRITICAL)

**Issue**: The extraction prompt was biased toward biomedical domains with hardcoded entity types (Drug, Gene, Protein, Disease, etc.).

**Problem**:
- Limits platform to biomedical research only
- Contradicts the goal of multidisciplinary knowledge synthesis
- Computer science, physics, social science papers cannot be properly processed
- Creates artificial constraints on concept classification

**Solution Implemented**:
- ✅ Removed all domain-specific entity type examples
- ✅ Changed to generic, context-appropriate type classification
- ✅ Updated prompt to use descriptive types based on function (Algorithm, Theory, Metric, Framework, Process, etc.)
- ✅ Made "Concept" the fallback type for uncertain classifications

**File Modified**: `backendAndUI/python_worker/app/services/openai_extract.py`

### 2. Natural Extraction Balance

**Issue**: Prompt forced 50% negative relationships, creating artificial balance.

**Problem**:
- Not all scientific texts have equal positive/negative findings
- Forcing a ratio can lead to hallucinated or forced extractions
- Natural distribution should reflect the actual content

**Solution Implemented**:
- ✅ Removed the 50% negative relationship requirement
- ✅ Changed to "extract negative relationships when EXPLICITLY stated"
- ✅ Removed forced balance instructions
- ✅ Let extraction reflect natural distribution in text

**File Modified**: `backendAndUI/python_worker/app/services/openai_extract.py`

### 3. Consistent Terminology

**Issue**: Mixing terms "entity", "subject", "object", and "concept" inconsistently.

**Problem**:
- Creates confusion between implementation and specification
- Makes documentation unclear
- Users don't know what terminology to use

**Solution Implemented**:
- ✅ Updated extraction prompt to use "concept" consistently
- ✅ Changed significance scores to reference "concept" not "entity"
- ✅ Updated dry-run examples to be domain-agnostic

**Remaining Work**:
- Update UI labels to use "concept" consistently
- Update API documentation
- Update database schema documentation

### 4. Flexible Graph Context Selection

**Issue**: Context selection only works with manually selected individual nodes (Shift+Click).

**Problem**:
- Too granular - users want to select by document, relationship type, or filtered view
- Not intuitive - shift-click is not discoverable
- Limited - cannot select edges/relationships
- Doesn't persist across tabs

**Required Implementation**:
- [ ] Add document-based selection (select all concepts from a paper)
- [ ] Add relationship-type selection (select all "inhibits" relationships)
- [ ] Implement edge/relationship selection in graph viewer
- [ ] Add "use current filtered view as context" option
- [ ] Fix state persistence across tabs
- [ ] Make selection mechanism more visible/intuitive

**Files to Modify**:
- `backendAndUI/python_worker/app/routes/main_ui.py` (UI)
- JavaScript graph interaction code
- Context building logic in extraction service

### 5. User-Controlled Context Intent

**Issue**: Graph context prompt assumes user wants to find agreements, disagreements, and additions.

**Problem**:
- Removes user agency - they cannot specify their research goal
- May want ONLY conflicts, or ONLY complementary findings
- May want to explicitly exclude certain concepts
- Research intent varies by use case

**Required Implementation**:
- [ ] Add checkboxes for context intent:
  - ☐ Complements (supports existing knowledge)
  - ☐ Conflicts (contradicts existing knowledge)
  - ☐ Extends (adds new related knowledge)
  - ☐ Distinct from (unrelated to existing knowledge)
- [ ] Update prompt generation to incorporate user's selected intent
- [ ] Make default behavior neutral (no assumptions)

**Files to Modify**:
- `backendAndUI/python_worker/app/routes/main_ui.py` (add UI controls)
- `backendAndUI/python_worker/app/services/openai_extract.py` (update prompt generation)
- `backendAndUI/python_worker/app/routes/ingest.py` (pass intent to extraction)

### 6. Re-Extraction from Existing Documents

**Issue**: No way to re-extract from a document already in the database.

**Problem**:
- First extraction may not capture everything
- User may want to focus on specific aspects after initial review
- Cannot iteratively refine extraction
- Must re-upload same PDF (wasteful, confusing)

**Required Implementation**:
- [ ] Add "existing documents" dropdown in ingestion tab
- [ ] Detect duplicate documents by title or hash
- [ ] Allow re-extraction with different parameters
- [ ] Preserve document ID (don't create duplicates)
- [ ] Add "elaborate on existing extraction" option
- [ ] Show extraction history for each document

**Files to Modify**:
- `backendAndUI/python_worker/app/routes/ingest.py`
- `backendAndUI/python_worker/app/routes/main_ui.py`
- `backendAndUI/python_worker/app/services/graph_write.py`

### 7. Relationship-Centric Filtering

**Issue**: Filtering shows relationship instances (X→Y) but not relationship types.

**Problem**:
- User may care about relationship TYPE (all "inhibits" relationships)
- Current UI requires hovering to see relationship type
- Cannot easily filter by relationship type
- Relationship is as important as concepts in knowledge graphs

**Required Implementation**:
- [ ] Add relationship type list in filtering panel
- [ ] Show count of instances per relationship type
- [ ] Allow filtering by relationship type
- [ ] Make relationship types first-class citizens in UI
- [ ] Add relationship type to search/query interface

**Files to Modify**:
- `backendAndUI/python_worker/app/routes/main_ui.py`
- Graph visualization JavaScript
- Query endpoints to support relationship type filtering

### 8. Minor UI Bugs

**Issue**: Various UI inconsistencies and bugs.

**Problems Identified**:
- Document count shows "0 documents, 0 entities" incorrectly
- Graph selection doesn't persist when switching tabs
- Selected nodes not visually clear (color changes subtle)
- Filtering doesn't refresh graph view correctly

**Required Fixes**:
- [ ] Fix document/entity count display
- [ ] Implement proper state management across tabs
- [ ] Improve selected node visual feedback
- [ ] Fix graph refresh after filtering

## Implementation Priority

### Phase 1: Critical Fixes (Completed)
1. ✅ Remove domain-specific biases from extraction
2. ✅ Remove forced negative relationship ratio
3. ✅ Update terminology to use "concept" consistently
4. ✅ Make graph context prompt neutral

### Phase 2: Context Selection (High Priority)
1. [ ] Implement edge/relationship selection
2. [ ] Add document-based context selection
3. [ ] Add relationship-type context selection
4. [ ] Fix state persistence across tabs
5. [ ] Add user-controlled context intent options

### Phase 3: Re-Extraction (High Priority)
1. [ ] Add existing document selection
2. [ ] Implement duplicate detection
3. [ ] Add re-extraction with context
4. [ ] Show extraction history

### Phase 4: Relationship-Centric Features (Medium Priority)
1. [ ] Add relationship type filtering
2. [ ] Show relationship type list with counts
3. [ ] Improve relationship visibility in UI

### Phase 5: UI Polish (Lower Priority)
1. [ ] Fix document/entity count display
2. [ ] Improve selection visual feedback
3. [ ] Fix graph refresh issues

## Design Principles Emphasized

1. **Domain Agnostic**: Platform must work for ANY scientific discipline
2. **User Agency**: Don't assume user intent - let them specify
3. **Flexibility**: Support multiple ways to select context (documents, concepts, relationships)
4. **Relationship Equality**: Relationships are as important as concepts
5. **Iterative Refinement**: Support re-extraction and elaboration
6. **Clear Communication**: Use consistent terminology throughout

## Communication Protocol

**Key Takeaway**: Before implementing significant changes:
1. Write a short proposal
2. Share with Dr. Kendal/Dr. Akbar
3. Get feedback before implementation
4. Avoid implementing then debugging

This prevents:
- Wasted implementation effort
- Domain-specific biases
- Misaligned features
- Terminology confusion

## Next Steps

1. Review this document with team
2. Prioritize Phase 2 implementations
3. Create detailed design docs for context selection UI
4. Implement and test incrementally
5. Get feedback before moving to next phase

## Files Modified (Phase 1)

### Backend
- `backendAndUI/python_worker/app/services/openai_extract.py`
  - Updated `_create_prompt()` function
  - Updated `_fake_extract()` examples
  - Modified graph context prompt generation

### Frontend
- `node-server/public/index.html`
  - Added comprehensive context configuration modal
  - Updated ingestion UI
  
- `node-server/public/js/ingestion/ingestion.js`
  - Added context configuration state management
  - Implemented `getGraphContextText()` with edge support
  - Added intent instruction generation
  
- `node-server/public/js/viewing/graph-viewer.js`
  - Implemented Shift+Click edge selection
  - Updated clearSelection to handle edges
  
- `node-server/public/js/viewing/cytoscape-config.js`
  - Added multi-selected edge styling (purple)
  
- `node-server/public/js/state.js`
  - Added `selectedEdges` to global state

## Testing Checklist

### Domain Agnosticism
- [ ] Test extraction with computer science paper
- [ ] Test extraction with physics paper
- [ ] Test extraction with social science paper
- [ ] Verify no biomedical bias in entity types
- [ ] Verify natural negative/positive ratio

### Context Configuration
- [ ] Test opening context configuration modal
- [ ] Test selecting nodes (Shift+Click) and using as context
- [ ] Test selecting edges (Shift+Click) and using as context
- [ ] Test combining nodes + edges as context
- [ ] Test document selection as context
- [ ] Test filtered view as context
- [ ] Test all four intent options (complement, conflict, extend, distinct)
- [ ] Verify selected relationships appear in context with "Focus on these" label
- [ ] Verify context text includes intent instructions
- [ ] Test apply/clear/cancel functionality

### Integration
- [ ] Test full ingestion workflow with node context
- [ ] Test full ingestion workflow with edge context
- [ ] Test full ingestion workflow with mixed context
- [ ] Verify extraction respects user intent
- [ ] Verify terminology consistency across UI

---

**Document Created**: October 27, 2025
**Meeting Date**: October 27, 2025
**Status**: Phase 1 Complete, Phase 2-5 Pending
