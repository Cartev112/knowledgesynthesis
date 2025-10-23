# Conversations Feature - AI Query Tab

## Overview
Replaced the settings sidebar with a saved conversations sidebar that persists chat history using a backend API.

## Changes Made

### 1. Backend API (`app/routes/conversations.py`)

**Endpoints:**
- `GET /api/conversations` - List all conversations (sorted by most recent)
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}` - Get conversation with all messages
- `POST /api/conversations/{id}/messages` - Add message to conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `PUT /api/conversations/{id}/title` - Update conversation title

**Data Model:**
```python
Conversation {
  id: str (UUID)
  title: str
  created_at: str (ISO timestamp)
  updated_at: str (ISO timestamp)
  messages: List[Message]
}

Message {
  role: str ("user" | "assistant")
  content: str
  timestamp: str (ISO timestamp)
  metadata: dict (optional - stores thinking traces, sources, etc.)
}
```

**Storage:**
- Currently uses in-memory dictionary (`conversations_db`)
- Replace with database (Redis, PostgreSQL, etc.) for production

**Auto-Title Feature:**
- New conversations start with "New Conversation"
- Automatically renamed to first 50 chars of first user message

### 2. Frontend Updates

#### CSS (`css/ai-query.css`)
- **Removed**: All settings-related styles
- **Added**: Conversation list styles
  - `.ai-query-sidebar-header` - Header with "New Chat" button
  - `.ai-query-conversations-list` - Scrollable conversation list
  - `.ai-query-conversation-item` - Individual conversation card
  - `.ai-query-conversation-item.active` - Active conversation (purple highlight)
  - `.ai-query-conversation-delete` - Delete button (appears on hover)
  - `.ai-query-new-chat-btn` - Purple gradient button

#### JavaScript (`js/ai-query/ai-query.js`)

**New Properties:**
```javascript
this.conversations = []           // List of conversation summaries
this.currentConversationId = null // Active conversation ID
```

**New Methods:**
- `loadConversations()` - Fetch all conversations from backend
- `createNewConversation()` - Create new conversation and switch to it
- `loadConversation(id)` - Load conversation messages from backend
- `deleteConversation(id, event)` - Delete conversation with confirmation
- `saveMessageToConversation(role, content, metadata)` - Save message to backend
- `renderConversationsList()` - Render conversation list in sidebar
- `renderMessages()` - Render all messages in current conversation
- `escapeHtml(text)` - Sanitize HTML for XSS protection

**Modified Methods:**
- `init()` - Now calls `loadConversations()` on startup
- `addMessage()` - Now calls `saveMessageToConversation()` after displaying
- `renderUI()` - Replaced settings sidebar with conversations sidebar

### 3. Height Fix
- Added `height: 100%` to `.ai-query-main` and `.ai-query-chat-panel`
- Chat panel now extends full height to bottom of screen

## UI Structure

```
┌─────────────────────────────────────────────────────────┐
│  🤖 AI Query Assistant                                  │
└─────────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────────────────────┐
│ 💬 Conversations                                        │
│ ┌──────────┐                                            │
│ │ ➕ New Chat│                                           │
│ └──────────┘                                            │
│                                                          │
│ ┌──────────────┐  ← Active conversation (purple)       │
│ │ What is ML?  │                                        │
│ │ 4 messages 🗑️│                                        │
│ └──────────────┘                                        │
│ ┌──────────────┐                                        │
│ │ Drug targets │                                        │
│ │ 2 messages 🗑️│                                        │
│ └──────────────┘                                        │
│                                                          │
│                  Chat Messages                          │
│                  (full height)                          │
│                                                          │
└──────────────┴──────────────────────────────────────────┘
```

## Features

### Conversation List
- **Sorted by recency**: Most recent conversations at top
- **Active highlight**: Purple background for current conversation
- **Message count**: Shows number of messages in each conversation
- **Delete on hover**: 🗑️ button appears when hovering over conversation
- **Click to load**: Click conversation to load its messages
- **Empty state**: "No conversations yet" when list is empty

### New Chat Button
- **Purple gradient**: Matches app theme
- **Creates conversation**: Automatically creates new conversation
- **Clears messages**: Starts fresh chat
- **Auto-switches**: Becomes active conversation

### Message Persistence
- **Auto-save**: Every message saved to backend immediately
- **Metadata preserved**: Thinking traces, sources, context all saved
- **Reload support**: Refresh page and conversations persist
- **Timestamps**: ISO format timestamps for all messages

### Auto-Title
- New conversations start as "New Conversation"
- First user message becomes the title (truncated to 50 chars)
- Updates automatically on first message

## API Usage Examples

### Create New Conversation
```javascript
const response = await API.post('/api/conversations', { 
  title: 'New Conversation' 
});
// Returns: { id, title, created_at, updated_at, messages: [] }
```

### Load Conversations
```javascript
const response = await API.get('/api/conversations');
// Returns: { conversations: [{ id, title, created_at, updated_at, message_count }] }
```

### Load Conversation Messages
```javascript
const response = await API.get(`/api/conversations/${conversationId}`);
// Returns: { id, title, created_at, updated_at, messages: [...] }
```

### Add Message
```javascript
await API.post(`/api/conversations/${conversationId}/messages`, {
  role: 'user',
  content: 'What is machine learning?',
  metadata: {}
});
```

### Delete Conversation
```javascript
await API.delete(`/api/conversations/${conversationId}`);
// Returns: { success: true }
```

## Data Flow

### Sending a Message
1. User types message and clicks Send
2. `sendQuery()` called
3. `addMessage('user', question)` displays message
4. `saveMessageToConversation()` saves to backend
5. Agent processes question
6. `addMessage('assistant', answer, metadata)` displays response
7. `saveMessageToConversation()` saves response to backend
8. `loadConversations()` refreshes conversation list

### Loading a Conversation
1. User clicks conversation in sidebar
2. `loadConversation(id)` called
3. Fetches conversation from `/api/conversations/{id}`
4. Sets `currentConversationId`
5. Loads messages into `this.messages`
6. `renderMessages()` displays all messages
7. `renderConversationsList()` updates active state

### Creating New Conversation
1. User clicks "➕ New Chat" button
2. `createNewConversation()` called
3. POST to `/api/conversations`
4. Backend returns new conversation with UUID
5. Sets as `currentConversationId`
6. Clears message display
7. Adds to conversations list at top

## Storage Considerations

### Current Implementation (In-Memory)
- **Pros**: Fast, simple, no dependencies
- **Cons**: Lost on server restart, not scalable
- **Use case**: Development, testing

### Production Recommendations

**Option 1: PostgreSQL**
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  title TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT,
  content TEXT,
  timestamp TIMESTAMP,
  metadata JSONB
);
```

