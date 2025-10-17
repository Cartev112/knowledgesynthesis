# Context-Aware Extraction Feature

## Overview
Implemented context-aware knowledge extraction that allows users to select a subgraph from the viewer and use it as context for new document ingestion. The AI will specifically identify relationships that **agree with**, **disagree with**, or **add new knowledge** compared to the existing graph.

## Key Features

### 1. Graph Context Selection
- **Checkbox on Ingestion Page**: "Use Selected Graph as Context"
- **Visual Feedback**: Shows count of selected nodes when enabled
- **Help Text**: Guides users on how to use the feature
- **Status Indicator**: Blue banner showing "Context Ready: X nodes selected"

### 2. Intelligent Context Formatting
- Selected subgraph is converted to structured text format
- Includes:
  - Entity list with types and significance scores
  - Relationship list with predicates, status, and evidence
  - Verification markers for confirmed relationships
  - Truncated original text for context

### 3. Context-Aware AI Prompt
The AI receives specialized instructions to:
- **Find Agreements** (✅): Relationships that support/confirm existing knowledge
- **Find Disagreements** (❌): Relationships that contradict existing knowledge
- **Find New Knowledge** (🆕): Novel entities or connections

### 4. Improved UI Layout
- Symmetric two-column layout for ingestion form
- Graph context checkbox positioned at top of right column
- Maintains visual balance between document source and extraction settings

## Implementation Details

### Frontend Changes (`main_ui.py`)

#### New UI Elements
```html
<div class="form-group">
  <label style="display: flex; align-items: center;">
    <input type="checkbox" id="use-graph-context" onchange="toggleGraphContext()" />
    <span>Use Selected Graph as Context</span>
  </label>
  <div class="help-text" id="graph-context-help">
    Select nodes in the Viewer (Shift+Click), then check this box...
  </div>
  <div id="graph-context-status" style="display: none;">
    <strong>📊 Context Ready:</strong> <span id="graph-context-count">0</span> nodes selected
  </div>
</div>
```

#### JavaScript Functions

**`toggleGraphContext()`**
- Validates that nodes are selected
- Shows/hides status indicator
- Updates help text color and content
- Prevents checkbox if no nodes selected

**`getGraphContextText()`**
- Fetches subgraph data via `/query/subgraph` endpoint
- Converts graph data to structured text format
- Returns formatted context string with markers:
  - `=== EXISTING KNOWLEDGE GRAPH CONTEXT ===`
  - Entity and relationship lists
  - `=== END CONTEXT ===`

**`ingestDocument()` (Modified)**
- Checks if graph context checkbox is enabled
- Calls `getGraphContextText()` to fetch context
- Prepends graph context to user's extraction context
- Handles errors gracefully

### Backend Changes

#### New Endpoint: `/query/subgraph` (`query.py`)
```python
@router.post("/subgraph")
def get_subgraph(request: dict):
    """Get the subgraph for a set of node IDs."""
```

**Cypher Query:**
```cypher
MATCH (n:Entity)
WHERE coalesce(n.id, n.name, elementId(n)) IN $node_ids
WITH collect(n) as nodes
UNWIND nodes as n1
UNWIND nodes as n2
OPTIONAL MATCH (n1)-[r]->(n2)
WITH nodes, collect(DISTINCT r) as rels
RETURN nodes, relationships
```

**Returns:**
- List of nodes with id, label, type, significance
- List of relationships between those nodes
- Full metadata for context generation

#### Enhanced Prompt Engineering (`openai_extract.py`)

**Context Detection:**
- Checks for `=== EXISTING KNOWLEDGE GRAPH CONTEXT ===` marker
- Separates user focus from graph context
- Applies different prompt strategies

