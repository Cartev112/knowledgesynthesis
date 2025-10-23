# AI Query Tab Implementation

## Overview
Replaced the Query Builder tab with a beautiful AI Query interface that connects to the Neo4j Aura Agent backend for natural language querying of the knowledge graph.

## Files Created/Modified

### New Files
1. **`node-server/public/css/ai-query.css`**
   - Modern chat-like UI with gradient headers
   - Responsive design with sidebar and main chat panel
   - Animated message bubbles with loading indicators
   - Source citations and context display components
   - Beautiful color scheme with purple/pink gradients

2. **`node-server/public/js/ai-query/ai-query.js`**
   - Main AI Query module with chat interface
   - Connects to `/api/agent/invoke` endpoint
   - Parses Aura Agent responses (handles both Aura format and local GraphRAG fallback)
   - Displays sources, citations, and retrieved context
   - Example questions for quick start
   - Configurable search settings (scope: hybrid/entity/document, top-k)

3. **`docs/AI_QUERY_IMPLEMENTATION.md`** (this file)

### Modified Files
1. **`node-server/public/index.html`**
   - Added `ai-query.css` to stylesheet imports
   - Changed tab from "🔎 Query Builder" to "🤖 AI Query"
   - Renamed `query-builder-tab` to `ai-query-tab`
   - Updated tab click handler from `query-builder` to `ai-query`

2. **`node-server/public/js/main.js`**
   - Replaced `QueryBuilder` import with `AIQuery`
   - Changed `this.queryBuilder` to `this.aiQuery` in AppManager
   - Renamed `initQueryBuilderTab()` to `initAIQueryTab()`
   - Updated tab initialization logic

## Features

### Chat Interface
- **Modern UI**: Gradient header, clean message bubbles, smooth animations
- **User Messages**: Purple gradient background, right-aligned
- **Assistant Messages**: Light gray with border, left-aligned with robot avatar
- **Loading Indicator**: Animated dots while waiting for response
- **Auto-scroll**: Messages automatically scroll to bottom

### Example Questions
Pre-configured example questions in the sidebar:
- "What drugs target BRAF mutations?"
- "Show me negative relationships involving protein inhibition"
- "What are the most significant findings about cancer treatment?"
- "Find contradictions in the knowledge graph"
- "What documents discuss drug resistance mechanisms?"

### Search Settings
- **Scope**: 
  - Hybrid (default): Search both entities and documents
  - Entity: Search only entity embeddings
  - Document: Search only document embeddings
- **Top K**: Number of results to retrieve (1-20, default 8)

### Response Display
- **Answer Text**: Formatted with markdown-like rendering (bold, italic, tables)
- **Sources**: Clickable list of source documents with page numbers
- **Retrieved Context**: Chips showing entities and documents used for the answer
- **Error Handling**: Clear error messages with visual indicators

## Backend Integration

### Endpoint Used
- **POST** `/api/agent/invoke`
  - Request body: `{ input: "question text", body: {} }`
  - Proxies to Neo4j Aura Agent endpoint
  - Handles OAuth token management automatically

### Response Parsing
The module handles two response formats:

1. **Aura Agent Format** (primary):
```json
{
  "content": [
    { "type": "thinking", "thinking": "..." },
    { "type": "cypher_template_tool_use", "name": "...", "input": {} },
    { "type": "cypher_template_tool_result", "output": { "records": [...] } },
    { "type": "text", "text": "Final answer..." }
  ],
  "status": "SUCCESS",
  "usage": { ... }
}
```

2. **Local GraphRAG Format** (fallback):
```json
{
  "answer": "...",
  "entities": [...],
  "documents": [...],
  "sources": [...]
}
```

## Vector Index Configuration

The AI Query tab works with the two vector indexes created by the backend:
- **`entity_embedding_idx`**: On `:Entity(embedding)`
- **`document_embedding_idx`**: On `:Document(embedding)`

