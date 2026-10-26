"""Published vocabulary IDs survive content corrections and row reordering."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('catalog', Path(__file__).with_name('build-vocabulary-catalog.py'))
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class IdentityTests(unittest.TestCase):
    def test_corrections_and_reordering(self):
        identities = json.loads(catalog.OUT.read_text())['entries']
        for field in ('malayalam', 'english'):
            entries = copy.deepcopy(identities)
            # Use a row whose spelling and meaning are unique in its chapter.
            target = next(e for e in entries if all(
                sum(other['chapter'] == e['chapter'] and other[f] == e[f]
                    for other in entries) == 1 for f in ('malayalam', 'english')))
            expected = target['id']
            target[field] += ' corrected'
            target['id'] = 'new-content-hash'
            entries.reverse()
            catalog.preserve_ids(entries, identities)
            self.assertEqual(target['id'], expected)
            self.assertEqual({e['id'] for e in entries}, {e['id'] for e in identities})

    def test_new_entry(self):
        entries = [dict(id='new-id', chapter=1, malayalam='new-word', english='new-meaning')]
        catalog.preserve_ids(entries, json.loads(catalog.OUT.read_text())['entries'])
        self.assertEqual(entries[0]['id'], 'new-id')


if __name__ == '__main__':
    unittest.main()