**Context-Aware Instructions:**
```
🎯 CONTEXT-AWARE EXTRACTION INSTRUCTIONS:
Based on the existing knowledge graph above, analyze the new document text to find relationships that:

1. ✅ AGREE WITH existing knowledge - relationships that support, confirm, or validate what's already in the graph
   Example: If graph shows 'Drug A inhibits Protein B', find evidence that confirms this

2. ❌ DISAGREE WITH existing knowledge - relationships that contradict or challenge existing relationships
   Example: If graph shows 'Drug A inhibits Protein B', but document says 'Drug A activates Protein B'
   Use 'does_not_' prefix for contradictions (e.g., 'does_not_inhibit' if expected to inhibit)

3. 🆕 ADD NEW knowledge - relationships involving entities not in the existing graph or new connections between existing entities
   Example: New drug targets, novel mechanisms, or interactions not previously documented

PRIORITIZE:
- Relationships that involve entities mentioned in the existing graph
- Contradictory evidence (these are scientifically valuable!)
- Supporting evidence for existing relationships
- New entities that interact with existing ones

Extract both positive and negative relationships. Aim for ~50% negative relationships when appropriate.
```

## User Workflow

### Step-by-Step Usage

1. **Select Nodes in Viewer**
   - Switch to "Viewing" tab
   - Shift+Click on nodes to select them (multi-select)
   - Selected nodes highlight in purple
   - Selection count shows at bottom

2. **Switch to Ingestion Tab**
   - Navigate to "Ingestion" tab
   - Selected nodes remain in memory

3. **Enable Graph Context**
   - Check "Use Selected Graph as Context" checkbox
   - System validates nodes are selected
   - Blue status banner appears: "Context Ready: X nodes selected"
   - Help text turns green with confirmation message

4. **Upload Document**
   - Upload PDF or paste text as normal
   - Optionally add extraction context (user focus)
   - Click "Extract Knowledge"

5. **Context-Aware Extraction**
   - System fetches selected subgraph
   - Converts to text format
   - Prepends to extraction context
   - AI analyzes document with graph context
   - Extracts agreements, disagreements, and new knowledge

6. **Review Results**
   - New relationships are added to graph
   - Can review in Review Queue
   - Contradictions are marked with `does_not_` prefix
   - Supporting evidence strengthens existing relationships

## Example Context Format

```
=== EXISTING KNOWLEDGE GRAPH CONTEXT ===

This subgraph contains 5 entities and 7 relationships:

ENTITIES:
- Vemurafenib (Drug) [Significance: 4/5]
- BRAF V600E (GeneMutation) [Significance: 5/5]
- MEK (Protein) [Significance: 3/5]
- ERK (Protein) [Significance: 3/5]
- Melanoma (Disease) [Significance: 5/5]

RELATIONSHIPS:
- Vemurafenib → [targets] → BRAF V600E ✓ [Significance: 5/5]
  Evidence: "Vemurafenib targets the BRAF V600E mutation in melanoma."
- BRAF V600E → [activates] → MEK [Significance: 4/5]
  Evidence: "The V600E mutation leads to constitutive activation of MEK..."
- MEK → [activates] → ERK [Significance: 4/5]
- Vemurafenib → [treats] → Melanoma ✓ [Significance: 5/5]
- BRAF V600E → [causes] → Melanoma [Significance: 5/5]

=== END CONTEXT ===
```

## Benefits

### 1. Literature Integration
- Systematically compare new papers against existing knowledge
- Identify confirmatory evidence
- Detect contradictions and controversies
- Build comprehensive understanding

### 2. Hypothesis Testing
- Test whether new studies support or refute existing relationships
- Track evolution of scientific understanding
- Identify areas of consensus vs. debate

### 3. Gap Analysis
- Find what's missing from current knowledge graph
- Identify novel connections
- Discover emerging research areas

### 4. Quality Assurance
- Cross-validate relationships across multiple sources
- Flag inconsistencies for expert review
- Build confidence through multiple confirmations

### 5. Efficient Curation
- Focus extraction on relevant entities
- Reduce noise from unrelated concepts
- Prioritize relationships that matter

## Technical Considerations

