import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'paper-to-course'
spec = importlib.util.spec_from_file_location('portable_install', SOURCE / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PortableInstallTests(unittest.TestCase):
    def test_custom_agent_directory_receives_complete_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            target, backup = installer.install(Path(temp) / 'custom agent' / 'skills')
            self.assertIsNone(backup)
            for source in SOURCE.rglob('*'):
                if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc':
                    dest = target / source.relative_to(SOURCE)
                    self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), hashlib.sha256(dest.read_bytes()).digest())

    def test_existing_installation_is_preserved_and_explicit_replace_keeps_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            target, _ = installer.install(temp)
            (target / 'user-note.txt').write_text('keep me', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                installer.install(temp)
            self.assertEqual((target / 'user-note.txt').read_text(), 'keep me')
            target, backup = installer.install(temp, replace=True)
            self.assertEqual((backup / 'user-note.txt').read_text(), 'keep me')
            self.assertFalse((target / 'user-note.txt').exists())

    def test_dry_run_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'not-created'
            target, _ = installer.install(root, dry_run=True)
            self.assertEqual(target, root / 'paper-to-course')
            self.assertFalse(root.exists())

    def test_nested_destination_cannot_copy_skill_into_itself(self):
        with self.assertRaises(ValueError):
            installer.install(SOURCE / 'nested', dry_run=True)


if __name__ == '__main__':
    unittest.main()
