import unittest
from scripts.local_remaining_server import completion_reason


class CompletionTests(unittest.TestCase):
    def test_eos_and_actual_token_limit_are_distinguished(self):
        self.assertEqual(completion_reason([42], 99, 1), 'length')
        self.assertEqual(completion_reason([99], [98, 99], 1), 'stop')
        self.assertEqual(completion_reason([42, 99], 99, 64), 'stop')
