"""Offline tests of the local DeepSeek adapter; never call external services."""

import json
import tempfile
import unittest
from pathlib import Path

import httpx
from jevout_pilot import NonThinkingClient


class ChatAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp.name) / "responses.jsonl"
        self.client = NonThinkingClient("https://example.invalid/v1", api_key="private-test-key", log_path=self.log_path)
        self.client.client.close()
        self.requests = []
        self.responses = []

        def handler(request):
            self.requests.append(json.loads(request.content))
            return self.responses.pop(0)

        self.client.client = httpx.Client(transport=httpx.MockTransport(handler))

    def tearDown(self):
        self.client.client.close()
        self.temp.cleanup()

    def response(self, content):
        return httpx.Response(200, json={"model": "test-model", "choices": [{"finish_reason": "stop", "message": {"content": content}}], "usage": {"total_tokens": 7}})

    def call(self):
        return self.client.structured_chat(model="test-model", system="Original task prompt.", user={"test": "synthetic"},
                                           schema_name="test", schema={"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
                                           temperature=0.8, top_p=0.95, max_tokens=160, seed=42)

    def test_schema_mirror_and_secret_free_log(self):
        self.responses = [self.response('{"ok": true}')]
        value, usage = self.call()
        self.assertEqual(value, {"ok": True})
        self.assertEqual(usage, {"total_tokens": 7})
        request = self.requests[0]
        self.assertEqual(request["thinking"], {"type": "disabled"})
        self.assertTrue(request["messages"][0]["content"].startswith("Original task prompt."))
        self.assertIn('"required": ["ok"]', request["messages"][0]["content"])
        self.assertEqual(request["seed"], 42)
        self.assertEqual(request["max_tokens"], 160)
        self.assertNotIn("private-test-key", self.log_path.read_text())

    def test_empty_body_retries_with_original_budgets_and_seeds(self):
        self.responses = [self.response(None), self.response('{"ok": true}')]
        self.assertEqual(self.call()[0], {"ok": True})
        self.assertEqual([r["max_tokens"] for r in self.requests], [160, 320])
        self.assertEqual([r["seed"] for r in self.requests], [42, 43])
        self.assertEqual(len(self.log_path.read_text().splitlines()), 2)

    def test_invalid_json_fails_after_two_attempts(self):
        self.responses = [self.response("bad"), self.response("still bad")]
        with self.assertRaisesRegex(ValueError, "invalid after retry"):
            self.call()
        self.assertEqual(len(self.requests), 2)

    def test_http_error_aborts_without_success_log(self):
        self.responses = [httpx.Response(403, json={"error": "test forbidden"})]
        with self.assertRaises(httpx.HTTPStatusError):
            self.call()
        self.assertEqual(len(self.requests), 1)
        self.assertFalse(self.log_path.exists())

    def test_never_fabricates_missing_checker_fields(self):
        self.responses = [self.response('{}')]
        self.assertEqual(self.call()[0], {})  # Downstream Pydantic checker must reject it.
        self.assertEqual(len(self.requests), 1)


if __name__ == "__main__":
    unittest.main()
