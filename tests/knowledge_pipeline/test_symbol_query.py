import re
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'UxbRAG/UXB_HYBRID_RAG_V4_YORUMLU_JSON/tools'))
from uxb_question_reducer import rule_reduce

class QueryTests(unittest.TestCase):
    def test_camel_case_symbol_precedes_slot_expansion(self):
        plan=rule_reduce('X64FindMethodSlotGlobal nerede tanımlı?')
        self.assertIn('X64FindMethodSlotGlobal',plan['symbols'])
        self.assertRegex('X64FindMethodSlotGlobal',plan['regex_patterns'][0])
        self.assertIsNone(re.search(plan['regex_patterns'][0],'EVENT SLOT TRIGGER'))

if __name__=='__main__': unittest.main()
