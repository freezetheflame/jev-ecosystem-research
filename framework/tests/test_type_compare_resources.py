import unittest

from framework.type_compare_resources import aggregate, percentile


class TypeCompareResourceTests(unittest.TestCase):
    def test_usage_counts_each_chunk_and_retry(self):
        rows = [{'latency_ms': 2000, 'calls': [
            {'response': {'usage': {'input_tokens': 1_000_000, 'output_tokens': 100}},
             'attempts': [{'error': 'timeout'}, {'status': 'success'}]},
            {'response': {'usage': {'input_tokens': 500_000, 'output_tokens': 50}},
             'attempts': [{'status': 'success'}]},
        ]}]
        result = aggregate(rows)
        self.assertEqual(result['input_tokens'], 1_500_000)
        self.assertEqual(result['output_tokens'], 150)
        self.assertEqual(result['attempt_count'], 3)
        self.assertEqual(result['failed_attempts'], 1)
        self.assertAlmostEqual(result['known_estimated_cost_usd'], .063)
        self.assertEqual(result['cumulative_record_seconds'], 2)

    def test_percentile_interpolation_and_unknown_usage(self):
        self.assertEqual(percentile([400, 100, 200, 300], .5), 250)
        self.assertEqual(percentile([400, 100, 200, 300], .95), 385)
        result = aggregate([{'latency_ms': 100, 'calls': [{'response': {}}]}])
        self.assertEqual(result['missing_usage_responses'], 1)


if __name__ == '__main__':
    unittest.main()
