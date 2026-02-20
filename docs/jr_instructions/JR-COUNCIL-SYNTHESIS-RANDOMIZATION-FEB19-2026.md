# Jr Instruction: Randomize Peace Chief Synthesis Order

**Task ID**: COUNCIL-SYNTH-001
**Priority**: 3 (medium)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 2
**use_rlm**: false
**Council Vote**: #e854c208794e9250 (PROCEED, 0.845)

## Context

When Peace Chief synthesizes consensus from specialist responses, the responses are summarized in dictionary insertion order (crawdad first, raven last). This creates a position bias — the first specialist summarized gets disproportionate influence on the synthesis. Per CMU adversarial robustness research (arXiv:2602.13093), LLMs are susceptible to primacy effects. Randomizing the order prevents any specialist from systematically dominating synthesis.

This applies to BOTH implementations (specialist_council.py AND gateway.py — dual pipeline).

## Step 1: Randomize Synthesis in specialist_council.py

File: `/ganuda/lib/specialist_council.py`

Find the `_synthesize_consensus()` method where it builds the summary string from responses. Add `import random` at the top of the file if not already present, then shuffle the response list before summarizing.

<<<<<<< SEARCH
import random
=======
import random
>>>>>>> REPLACE

If `import random` does not exist at the top of the file, add it after the other imports:

<<<<<<< SEARCH
from datetime import datetime
=======
from datetime import datetime
import random
>>>>>>> REPLACE

Then find the consensus synthesis loop. It will look approximately like:

<<<<<<< SEARCH
        summary = f"Question: {question}\n\nSpecialist responses:\n"
        for r in responses:
            summary += f"\n{r.name} ({r.role}): {r.response[:300]}"
=======
        summary = f"Question: {question}\n\nSpecialist responses:\n"
        shuffled = list(responses)
        random.shuffle(shuffled)
        for r in shuffled:
            summary += f"\n{r.name} ({r.role}): {r.response[:300]}"
>>>>>>> REPLACE

## Step 2: Randomize Synthesis in gateway.py

File: `/ganuda/scripts/cherokee_council_gateway.py`

Find where the gateway builds the consensus synthesis prompt. It will look approximately like:

<<<<<<< SEARCH
        summaries = [f"- {name}: {resp[:150].replace(chr(10), ' ')}..." for name, resp in responses.items()]
=======
        response_items = list(responses.items())
        random.shuffle(response_items)
        summaries = [f"- {name}: {resp[:150].replace(chr(10), ' ')}..." for name, resp in response_items]
>>>>>>> REPLACE

Ensure `import random` is present at the top of gateway.py as well.

## Manual Steps (TPM)

After Jr execution:
1. `rm -rf /ganuda/lib/__pycache__/ /ganuda/scripts/__pycache__/` on redfin
2. `ganuda-service-ctl restart llm-gateway` on redfin
3. Run 3 council votes on the same question and verify that synthesis order varies
