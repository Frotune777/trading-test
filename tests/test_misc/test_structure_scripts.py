import unittest
from structure import find_project_root, scan_python_files

class TestStructureScripts(unittest.TestCase):
    def test_find_project_root(self):
        root = find_project_root()
        self.assertTrue(root)

    def test_scan_python_files(self):
        files = scan_python_files(find_project_root())
        self.assertIsInstance(files, list)
