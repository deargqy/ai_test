import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image


class ObserveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        Image.new('RGB', (100, 80), '#123456').save(self.root/'shot.png')
        spec = importlib.util.spec_from_file_location('observe', Path(__file__).with_name('observe.py'))
        self.assertTrue(Path(spec.origin).is_file(), 'observation packer not implemented')
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def pack(self, entries, size=(100, 80)):
        manifest = {'batchId': 'test-round2', 'expectedSize': size,
                    'context': {'gold': 55, 'purchases': [{'name': 'bridge', 'cost': 32}], 'unknown': None},
                    'entries': entries}
        p = self.root/'input.json'
        p.write_text(json.dumps(manifest), encoding='utf-8')
        return self.mod.pack(p, self.root/'out')

    def test_invalid_resolution_and_crop_rejected(self):
        for size, box in [((200, 80), [0, 0, 90, 70]), ((100, 80), [-1, 0, 90, 70]),
                          ((100, 80), [0, 0, 101, 80]), ((100, 80), [20, 20, 20, 30])]:
            with self.subTest(size=size, box=box), self.assertRaises(ValueError):
                self.pack([{'id': 'a', 'source': 'shot.png', 'box': box}], size)

    def test_exact_duplicate_retains_both_ids_and_context(self):
        result = self.pack([{'id': n, 'source': 'shot.png', 'box': [10, 10, 90, 70]} for n in ['a', 'b']])
        self.assertEqual([e['id'] for e in result['entries']], ['a', 'b'])
        self.assertEqual(result['entries'][0]['crop'], result['entries'][1]['crop'])
        self.assertEqual(result['context']['purchases'][0]['cost'], 32)
        self.assertIsNone(result['context']['unknown'])
        self.assertIsNone(result['entries'][0]['reading'])
        with Image.open(self.root/'out'/result['entries'][0]['crop']) as crop:
            self.assertEqual(crop.size, (80, 60))
        self.assertEqual(result['metrics']['uniqueCrops'], 1)

    def test_annotations_link_to_evidence_and_unknown_ids_fail(self):
        self.pack([{'id': 'a', 'source': 'shot.png', 'box': [0, 0, 100, 80]}])
        b = self.root/'out/bundle.json'
        p = self.root/'readings.json'
        p.write_text(json.dumps({'entries': [{'id': 'bad', 'uncertain': []}]}))
        with self.assertRaises(ValueError): self.mod.annotate(b, p)
        p.write_text(json.dumps({'entries': [{'id': 'a', 'name': 'test', 'price': None, 'uncertain': ['price']}]}))
        result = self.mod.annotate(b, p)
        self.assertEqual(result['entries'][0]['reading']['method'], 'assistant-visual')
        self.assertIsNone(result['entries'][0]['reading']['price'])
        self.assertEqual(result['entries'][0]['reading']['evidenceSha256'], result['entries'][0]['sourceSha256'])


if __name__ == '__main__': unittest.main()
