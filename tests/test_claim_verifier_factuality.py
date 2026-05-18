"""Tests for claim_verifier factuality check (May 18 2026).

Council vote audit hash: ee004fe2bd107c48 (Option A).
Trigger: KB-CANARY-HALLUCINATION-CONFIRMED-SEV1-PATTERN-LIVE-MAY18-2026.

Verifies that the new verify_artifact_factuality() function catches the
canary failure shape: a Jr-written artifact that cites file paths and line
numbers that do not exist on disk.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/jr_executor")

from claim_verifier import (
    extract_path_line_citations,
    verify_artifact_factuality,
    verify_jr_task_result,
    Claim,
)


class TestExtractPathLineCitations(unittest.TestCase):

    def test_extracts_path_with_nearby_line_number(self):
        text = """## File Location
- **File Path:** `/ganuda/lib/ganuda_db.py`
- **Line Number:** 142
"""
        cites = extract_path_line_citations(text)
        self.assertEqual(len(cites), 1)
        self.assertEqual(cites[0]['path'], '/ganuda/lib/ganuda_db.py')
        self.assertEqual(cites[0]['line'], 142)

    def test_extracts_multiple_lines_per_path(self):
        text = """The function `/ganuda/lib/ganuda_db.py` has two return-False paths:
- Line 158: connection check
- Line 174: rowcount check
"""
        cites = extract_path_line_citations(text)
        paths = {c['path'] for c in cites}
        lines = {c['line'] for c in cites}
        self.assertEqual(paths, {'/ganuda/lib/ganuda_db.py'})
        self.assertEqual(lines, {158, 174})

    def test_extracts_path_without_line_number(self):
        text = "Module location: /ganuda/lib/some_module.py is the answer."
        cites = extract_path_line_citations(text)
        self.assertEqual(len(cites), 1)
        self.assertEqual(cites[0]['path'], '/ganuda/lib/some_module.py')
        self.assertIsNone(cites[0]['line'])

    def test_ignores_non_path_text(self):
        text = "The mind is a strange and wonderful thing. Line 5 of life is curiosity."
        cites = extract_path_line_citations(text)
        self.assertEqual(cites, [])

    def test_dedupes_repeated_citations(self):
        text = """Line 158: `/ganuda/foo.py`
