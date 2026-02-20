# Jr Instruction: VetAssist P0 — Voting-First Council Mode

**Kanban:** #1824
**Council Vote:** #fadf71ec28884489 (PROCEED, 0.89) + #0774f4580abd0cdb (original roadmap)
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.
**Long Man Phase:** BUILD

---

## Overview

Wire the existing `council_vote_first()` function from specialist_council.py into VetAssist's chat endpoint. This gives veterans faster responses (2-3s vs 8-12s) when all 7 specialists agree, and only triggers full deliberation when there's disagreement or high-stakes content.

The `vote_first()` method ALREADY EXISTS in specialist_council.py. We just need to:
1. Import it into council_chat.py
2. Add an `ask_council_vote_first()` method to CouncilChatService
3. Wire it into the chat endpoint with a mode parameter

---

## Step 1: Import council_vote_first into council_chat.py

File: `/ganuda/vetassist/backend/app/services/council_chat.py`

<<<<<<< SEARCH
SpecialistCouncil = _council_module.SpecialistCouncil
council_vote = _council_module.council_vote
=======
SpecialistCouncil = _council_module.SpecialistCouncil
council_vote = _council_module.council_vote
council_vote_first = _council_module.council_vote_first
>>>>>>> REPLACE

---

## Step 2: Add ask_council_vote_first method to CouncilChatService

File: `/ganuda/vetassist/backend/app/services/council_chat.py`

<<<<<<< SEARCH
    def get_specialist_badge_color(self, specialist_name: str) -> str:
        """
        Get color code for specialist badge in UI.

        Returns:
            Hex color code
=======
    def ask_council_vote_first(
        self,
        user_question: str,
        session_history: List[Dict] = None,
        high_stakes: bool = False
    ) -> Dict:
        """
        Ask the Council using vote-first mode: fast vote → conditional deliberation.

        6/7 APPROVE = skip deliberation (2-3s response).
        Contested or high_stakes = full deliberation (8-12s response).

        Returns same dict shape as ask_council() for drop-in compatibility.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Format question with VA context (same as standard mode)
        formatted_question = self.format_question_for_council(user_question, session_history)

        # Inject CFR regulatory context if available
        if CFR_RETRIEVER_AVAILABLE:
            try:
                retriever = get_cfr_retriever()
                if retriever.ready:
                    cfr_results = retriever.retrieve(user_question, top_k=3)
                    if cfr_results:
                        cfr_context = retriever.format_context(cfr_results, max_chars=3000)
                        formatted_question = cfr_context + "\n\n" + formatted_question
            except Exception as e:
                logger.warning(f"[RAG-CFR] Context retrieval failed: {e}")

        # Use vote-first mode from specialist_council.py
        vote_result = council_vote_first(
            question=formatted_question,
            threshold=6,
            high_stakes=high_stakes
        )

        # Map vote_first result to standard ask_council response shape
        decision = vote_result.get("decision", "CONTESTED")
        votes = vote_result.get("votes", {})
        deliberation = vote_result.get("deliberation", "")
        vote_counts = vote_result.get("vote_counts", {})

        # Build consensus text from deliberation or vote reasons
        if deliberation:
            consensus = deliberation
        else:
            # No deliberation needed — build response from vote reasons
            approve_reasons = []
            for spec_id, vote_data in votes.items():
                if isinstance(vote_data, dict):
                    if vote_data.get("vote") == "APPROVE":
                        reason = vote_data.get("reason", "")
                        if reason:
                            approve_reasons.append(reason)
            consensus = " ".join(approve_reasons) if approve_reasons else "The Council approved this response unanimously."

        # Add educational disclaimer
        if "educational" not in consensus.lower() and "not legal advice" not in consensus.lower():
            consensus += "\n\n*This is educational information only, not legal advice. For personalized guidance, consult a Veterans Service Organization (VSO).*"

        # Extract citations
        citations = self.extract_citations(consensus)

        # Map decision to recommendation
        if decision == "APPROVED":
            recommendation = "PROCEED"
            confidence = 0.90
        elif decision == "CONTESTED":
            recommendation = "PROCEED WITH CAUTION"
            confidence = 0.70
        else:
            recommendation = "REVIEW REQUIRED"
            confidence = 0.50

        # Build all_responses from votes for specialist attribution
        all_responses = []
        for spec_id, vote_data in votes.items():
            if isinstance(vote_data, dict):
                all_responses.append({
                    "name": vote_data.get("name", spec_id),
                    "response": vote_data.get("reason", ""),
                    "has_concern": vote_data.get("vote") == "REJECT"
                })

        # Get primary specialist from responses
        primary_specialist = self.get_primary_specialist(all_responses) if all_responses else "Council"

        # Collect concerns (REJECT votes)
        concerns = [
            f"{v.get('name', k)}: {v.get('reason', '')}"
            for k, v in votes.items()
            if isinstance(v, dict) and v.get("vote") == "REJECT"
        ]

        return {
            "response": consensus,
            "specialist": primary_specialist,
            "confidence": float(confidence),
            "citations": citations,
            "concerns": concerns,
            "recommendation": recommendation,
            "all_responses": all_responses,
            "audit_hash": vote_result.get("audit_hash", ""),
            "council_mode": "vote-first",
            "vote_counts": vote_counts,
            "decision": decision
        }

    def get_specialist_badge_color(self, specialist_name: str) -> str:
        """
        Get color code for specialist badge in UI.

        Returns:
            Hex color code
>>>>>>> REPLACE

---

## Step 3: Wire vote-first mode into chat endpoint

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

<<<<<<< SEARCH
    # Query Ganuda Council
    council_service = CouncilChatService()
    try:
        council_response = council_service.ask_council(
            user_question=message_data.content,
            session_history=history
        )
=======
    # Query Ganuda Council
    council_service = CouncilChatService()
    try:
        # Use vote-first mode for faster responses (2-3s vs 8-12s)
        # Falls back to full deliberation when contested or high_stakes
        council_response = council_service.ask_council_vote_first(
            user_question=message_data.content,
            session_history=history,
            high_stakes=False
        )
>>>>>>> REPLACE

---

## Manual Steps (TPM)

After Jr completes:

1. Restart VetAssist backend on redfin:
```text
sudo systemctl restart vetassist-backend
```

2. Test via curl:
```text
curl -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<valid-session-id>", "content": "What evidence do I need for a PTSD claim?"}'
```

3. Check response includes `council_mode: "vote-first"` and `vote_counts`.

4. Monitor response latency — should be 2-3s for consensus, 8-12s for contested.

---

## Acceptance Criteria

- [ ] `council_vote_first` imported in council_chat.py
- [ ] `ask_council_vote_first()` method returns same shape as `ask_council()`
- [ ] Chat endpoint uses vote-first by default
- [ ] Response includes `council_mode`, `vote_counts`, `decision` fields
- [ ] Educational disclaimer appended when missing
- [ ] CFR regulatory context injected when available
- [ ] No breaking changes to crisis detection flow
- [ ] Falls back to deliberation on contested votes
