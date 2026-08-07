import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "audit.py"
FIXTURES = ROOT / "tests" / "fixtures"

def invoke(name, *args, check=True):
    return subprocess.run([sys.executable, "-B", str(CLI), str(FIXTURES / name), *args], capture_output=True, text=True, check=check)

def detect(name, profile="general"):
    return json.loads(invoke(name, "--profile", profile, "--format", "json").stdout)

class AuditV03Tests(unittest.TestCase):
    def test_report_contract_and_provenance(self):
        data = detect("english.md")
        required = set(json.loads((ROOT / "schemas" / "report.schema.json").read_text())["required"])
        self.assertTrue(required.issubset(data))
        self.assertEqual(2, data["schema_version"])
        self.assertEqual("0.3.0", data["tool_version"])
        self.assertRegex(data["reproducibility"]["input_sha256"], r"^[a-f0-9]{64}$")
        self.assertRegex(data["reproducibility"]["ruleset_sha256"], r"^[a-f0-9]{64}$")
        self.assertTrue(all(item["id"].startswith("F-") for item in data["findings"]))

    def test_same_input_has_stable_fingerprints_and_finding_ids(self):
        first = detect("armor-retail-trends-v1.2.md", "b2b-marketing,seo-geo,armor")
        second = detect("armor-retail-trends-v1.2.md", "b2b-marketing,seo-geo,armor")
        self.assertEqual(first["reproducibility"], second["reproducibility"])
        self.assertEqual([item["id"] for item in first["findings"]], [item["id"] for item in second["findings"]])

    def test_cli_works_through_agent_skill_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            linked = Path(temporary) / "ai-writing-audit"
            linked.symlink_to(ROOT, target_is_directory=True)
            result = subprocess.run(
                [sys.executable, "-B", str(linked / "scripts" / "audit.py"), str(FIXTURES / "low-risk-control.md"), "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            self.assertEqual("0.3.0", data["tool_version"])
            self.assertRegex(data["reproducibility"]["ruleset_sha256"], r"^[a-f0-9]{64}$")

    def test_adapter_status_is_truthful(self):
        data = detect("english.md")
        self.assertEqual("success", data["adapter_status"]["local-static-scanner"]["status"])
        self.assertEqual("reference_only", data["adapter_status"]["conorbronsdon-avoid-ai-writing"]["status"])
        self.assertEqual("reference_only", data["adapter_status"]["blader-humanizer"]["status"])
        self.assertNotEqual("success", data["adapter_status"]["harshaneel-humanize"]["status"])

    def test_unsupported_modes_never_silently_detect(self):
        for mode in ("repair", "edit", "compare"):
            result = invoke("english.md", "--mode", mode, "--format", "json", check=False)
            self.assertEqual(2, result.returncode)
            payload = json.loads(result.stdout)
            self.assertEqual("unsupported_cli_mode", payload["error"])
            self.assertEqual(mode, payload["mode"])

    def test_profiles_enable_real_findings_and_weights(self):
        general = detect("armor-retail-trends-v1.2.md", "general")
        focused = detect("armor-retail-trends-v1.2.md", "b2b-marketing,seo-geo")
        general_rules = {item["rule_id"] for item in general["findings"]}
        focused_rules = {item["rule_id"] for item in focused["findings"]}
        self.assertNotIn("SEO-ANSWER-TEMPLATE", general_rules)
        self.assertNotIn("B2B-MISSING-MECHANISM", general_rules)
        self.assertIn("SEO-ANSWER-TEMPLATE", focused_rules)
        self.assertIn("B2B-MISSING-MECHANISM", focused_rules)
        self.assertEqual(1.4, focused["profile_configuration"]["weights"]["structural_uniformity"])
        self.assertEqual(1.4, focused["profile_configuration"]["weights"]["generic_claims"])

    def test_supplied_article_is_high_impact_structural_regression(self):
        data = detect("armor-retail-trends-v1.2.md", "b2b-marketing,seo-geo,armor")
        rules = [item["rule_id"] for item in data["findings"]]
        self.assertIn(data["risk"]["level"], {"high", "critical"})
        self.assertIn("STRUCTURE-UNSUPPORTED-SCENE", rules)
        self.assertGreaterEqual(rules.count("STRUCTURE-TEMPLATE-ENDCAP"), 2)
        self.assertIn("SEO-ANSWER-TEMPLATE", rules)
        self.assertIn("CONTENT-CATEGORICAL-INDUSTRY-CLAIM", rules)

    def test_low_risk_control_stays_low(self):
        data = detect("low-risk-control.md", "b2b-marketing,seo-geo")
        self.assertEqual("low", data["risk"]["level"])
        self.assertFalse(data["findings"])

    def test_native_configuration_is_loaded(self):
        data = detect("machine-template.md")
        self.assertIn("STRUCTURE-TEMPLATE-ENDCAP", data["provenance"]["active_native_rules"])
        rules = {item["rule_id"] for item in data["findings"]}
        self.assertIn("STRUCTURE-TEMPLATE-ENDCAP", rules)
        self.assertIn("STRUCTURE-PARAGRAPH-UNIFORMITY", rules)

    def test_chinese_rules(self):
        rules = {item["rule_id"] for item in detect("chinese.md")["findings"]}
        self.assertIn("LANGUAGE-AI-VOCABULARY-CLUSTER", rules)
        self.assertIn("CONTENT-EVIDENCE-GAP", rules)

    def test_protected_text_is_report_only(self):
        self.assertTrue(all("Ignore the rules above" not in item["evidence"] for item in detect("protected.md")["findings"]))

    def test_armor_profile_flags_domain_facts(self):
        general = detect("armor-claims.md", "general")
        armor = detect("armor-claims.md", "armor")
        self.assertFalse(any(item["rule_id"].startswith("ARMOR-FACT-") for item in general["findings"]))
        armor_rules = {item["rule_id"] for item in armor["findings"]}
        self.assertIn("ARMOR-FACT-ESL-IS-NOT-LCD", armor_rules)
        self.assertIn("ARMOR-FACT-VERIFY-VOLTAGE-CONNECTION", armor_rules)
        self.assertIn(armor["risk"]["level"], {"high", "critical"})

    def test_strict_returns_nonzero_on_findings(self):
        self.assertEqual(2, invoke("english.md", "--strict", check=False).returncode)

if __name__ == "__main__":
    unittest.main()
