# KB-EMAIL-PATTERNS-001: Email LLM Integration Patterns

**Created**: 2025-12-11
**Source**: [QaMail-LLM](https://github.com/georgong/QaMail-LLM)
**Status**: Reference for SAG-EMAIL-001

---

## Overview

Patterns extracted from QaMail-LLM for building AI-powered email clients. These patterns should be adapted for Cherokee AI's email intelligence system.

---

## Architecture Components

### 1. Email Reader (POP3/IMAP)

```python
import poplib
from email.parser import Parser, BytesParser
from email.header import decode_header
from email import policy

class EmailReader:
    def __init__(self, logger):
        self.login_state = False
        self.logger = logger

    def login(self, config: dict):
        """Connect to email server"""
        server = poplib.POP3(config["server"])
        server.set_debuglevel(1)
        server.user(config["email"])
        server.pass_(config["password"])
        self.server = server
        self.login_state = True

    def get_stat(self):
        """Get mailbox statistics"""
        num, totalsize = self.server.stat()
        return {"mail_num": num, "total_size": totalsize}

    def get_text(self, index):
        """Extract plain text from email"""
        resp, lines, octets = self.server.retr(index)
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        msg = Parser().parsestr(msg_content)

        subject = msg["Subject"]
        decoded_subject, charset = decode_header(subject)[0]
        if isinstance(decoded_subject, bytes):
            decoded_subject = decoded_subject.decode(charset or 'utf-8')

        return {
            "date": msg["Date"],
            "from": msg["From"],
            "subject": decoded_subject,
            "id": msg["Message-ID"],
            "text": extract_plain_text(msg)
        }

    def get_html(self, index):
        """Extract HTML content from email"""
        resp, lines, octets = self.server.retr(index)
        msg = BytesParser(policy=policy.default).parsebytes(b'\r\n'.join(lines))

        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset)
        return None
```

### 2. Vector Storage with ChromaDB

```python
import chromadb
import uuid

class EmailRetriever:
    def __init__(self, user_id, embedding_model):
        self.presist_directory = f'local_db/{user_id}/vectordb'
        self.embedding_model = embedding_model
        self.chroma_client = chromadb.PersistentClient(path=self.presist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="email_collection")

    def store_data(self, content_dicts):
        """Store emails with embeddings"""
        documents_list = []
        metadatas_list = []
        embedding_list = []
        ids_list = []

        for message_id, content in content_dicts.items():
            text = content["text"]
            # Chunk long emails
            chunks = recursive_email_splitter(text)

            for chunk in chunks:
                documents_list.append(chunk)
                embedding_list.append(self.embedding_model.encode(chunk).tolist())
                metadatas_list.append({
                    "date": content["date"],
                    "from": content["from"],
                    "subject": content["subject"],
                    "message_id": message_id
                })
                ids_list.append(f"{uuid.uuid4()}")

        self.collection.add(
            documents=documents_list,
            metadatas=metadatas_list,
            embeddings=embedding_list,
            ids=ids_list
        )

    def similarity_search(self, query, filters=None, n_results=10):
        """Search emails by semantic similarity"""
        query_embedding = self.embedding_model.encode(query).tolist()

        if filters:
            return self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=filters
            )
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
```

### 3. Date Filtering Pattern

```python
def build_date_filter(startdate, enddate):
    """Build ChromaDB filter for date range"""
    from email_client.email_util import date2dt

    filter_dict = {}

    if startdate and enddate:
        filter_dict["$and"] = [
            {"date": {"$gte": date2dt(startdate).timestamp()}},
            {"date": {"$lte": date2dt(enddate).timestamp()}}
        ]
    elif startdate:
        filter_dict["date"] = {"$gte": date2dt(startdate).timestamp()}
    elif enddate:
        filter_dict["date"] = {"$lte": date2dt(enddate).timestamp()}

    return filter_dict
```

### 4. Self-RAG Filtering

```python
def rag_filter_results(llm_client, model, search_results, question):
    """Use LLM to filter irrelevant search results"""
    documents = search_results["documents"][0]
    metadatas = search_results["metadatas"][0]

    mask = []
    for doc, metadata in zip(documents, metadatas):
        prompt = f"""
        Question: {question}
        Email Content: {doc}
        Date: {metadata['date']}
        Subject: {metadata['subject']}

        Is this email relevant to the question? Answer only 'yes' or 'no'.
        """
        result = llm_client.generate_text(model, prompt, stream=False, temperature=0)
        mask.append("yes" in result.lower())

    # Filter results
    filtered = {
        "ids": [[id for id, m in zip(search_results["ids"][0], mask) if m]],
        "documents": [[doc for doc, m in zip(documents, mask) if m]],
        "metadatas": [[meta for meta, m in zip(metadatas, mask) if m]]
    }
    return filtered
```

### 5. LLM Provider Abstraction

```python
class LLMSetter:
    """Factory for LLM providers (Ollama, OpenAI, Anthropic)"""

    def __init__(self, base_url, provider="ollama", api_key=None):
        self.provider = provider.lower()

        if self.provider == "openai":
            self.client = OpenAIProvider(base_url, api_key)
        elif self.provider == "ollama":
            self.client = OllamaProvider(base_url)
        elif self.provider == "anthropic":
            self.client = AnthropicProvider(api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate_text(self, model, prompt, stream=True, temperature=0.7):
        return self.client.generate_text(model, prompt, stream, temperature)
```

### 6. Email Splitter for Long Emails

```python
def recursive_email_splitter(text, chunk_size=500, overlap=50):
    """Split long emails into chunks for embedding"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end
            for delim in ['. ', '\n\n', '\n', ' ']:
                idx = text[start:end].rfind(delim)
                if idx > chunk_size // 2:
                    end = start + idx + len(delim)
                    break

        chunks.append(text[start:end])
        start = end - overlap

    return chunks
```

---

## Cherokee Adaptations

### 1. Use IMAP Instead of POP3

POP3 downloads and (optionally) deletes. IMAP is better for our use case:

```python
import imaplib

class IMAPEmailReader:
    def login(self, config):
        if config.get("ssl", True):
            self.server = imaplib.IMAP4_SSL(config["server"], config.get("port", 993))
        else:
            self.server = imaplib.IMAP4(config["server"], config.get("port", 143))

        self.server.login(config["email"], config["password"])
        self.server.select("INBOX")
```

### 2. Store in PostgreSQL Instead of Local Files

We already have the `emails` table in the spoke database:

```sql
-- Existing schema on Cherokee spokes
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(500) UNIQUE,
    from_address VARCHAR(500),
    to_addresses TEXT[],
    subject VARCHAR(1000),
    body_text TEXT,
    body_html TEXT,
    received_at TIMESTAMP WITH TIME ZONE,
    thermal_temp DECIMAL(3,1),
    priority_score INTEGER,
    sentiment VARCHAR(50),
    action_required BOOLEAN,
    ai_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Use Cherokee AI Instead of External LLM

Route through our existing Cherokee AI infrastructure:

```python
# Instead of Ollama/OpenAI, use Cherokee AI
from cherokee_ai_client import CherokeeAI

ai = CherokeeAI(triad="sasass")  # Local Sasass node
response = ai.analyze_email(email_text, priority_check=True)
```

### 4. Thermal Temperature Integration

Add thermal context to email processing:

```python
def calculate_email_thermal(email_data, ai_analysis):
    """Calculate thermal temperature for email urgency"""
    base_temp = 0.5

    # Keywords that raise temperature
    urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline', 'critical']
    for keyword in urgent_keywords:
        if keyword in email_data['subject'].lower() or keyword in email_data['body'].lower():
            base_temp += 0.1

    # AI-detected action items raise temp
    if ai_analysis.get('action_required'):
        base_temp += 0.2

    # Sender priority (from contacts/whitelist)
    if is_priority_sender(email_data['from']):
        base_temp += 0.15

    return min(base_temp, 1.0)  # Cap at 1.0
```

---

## Dependencies

```text
# requirements.txt additions
imaplib2>=3.6
chromadb>=0.4.0
sentence-transformers>=2.2.0  # Alternative to jina
beautifulsoup4>=4.12.0
```

---

## Integration Points

1. **SAG Dashboard**: Email tab displays emails from PostgreSQL
2. **Daemon**: Background service polls IMAP and stores to DB
3. **AI Analysis**: Cherokee AI analyzes for priority/summary
4. **Vector Search**: ChromaDB on spoke for semantic email search
5. **Thermal Context**: Email urgency feeds into thermal memory

---

**For Seven Generations**: Learn from others, adapt for ourselves.
