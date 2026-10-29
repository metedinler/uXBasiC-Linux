"""Fault-injection tests for index durability, using an isolated in-memory store."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

V4=Path(__file__).resolve().parents[3]/'UxbRAG/UXB_HYBRID_RAG_V4_YORUMLU_JSON'
sys.path.insert(0,str(V4/'tools'))
import uxb_chroma_index as index

class Store:
    def __init__(self,source): self.rows={'old':{'file':source.name,'sha1':'old'}}
    def get(self,where,include):
        selected={k:v for k,v in self.rows.items() if v['file']==where['file']}
        return {'ids':list(selected),'metadatas':list(selected.values())}
    def upsert(self,ids,documents,metadatas,embeddings): self.rows.update(zip(ids,metadatas))
    def delete(self,ids):
        for key in ids: self.rows.pop(key)

class ResumeTests(unittest.TestCase):
    def test_failure_preserves_old_vectors_and_manifest(self):
        self.scenario(fail=True)
    def test_budget_resume_embeds_each_new_chunk_only_once(self):
        self.scenario(fail=False)
    def scenario(self,fail):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'source.md'; source.write_text('new content',encoding='utf-8')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'files':[{'file':source.name,'sha1':'old','chunks':1}]}),encoding='utf-8')
            cfg={'_root':str(root),'chroma_path':'db','collection_name':'test','manifest_path':'manifest.json'}
            store=Store(source)
            chunks=[{'text':s,'chunk_index':i,'line_start':i+1,'line_end':i+1} for i,s in enumerate(['a','b'])]
            with patch.object(index,'load_config',return_value=cfg), patch.object(index,'ensure_dirs'), \
                 patch.object(index,'iter_source_files',return_value=[source]), \
                 patch.object(index.chromadb,'PersistentClient'), patch.object(index,'get_or_create_collection',return_value=store), \
                 patch.object(index,'make_chunks',return_value=chunks), \
                 patch.object(index,'embed_texts',side_effect=RuntimeError('injected failure') if fail else lambda cfg,docs:[[1.0] for _ in docs]) as embed:
                if fail:
                    with self.assertRaisesRegex(RuntimeError,'injected failure'): index.build_index('unused',max_chunks=1)
                    self.assertEqual(set(store.rows),{'old'})
                    self.assertEqual(json.loads(manifest.read_text())['files'][0]['sha1'],'old')
                else:
                    index.build_index('unused',max_chunks=1)
                    self.assertIn('old',store.rows)
                    self.assertEqual(json.loads(manifest.read_text())['files'][0]['sha1'],'old')
                    index.build_index('unused',max_chunks=1)
                    self.assertNotIn('old',store.rows)
                    self.assertEqual(len(store.rows),2)
                    self.assertEqual(index.build_index('unused',max_chunks=1)['status'],'complete')
                    self.assertEqual(embed.call_count,2)

if __name__=='__main__': unittest.main()
