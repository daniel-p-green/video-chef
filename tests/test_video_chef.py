from __future__ import annotations

import json
import http.client
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
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
        self.assertEqual(manifest["version"], "1.2.0")

    def test_all_skills_have_valid_identity_and_no_placeholders(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 11)
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

    def test_premiere_connector_is_localhost_only_and_read_only(self):
        manifest = json.loads((PLUGIN / "premiere-uxp/video-chef-bridge/manifest.json").read_text())
        capabilities = json.loads((PLUGIN / "premiere-uxp/video-chef-bridge/capabilities.json").read_text())
        self.assertEqual(manifest["host"]["app"], "premierepro")
        self.assertEqual(manifest["host"]["minVersion"], "25.6.0")
        self.assertEqual(manifest["requiredPermissions"]["network"]["domains"], ["http://127.0.0.1:17841"])
        self.assertFalse(capabilities["mutationEnabled"])
        self.assertEqual(set(capabilities["capabilities"]), {"ping", "snapshot_active_sequence"})
        runtime = (PLUGIN / "premiere-uxp/video-chef-bridge/main.js").read_text()
        self.assertNotIn("eval(", runtime)
        self.assertNotIn("Function(", runtime)
        self.assertNotIn("executeTransaction", runtime)


class ToolTests(unittest.TestCase):
    def test_premiere_sequence_snapshot_and_guarded_rough_cut(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            report = temp / "sequence.md"
            subprocess.run([
                "python3", str(SCRIPTS / "premiere_sequence_analysis.py"),
                str(ROOT / "tests/fixtures/premiere-snapshot.json"), str(report),
            ], check=True)
            text = report.read_text()
            self.assertIn("Launch Film v03", text)
            self.assertIn("0.000-5.000", text)
            self.assertIn("interpretation boundary", text)

            plan = temp / "plan.json"
            subprocess.run([
                "python3", str(SCRIPTS / "premiere_rough_cut.py"),
                str(ROOT / "tests/fixtures/rough-cut-selects.csv"), str(plan),
                "--target-sequence", "VC_ROUGH_CUT_20260827_v01", "--fps", "29.97",
            ], check=True)
            data = json.loads(plan.read_text())
            self.assertEqual(data["mode"], "plan_only")
            self.assertFalse(data["execution"]["requested"])
            self.assertFalse(data["execution"]["supported_by_bundled_connector"])
            self.assertEqual(data["segments"][1]["timeline_in_seconds"], 5.0)
            self.assertEqual(len(data["plan_sha256"]), 64)

            data["segments"][0]["source_out_seconds"] = 99
            tampered = temp / "tampered.json"
            tampered.write_text(json.dumps(data))
            tamper_check = subprocess.run([
                "python3", str(SCRIPTS / "premiere_rough_cut.py"), str(tampered),
                str(temp / "tampered-output.json"), "--target-sequence", "IGNORED", "--validate-only",
            ], capture_output=True, text=True)
            self.assertEqual(tamper_check.returncode, 1)
            self.assertIn("plan_sha256", tamper_check.stderr)

            blocked = subprocess.run([
                "python3", str(SCRIPTS / "premiere_rough_cut.py"),
                str(ROOT / "tests/fixtures/rough-cut-selects.csv"), str(temp / "blocked.json"),
                "--target-sequence", "MASTER", "--fps", "29.97",
            ], capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("VC_ROUGH_CUT_", blocked.stderr)

    def test_premiere_broker_authenticated_round_trip_and_mutation_guard(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            config = temp / "bridge.json"
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            subprocess.run([
                "python3", str(SCRIPTS / "premiere_bridge.py"), "--config", str(config),
                "init", "--port", str(port),
            ], check=True, capture_output=True, text=True)
            self.assertEqual(config.stat().st_mode & 0o077, 0)
            details = json.loads(config.read_text())
            headers = {"Authorization": f"Bearer {details['token']}", "Content-Type": "application/json"}

            def local_request(method, path, body=None, authorized=True, timeout=1):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
                request_headers = dict(headers) if authorized else {"Authorization": "Bearer wrong"}
                encoded = json.dumps(body).encode() if body is not None else None
                try:
                    connection.request(method, path, body=encoded, headers=request_headers)
                    response = connection.getresponse()
                    raw_body = response.read()
                    parsed = json.loads(raw_body) if raw_body else None
                    return response.status, parsed
                finally:
                    connection.close()
            server = subprocess.Popen([
                "python3", str(SCRIPTS / "premiere_bridge.py"), "--config", str(config),
                "serve", "--request-timeout", "3",
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                for _ in range(50):
                    try:
                        status, _ = local_request("GET", "/v1/status", timeout=0.2)
                        self.assertEqual(status, 200)
                        break
                    except OSError:
                        time.sleep(0.05)
                else:
                    self.fail("broker did not start")

                status, _ = local_request("POST", "/v1/connector/register", {
                    "protocol_version": "1.0", "connector_version": "test",
                    "premiere_version": "test", "capabilities": ["ping"],
                })
                self.assertEqual(status, 200)
                status, _ = local_request("OPTIONS", "/v1/connector/register", authorized=False)
                self.assertEqual(status, 204)

                def fake_connector():
                    for _ in range(60):
                        status, job = local_request("GET", "/v1/connector/next", timeout=0.5)
                        if status == 200:
                            result_status, _ = local_request("POST", "/v1/connector/result", {
                                "id": job["id"], "result": {"ok": True, "data": {"message": "pong"}},
                            })
                            if result_status != 200:
                                raise AssertionError(f"connector result returned {result_status}")
                            return
                        if status != 204:
                            raise AssertionError(f"connector poll returned {status}")
                        time.sleep(0.05)

                worker = threading.Thread(target=fake_connector, daemon=True)
                worker.start()
                completed = subprocess.run([
                    "python3", str(SCRIPTS / "premiere_bridge.py"), "--config", str(config),
                    "request", "ping", "--timeout", "4",
                ], check=True, capture_output=True, text=True)
                worker.join(timeout=2)
                self.assertEqual(json.loads(completed.stdout)["result"]["data"]["message"], "pong")

                status, _ = local_request("POST", "/v1/request", {"operation": "apply_rough_cut", "payload": {}})
                self.assertEqual(status, 403)
                status, _ = local_request("GET", "/v1/status", authorized=False)
                self.assertEqual(status, 401)
            finally:
                server.terminate()
                server.wait(timeout=5)
                if server.stdout:
                    server.stdout.close()
                if server.stderr:
                    server.stderr.close()

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
