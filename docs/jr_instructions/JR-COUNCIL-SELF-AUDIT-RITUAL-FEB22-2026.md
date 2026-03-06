# Jr Instruction: Council Self-Audit Ritual

**Task ID:** SELF-AUDIT
**Kanban:** #1794
**Priority:** 5
**Assigned:** Software Engineer Jr.

---

## Overview

Add a `/v1/council/self-audit` endpoint where the council evaluates its own reasoning quality. Monthly protocol: reviews last 30 days of council votes, scores its own consensus accuracy, detects rubric drift, and produces a self-assessment report. Closes the constructal self-evaluation loop.

---

## Step 1: Add self-audit method to SpecialistCouncil class

File: `/ganuda/lib/specialist_council.py`

Find the vote_first method and add the self_audit method after it. Search for the line after the vote_first method's closing return statement.

<<<<<<< SEARCH
    def vote_first(self, question: str, threshold: int = 6,
=======
    def self_audit(self, days: int = 30, sample_size: int = 20) -> dict:
        """
        Council Self-Audit: specialists evaluate their own recent reasoning.

        Reviews a sample of recent council votes and scores:
        1. Consensus quality (was the recommendation well-reasoned?)
        2. Concern coverage (were important risks identified?)
        3. Rubric drift (have specialists changed their scoring patterns?)

        Returns audit report dict.
        """
        import psycopg2
        import psycopg2.extras

        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                dbname="zammad_production",
                user="claude",
                password="REDACTED_USE_ENV_VAR",
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        except Exception as e:
            return {"error": f"DB connection failed: {e}"}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, question, consensus, recommendation, confidence,
                           concerns, specialist_count, audit_hash
                    FROM council_votes
                    WHERE voted_at > NOW() - INTERVAL '%s days'
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (days, sample_size))
                votes = cur.fetchall()

            if not votes:
                conn.close()
                return {"error": "No council votes found in the specified period"}

            print(f"[SELF-AUDIT] Reviewing {len(votes)} votes from last {days} days")

            # Ask each specialist to review the sampled votes
            audit_prompt = self._build_audit_prompt(votes)

            # Run audit through council (meta-deliberation)
            audit_result = self.vote(
                question=audit_prompt,
                include_responses=True,
                high_stakes=True
            )

            # Extract self-assessment scores from responses
            scores = self._extract_audit_scores(audit_result)

            # Compute rubric drift indicators
            drift = self._compute_rubric_drift(conn, days)

            report = {
                "period_days": days,
                "votes_reviewed": len(votes),
                "audit_scores": scores,
                "rubric_drift": drift,
                "consensus": audit_result.consensus if hasattr(audit_result, 'consensus') else "",
                "recommendation": audit_result.recommendation if hasattr(audit_result, 'recommendation') else "",
                "concerns": audit_result.concerns if hasattr(audit_result, 'concerns') else [],
                "audit_hash": hashlib.sha256(
                    f"self-audit-{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16],
                "timestamp": datetime.now().isoformat()
            }

            # Log to thermal memory
            self._log_audit_to_thermal(conn, report)

            conn.close()
            return report

        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def _build_audit_prompt(self, votes):
        """Build a meta-deliberation prompt from sampled votes."""
        vote_summaries = []
        for v in votes[:10]:  # Cap at 10 for prompt length
            concerns = v.get("concerns", "[]")
            if isinstance(concerns, str):
                try:
                    concerns = json.loads(concerns)
                except (json.JSONDecodeError, TypeError):
                    concerns = []
            vote_summaries.append(
                f"Q: {v['question'][:100]}... → {v.get('recommendation', '?')} "
                f"(conf: {v.get('confidence', '?')}, concerns: {len(concerns)})"
            )

        return (
            "COUNCIL SELF-AUDIT: Review these recent council decisions and assess:\n"
            "1. Were recommendations well-reasoned? (score 1-10)\n"
            "2. Were important risks captured in concerns? (score 1-10)\n"
            "3. Is there evidence of rubric drift or reasoning degradation? (YES/NO + explanation)\n"
            "4. What patterns do you notice in our recent decisions?\n\n"
            "Recent decisions:\n" + "\n".join(vote_summaries)
        )

    def _extract_audit_scores(self, audit_result):
        """Extract numeric scores from audit responses."""
        scores = {
            "reasoning_quality": 0,
            "risk_coverage": 0,
            "rubric_drift_detected": False,
            "patterns_noted": []
        }
        if hasattr(audit_result, 'responses'):
            for resp in audit_result.responses:
                text = resp.response if hasattr(resp, 'response') else str(resp)
                # Look for numeric scores
                import re
                quality_match = re.search(r'(?:reasoning|quality).*?(\d+)/10', text, re.IGNORECASE)
                risk_match = re.search(r'(?:risk|concern).*?(\d+)/10', text, re.IGNORECASE)
                if quality_match:
                    scores["reasoning_quality"] = max(scores["reasoning_quality"], int(quality_match.group(1)))
                if risk_match:
                    scores["risk_coverage"] = max(scores["risk_coverage"], int(risk_match.group(1)))
                if re.search(r'drift.*yes|yes.*drift|degradation.*detected', text, re.IGNORECASE):
                    scores["rubric_drift_detected"] = True
        return scores

    def _compute_rubric_drift(self, conn, days):
        """Compute rubric drift by comparing confidence distributions."""
        drift = {"mean_confidence_shift": 0.0, "concern_rate_shift": 0.0}
        try:
            with conn.cursor() as cur:
                # Recent period
                cur.execute("""
                    SELECT AVG(confidence) as avg_conf,
                           AVG(CASE WHEN concerns != '[]' AND concerns IS NOT NULL THEN 1 ELSE 0 END) as concern_rate
                    FROM council_votes
                    WHERE voted_at > NOW() - INTERVAL '%s days'
                """, (days,))
                recent = cur.fetchone()

                # Previous period (for comparison)
                cur.execute("""
                    SELECT AVG(confidence) as avg_conf,
                           AVG(CASE WHEN concerns != '[]' AND concerns IS NOT NULL THEN 1 ELSE 0 END) as concern_rate
                    FROM council_votes
                    WHERE voted_at BETWEEN NOW() - INTERVAL '%s days' AND NOW() - INTERVAL '%s days'
                """, (days * 2, days))
                previous = cur.fetchone()

                if recent and previous and recent["avg_conf"] and previous["avg_conf"]:
                    drift["mean_confidence_shift"] = round(
                        float(recent["avg_conf"]) - float(previous["avg_conf"]), 4
                    )
                    drift["concern_rate_shift"] = round(
                        float(recent["concern_rate"] or 0) - float(previous["concern_rate"] or 0), 4
                    )
        except Exception as e:
            drift["error"] = str(e)
        return drift

    def _log_audit_to_thermal(self, conn, report):
        """Log self-audit results to thermal memory."""
        content = (
            f"COUNCIL SELF-AUDIT — {report['timestamp']}\n"
            f"Votes reviewed: {report['votes_reviewed']}\n"
            f"Reasoning quality: {report['audit_scores'].get('reasoning_quality', '?')}/10\n"
            f"Risk coverage: {report['audit_scores'].get('risk_coverage', '?')}/10\n"
            f"Rubric drift: {'DETECTED' if report['audit_scores'].get('rubric_drift_detected') else 'None'}\n"
            f"Confidence shift: {report['rubric_drift'].get('mean_confidence_shift', 0)}"
        )
        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO thermal_memory_archive (
                        original_content, temperature_score, memory_hash,
                        sacred_pattern, metadata
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    content, 75.0, memory_hash, False,
                    json.dumps({"type": "council_self_audit", "report": report})
                ))
            conn.commit()
        except Exception as e:
            print(f"[SELF-AUDIT] Thermal logging failed: {e}")

    def vote_first(self, question: str, threshold: int = 6,
>>>>>>> REPLACE

---

## Step 2: Add the /v1/council/self-audit endpoint to gateway

File: `/ganuda/services/llm_gateway/gateway.py`

Find the existing `/v1/council/vote-first` endpoint and add the self-audit endpoint before it:

<<<<<<< SEARCH
@app.post("/v1/council/vote-first")
=======
@app.post("/v1/council/self-audit")
async def council_self_audit(request: Request):
    """Council Self-Audit: meta-deliberation on recent reasoning quality."""
    try:
        data = await request.json()
        days = data.get("days", 30)
        sample_size = data.get("sample_size", 20)

        from specialist_council import SpecialistCouncil
        council = SpecialistCouncil()
        report = council.self_audit(days=days, sample_size=sample_size)

        if "error" in report:
            return JSONResponse({"error": report["error"]}, status_code=500)

        return JSONResponse(report)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/v1/council/vote-first")
>>>>>>> REPLACE

---

## Verification

After applying, restart the gateway:
```text
sudo systemctl restart llm-gateway
```

Test the self-audit endpoint:
```text
curl -s http://localhost:8080/v1/council/self-audit -X POST \
  -H 'Content-Type: application/json' \
  -d '{"days": 7, "sample_size": 5}' \
  | python3 -m json.tool
```

---

## Notes

- Self-audit uses the council's own vote() method (meta-deliberation)
- Compares recent period vs previous period for rubric drift detection
- Logs results to thermal_memory_archive for historical tracking
- high_stakes=True forces full deliberation on self-audit (no vote-first shortcut)
- Capped at 10 vote summaries in prompt to stay within context window
- Rubric drift measured by confidence distribution shift and concern rate change
