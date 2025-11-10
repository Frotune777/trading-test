# tests/_helpers/temp_dirs.py
import tempfile
import shutil

class TempDir:
    def __init__(self):
        self.path = tempfile.mkdtemp()

    def cleanup(self):
        shutil.rmtree(self.path)
