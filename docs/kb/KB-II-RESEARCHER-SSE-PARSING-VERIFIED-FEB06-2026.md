# KB: ii-researcher SSE Parsing Fix Verified

**Date:** 2026-02-06
**Category:** Research Infrastructure
**Status:** Resolved - Production Ready

## Summary

The ii-researcher SSE parsing bug has been fixed and verified in production. Research tasks now correctly capture full deep search reports from ii-researcher.

## Root Cause

The ResearchTaskExecutor was looking for SSE events in the wrong format:
- **Expected:** `event_data.get('answer')`
- **Actual ii-researcher format:** `event_data['data']['final_report']`

## Fix Applied

File: `/ganuda/jr_executor/research_task_executor.py` (lines ~308-335)

```python
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])
                event_type = event_data.get('type', '')
                # ii-researcher nests data in 'data' field
                data = event_data.get('data', {})

                if event_type == 'complete':
                    answer = data.get('final_report', '')
```

Additional fixes:
- Increased timeout from 180s to 300s
- Added `assigned_jr` to `jr_queue_client.py` RETURNING clause
- Added `stream_closed` event handling

## Verification

**Task 625** - "FINAL: Research Pipeline Test"
- Status: Completed successfully
- Steps: 22/22 succeeded
- Output quality: Excellent (200+ line research reports with citations)
- Sample output: `/ganuda/docs/research/fetched_web_ea38b486.md`

Example output quality (Claude Constitution research):
- Detailed principal hierarchy analysis
- Proper source citations (Anthropic News, Nate's Newsletter)
- Well-structured sections with headings
- Reference list with URLs

## Remaining Cosmetic Issue

The step tracking shows "sources_fetched: 0" even though content is captured. This is because:
- Source events (`type: 'source'`) may not be sent by ii-researcher
- Only the final report is captured via `complete` event
- The content IS captured correctly, just not the source URL count

**Priority:** P3 - Cosmetic only, doesn't affect functionality

## Commits

- `f612ca1` - SSE parsing fix for `final_report` extraction
- `526f7b1` - Added `assigned_jr` to RETURNING clause

## Related Files

- `/ganuda/jr_executor/research_task_executor.py`
- `/ganuda/jr_executor/jr_queue_client.py`
- `/ganuda/services/ii-researcher/ii_researcher/utils/stream.py`

## For Seven Generations

This fix enables the Research Jr. to properly leverage ii-researcher's deep search capabilities, building the Federation's knowledge base with high-quality research outputs.
