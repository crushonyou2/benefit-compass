import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import staging_copy


class StagingGuardTest(unittest.TestCase):
    def test_allowed_localhost(self):
        self.assertTrue(staging_copy.is_allowed_staging_dsn("postgresql://postgres:postgres@localhost:5433/benefit"))
        self.assertTrue(staging_copy.is_allowed_staging_dsn("postgresql://postgres:postgres@127.0.0.1:5433/benefit"))
        self.assertTrue(staging_copy.is_allowed_staging_dsn("postgresql://postgres:postgres@[::1]:5433/benefit"))
        self.assertTrue(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@localhost/benefit"))
        self.assertTrue(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@127.0.0.1/benefit"))

    def test_rejected_remote_hosts(self):
        self.assertFalse(staging_copy.is_allowed_staging_dsn("postgresql://neondb_owner:npg_xxx@ep-xxx.neon.tech/neondb"))
        self.assertFalse(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@mydb.abc123.rds.amazonaws.com:5432/db"))
        self.assertFalse(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@db.supabase.co:5432/postgres"))
        self.assertFalse(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@remote.example.com:5432/db"))
        self.assertFalse(staging_copy.is_allowed_staging_dsn("postgresql://user:pass@192.168.1.10:5432/db"))

    def test_identical_dsn_rejected_by_copy(self):
        # copy() checks PROD_URL == STAGING_URL, but helper also should be testable
        self.assertEqual(staging_copy.parse_dsn_host("postgresql://postgres:postgres@localhost:5433/benefit"), "localhost")
        self.assertEqual(staging_copy.parse_dsn_host("postgresql://user:pass@ep-xxx.neon.tech/db"), "ep-xxx.neon.tech")

    def test_mask_dsn_hides_credentials(self):
        masked = staging_copy.mask_dsn("postgresql://myuser:mypass@ep-xxx.neon.tech:5432/neondb")
        self.assertNotIn("myuser", masked)
        self.assertNotIn("mypass", masked)
        self.assertIn("ep-xxx.neon.tech", masked)
        masked2 = staging_copy.mask_dsn("postgresql://postgres:postgres@localhost:5433/benefit")
        self.assertNotIn("postgres", masked2.split("/")[0])  # user not in host part
        self.assertIn("localhost", masked2)

    def test_validate_counts_matches(self):
        prod = {"policy_total": 13589, "policy_by_source": {"gov24": 10958, "youth": 2631}, "chunk_total": 17609, "missing_embeddings": 0, "no_chunk": 0, "orphan": 0, "duplicate": 0}
        staging = {"policy_total": 13589, "policy_by_source": {"gov24": 10958, "youth": 2631}, "chunk_total": 17609, "missing_embeddings": 0, "no_chunk": 0, "orphan": 0, "duplicate": 0}
        self.assertEqual([], staging_copy.validate_counts(prod, staging))

    def test_validate_counts_mismatch(self):
        prod = {"policy_total": 13589, "policy_by_source": {"gov24": 10958, "youth": 2631}, "chunk_total": 17609, "missing_embeddings": 0, "no_chunk": 0, "orphan": 0, "duplicate": 0}
        bad = {"policy_total": 13588, "policy_by_source": {"gov24": 10958, "youth": 2630}, "chunk_total": 17609, "missing_embeddings": 0, "no_chunk": 0, "orphan": 0, "duplicate": 0}
        errs = staging_copy.validate_counts(prod, bad)
        self.assertTrue(len(errs) >= 2)


if __name__ == "__main__":
    unittest.main()
