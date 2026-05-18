"""
Tests for lib.duplo.recovery_enzymes — the SEV1-prevention first-cohort enzymes.

Tests against real federation backup files where read-only, isolated tempdirs
for any write operations.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/ganuda")

from lib.duplo.recovery_enzymes import (
    find_backup,
    surgical_restore,
    quarantine,
    QUARANTINE_DIR_PREFIX,
)


class TestFindBackup(unittest.TestCase):
    """find_backup is read-only; tests against real federation paths."""

    def test_finds_real_secrets_env_backups(self):
        """secrets.env has 3+ known backup_<ts> siblings from May 16 SEV1."""
        result = find_backup("/ganuda/config/secrets.env")
        backup_paths = [c["path"] for c in result if c["shape"] == "backup"]
        # We know at least 20260516_222728 exists
        self.assertTrue(
            any("backup_20260516_222728" in p for p in backup_paths),
            f"Expected SEV1 backup not found in {backup_paths}",
        )
        # Newest-first ordering
        if len(result) >= 2:
            self.assertGreaterEqual(result[0]["mtime_iso"], result[1]["mtime_iso"])

    def test_nonexistent_parent_returns_empty(self):
        result = find_backup("/this/path/does/not/exist/file.txt")
        self.assertEqual(result, [])

    def test_no_backups_returns_empty(self):
        """File with no backup siblings should return empty list, not error."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "lonely.txt"
            target.write_text("solo")
            result = find_backup(str(target))
            self.assertEqual(result, [])

    def test_finds_broken_siblings(self):
        """`.broken-<timestamp>` files are forensics-preserved corrupted versions."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "code.py"
            target.write_text("clean")
            (tmp_path / "code.py.broken-20260517-2055").write_text("corrupted")
            (tmp_path / "code.py.backup_20260101_120000").write_text("good")

            result = find_backup(str(target))
            shapes = sorted(c["shape"] for c in result)
            self.assertEqual(shapes, ["backup", "broken"])


class TestSurgicalRestoreFullCopy(unittest.TestCase):
    """Full-copy mode (no section markers)."""

    def test_full_copy_restores_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            damaged = tmp_path / "secrets.env"
            backup = tmp_path / "secrets.env.backup_20260101"
            damaged.write_text("CORRUPTED=value\n")
            backup.write_text("DB_PASSWORD=goodpw\nAPI_KEY=goodkey\n")

            result = surgical_restore(str(damaged), str(backup))

            self.assertEqual(result["action"], "full_copy")
            self.assertEqual(damaged.read_text(), "DB_PASSWORD=goodpw\nAPI_KEY=goodkey\n")
            # broken-preservation
            self.assertTrue(result["broken_preserved_at"])
            self.assertTrue(Path(result["broken_preserved_at"]).exists())
            self.assertIn("CORRUPTED", Path(result["broken_preserved_at"]).read_text())

    def test_missing_damaged_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup = Path(tmp) / "backup.txt"
            backup.write_text("good")
            with self.assertRaises(FileNotFoundError):
                surgical_restore(str(Path(tmp) / "missing.txt"), str(backup))

    def test_missing_backup_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            damaged = Path(tmp) / "damaged.txt"
            damaged.write_text("x")
            with self.assertRaises(FileNotFoundError):
                surgical_restore(str(damaged), str(Path(tmp) / "no_backup.txt"))


class TestSurgicalRestoreSectionSplice(unittest.TestCase):
    """Section-splice mode (with regex markers)."""

    def test_section_replace_when_section_present_in_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            damaged = tmp_path / "config.py"
            backup = tmp_path / "config.py.backup"
            damaged.write_text(
                "preamble\n"
                "# DC-15 START\nCORRUPTED_DC15_CONTENT\n# DC-15 END\n"
                "postamble\n"
            )
            backup.write_text(
                "different preamble\n"
                "# DC-15 START\nCLEAN_DC15_CONTENT\n# DC-15 END\n"
                "different postamble\n"
            )

            result = surgical_restore(
                str(damaged), str(backup),
                section_start_pattern=r"^# DC-15 START",
                section_end_pattern=r"^# DC-15 END",
            )

            self.assertEqual(result["action"], "section_replace")
            restored = damaged.read_text()
            self.assertIn("preamble\n", restored)
            self.assertIn("CLEAN_DC15_CONTENT", restored)
            self.assertNotIn("CORRUPTED_DC15_CONTENT", restored)
            self.assertIn("postamble\n", restored)
            # damaged preamble/postamble preserved (only section swapped)
            self.assertNotIn("different preamble", restored)
            self.assertNotIn("different postamble", restored)

    def test_section_insert_when_missing_in_damaged(self):
        """If damaged file is missing the section entirely, append clean section."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            damaged = tmp_path / "config.py"
            backup = tmp_path / "config.py.backup"
            damaged.write_text("only preamble\n")
            backup.write_text(
                "irrelevant\n"
                "# DC-15 START\nCLEAN\n# DC-15 END\n"
            )

            result = surgical_restore(
                str(damaged), str(backup),
                section_start_pattern=r"^# DC-15 START",
                section_end_pattern=r"^# DC-15 END",
            )

            self.assertEqual(result["action"], "section_insert")
            self.assertIn("only preamble", damaged.read_text())
            self.assertIn("CLEAN", damaged.read_text())

    def test_missing_section_in_backup_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            damaged = tmp_path / "f.py"
            backup = tmp_path / "f.py.backup"
            damaged.write_text("x")
            backup.write_text("y")
            with self.assertRaises(ValueError):
                surgical_restore(
                    str(damaged), str(backup),
                    section_start_pattern=r"^MISSING_START",
                    section_end_pattern=r"^MISSING_END",
                )

    def test_only_one_pattern_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            damaged = tmp_path / "f.py"
            backup = tmp_path / "f.py.backup"
            damaged.write_text("x")
            backup.write_text("y")
            with self.assertRaises(ValueError):
                surgical_restore(
                    str(damaged), str(backup),
                    section_start_pattern=r"^START",
                    section_end_pattern=None,
                )


