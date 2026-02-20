# Jr Instruction: Create Jane Street Track 1 Submission Draft in Gmail

**Ticket**: #1780
**Priority**: 3
**Story Points**: 1
**Assigned**: Software Engineer Jr.

## Context

We need to create a Gmail draft (NOT send) with our Jane Street Track 1 Archaeology submission.
The Gmail API OAuth token is at `~/.gmail_credentials/token.pickle`. We've used this before
(see `/ganuda/scripts/send_vetassist_features_email.py` for the pattern).

The submission content is at `/ganuda/experiments/jane-street/track1_archaeology/SUBMISSION_DRAFT.md`.

## Step 1: Create the draft email script

Create `/ganuda/experiments/jane-street/track1_archaeology/create_gmail_draft.py`

```python
#!/usr/bin/env python3
"""
Create Gmail draft for Jane Street Track 1 Archaeology submission.
Creates a DRAFT only — does NOT send.

Uses OAuth token from ~/.gmail_credentials/token.pickle
"""
import pickle
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build


TOKEN_PATH = os.path.expanduser('~/.gmail_credentials/token.pickle')
SUBMISSION_PATH = Path(__file__).parent / 'SUBMISSION_DRAFT.md'


def get_gmail_service():
    """Connect to Gmail API using existing OAuth token."""
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f'Token not found at {TOKEN_PATH}')

    with open(TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def load_submission():
    """Load submission content from SUBMISSION_DRAFT.md, strip metadata."""
    content = SUBMISSION_PATH.read_text()

    # Strip the markdown header and metadata lines
    lines = content.split('\n')
    # Find the line after the --- separator (email body starts there)
    body_start = 0
    separator_count = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            separator_count += 1
            if separator_count == 1:
                body_start = i + 1
                break

    # Also strip the final --- and signature block from the end
    body_lines = lines[body_start:]
    body_end = len(body_lines)
    for i in range(len(body_lines) - 1, -1, -1):
        if body_lines[i].strip() == '---':
            body_end = i
            break

    body = '\n'.join(body_lines[:body_end]).strip()

    # Add signature back cleanly
    body += '\n\n---\nDarrell Reading\nCherokee AI Federation\n'

    return body


def create_draft():
    """Create a Gmail draft with the submission."""
    print("Connecting to Gmail API...")
    service = get_gmail_service()
    print("Connected.")

    print("Loading submission content...")
    body = load_submission()

    # Build the email
    message = MIMEMultipart('alternative')
    message['Subject'] = 'Track 1 Archaeology — The model is a compiled Triple DES circuit'
    message['To'] = 'archaeology@janestreet.com'

    # Plain text version
    text_part = MIMEText(body, 'plain')
    message.attach(text_part)

    # Encode for Gmail API
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Create DRAFT (not send)
    draft = service.users().drafts().create(
        userId='me',
        body={'message': {'raw': raw}}
    ).execute()

    print(f"\nDraft created successfully!")
    print(f"Draft ID: {draft['id']}")
    print(f"Message ID: {draft['message']['id']}")
    print(f"To: archaeology@janestreet.com")
    print(f"Subject: Track 1 Archaeology — The model is a compiled Triple DES circuit")
    print(f"\nOpen Gmail to review and send the draft.")


if __name__ == '__main__':
    create_draft()
```
