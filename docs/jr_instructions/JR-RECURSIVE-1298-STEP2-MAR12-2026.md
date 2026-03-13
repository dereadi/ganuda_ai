# [RECURSIVE] Peace Chief Curiosity Engine — Stub-Filling Pipeline - Step 2

**Parent Task**: #1298
**Auto-decomposed**: 2026-03-12T09:03:34.718429
**Original Step Title**: Stub Extraction (Tier 1 — local model, <5 seconds)

---

### Step 2: Stub Extraction (Tier 1 — local model, <5 seconds)

Dispatch to local model (redfin :9100 or sasass qwen2.5-7B):

System prompt:
```
Extract all named entities and concepts from the following content.
Return a JSON array of objects:
{
  "type": "person|company|organization|regulation|concept|event|technology",
  "name": "exact name as mentioned",
  "context": "one sentence — what was said about them or why they were mentioned",
  "stub_depth": "shallow|medium|deep"
}

shallow = just a name drop, probably not worth researching
medium = mentioned with some context, worth a quick lookup
deep = central to the content, worth full research

Be thorough. Every proper noun. Every company. Every law or act mentioned.
Every person who commented or was quoted. Every technology named.
```

#
