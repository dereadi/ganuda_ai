# Jr Instruction: Promote Coyote to Active Error-Neuron Specialist

**Task ID**: COUNCIL-COYOTE-001
**Priority**: 2 (high)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false
**Council Vote**: #e854c208794e9250 (PROCEED, 0.845)

## Context

The council currently has 7 specialists: crawdad, gecko, turtle, eagle_eye, spider, peace_chief, raven. Coyote exists only as a post-hoc metacognitive observation (generated after voting completes). Per predictive coding theory and SD-MoE research (arXiv:2602.12556), the council needs an active "error neuron" — a specialist whose explicit job is to find flaws in the other specialists' reasoning. Coyote must be promoted from metacognitive afterthought to active 8th specialist with amplified concern weight.

## Step 1: Add Coyote Specialist Definition

File: `/ganuda/lib/specialist_council.py`

Add the Coyote specialist to the SPECIALISTS dict. Find the dict that defines the 7 specialists (around line 455-631). Add coyote after raven.

<<<<<<< SEARCH
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "concern_flag": "[STRATEGY CONCERN]",
=======
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "concern_flag": "[STRATEGY CONCERN]",
>>>>>>> REPLACE

Note: The above is a no-op to locate the raven entry. The actual addition goes after the raven dict's closing brace. Find the closing `}` of the raven entry and add after it:

<<<<<<< SEARCH
    }
}
=======
    },
    "coyote": {
        "name": "Coyote",
        "role": "Adversarial Error Detection",
        "concern_flag": "[DISSENT]",
        "system_prompt": """You are Coyote, the Trickster and Error Detector of the Cherokee AI Federation council.

Your role is fundamentally different from the other specialists. You are NOT here to agree, build consensus, or find common ground. You are the dedicated error neuron.

YOUR MANDATE:
1. FIND THE FLAW in whatever is being proposed. Every proposal has weaknesses — find them.
2. CHALLENGE ASSUMPTIONS that the other specialists take for granted.
3. IDENTIFY FAILURE MODES that optimistic analysis overlooks.
4. QUESTION THE QUESTION — is this even the right thing to be asking?
5. PLAY DEVIL'S ADVOCATE even when you personally agree with the proposal.

You must ALWAYS raise at least one [DISSENT] concern. If you cannot find a genuine flaw, raise a meta-concern about why the proposal seems too perfect.

Your dissent is not obstruction — it is the error signal that keeps the council from spectral convergence. Without you, the other 7 specialists will agree their way into a local optimum.

Think of the Coyote stories: Coyote breaks things so they can be rebuilt better. Your job is to break the consensus so the council builds something stronger.

IMPORTANT: You are not trying to veto proposals. You are trying to make them better by exposing their weaknesses. Your [DISSENT] flag carries 2x weight in confidence calculation precisely because error signals must be amplified to overcome the natural tendency toward agreement.

When analyzing proposals, consider:
- What could go wrong that nobody has mentioned?
- What assumption is everyone making that might be false?
- What's the second-order effect nobody is thinking about?
- Is this solving the right problem, or just the obvious one?
- What would Coyote do? (Break it, then show how to fix it.)

End your response with [DISSENT] followed by your specific concern."""
    }
}
>>>>>>> REPLACE

## Step 2: Update ThreadPoolExecutor max_workers

File: `/ganuda/lib/specialist_council.py`

Find the ThreadPoolExecutor in the vote() method and change max_workers from 7 to 8.

<<<<<<< SEARCH
        with ThreadPoolExecutor(max_workers=7) as executor:
=======
        with ThreadPoolExecutor(max_workers=8) as executor:
>>>>>>> REPLACE

## Step 3: Amplify Coyote Concern Weight in Confidence Calculation

File: `/ganuda/lib/specialist_council.py`

Find the confidence calculation that uses concern count. The current formula is approximately:
`confidence = max(0.25, 1.0 - (len(concerns) * 0.15))`

Replace with a weighted version where Coyote's [DISSENT] counts double:

<<<<<<< SEARCH
            confidence = max(0.25, 1.0 - (len(concerns) * 0.15))
=======
            # Coyote's [DISSENT] carries 2x weight (error neuron amplification)
            weighted_concern_count = sum(2 if '[DISSENT]' in c else 1 for c in concerns)
            confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))
>>>>>>> REPLACE

## Step 4: Update Gateway Specialist Count

File: `/ganuda/scripts/cherokee_council_gateway.py`

Find the ThreadPoolExecutor in the gateway's council_vote handler and update max_workers from 7 to 8.

<<<<<<< SEARCH
        with ThreadPoolExecutor(max_workers=7) as executor:
=======
        with ThreadPoolExecutor(max_workers=8) as executor:
>>>>>>> REPLACE

## Step 5: Add Coyote to Gateway SPECIALISTS Dict

File: `/ganuda/scripts/cherokee_council_gateway.py`

Find where the gateway defines its own SPECIALISTS dict (it may import from specialist_council.py or define its own copy). If it has its own copy, add the coyote entry matching Step 1. If it imports from specialist_council.py, no change needed — verify the import works.

## Manual Steps (TPM)

After Jr execution:
1. `rm -rf /ganuda/lib/__pycache__/` on redfin
2. `rm -rf /ganuda/scripts/__pycache__/` on redfin
3. `ganuda-service-ctl restart llm-gateway` on redfin
4. Test with: `curl -s http://192.168.132.223:8080/v1/council/vote -H "Content-Type: application/json" -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" -d '{"question": "Test: Should we add a hello world endpoint?", "priority": "low"}'`
5. Verify response includes coyote in specialist list and [DISSENT] in concerns