class TestQuarantine(unittest.TestCase):

    def test_basic_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            suspect = tmp_path / "stub.py"
            suspect.write_text("# ... (rest of the code)\n")

            result = quarantine(
                str(suspect),
                reason="Jr-stub deliverable",
                quarantine_root=str(tmp_path),
            )

            self.assertFalse(suspect.exists())
            self.assertTrue(Path(result["quarantined_path"]).exists())
            self.assertEqual(
                Path(result["quarantined_path"]).read_text(),
                "# ... (rest of the code)\n",
            )
            # Sidecar metadata
            meta = Path(result["meta_path"]).read_text()
            self.assertIn("Jr-stub deliverable", meta)
            self.assertIn(str(suspect), meta)
            # Quarantine dir naming
            self.assertIn(QUARANTINE_DIR_PREFIX, result["quarantined_path"])

    def test_quarantine_handles_name_collision(self):
        """Two files with the same name on the same day get distinct paths."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # First file
            src1 = tmp_path / "dup.py"
            src1.write_text("first")
            r1 = quarantine(str(src1), quarantine_root=str(tmp_path))

            # Second file with same name (re-created)
            src2 = tmp_path / "dup.py"
            src2.write_text("second")
            r2 = quarantine(str(src2), quarantine_root=str(tmp_path))

            self.assertNotEqual(r1["quarantined_path"], r2["quarantined_path"])
            self.assertTrue(Path(r1["quarantined_path"]).exists())
            self.assertTrue(Path(r2["quarantined_path"]).exists())

    def test_missing_source_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                quarantine(str(Path(tmp) / "nope.txt"), quarantine_root=tmp)

    def test_refuses_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subdir = tmp_path / "a_dir"
            subdir.mkdir()
            with self.assertRaises(ValueError):
                quarantine(str(subdir), quarantine_root=str(tmp_path))


class TestRegistrySync(unittest.TestCase):
    """Verify the three enzymes are registered in build_federation_registry."""

    def test_recovery_enzymes_registered(self):
        from lib.duplo.registry import build_federation_registry
        reg = build_federation_registry()
        for name in ("find_backup", "surgical_restore", "quarantine"):
            spec = reg.get_spec(name)
            self.assertIsNotNone(spec, f"{name} not registered")
            self.assertEqual(spec.module_path, "lib.duplo.recovery_enzymes")

        # Safety classes correct
        self.assertEqual(reg.get_spec("find_backup").safety_class, "read")
        self.assertEqual(reg.get_spec("surgical_restore").safety_class, "write")
        self.assertEqual(reg.get_spec("quarantine").safety_class, "write")


if __name__ == "__main__":
    unittest.main(verbosity=2)
