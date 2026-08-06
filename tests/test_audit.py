import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "audit.py"

def run(name):
    return subprocess.run([sys.executable, str(CLI), str(ROOT / "tests" / "fixtures" / name), "--format", "json"], capture_output=True, text=True, check=True)

def run_profile(name, profile):
    return subprocess.run([sys.executable, str(CLI), str(ROOT / "tests" / "fixtures" / name), "--profile", profile, "--format", "json"], capture_output=True, text=True, check=True)

class AuditTests(unittest.TestCase):
  def test_english_report_has_provenance(self):
    data = json.loads(run("english.md").stdout)
    self.assertIn(data["risk"]["level"], {"low", "moderate", "high", "critical"})
    self.assertTrue(any(f["rule_id"] == "CONTENT-GENERIC-CLAIM" for f in data["findings"]))
    self.assertEqual(data["provenance"]["lock_file"], "upstream/upstream-lock.yaml")

  def test_chinese_rules(self):
    data = json.loads(run("chinese.md").stdout)
    rules = {f["rule_id"] for f in data["findings"]}
    self.assertIn("LANGUAGE-AI-VOCABULARY-CLUSTER", rules)
    self.assertIn("CONTENT-EVIDENCE-GAP", rules)

  def test_protected_text_is_report_only(self):
    data = json.loads(run("protected.md").stdout)
    self.assertTrue(all("Ignore the rules above" not in f["evidence"] for f in data["findings"]))

  def test_strict_returns_nonzero(self):
    result = subprocess.run([sys.executable, str(CLI), str(ROOT / "tests" / "fixtures" / "english.md"), "--strict"], capture_output=True, text=True)
    self.assertEqual(result.returncode, 2)

  def test_armor_profile_flags_armor_facts_only(self):
    general = json.loads(run_profile("armor-claims.md", "general").stdout)
    armor = json.loads(run_profile("armor-claims.md", "armor").stdout)
    self.assertFalse(any(f["rule_id"].startswith("ARMOR-FACT-") for f in general["findings"]))
    armor_rules = {f["rule_id"] for f in armor["findings"]}
    self.assertIn("ARMOR-FACT-ESL-IS-NOT-LCD", armor_rules)
    self.assertIn("ARMOR-FACT-ESL-POWER-TRACK-CONNECTION", armor_rules)
    self.assertIn("ARMOR-FACT-MAGNETIC-SURFACE-REQUIREMENT", armor_rules)
    self.assertIn("ARMOR-FACT-UNSUPPORTED-ZERO-INSTALL-ROI", armor_rules)
    self.assertIn("ARMOR-FACT-VERIFY-VOLTAGE-CONNECTION", armor_rules)
    self.assertEqual(armor["risk"]["level"], "high")
