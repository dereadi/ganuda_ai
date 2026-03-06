# JR Instruction: VetAssist Chat Backend Auth Hardening
## Task ID: CHAT-AUTH-003
## Kanban: #1719
## Priority: P1 (Security — Coyote flagged)
## Assigned Jr: Software Engineer Jr.

---

## Objective

The chat backend (`chat.py`) has NO authentication. All endpoints accept `user_id` from the client request body or query params — any client can impersonate any user. Other VetAssist endpoints (dashboard, evidence, forms) already use `Depends(get_current_user)` from JWT. Chat must follow the same pattern.

**Scope: Backend only** (`/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`). Frontend already uses `useAuth()` hook correctly.

---

## Step 1: Add auth import and update SessionCreate schema

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
from app.core.database import get_db
from app.core.sanitize import sanitize_session_title, sanitize_message
=======
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.sanitize import sanitize_session_title, sanitize_message
>>>>>>> REPLACE
```

---

## Step 2: Remove user_id from SessionCreate request body

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
class SessionCreate(BaseModel):
    """Request schema for creating a chat session"""
    user_id: uuid.UUID
    title: Optional[str] = "New Chat"
=======
class SessionCreate(BaseModel):
    """Request schema for creating a chat session"""
    title: Optional[str] = "New Chat"
>>>>>>> REPLACE
```

---

## Step 3: Wire create_chat_session to JWT auth

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new chat session for a user.

    Args:
        session_data: Session creation data (user_id, title)
        db: Database session

    Returns:
        Created chat session
    """
    # Create new session with sanitized title
    new_session = ChatSession(
        id=uuid.uuid4(),
        user_id=session_data.user_id,
        title=sanitize_session_title(session_data.title or "New Chat")
    )
=======
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session for the authenticated user.

    Args:
        session_data: Session creation data (title)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Created chat session
    """
    # Create new session with sanitized title — user_id from JWT, never from client
    new_session = ChatSession(
        id=uuid.uuid4(),
        user_id=uuid.UUID(current_user["user_id"]),
        title=sanitize_session_title(session_data.title or "New Chat")
    )
>>>>>>> REPLACE
```

---

## Step 4: Wire list_chat_sessions to JWT auth (remove user_id query param)

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.get("/sessions", response_model=List[SessionResponse])
async def list_chat_sessions(
    user_id: uuid.UUID,
    include_archived: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for a user.

    Args:
        user_id: User UUID
        include_archived: Include archived sessions (default: False)
        limit: Max number of sessions to return (default: 50)
        db: Database session

    Returns:
        List of chat sessions
    """
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
=======
@router.get("/sessions", response_model=List[SessionResponse])
async def list_chat_sessions(
    include_archived: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for the authenticated user.

    Args:
        include_archived: Include archived sessions (default: False)
        limit: Max number of sessions to return (default: 50)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        List of chat sessions
    """
    user_id = uuid.UUID(current_user["user_id"])
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
>>>>>>> REPLACE
```

---

## Step 5: Add ownership check to get_session_messages

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all messages for a chat session.

    Args:
        session_id: Session UUID
        limit: Max number of messages (default: 100)
        db: Database session

    Returns:
        List of messages ordered by creation time
    """
    # Verify session exists
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
=======
@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a chat session (must be owned by authenticated user).

    Args:
        session_id: Session UUID
        limit: Max number of messages (default: 100)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        List of messages ordered by creation time
    """
    # Verify session exists AND belongs to authenticated user
    user_id = uuid.UUID(current_user["user_id"])
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
>>>>>>> REPLACE
```

---

## Step 6: Add ownership check to send_message

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Send a message and get Council response.

    This is the main chatbot endpoint:
    1. Saves user message to database
    2. Gets conversation history
    3. Queries Ganuda 7-specialist Council
    4. Saves assistant response with specialist attribution
    5. Stores Council validation votes
    6. Returns both messages with metadata

    Args:
        message_data: Message content and session_id
        db: Database session

    Returns:
        User message, assistant response, and metadata
    """
    # Verify session exists
    session = db.query(ChatSession).filter(
        ChatSession.id == message_data.session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {message_data.session_id} not found"
        )
=======
@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and get Council response.

    This is the main chatbot endpoint:
    1. Verifies session ownership via JWT
    2. Saves user message to database
    3. Gets conversation history
    4. Queries Ganuda 7-specialist Council
    5. Saves assistant response with specialist attribution
    6. Stores Council validation votes
    7. Returns both messages with metadata

    Args:
        message_data: Message content and session_id
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        User message, assistant response, and metadata
    """
    # Verify session exists AND belongs to authenticated user
    user_id = uuid.UUID(current_user["user_id"])
    session = db.query(ChatSession).filter(
        ChatSession.id == message_data.session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {message_data.session_id} not found"
        )
>>>>>>> REPLACE
```

---

## Step 7: Add ownership check to delete_chat_session

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its messages.

    Args:
        session_id: Session UUID
        db: Database session
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    db.delete(session)
    db.commit()