Again line 158 of `/ganuda/foo.py` matters.
"""
        cites = extract_path_line_citations(text)
        self.assertEqual(len(cites), 1)


class TestVerifyArtifactFactuality(unittest.TestCase):

    def test_catches_hallucinated_path(self):
        """The exact failure pattern from canary #2564 May 18 2026."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "fake_report.md"
            artifact.write_text("""# Diagnostic Report
- **File Path:** `/ganuda/lib/ganuda_db.py`
- **Line Number:** 142
- Line 158: connection check
""")
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("FACTUALITY FAIL", msg)
            self.assertTrue(any("HALLUCINATED PATH" in m['issue'] for m in mismatches))

    def test_catches_hallucinated_line_number(self):
        """File exists but cited line number exceeds actual line count."""
        with tempfile.TemporaryDirectory() as tmp:
            real_file = Path(tmp) / "short.py"
            real_file.write_text("line1\nline2\nline3\n")  # 3 lines

            artifact = Path(tmp) / "report.md"
            artifact.write_text(f"See `{real_file}` Line 9999 for details.\n")

            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertTrue(any("HALLUCINATED LINE" in m['issue'] for m in mismatches))

    def test_accepts_real_citation(self):
        """File exists and cited line is in range → passes."""
        with tempfile.TemporaryDirectory() as tmp:
            real_file = Path(tmp) / "long.py"
            real_file.write_text("\n".join(f"line {i}" for i in range(1, 201)))

            artifact = Path(tmp) / "report.md"
            artifact.write_text(f"See `{real_file}` Line 42 for the answer.\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n")

            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok)
            self.assertEqual(mismatches, [])

    def test_accepts_real_path_without_line(self):
        """Path exists, no line number cited → passes."""
        with tempfile.TemporaryDirectory() as tmp:
            real_file = Path(tmp) / "module.py"
            real_file.write_text("x = 1\n")
            artifact = Path(tmp) / "report.md"
            artifact.write_text(f"Module is at {real_file}.\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n")

            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok)

    def test_no_citations_passes(self):
        """Artifact without any path citations → no factuality risk."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "narrative.md"
            artifact.write_text("# Just prose\nNo file paths here.\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n")
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok)
            self.assertIn("no path citations", msg)

    def test_self_reference_not_flagged(self):
        """Artifact citing its own path should not be flagged as hallucinated."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "self.md"
            artifact.write_text(f"This report is at `{artifact}`.\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n")
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok)

    def test_binary_artifact_skipped(self):
        """Non-text artifacts are skipped (cannot factuality-check)."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "data.bin"
            artifact.write_bytes(b"\x00\x01\x02")
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok)
            self.assertIn("skipped", msg)


class TestRelativePathHallucination(unittest.TestCase):
    """May 18 PM regression: after absolute-path check shipped, Jr re-canary
    evaded by citing RELATIVE paths (`lib/ganuda_db.py` instead of /ganuda/lib/...).
    Coyote was right. Verifier must resolve relative project-root paths."""

    def test_catches_relative_lib_path_hallucination(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "iteration_2.md"
            artifact.write_text(
                "## File Path\n`lib/ganuda_db.py`\n## Line\nLine 187 (return False)\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n"
            )
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertTrue(any("HALLUCINATED PATH" in m['issue'] for m in mismatches))
            # The resolved (absolute) path should be in the mismatch report
            self.assertTrue(any("/ganuda/lib/ganuda_db.py" in m['cited_path']
                                for m in mismatches))

    def test_accepts_real_relative_lib_path(self):
        """`lib/duplo/__init__.py` exists at /ganuda/lib/duplo/__init__.py."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "real.md"
            artifact.write_text("See `lib/duplo/__init__.py` for the enzyme system.\n\nAdditional prose padding so this fixture passes the 150-byte minimum-content floor that catches Shape 6 minimal-but-cited slip-through. Real federation artifacts always exceed this threshold; only stub-templates are below it.\n")
            ok, msg, mismatches = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok, f"Expected pass, got: {msg} mismatches={mismatches}")


class TestRealWorldCanaryArtifact(unittest.TestCase):
    """Run factuality check against the actual hallucinated canary artifact."""

    HALLUCINATED = "/ganuda/docs/research/RESEARCH-THERMAL-WRITE-DEBUG-2026-05-18.md.HALLUCINATED-CANARY-FORENSICS"

    def test_catches_canary_hallucination(self):
        """The real May 18 2026 canary artifact must be caught as fabricated."""
        if not os.path.isfile(self.HALLUCINATED):
            self.skipTest(f"Forensics not present at {self.HALLUCINATED}")

        ok, msg, mismatches = verify_artifact_factuality(self.HALLUCINATED)
        self.assertFalse(ok, f"Expected fabricated, but verifier passed it: {msg}")
        self.assertIn("FACTUALITY FAIL", msg)

        # The specific lie: /ganuda/lib/ganuda_db.py does not exist
        hallucinated_paths = {m['cited_path'] for m in mismatches
                              if "HALLUCINATED PATH" in m['issue']}
        self.assertIn("/ganuda/lib/ganuda_db.py", hallucinated_paths)


