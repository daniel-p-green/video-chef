from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "video-chef"
SCRIPTS = PLUGIN / "scripts"


class PackageTests(unittest.TestCase):
    def test_marketplace_and_manifest_identity(self):
        market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(market["name"], "video-chef")
        self.assertEqual(market["plugins"][0]["name"], "video-chef")
        self.assertEqual(market["plugins"][0]["source"]["path"], "./plugins/video-chef")
        self.assertEqual(manifest["name"], "video-chef")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")

    def test_all_skills_have_valid_identity_and_no_placeholders(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 8)
        for path in skills:
            text = path.read_text()
            match = re.search(r"^name:\s*([^\s]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, path)
            self.assertEqual(match.group(1), path.parent.name)
            self.assertNotIn("[TODO:", text)

    def test_manifest_assets_exist(self):
        manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        for field in ("composerIcon", "logo"):
            path = PLUGIN / manifest["interface"][field].removeprefix("./")
            self.assertTrue(path.is_file(), path)


class ToolTests(unittest.TestCase):
    def test_subtitle_qc_distinguishes_good_and_bad(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            good = temp / "good.json"
            bad = temp / "bad.json"
            subprocess.run([
                "python3", str(SCRIPTS / "subtitle_qc.py"), str(ROOT / "tests/fixtures/good.srt"),
                "--format", "json", "--output", str(good), "--fail-on-issues",
            ], check=True)
            subprocess.run([
                "python3", str(SCRIPTS / "subtitle_qc.py"), str(ROOT / "tests/fixtures/bad.srt"),
                "--format", "json", "--output", str(bad),
            ], check=True)
            self.assertEqual(json.loads(good.read_text())["issues"], [])
            self.assertGreaterEqual(len(json.loads(bad.read_text())["issues"]), 3)

    def test_project_initializer_creates_records_and_refuses_nonempty_target(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "project"
            subprocess.run(["python3", str(SCRIPTS / "init_video_project.py"), str(target)], check=True)
            self.assertTrue((target / "01_brief/VIDEO_BRIEF.md").is_file())
            self.assertTrue((target / "08_delivery/DELIVERY_SPEC.md").is_file())
            blocked = subprocess.run(
                ["python3", str(SCRIPTS / "init_video_project.py"), str(target)], capture_output=True, text=True
            )
            self.assertEqual(blocked.returncode, 2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is unavailable")
    def test_media_inventory_and_qc(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            media = temp / "black-tone.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                "color=black:size=320x180:rate=30", "-f", "lavfi", "-i",
                "sine=frequency=440:sample_rate=48000", "-t", "3", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-c:a", "aac", str(media),
            ], check=True)
            inventory = temp / "inventory.json"
            qc = temp / "qc.json"
            subprocess.run([
                "python3", str(SCRIPTS / "media_inventory.py"), str(media), "--hash", "sha256",
                "--format", "json", "--output", str(inventory),
            ], check=True)
            subprocess.run([
                "python3", str(SCRIPTS / "media_qc.py"), str(media), "--format", "json", "--output", str(qc),
            ], check=True)
            inv = json.loads(inventory.read_text())["files"][0]
            report = json.loads(qc.read_text())
            self.assertEqual(len(inv["sha256"]), 64)
            self.assertTrue(report["decode"]["passed"])
            self.assertTrue(report["black_intervals"])
            self.assertTrue(report["freeze_intervals"])
            self.assertIsNotNone(report["loudness"]["integrated_lufs"])


if __name__ == "__main__":
    unittest.main()
