import copy
import unittest
from www_posim_autonomy.standalone import compatible,runtime_matches

class UpdateSafety(unittest.TestCase):
    def setUp(self):
        self.manifest=dict(version='0.2.0',minimum_client='0.2.0',protocol=2,rules_version='maritime-class-2',adapter_sha256='a'*64)
    def test_new_protocol_or_minimum_client_requires_update(self):
        self.assertTrue(compatible(self.manifest))
        for changes in (dict(protocol=3),dict(minimum_client='0.3.0')):
            self.assertFalse(compatible(dict(self.manifest,**changes)))
    def test_runtime_content_or_rules_mismatch_and_missing_manifest_fail_closed(self):
        self.assertTrue(runtime_matches(self.manifest,copy.deepcopy(self.manifest)))
        self.assertFalse(runtime_matches({},{}))
        for key in ('version','protocol','rules_version','adapter_sha256'):
            changed=copy.deepcopy(self.manifest);changed[key]='different'
            self.assertFalse(runtime_matches(changed,self.manifest))

if __name__=='__main__':unittest.main()