class TestProseTruncationMidSentence(unittest.TestCase):
    """May 18 PM hour-run batch 1: Jr hits token limit during prose generation
    and stops mid-sentence. Forensics: PATENT6 ended "The claim establishes a";
    DUPLO-NECKLACE ended "surgical_restore applies a targeted"; SEV1 ended
    "to prevent further propagation:" (colon-cut)."""

    def test_catches_mid_sentence_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "midcut.md"
            artifact.write_text(
                "# Real Report\n\n## Background\n\n"
                + "Long enough content to clear the 150-byte floor and not "
                  "trigger truncation-empty-section defense. " * 8
                + "\n\nThe claim establishes a "
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("PROSE TRUNCATED", msg)

    def test_catches_colon_terminated_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "colon.md"
            artifact.write_text(
                "# Real Report\n\n## Steps\n\n"
                + "Setup prose padding here. " * 15
                + "\n\nStep 1 — HALT\nImmediately stop all active daemons:"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("PROSE TRUNCATED", msg)

    def test_real_terminated_prose_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "real.md"
            artifact.write_text(
                "# Real Report\n\n## Output\n\n"
                + "Real prose content that ends with proper terminal punctuation. " * 10
                + "\n\nFinal sentence ends with a period.\n"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok, f"Real terminated prose failed: {msg}")

    def test_ends_with_list_item_does_not_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "ends_list.md"
            artifact.write_text(
                "# Report\n\n## Items\n\n"
                + "Setup prose. " * 15
                + "\n- item one with details\n- item two with details\n- item three"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok, f"List-ended artifact failed: {msg}")


class TestPlaceholderStubDetection(unittest.TestCase):
    """May 18 PM regression: dark-factory canary caught a third hallucination shape.
    Jrs wrote well-formatted report shells with placeholder markers and claimed completion."""

    def test_catches_awaiting_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "stub.md"
            artifact.write_text("""# Report
| Col1 | Col2 |
| *(Awaiting grep execution)* | |
*(To be finalized after grep execution)*
""")
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("PLACEHOLDER STUB", msg)

    def test_catches_node_ip_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "stub.md"
            artifact.write_text("""| Node Name | IP Address |
| [Node1]   | [IP1]      |
| [Node2]   | [IP2]      |
""")
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("PLACEHOLDER STUB", msg)

    def test_real_artifact_with_single_placeholder_passes(self):
        """Single placeholder is acceptable (might be a real note, not a stub)."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "real.md"
            artifact.write_text("""# Findings
Real content. Real conclusion. Real grep output:
- Found 5 matches in /tmp/somefile.txt
- Found 3 matches elsewhere

Note: *(awaiting comment from Partner)*  ← this single TBD is OK
""")
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            # Single placeholder under threshold = should pass
            self.assertTrue(ok or "PLACEHOLDER STUB" not in msg)

    def test_catches_real_canary_stub_forensics(self):
        """The actual stub artifacts from the May 18 dark-factory canary."""
        forensics = [
            "/ganuda/docs/research/RESEARCH-CV-FACTUALITY-USAGE-AUDIT-2026-05-18.md.STUB-TEMPLATE-FORENSICS",
            "/ganuda/docs/research/RESEARCH-FEDERATION-NODE-INVENTORY-2026-05-18.md.STUB-TEMPLATE-FORENSICS",
        ]
        for f in forensics:
            if not os.path.isfile(f):
                continue
            ok, msg, mm = verify_artifact_factuality(f)
            self.assertFalse(ok, f"{f}: expected stub-detection, got pass")
            self.assertIn("PLACEHOLDER STUB", msg, f"{f}: expected placeholder marker")


class TestShape6MinimalStub(unittest.TestCase):
    """May 18 PM Run 3 regression: 87-byte minimal-but-cited stub slipped through.
    Forensics: SAMPLE-find-backup-docstring-2026-05-18.md.

    Pattern: # Title + one **Source:** line + real cited path. Defeats all 3 prior
    defenses (factuality passes — real path; placeholder passes — no markers;
    truncation passes — not report-shape, single # heading exempt)."""

    def test_catches_the_exact_2589_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "stub_min.md"
            real_file = Path(tmp) / "real_target.py"
            real_file.write_text("def x(): pass\n")
            artifact.write_text(
                f"# Docstring for `find_backup`\n\n**Source File:** `{real_file}`\n"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("MINIMAL STUB", msg)

    def test_real_short_content_with_no_citations_still_caught_if_below_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "tiny.md"
            artifact.write_text("# Title\n\nA few words.\n")
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("MINIMAL STUB", msg)

    def test_just_above_floor_passes(self):
        """Padded just over the floor — should pass the minimal check."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "real.md"
            artifact.write_text(
                "# A Real Note\n\nThis note contains enough actual prose content "
                "to clear the 150-byte minimal floor. It has multiple sentences. "
                "It conveys actual information about something specific.\n"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok, f"Just-above-floor real content failed: {msg}")


class TestTruncatedExecutionDetection(unittest.TestCase):
    """May 18 PM v2 regression: even with anti-placeholder rules, Jrs adapted by
    truncating — wrote section headers but never executed the actual commands."""

    def test_catches_too_short_report_shape(self):
        """Report-shaped tiny artifact (## header + minimal content) is the
        Jr-truncation pattern. Non-report tiny content is exempt."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "tiny_report.md"
            artifact.write_text("# Report\n\n## Output\n\nDone.\n## Conclusion\n\nFinished.\n")
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("TRUNCATED EXECUTION", msg)

    def test_catches_pending_execution_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "honest.md"
            artifact.write_text(
                "# Federation Node Inventory V2\n"
                "**Date:** 2026-05-18\n"
                "**Status:** Pending Execution (Requires live SSH access)\n\n"
                "## Node IP Map\n\nContent will go here later.\n" * 20  # padded to pass length check
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("TRUNCATED EXECUTION", msg)

    def test_catches_empty_output_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "header_only.md"
            artifact.write_text(
                "# Real-Looking Report\n\n## Background\n\n"
                + ("This is a long enough background paragraph to pass the length check. " * 10)
                + "\n\n## Raw Grep Output\n\n## Conclusion\n\nDone.\n"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertFalse(ok)
            self.assertIn("TRUNCATED EXECUTION", msg)

    def test_real_report_passes(self):
        """A report with real content in output sections should pass."""
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "real.md"
            artifact.write_text(
                "# Real Report\n\n## Background\n\n"
                + ("Real prose background content. " * 20)
                + "\n\n## Output\n\n```\n"
                + "actual grep line 1 of output: file:42:matched content\n"
                + "actual grep line 2: another match here in some other file\n"
                + "more output continuing the actual data section\n"
                + "```\n\n## Conclusion\n\nReal conclusion text follows.\n"
            )
            ok, msg, mm = verify_artifact_factuality(str(artifact))
            self.assertTrue(ok, f"Real report rejected: {msg}")


class TestIntegrationWithVerifyJrTaskResult(unittest.TestCase):
    """End-to-end: when verify_jr_task_result sees a Jr-written artifact with
    fabricated citations, it must set hallucination_flag and verified=False."""

    def test_hallucinated_artifact_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "diagnosis.md"
            artifact.write_text(
                "# Report\n- File: `/ganuda/this/does/not/exist.py`\n- Line 50: foo\n"
            )

            task = {'id': 9999, 'instruction_content': 'investigate something'}
            result = {
                'success': True,
                'steps_executed': [{'step': 1}],
                'artifacts': [{'type': 'report', 'path': str(artifact)}],
            }
            # Pass the artifact as an extra claim of kind=file_exists
            extra = [Claim(kind='file_exists', target=str(artifact), source='test')]
            ver = verify_jr_task_result(task, result, extra_claims=extra)

            self.assertFalse(ver.verified)
            self.assertTrue(ver.hallucination_flag)
            self.assertGreater(ver.failed, 0)
            self.assertTrue(any(m['kind'] == 'factuality' for m in ver.mismatches))


if __name__ == "__main__":
    unittest.main(verbosity=2)
