import unittest

from fix_youth_urls import is_commit_allowed


class FixYouthUrlsCommitGateTest(unittest.TestCase):
    def test_all_valid_allows_commit(self):
        self.assertTrue(is_commit_allowed(
            after_missing=599, expected_after=599,
            missing_embeddings=0, duplicate_policies=0,
            policies_without_chunks=0, orphan_chunks=0,
            updated_rows=15, expected_rows=15,
        ))

    def test_after_missing_mismatch_blocks(self):
        self.assertFalse(is_commit_allowed(
            after_missing=600, expected_after=599,
            missing_embeddings=0, duplicate_policies=0,
            policies_without_chunks=0, orphan_chunks=0,
            updated_rows=15, expected_rows=15,
        ))

    def test_missing_embeddings_blocks(self):
        self.assertFalse(is_commit_allowed(
            after_missing=599, expected_after=599,
            missing_embeddings=1, duplicate_policies=0,
            policies_without_chunks=0, orphan_chunks=0,
            updated_rows=15, expected_rows=15,
        ))

    def test_duplicate_blocks(self):
        self.assertFalse(is_commit_allowed(599, 599, 0, 1, 0, 0, 15, 15))

    def test_no_chunk_blocks(self):
        self.assertFalse(is_commit_allowed(599, 599, 0, 0, 1, 0, 15, 15))

    def test_orphan_blocks(self):
        self.assertFalse(is_commit_allowed(599, 599, 0, 0, 0, 1, 15, 15))

    def test_rowcount_mismatch_blocks(self):
        self.assertFalse(is_commit_allowed(599, 599, 0, 0, 0, 0, 14, 15))
        self.assertFalse(is_commit_allowed(599, 599, 0, 0, 0, 0, 16, 15))
        # psycopg2 unknown rowcount -1 must not be treated as success
        self.assertFalse(is_commit_allowed(599, 599, 0, 0, 0, 0, -1, 15))

    def test_idempotent_zero_updates_allows_when_already_fixed(self):
        # already fixed: before 599, 0 updates, after 599
        self.assertTrue(is_commit_allowed(599, 599, 0, 0, 0, 0, 0, 0))

if __name__ == "__main__":
    unittest.main()