**Option 2: Redis**
```python
# Store conversation as hash
redis.hset(f"conversation:{id}", mapping={
  "title": title,
  "created_at": created_at,
  "updated_at": updated_at
})

# Store messages as list
redis.rpush(f"conversation:{id}:messages", json.dumps(message))
```

**Option 3: MongoDB**
```javascript
{
  _id: ObjectId,
  title: String,
  created_at: ISODate,
  updated_at: ISODate,
  messages: [
    { role: String, content: String, timestamp: ISODate, metadata: Object }
  ]
}
```

## Security Considerations

### XSS Prevention
- `escapeHtml()` method sanitizes conversation titles
- Message content rendered with `textContent` (not `innerHTML`) where possible
- Metadata stored as objects, not executed code

### Access Control
- **TODO**: Add user authentication
- **TODO**: Filter conversations by user_id
- **TODO**: Verify user owns conversation before loading/deleting

### Rate Limiting
- **TODO**: Limit conversation creation (e.g., 100 per user)
- **TODO**: Limit message rate (e.g., 10 per minute)

## Testing Checklist

- [x] New Chat button creates conversation
- [x] Conversations load on page load
- [x] Click conversation loads its messages
- [x] Messages save to backend automatically
- [x] Delete button removes conversation
- [x] Active conversation highlighted in purple
- [x] Auto-title from first user message
- [x] Empty state shows when no conversations
- [x] Chat panel extends full height
- [x] Delete confirmation dialog appears
- [x] Hover shows delete button
- [x] Conversation list scrollable

## Future Enhancements

1. **Search conversations**: Add search bar to filter by title/content
2. **Edit titles**: Click title to rename conversation
3. **Export conversation**: Download as JSON/Markdown
4. **Share conversation**: Generate shareable link
5. **Conversation folders**: Organize conversations into categories
6. **Pin conversations**: Keep important conversations at top
7. **Archive**: Hide old conversations without deleting
8. **Conversation stats**: Show token count, cost, duration
9. **Multi-user support**: User authentication and isolation
10. **Real-time sync**: WebSocket updates for multi-device support

## Migration from Settings

### Removed
- Search scope dropdown (hybrid/entity/document)
- Top K results input
- All settings-related CSS classes
- Settings event listeners

### Why Removed
- Settings don't actually configure Aura Agent (configured in Aura UI)
- Misleading to users
- Conversations provide more value
- Cleaner, more focused interface

## Responsive Behavior

- Desktop: Sidebar visible (280px)
- Mobile (<1024px): Sidebar hidden (TODO: add hamburger menu)
- Conversations list scrollable on overflow
- Delete button always visible on mobile (no hover state)
