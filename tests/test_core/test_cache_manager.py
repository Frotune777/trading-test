import unittest
import shutil
from pathlib import Path
from core.cache_manager import CacheManager

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path("./.tmp_cache_tests")
        self.temp_dir.mkdir(exist_ok=True)
        self.cache = CacheManager(enabled=True, cache_dir=str(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_get_clear_stats(self):
        self.cache.set("k1", {"a": 1}, ttl=60)
        v = self.cache.get("k1")
        self.assertEqual(v["a"], 1)

        stats_before = self.cache.get_stats()
        self.assertIn("hits", stats_before)
        self.assertIn("misses", stats_before)

        self.cache.clear()
        self.assertIsNone(self.cache.get("k1"))

    def test_expiry(self):
        self.cache.set("k2", "x", ttl=-1)
        self.assertIsNone(self.cache.get("k2"))
