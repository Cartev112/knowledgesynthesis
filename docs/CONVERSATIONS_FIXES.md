# Conversations Feature - Bug Fixes

## Issues Fixed

### 1. ✅ New Conversation Glitch & Missing First Query

**Problem:**
- Starting a new conversation with a query caused a glitch
- First user message wasn't visible when reopening the conversation
- Race condition: message sent before conversation was created

**Root Cause:**
- `addMessage()` was calling `saveMessageToConversation()` which would create a new conversation
- But `sendQuery()` wasn't waiting for conversation creation
- Messages were being saved to a conversation that didn't exist yet

**Fix:**
```javascript
// In sendQuery() - ensure conversation exists BEFORE adding messages
if (!this.currentConversationId) {
  await this.createNewConversation();
}
```

**Changes Made:**
- `js/ai-query/ai-query.js` - `sendQuery()` now awaits conversation creation
- `saveMessageToConversation()` no longer creates conversations (just logs error)
- Removed `await` from `loadConversations()` call in save (non-blocking)

**Result:**
- Conversation created first, then messages added
- No race condition
- First message always visible

---

### 2. ✅ Message Bubble Alignment

**Problem:**
- User messages weren't hugging the right side of the container
- They were aligned to the left despite `flex-direction: row-reverse`

**Root Cause:**
- `justify-content: flex-start` was used for both user and assistant messages
- For reversed flex direction, `flex-start` still aligns to the left

**Fix:**
```css
.ai-query-message.user {
  flex-direction: row-reverse;
  justify-content: flex-end;  /* Changed from flex-start */
}
```

**Changes Made:**
- `css/ai-query.css` - Changed user message `justify-content` to `flex-end`

**Result:**
- User messages now properly aligned to right side
- Assistant messages remain on left
- Proper chat bubble layout

---

### 3. ✅ User Authentication & Conversation Filtering

**Problem:**
- All users could see all conversations
- No access control
- Security vulnerability

**Solution:**
- Added user authentication to all conversation endpoints
- Filter conversations by `user_id`
- Verify ownership before access/modification

**Implementation:**

#### Helper Function
```python
def get_current_user_from_request(request: Request) -> str:
    """Get current user from session cookie."""
    session_id = request.cookies.get("session_id")
    
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_data = sessions[session_id]
    return user_data.get("username", "anonymous")
```

#### Updated Endpoints

**GET /api/conversations**
- Added `request: Request` parameter
- Gets username from session
- Filters: `[c for c in conversations_db.values() if c.get("user_id") == username]`
- Returns only user's conversations

**POST /api/conversations**
- Added `request: Request` parameter
- Gets username from session
- Sets `user_id` field on new conversation
- Returns conversation with user_id

**GET /api/conversations/{id}**
- Added `request: Request` parameter
- Gets username from session
- Verifies: `conversation.get("user_id") == username`
- Returns 403 if access denied

**POST /api/conversations/{id}/messages**
- Added `request: Request` parameter
- Gets username from session
- Verifies ownership before adding message
- Returns 403 if access denied

**DELETE /api/conversations/{id}**
- Added `request: Request` parameter
- Gets username from session
- Verifies ownership before deletion
- Returns 403 if access denied

**PUT /api/conversations/{id}/title**
- Added `request: Request` parameter
- Gets username from session
- Verifies ownership before update
- Returns 403 if access denied

**Changes Made:**
- `app/routes/conversations.py` - All endpoints updated
- Imported `sessions` from `auth` module
- Added `user_id` field to conversation model
- Added ownership verification to all operations

**Security Benefits:**
- ✅ Users only see their own conversations
- ✅ Cannot access other users' conversations (403 error)
- ✅ Cannot modify other users' conversations
- ✅ Cannot delete other users' conversations
- ✅ Session-based authentication (existing system)

---

## Testing Checklist

### New Conversation Flow
- [x] Click "New Chat" creates conversation immediately
- [x] Type message and send - no glitch
- [x] Message appears in chat
- [x] Message saved to backend
- [x] Reload page - conversation appears in list
- [x] Click conversation - first message visible

### Message Alignment
- [x] User messages aligned to right
- [x] User messages have purple background
- [x] Assistant messages aligned to left
- [x] Assistant messages have gray background
- [x] Avatar positions correct (user right, assistant left)

### User Authentication
- [x] Login as User A - see only User A's conversations
- [x] Login as User B - see only User B's conversations
- [x] User A cannot access User B's conversation (403)
- [x] User A cannot delete User B's conversation (403)
- [x] Logout and back in - conversations persist
- [x] Unauthenticated request returns 401

## Code Changes Summary

### Frontend (`js/ai-query/ai-query.js`)
```javascript
// Before
async sendQuery() {
  this.addMessage('user', question);
  // ... send to agent
}

// After
async sendQuery() {
  if (!this.currentConversationId) {
    await this.createNewConversation();  // ← Wait for creation
  }
  this.addMessage('user', question);
  // ... send to agent
}
```

### CSS (`css/ai-query.css`)
```css
/* Before */
.ai-query-message.user {
  flex-direction: row-reverse;
  justify-content: flex-start;  /* ← Wrong */
}

/* After */
.ai-query-message.user {
  flex-direction: row-reverse;
  justify-content: flex-end;  /* ← Correct */
}
```

### Backend (`app/routes/conversations.py`)
```python
# Before
@router.get("/conversations")
def list_conversations():
    conversations = list(conversations_db.values())
    # ... returns ALL conversations

# After
@router.get("/conversations")
def list_conversations(request: Request):
    username = get_current_user_from_request(request)
    user_conversations = [
        c for c in conversations_db.values() 
        if c.get("user_id") == username
    ]
    # ... returns ONLY user's conversations
```

## Database Schema Update

### Conversation Model (Before)
```python
{
  "id": "uuid",
  "title": "string",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "messages": []
}
```

### Conversation Model (After)
```python
{
  "id": "uuid",
  "user_id": "username",  # ← NEW FIELD
  "title": "string",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "messages": []
}
```

## Migration Notes

### Existing Conversations
- Old conversations without `user_id` will not be visible
- They'll remain in memory but filtered out
- For production: run migration to add `user_id` to existing conversations

### Production Database Migration
```python
# Pseudocode for migration
for conversation in conversations_db.values():
    if "user_id" not in conversation:
        # Option 1: Assign to admin
        conversation["user_id"] = "admin"
        
        # Option 2: Delete orphaned conversations
        # del conversations_db[conversation["id"]]
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**When:** No session cookie or invalid session

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```
**When:** User tries to access another user's conversation

### 404 Not Found
```json
{
  "detail": "Conversation not found"
}
```
**When:** Conversation ID doesn't exist

## Future Enhancements

1. **Shared Conversations**: Allow users to share conversations with others
2. **Team Workspaces**: Conversations scoped to teams, not just users
3. **Admin Access**: Allow admins to view all conversations
4. **Conversation Transfer**: Transfer ownership between users
5. **Audit Log**: Track who accessed/modified conversations
