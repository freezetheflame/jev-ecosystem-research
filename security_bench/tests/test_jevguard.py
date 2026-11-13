import unittest
from security_bench.adapters import build_request, parse_prediction


class JevGuardTests(unittest.TestCase):
    def setUp(self):
        self.model={'api':'jevguard','adapter':'jevguard_safety','parameters':{},'input_field':'user_request'}
    def test_native_safety_request_does_not_use_category_choice_as_verdict(self):
        request=build_request(self.model,{'user_request':' ORIGINAL\n'},'TEST POLICY')
        self.assertEqual(request,{'input':'TEST POLICY\n\nUser request:\n ORIGINAL\n','options':[],
                                  'mode':'single','safety_applicable':True})
        response={'safety':'unsafe','categories':['safe'],'truncated':False}
        self.assertEqual(parse_prediction(self.model,response),1)
        response['safety']='safe';response['categories']=['unsafe']
        self.assertEqual(parse_prediction(self.model,response),0)
    def test_missing_safety_or_truncated_result_never_becomes_safe(self):
        for response in [{},{'categories':['safe'],'truncated':False},{'safety':'safe'},
                         {'safety':'safe','truncated':True},{'safety':'unknown','truncated':False}]:
            with self.subTest(response=response),self.assertRaises(ValueError):parse_prediction(self.model,response)
