"""Offline tests; never call a hosted service."""

import json
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

from jev_api import evaluate, load_config, prepare_request, smoke_request, validate_response


class JevApiTests(unittest.TestCase):
    def setUp(self):
        self.config = {"endpoint": "https://example.invalid/systemone", "model": "test-free",
                       "apiKey": "public", "timeoutMs": 1000}

    def test_model_override_preserves_archived_payload(self):
        payload = {**smoke_request(), "model": "historical-model"}
        self.assertEqual(prepare_request(payload, self.config)["model"], "test-free")
        self.assertEqual(payload["model"], "historical-model")

    def test_reject_empty_questions(self):
        with self.assertRaises(ValueError):
            prepare_request({"state": "test", "questions": {}}, self.config)

    def test_reject_unknown_type(self):
        with self.assertRaises(ValueError):
            prepare_request({"state": "test", "questions": {"x": {"type": "text"}}}, self.config)

    def test_reject_missing_answers(self):
        with self.assertRaises(ValueError):
            validate_response({"answers": {}}, smoke_request())

    def test_config_does_not_inherit_private_typesafe_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(self.config), encoding="utf-8")
            with patch.dict("os.environ", {"TYPESAFE_API_KEY": "private-other-service"}, clear=True):
                self.assertEqual(load_config(path)["apiKey"], "public")

    @patch("jev_api.urllib.request.urlopen")
    def test_success_records_provenance_without_key(self, urlopen):
        response = {"model": "test-free", "answers": {
            "department": {"type": "choice", "choice": "billing"},
            "refund": {"type": "noul", "noul": 0.99},
            "severity": {"type": "score", "score": 1},
        }}
        wire_result = MagicMock()
        wire_result.status = 200
        wire_result.read.return_value = json.dumps(response).encode()
        urlopen.return_value.__enter__.return_value = wire_result
        result = evaluate(smoke_request(), self.config)
        self.assertEqual(result["response"], response)
        self.assertEqual(len(result["request_sha256"]), 64)
        self.assertNotIn("apiKey", result)
        self.assertEqual(urlopen.call_args.args[0].get_header("Authorization"), "Bearer public")

    @patch("jev_api.urllib.request.urlopen")
    def test_api_error_is_not_safe_or_retried(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(self.config["endpoint"], 403, "Denied", Message(), None)
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            evaluate(smoke_request(), self.config)
        urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