=======
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its messages (must be owned by authenticated user).

    Args:
        session_id: Session UUID
        current_user: Authenticated user from JWT
        db: Database session
    """
    user_id = uuid.UUID(current_user["user_id"])
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    db.delete(session)
    db.commit()
>>>>>>> REPLACE
```

---

## Step 8: Add ownership check to archive_chat_session

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

```
<<<<<<< SEARCH
@router.patch("/sessions/{session_id}/archive", response_model=SessionResponse)
async def archive_chat_session(
    session_id: uuid.UUID,
    archived: bool = True,
    db: Session = Depends(get_db)
):
    """
    Archive or unarchive a chat session.

    Args:
        session_id: Session UUID
        archived: Archive (True) or unarchive (False)
        db: Database session

    Returns:
        Updated session
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
=======
@router.patch("/sessions/{session_id}/archive", response_model=SessionResponse)
async def archive_chat_session(
    session_id: uuid.UUID,
    archived: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Archive or unarchive a chat session (must be owned by authenticated user).

    Args:
        session_id: Session UUID
        archived: Archive (True) or unarchive (False)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Updated session
    """
    user_id = uuid.UUID(current_user["user_id"])
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
>>>>>>> REPLACE
```

---

## Step 9: Update frontend — remove user_id from request bodies

The frontend already uses `useAuth()` correctly, but it still sends `user_id` in request bodies (which the backend will now ignore since it reads from JWT). The frontend must also send the Authorization header.

File: `/ganuda/vetassist/frontend/app/chat/page.tsx`

```
<<<<<<< SEARCH
      const response = await axios.get(`${API_URL}/chat/sessions`, {
        params: { user_id: user.id, limit: 50 },
      });
=======
      const response = await axios.get(`${API_URL}/chat/sessions`, {
        params: { limit: 50 },
        headers: { Authorization: `Bearer ${user.token}` },
      });
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
      const response = await axios.post(`${API_URL}/chat/sessions`, {
        user_id: user.id,
        title: "New Chat",
      });
=======
      const response = await axios.post(`${API_URL}/chat/sessions`,
        { title: "New Chat" },
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
      const response = await axios.post<ChatResponse>(`${API_URL}/chat/message`, {
        session_id: currentSession.id,
        content: userMessage,
      });
=======
      const response = await axios.post<ChatResponse>(`${API_URL}/chat/message`,
        { session_id: currentSession.id, content: userMessage },
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
      await axios.delete(`${API_URL}/chat/sessions/${sessionId}`);
=======
      await axios.delete(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
>>>>>>> REPLACE
```

---

## Step 10: Update WizardChatHelper to send auth header

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/WizardChatHelper.tsx`

```
<<<<<<< SEARCH
      const response = await axios.post(`${apiUrl}/chat/sessions`, {
        user_id: user.id,
        title: `Wizard Help: ${wizardType} Step ${currentStep}`,
        source: 'wizard_helper',
        metadata: {
          wizard_type: wizardType,
          step: currentStep,
          step_title: stepTitle
        }
      });
=======
      const response = await axios.post(`${apiUrl}/chat/sessions`,
        {
          title: `Wizard Help: ${wizardType} Step ${currentStep}`,
          source: 'wizard_helper',
          metadata: {
            wizard_type: wizardType,
            step: currentStep,
            step_title: stepTitle
          }
        },
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
      const response = await axios.post<ChatResponse>(`${apiUrl}/chat/message`, {
        session_id: chatSessionId,
        content: contextMessage
      });
=======
      const response = await axios.post<ChatResponse>(`${apiUrl}/chat/message`,
        { session_id: chatSessionId, content: contextMessage },
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
>>>>>>> REPLACE
```

---

## Verification

After deployment, verify on bluefin:

```text
# Test unauthenticated request is rejected
curl -s -X POST http://localhost:8001/api/v1/chat/sessions -H "Content-Type: application/json" -d '{"title":"test"}' | python3 -m json.tool
# Expected: 401 Unauthorized

# Test with valid JWT
curl -s -X POST http://localhost:8001/api/v1/chat/sessions -H "Content-Type: application/json" -H "Authorization: Bearer <valid_jwt>" -d '{"title":"test"}' | python3 -m json.tool
# Expected: 201 Created with user_id from JWT
```

---

## Acceptance Criteria

1. All 6 chat endpoints require JWT authentication
2. Session creation uses user_id from JWT, not request body
3. Session listing uses user_id from JWT, not query param
4. Messages, delete, archive all verify session ownership
5. Unauthenticated requests return 401
6. User A cannot access User B's sessions
7. Frontend sends Authorization header on all chat API calls
8. No hardcoded user IDs remain anywhere

---

## Risk Note (Coyote)

The `user.token` property on the frontend auth context must exist and contain the raw JWT. If the auth context stores the token differently (e.g., `user.accessToken` or via httpOnly cookie), Step 9-10 will need adjustment. Verify the auth context shape before deploying.

---

*Cherokee AI Federation — For Seven Generations*
