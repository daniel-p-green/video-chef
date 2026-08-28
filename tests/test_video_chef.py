from __future__ import annotations

import json
import os
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
        self.assertEqual(manifest["version"], "1.1.0")

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

    def test_brent_source_fidelity_map(self):
        source_notes = (PLUGIN / "skills/video-chef/references/source-notes.md").read_text()
        self.assertIn("Brent Schooley", source_notes)
        self.assertNotIn("Brent Choi", source_notes)
        self.assertNotIn("heccbrent", source_notes)
        for phrase in (
            "What are we making?", "What are we working with?", "What did they say?",
            "What can Codex see?", "What's the story?",
        ):
            self.assertIn(phrase, source_notes)


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
            self.assertTrue((target / "03_analysis/SCREEN_REVIEW.csv").is_file())
            self.assertTrue((target / "03_analysis/SPEAKER_MAP.csv").is_file())
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

    def test_asset_inventory_includes_non_media_and_roles(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            (temp / "brand").mkdir()
            (temp / "brand/logo.svg").write_text("<svg/>")
            (temp / "script.md").write_text("# Script")
            (temp / ".private.txt").write_text("hidden")
            output = temp / "inventory.json"
            subprocess.run([
                "python3", str(SCRIPTS / "asset_inventory.py"), str(temp), "--format", "json",
                "--hash", "sha256", "--output", str(output),
            ], check=True)
            files = json.loads(output.read_text())["files"]
            by_name = {item["name"]: item for item in files}
            self.assertEqual(by_name["logo.svg"]["likely_role"], "brand")
            self.assertEqual(by_name["script.md"]["likely_role"], "script")
            self.assertNotIn(".private.txt", by_name)
            self.assertEqual(len(by_name["logo.svg"]["sha256"]), 64)

    def test_transcript_workbench_writes_words_speakers_and_cues(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "transcript"
            subprocess.run([
                "python3", str(SCRIPTS / "transcript_workbench.py"),
                str(ROOT / "tests/fixtures/whisper.json"), str(output),
                "--speaker-map", str(ROOT / "tests/fixtures/speaker-map.csv"),
            ], check=True)
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["words"], 7)
            self.assertEqual(summary["speakers"], ["DIRECTOR", "PRODUCER"])
            self.assertTrue(summary["word_timestamps_present"])
            self.assertTrue(summary["speaker_labels_present"])
            self.assertTrue(summary["speaker_map_applied"])
            cues = (output / "production_cues.csv").read_text()
            self.assertIn("that was perfect", cues)
            self.assertIn("one more", cues)

    def test_transcript_workbench_invokes_openai_whisper_cli_contract(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            fake_bin = temp / "bin"
            fake_bin.mkdir()
            fake = fake_bin / "whisper"
            fixture = ROOT / "tests/fixtures/whisper.json"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import shutil, sys\n"
                "from pathlib import Path\n"
                "args = sys.argv[1:]\n"
                "assert '--output_dir' in args and '--output_format' in args and '--word_timestamps' in args\n"
                "output = Path(args[args.index('--output_dir') + 1])\n"
                f"shutil.copy2({str(fixture)!r}, output / 'fake.json')\n"
            )
            fake.chmod(0o755)
            media = temp / "speech.wav"
            media.write_bytes(b"fake")
            output = temp / "output"
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            subprocess.run([
                "python3", str(SCRIPTS / "transcript_workbench.py"), str(media), str(output),
                "--engine", "whisper", "--model", "tiny.en", "--language", "en",
            ], check=True, env=environment)
            self.assertEqual(json.loads((output / "summary.json").read_text())["engine"], "whisper")

    def test_transcript_workbench_marks_cross_speaker_segment_mixed(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            transcript = temp / "crossing.json"
            data = json.loads((ROOT / "tests/fixtures/whisper.json").read_text())
            data["segments"] = [{
                "start": 0.0, "end": 2.4, "text": data["text"],
                "words": data["segments"][0]["words"] + data["segments"][1]["words"],
            }]
            transcript.write_text(json.dumps(data))
            output = temp / "output"
            subprocess.run([
                "python3", str(SCRIPTS / "transcript_workbench.py"), str(transcript), str(output),
                "--speaker-map", str(ROOT / "tests/fixtures/speaker-map.csv"),
            ], check=True)
            segments = (output / "segments.csv").read_text()
            words = (output / "words.csv").read_text()
            self.assertIn("MIXED", segments)
            self.assertIn("PRODUCER", words)
            self.assertIn("DIRECTOR", words)

    def test_transcript_workbench_rejects_malformed_speaker_map_cleanly(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            malformed = temp / "malformed.csv"
            malformed.write_text("start,end,speaker\n0,1,PRODUCER\n1.1\n")
            completed = subprocess.run([
                "python3", str(SCRIPTS / "transcript_workbench.py"),
                str(ROOT / "tests/fixtures/whisper.json"), str(temp / "output"),
                "--speaker-map", str(malformed),
            ], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("error:", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is unavailable")
    def test_scene_detection_and_bounded_frame_sequence(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            media = temp / "two-scenes.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=red:size=320x180:rate=30:d=1",
                "-f", "lavfi", "-i", "color=blue:size=320x180:rate=30:d=1",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(media),
            ], check=True)
            scenes = temp / "scenes.json"
            boundary_frames = temp / "scene-frames"
            subprocess.run([
                "python3", str(SCRIPTS / "scene_detect.py"), str(media), str(scenes),
                "--threshold", "0.2", "--frames-dir", str(boundary_frames),
            ], check=True)
            self.assertGreaterEqual(len(json.loads(scenes.read_text())["scenes"]), 2)
            self.assertGreaterEqual(len(list(boundary_frames.glob("*.jpg"))), 2)

            sequence = temp / "sequence"
            subprocess.run([
                "python3", str(SCRIPTS / "extract_frame_sequence.py"), str(media), str(sequence),
                "--start", "0", "--end", "1", "--fps", "4", "--max-frames", "10",
            ], check=True)
            self.assertEqual(len(list(sequence.glob("frame-*.jpg"))), 4)
            blocked = subprocess.run([
                "python3", str(SCRIPTS / "extract_frame_sequence.py"), str(media), str(temp / "blocked"),
                "--start", "0", "--end", "2", "--fps", "30", "--max-frames", "10",
            ], capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2)


if __name__ == "__main__":
    unittest.main()