### Performance
- Subgraph query optimized for small to medium selections (< 100 nodes)
- Context text kept under 2000 characters for optimal AI performance
- Async fetching prevents UI blocking

### Error Handling
- Graceful fallback if subgraph fetch fails
- User-friendly error messages
- Checkbox auto-unchecks if validation fails

### Memory Management
- Selected nodes stored in global `selectedNodes` Set
- Persists across tab switches
- Cleared only on explicit user action

### Prompt Token Usage
- Graph context adds ~500-2000 tokens depending on subgraph size
- Context-aware instructions add ~300 tokens
- Total overhead: ~800-2300 tokens per extraction
- Still well within GPT-4 context limits

## Future Enhancements

### Potential Improvements
1. **Visual Preview**: Show subgraph visualization before extraction
2. **Context Templates**: Save common subgraph selections for reuse
3. **Smart Filtering**: Auto-filter relationships by relevance to context
4. **Conflict Resolution**: Dedicated UI for resolving contradictions
5. **Confidence Scoring**: Adjust confidence based on agreement/disagreement
6. **Citation Linking**: Link new evidence to existing relationships
7. **Batch Processing**: Apply context to multiple documents
8. **Context History**: Track which contexts were used for each extraction

### Advanced Features
- **Semantic Similarity**: Find relationships semantically similar to context
- **Entity Linking**: Auto-link new entities to existing ones
- **Relationship Merging**: Combine evidence from multiple sources
- **Contradiction Dashboard**: Visualize all disagreements
- **Consensus Scoring**: Calculate agreement level across sources

## Testing Recommendations

### Test Scenarios

1. **Basic Functionality**
   - Select 3-5 nodes
   - Enable checkbox
   - Upload document
   - Verify context is included in extraction

2. **Agreement Detection**
   - Select nodes with known relationships
   - Upload document that confirms those relationships
   - Verify AI extracts confirmatory evidence

3. **Disagreement Detection**
   - Select nodes with specific relationships
   - Upload document that contradicts them
   - Verify AI uses `does_not_` prefix

4. **New Knowledge**
   - Select small subgraph
   - Upload document with novel entities
   - Verify new entities are extracted and linked

5. **Edge Cases**
   - No nodes selected → checkbox should prevent
   - Very large subgraph (50+ nodes) → performance test
   - Empty subgraph (isolated nodes) → should handle gracefully
   - Network error during fetch → should show error message

### Validation Checks
- ✅ Context text is properly formatted
- ✅ Graph data is correctly serialized
- ✅ AI prompt includes context-aware instructions
- ✅ Extracted relationships reference context entities
- ✅ Contradictions are properly marked
- ✅ UI updates correctly on checkbox toggle
- ✅ Error messages are user-friendly

## Files Modified

### Frontend
- `backendAndUI/python_worker/app/routes/main_ui.py`
  - Added checkbox UI element
  - Added `toggleGraphContext()` function
  - Added `getGraphContextText()` function
  - Modified `ingestDocument()` to include graph context

### Backend
- `backendAndUI/python_worker/app/routes/query.py`
  - Added `/query/subgraph` POST endpoint
  - Cypher query to fetch subgraph data

- `backendAndUI/python_worker/app/services/openai_extract.py`
  - Enhanced context detection logic
  - Added context-aware prompt instructions
  - Separated user focus from graph context

## Deployment Notes

- No database schema changes required
- No new dependencies needed
- Backward compatible with existing extractions
- Server restart required to apply changes
- No migration scripts needed

## Success Metrics

### Quantitative
- % of extractions using graph context
- Average subgraph size selected
- Number of agreements/disagreements found
- Extraction time with vs. without context

### Qualitative
- User feedback on feature usefulness
- Expert assessment of context-aware extractions
- Quality of contradiction detection
- Relevance of new knowledge discovered

---

**Status**: ✅ Implemented and Ready for Testing
**Version**: 1.0
**Date**: 2025-10-15




