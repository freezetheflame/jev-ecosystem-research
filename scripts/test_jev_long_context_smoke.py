"""Offline transport fixtures, not model measurements."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from jev_long_context_smoke import LONG_HEADER, make_payload, send


class MonitorFixture:
    run_id = "offline-test"

    def __init__(self):
        self.events = []

    def record(self, **event):
        self.events.append(event)


class SmokeTests(unittest.TestCase):
    def test_deterministic_large_body_with_single_middle_marker(self):
        payload = make_payload()
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        self.assertGreater(len(body), 200000)
        self.assertLess(len(body), 240000)
        self.assertEqual(payload["state"].count("TARGET-582401"), 1)
        self.assertEqual(payload["state"].splitlines()[4001], "TARGET-582401 has decision DENY.")
        self.assertEqual(make_payload(), payload)

    def test_failed_transport_is_counted_and_credentials_are_redacted(self):
        secret = "synthetic-test-secret-not-a-real-key"
        failure = urllib.error.HTTPError("https://api.typesafe.ai/v1/systemone", 401,
                                        "Unauthorized", {}, io.BytesIO(secret.encode()))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "raw").mkdir()
            monitor = MonitorFixture()
            with patch("urllib.request.OpenerDirector.open", side_effect=failure):
                row = send(out, b"{}", enabled=True, key=secret, monitor=monitor, timeout=1)
            self.assertEqual(row["http_status"], 401)
            self.assertFalse(row["valid_response"])
            self.assertTrue(row["response_redacted"])
            self.assertEqual(len(monitor.events), 1)
            self.assertIsNotNone(monitor.events[0]["error"])
            for path in out.rglob("*"):
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes())

    def test_header_on_off_preserves_body_and_counts_each_request_once(self):
        class Response:
            status = 200
            headers = {}

            def read(self):
                return json.dumps({"model": "jev-1.14.0", "answers": {
                    "target_decision": {"type": "choice", "choice": "deny"}},
                    "usage": {"input_tokens": 100000, "output_tokens": 1}}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "raw").mkdir()
            monitor = MonitorFixture()
            with patch("urllib.request.OpenerDirector.open", return_value=Response()) as transport:
                for enabled in (False, True):
                    row = send(out, b'{"fixture":true}', enabled=enabled,
                               key="fake-key", monitor=monitor, timeout=1)
                    self.assertTrue(row["valid_response"])
            requests = [call.args[0] for call in transport.call_args_list]
            self.assertEqual(requests[0].data, requests[1].data)
            self.assertIsNone(requests[0].get_header(LONG_HEADER.capitalize()))
            self.assertEqual(requests[1].get_header(LONG_HEADER.capitalize()), "true")
            self.assertEqual(len(monitor.events), 2)


if __name__ == "__main__":
    unittest.main()
