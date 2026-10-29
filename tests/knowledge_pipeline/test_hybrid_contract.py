"""Failure and context-budget contracts; no model quality is inferred here."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

V4=Path(__file__).resolve().parents[3]/'UxbRAG/UXB_HYBRID_RAG_V4_YORUMLU_JSON'
sys.path.insert(0,str(V4/'tools'))
import uxb_hybrid_ask as hybrid
from uxb_common import detect_layer,load_config
from uxb_ollama import OllamaError

class HybridContract(unittest.TestCase):
    def test_definition_location_uses_body_not_forward_declaration(self):
        hits=[dict(source='guide.md:2',text='Private Function X64Helper() As String',rank=1),
              dict(source='live.fbs:2',text='Declare Function X64Helper() As String',rank=2),
              dict(source='live.fbs:167',text='Private Function X64Helper() As String',rank=3)]
        answer=hybrid.source_definition_answer('X64Helper nerede tanımlı?',{'symbols':['X64Helper']},hits)
        self.assertEqual(answer,'X64Helper: live.fbs:167 [RG3]')
        self.assertEqual(hybrid.source_definition_answer('X64Helper nerede tanimli?',{'symbols':['X64Helper']},hits),answer)

    def test_behavior_question_keeps_normal_answer_route(self):
        self.assertIsNone(hybrid.source_definition_answer('X64Helper ne yapar?',{'symbols':['X64Helper']},[
            dict(source='live.fbs:167',text='Private Function X64Helper() As String',rank=1)]))

    def test_instructions_survive_large_evidence(self):
        prompt=hybrid.build_prompt({'max_context_chars':1600},'Where is Method?',{},[],[],[
            {'kind':'rg','source':'live.fbs:3','text':'x'*5000} for _ in range(30)])
        self.assertLessEqual(len(prompt),1600)
        self.assertIn('live.fbs:3',prompt)
        self.assertIn('Uydurma dosya adı',prompt)

    def test_backend_path_beats_parse_state_hint(self):
        cfg=load_config(str(V4/'config.core.json'))
        self.assertEqual(detect_layer(cfg, V4.parent.parent/'uxb/src/codegen/x64/code_generator.fbs',
                                      'Function Check(ByRef ps As ParseState)'), 'backend_x64')

    def test_chat_failure_and_empty_answer_are_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            destination=Path(folder)
            with patch.object(hybrid,'load_config',return_value={}), \
                 patch.object(hybrid,'reduce_question',return_value={}), \
                 patch.object(hybrid,'run_rg',return_value=[]), \
                 patch.object(hybrid,'chroma_search',return_value=[]), \
                 patch.object(hybrid,'abs_from_root',side_effect=lambda *a:destination/'evidence.json'), \
                 patch.object(hybrid,'chat',side_effect=OllamaError('connection failed')):
                with self.assertRaises(OllamaError): hybrid.ask_hybrid('unused','question')
                self.assertTrue((destination/'evidence.json').is_file())
                self.assertEqual(json.loads((destination/'evidence.json').read_text(encoding='utf-8'))['question'],'question')
                with patch.object(hybrid,'chat',return_value=''):
                    with self.assertRaises(OllamaError): hybrid.ask_hybrid('unused','question')

if __name__=='__main__': unittest.main()
