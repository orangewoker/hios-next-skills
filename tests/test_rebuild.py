import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from rebuild import rebuild
from catalog_lib import manifest, version_of


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='hios-skill-publish-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = self.root / 'skills-index.json'
        self.index.write_text(json.dumps({'schemaVersion': 1, 'skills': []}), encoding='utf-8')
        self.folder = self.root / 'skills' / 'test-skill'
        self.folder.mkdir(parents=True)
        self.skill = self.folder / 'SKILL.md'
        self.skill.write_text('---\nname: test-skill\ndescription: Test description\nmetadata:\n  title: Test title\n  category: Space\n  version: "1.0.0"\n---\nBody\n', encoding='utf-8')

    def test_first_publication_and_upgrade_are_flat_and_immutable(self):
        (self.folder / 'lib').mkdir()
        (self.folder / 'lib' / 'tool.py').write_text('VALUE=1\n', encoding='utf-8')
        cache = self.folder / 'lib' / '__pycache__'
        cache.mkdir()
        (cache / 'tool.cpython-313.pyc').write_bytes(b'private generated cache')
        first = rebuild(self.root, 'test-skill', '1.0.0', new=True)
        package = self.root / first['package']
        original = package.read_bytes()
        self.assertEqual(first['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(first['size'], len(original))
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(set(archive.namelist()), {'SKILL.md', 'lib/tool.py'})
        with self.assertRaisesRegex(ValueError, 'increase'):
            rebuild(self.root, 'test-skill', '1.0.0')
        with self.assertRaisesRegex(ValueError, 'already registered'):
            rebuild(self.root, 'test-skill', '1.0.1', new=True)
        next_entry = rebuild(self.root, 'test-skill', '1.0.1')
        self.assertEqual(version_of(manifest(self.skill.read_text('utf-8'))[0]), '1.0.1')
        self.assertEqual(package.read_bytes(), original)
        self.assertNotEqual(next_entry['sha256'], first['sha256'])
        self.assertEqual(len(json.loads(self.index.read_text('utf-8'))['skills']), 1)

    def test_invalid_inputs_do_not_modify_manifest_or_index(self):
        before = (self.index.read_bytes(), self.skill.read_bytes())
        with self.assertRaisesRegex(ValueError, '--new'):
            rebuild(self.root, 'test-skill', '1.0.0')
        for sid, version in [('../outside', '1.0.0'), ('test-skill', 'bad')]:
            with self.assertRaises(ValueError):
                rebuild(self.root, sid, version, new=True)
        self.assertEqual((self.index.read_bytes(), self.skill.read_bytes()), before)
        self.assertFalse((self.root / 'packages').exists())

    def test_json_frontmatter_updates_remain_supported(self):
        self.skill.write_text('---\n' + json.dumps({'name': 'test-skill', 'description': 'Legacy JSON', 'metadata': {'title': 'Legacy', 'category': 'Other', 'version': '1.0.0'}}) + '\n---\nLegacy body\n', encoding='utf-8')
        rebuild(self.root, 'test-skill', '1.0.0', new=True)
        rebuild(self.root, 'test-skill', '1.1.0')
        meta = json.loads(self.skill.read_text('utf-8').split('---')[1])
        self.assertEqual(meta['metadata']['version'], '1.1.0')

    def test_existing_archive_is_never_overwritten(self):
        packages = self.root / 'packages'
        packages.mkdir()
        target = packages / 'test-skill-1.0.0.zip'
        target.write_bytes(b'already published')
        before = self.index.read_bytes()
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            rebuild(self.root, 'test-skill', '1.0.0', new=True)
        self.assertEqual(target.read_bytes(), b'already published')
        self.assertEqual(self.index.read_bytes(), before)

    def test_name_mismatch_and_invalid_hios_metadata_are_rejected(self):
        original = self.skill.read_text('utf-8')
        for content in [original.replace('name: test-skill', 'name: different-skill'),
                        original.replace('metadata:\n', 'metadata:\n  hios: invalid\n')]:
            self.skill.write_text(content, encoding='utf-8')
            before = self.index.read_bytes()
            with self.assertRaises(ValueError):
                rebuild(self.root, 'test-skill', '1.0.0', new=True)
            self.assertEqual(self.index.read_bytes(), before)
            self.assertFalse((self.root / 'packages').exists())


if __name__ == '__main__':
    unittest.main()