### Aura Agent Configuration
In your Neo4j Aura Agent UI, add two Similarity Search tools:

**Tool 1: Entity Search**
- Name: `entity_similarity_search`
- Index: `entity_embedding_idx`
- Embedding Model: `text-embedding-3-small` (or your configured model)
- Top K: 8

**Tool 2: Document Search**
- Name: `document_similarity_search`
- Index: `document_embedding_idx`
- Embedding Model: `text-embedding-3-small` (or your configured model)
- Top K: 8

## Usage Flow

1. **User opens AI Query tab**
   - Beautiful interface loads with example questions
   - Settings panel shows current configuration

2. **User asks a question**
   - Types in textarea or clicks example question
   - Presses Enter or clicks Send button
   - User message appears in chat

3. **Backend processing**
   - Loading indicator shows (animated dots)
   - Request sent to `/api/agent/invoke`
   - Backend exchanges credentials for OAuth token
   - Aura Agent processes question using vector similarity tools
   - Response returned to frontend

4. **Response displayed**
   - Loading indicator removed
   - Assistant message appears with formatted answer
   - Sources listed with document titles and page numbers
   - Retrieved context shown as chips
   - User can continue conversation

## Styling Details

### Color Scheme
- **Primary Gradient**: `#667eea` → `#764ba2` (purple)
- **Secondary Gradient**: `#f093fb` → `#f5576c` (pink)
- **Background**: White with subtle shadows
- **Text**: Dark gray (`#374151`) on light backgrounds

### Responsive Design
- Desktop: Two-column layout (sidebar + chat)
- Tablet/Mobile: Single column, sidebar moves below chat
- Minimum chat height: 30rem on mobile

### Animations
- **Message Entry**: Slide in from bottom with fade
- **Loading Dots**: Pulsing animation with staggered delays
- **Hover Effects**: Smooth transitions on buttons and examples

## Testing Checklist

- [ ] Tab switches correctly from other tabs
- [ ] Example questions populate input field
- [ ] Send button triggers query
- [ ] Enter key sends message (Shift+Enter for new line)
- [ ] Loading indicator appears during processing
- [ ] User messages display correctly (right-aligned, purple)
- [ ] Assistant messages display correctly (left-aligned, gray)
- [ ] Sources render with document titles and page numbers
- [ ] Retrieved context chips display entities and documents
- [ ] Error messages show when backend fails
- [ ] Settings (scope, k) can be changed
- [ ] Textarea auto-resizes with content
- [ ] Messages auto-scroll to bottom
- [ ] Responsive layout works on mobile

## Environment Variables Required

Backend `.env` must have:
```env
AURA_AGENT_CLIENT_ID=your_client_id
AURA_AGENT_CLIENT_SECRET=your_client_secret
AURA_AGENT_ENDPOINT_URL=https://api.neo4j.io/v2beta1/projects/.../agents/.../invoke
OPENAI_API_KEY=your_openai_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIM=1536
```

## Next Steps

1. **Test with real data**: Ingest documents and verify embeddings are created
2. **Configure Aura Agent**: Add the two similarity search tools
3. **Test queries**: Try various questions and verify responses
4. **Tune settings**: Adjust k and scope based on results
5. **Add features**: Consider adding conversation history, export, or graph visualization from results

## Troubleshooting

### No response from agent
- Check backend logs for OAuth token errors
- Verify `AURA_AGENT_*` env vars are set correctly
- Ensure Aura Agent endpoint is accessible

### Empty or incorrect answers
- Verify vector indexes exist in Neo4j
- Check that embeddings are being generated during ingestion
- Ensure Aura Agent tools are configured with correct index names

### UI not loading
- Check browser console for JavaScript errors
- Verify all CSS and JS files are being served correctly
- Clear browser cache and reload

### Styling issues
- Ensure `ai-query.css` is loaded before other stylesheets
- Check for CSS conflicts with existing styles
- Verify responsive breakpoints work on your device
