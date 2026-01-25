# JR Instruction: VetAssist Chat PII Integration

## Overview

Integrate PIIService into VetAssist chat endpoint.

## Tasks

### Task 1: Backup Current Chat Endpoint

```bash
cp /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py.backup_$(date +%Y%m%d)
```

### Task 2: Create Integration Patch Script

Create `/ganuda/vetassist/backend/integrate_pii.py`:

```python
#!/usr/bin/env python3
"""
Integrate PIIService into chat.py
Cherokee AI Federation - January 2026
"""

import re

CHAT_FILE = '/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py'

# Read current file
with open(CHAT_FILE, 'r') as f:
    content = f.read()

# Check if already integrated
if 'pii_service' in content:
    print('PIIService already integrated')
    exit(0)

# Add import after existing imports
import_line = 'from app.services.council_chat import CouncilChatService'
new_imports = '''from app.services.council_chat import CouncilChatService
from app.services.pii_service import pii_service
import logging

logger = logging.getLogger(__name__)'''

content = content.replace(import_line, new_imports)

# Find the send_message function and add PII analysis
# Look for: "# Save user message with sanitized content"
old_save_comment = '# Save user message with sanitized content (for storage)'
new_pii_section = '''# Analyze message for PII before storage
    pii_entities = pii_service.analyze(message_data.content)
    if pii_entities:
        entity_types = set(e['entity_type'] for e in pii_entities)
        logger.info(f"PII detected in session {message_data.session_id}: {len(pii_entities)} entities of types {entity_types}")

    # Create redacted version for database storage
    storage_content = pii_service.redact_for_logging(message_data.content)

    # Save user message with REDACTED content (for storage)'''

content = content.replace(old_save_comment, new_pii_section)

# Change content=sanitize_message(message_data.content) to content=storage_content
old_content_line = 'content=sanitize_message(message_data.content)'
new_content_line = 'content=storage_content  # REDACTED for PII protection'

content = content.replace(old_content_line, new_content_line)

# Write updated file
with open(CHAT_FILE, 'w') as f:
    f.write(content)

print('PIIService integration complete')
print('Changes made:')
print('  - Added pii_service import')
print('  - Added PII analysis before storage')
print('  - Changed storage content to redacted version')
```

### Task 3: Run Integration Script

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python integrate_pii.py
```

## Verification

```bash
cd /ganuda/vetassist/backend && grep -n "pii_service\|storage_content\|REDACTED" app/api/v1/endpoints/chat.py
```

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -c "from app.api.v1.endpoints.chat import router; print('Import OK')"
```

---

*Cherokee AI Federation - For the Seven Generations*
