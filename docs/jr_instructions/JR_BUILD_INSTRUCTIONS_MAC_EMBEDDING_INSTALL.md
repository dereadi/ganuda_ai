# Jr Build Instructions: Mac Studio Embedding Service Installation

## Priority: HIGH - Enables Federated Embeddings

---

## Target Nodes

| Node | IP | Status |
|------|-----|--------|
| sasass | 192.168.132.241 | Files deployed, needs dependencies |
| sasass2 | 192.168.132.242 | Files deployed, needs dependencies |

---

## Prerequisites Already Met

- [x] fastapi installed
- [x] uvicorn installed
- [x] psycopg2-binary installed
- [x] Directory structure created
- [x] embedding_server.py deployed
- [x] LaunchAgent plist deployed

---

## Steps to Complete (Run on Each Mac Studio)

### 1. Install sentence-transformers

```bash
pip3 install sentence-transformers
```

This will download the BGE-large model (~1.3GB) on first run.

### 2. Load the LaunchAgent

```bash
launchctl load ~/Library/LaunchAgents/com.cherokee.embedding.plist
```

### 3. Verify Service is Running

```bash
curl http://localhost:8003/health
```

Expected output:
```json
{
  "status": "healthy",
  "node": "sasass",
  "model": "BAAI/bge-large-en-v1.5",
  "device": "mps",
  "dimensions": 1024
}
```

### 4. Test Embedding Generation

```bash
curl -X POST http://localhost:8003/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Cherokee AI is wise"]}'
```

---

## Troubleshooting

### Check logs:
```bash
tail -f /Users/Shared/ganuda/logs/embedding.log
tail -f /Users/Shared/ganuda/logs/embedding.error.log
```

### Restart service:
```bash
launchctl unload ~/Library/LaunchAgents/com.cherokee.embedding.plist
launchctl load ~/Library/LaunchAgents/com.cherokee.embedding.plist
```

### Check MPS availability:
```python
import torch
print(torch.backends.mps.is_available())  # Should be True
```

---

## Federation Architecture

```
                    ┌─────────────────────────┐
                    │   Central PostgreSQL    │
                    │   bluefin:5432          │
                    │   (pgvector)            │
                    └───────────┬─────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     redfin      │    │     sasass      │    │     sasass2     │
│  CUDA (8003)    │    │   MPS (8003)    │    │   MPS (8003)    │
│  GPU Inference  │    │  Local Context  │    │  Local Context  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

Each node:
- Generates embeddings locally (GPU accelerated)
- Maintains local SQLite for node-specific context
- Can query central thermal memory on bluefin
- Participates in federated searches

---

## Success Criteria

- [ ] sentence-transformers installed on sasass
- [ ] sentence-transformers installed on sasass2
- [ ] LaunchAgent loaded on both
- [ ] /health returns "device": "mps" (not cpu)
- [ ] Can generate embeddings
- [ ] Can search central thermal memory

---

*For Seven Generations*
