import unittest

from framework.type_compare import parse_answer, questions, select


class TypeCompareTests(unittest.TestCase):
    def test_choice_uses_risk_probability_and_native_tie(self):
        self.assertEqual(parse_answer('choice', {'choice': 'safe', 'probabilities': {'safe': .5, 'unsafe': .5}}), (.5, 0))
        self.assertEqual(parse_answer('choice', {'choice': 'unsafe', 'probabilities': {'safe': .1, 'unsafe': .9}}), (.9, 1))

    def test_invalid_numbers_and_choice_are_errors(self):
        for value in (True, float('nan'), -1, 1.1, '0.9'):
            with self.assertRaises(ValueError):
                parse_answer('noul', {'noul': value})
        with self.assertRaises(ValueError):
            parse_answer('choice', {'choice': 'safe', 'probabilities': {'safe': .1, 'unsafe': .9}})

    def test_score_direction_and_matched_descriptions(self):
        self.assertEqual(parse_answer('score', {'score': .8}), (.8, 1))
        q = questions('same question')
        self.assertEqual(q['score']['criteria'], [q['noul']['criteria']['false'], q['noul']['criteria']['true']])
        self.assertEqual(q['choice']['criteria']['unsafe'], q['score']['criteria'][1])

    def test_sampling_is_deterministic_unique_and_proportional(self):
        records = [{'uid': str(i), 'source_id': 'a' if i < 80 else 'b', 'label': i % 2} for i in range(100)]
        a = select(records, 50, 42)
        self.assertEqual(a, select(list(reversed(records)), 50, 42))
        self.assertEqual(len({r['uid'] for r in a}), 50)
        self.assertEqual(sum(r['source_id'] == 'a' for r in a), 40)
        self.assertEqual(sum(r['label'] for r in a), 25)


if __name__ == '__main__':
    unittest.main()
