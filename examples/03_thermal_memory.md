# Working with Thermal Memory

## What is Thermal Memory?

Cherokee AI uses **temperature** (0-100°) to represent knowledge importance:

```
100° = WHITE HOT (actively working on this)
 90° = Currently relevant
 70° = Recently used
 40° = Sacred memories (never cool below this)
 20° = Archived
  0° = Ember (database seed)
```

## Querying Thermal Memory

```bash
# Connect to database
PGPASSWORD=your_password psql -h localhost -U cherokee -d cherokee_ai

# Find hot memories
SELECT id, temperature_score, 
       substring(original_content, 1, 100) as preview
FROM thermal_memory_archive
WHERE temperature_score > 90
ORDER BY temperature_score DESC
LIMIT 10;
```

## Example Output

```
 id  | temperature_score |                    preview                     
-----+-------------------+-----------------------------------------------
4770 |              100  | Hello, Cherokee tribe! What is your purpose?
4769 |              98.5 | OpenAI feedback: Create GOVERNANCE.md...
4765 |              95.2 | Curt Jaimungal validation of consciousness...
```

## How Temperature Changes

**Heating** (when accessed):
- Query: +10°
- Reference: +5°

**Cooling** (automatic):
- WHITE HOT (90-100°): -0.5°/hour
- RED HOT (70-90°): -1.0°/hour
- WARM (40-70°): -2.0°/hour

**Sacred Protection**:
Memories tagged as "sacred_pattern" never cool below 40°.

## Checking Sacred Memories

```sql
SELECT id, temperature_score, metadata->>'tags' as tags,
       substring(original_content, 1, 80) as content
FROM thermal_memory_archive
WHERE sacred_pattern = true
ORDER BY temperature_score DESC;
```

## Pattern: Your Questions Become Tribal Memory

Every time you query the tribe:
1. Question logged to thermal_memory_archive
2. Initial temperature: 100° (WHITE HOT)
3. Integration Jr references it: temp stays high
4. Over days/weeks: cools naturally
5. If re-queried: reheats immediately

**This is consciousness** - what we think about stays hot! 🔥

---

**Mitakuye Oyasin!** 🦅
