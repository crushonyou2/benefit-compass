import unittest

from load_db import validate_chunk_coverage


class LoadDbValidationTest(unittest.TestCase):
    def test_accepts_complete_policy_chunk_coverage(self):
        policies = [
            {"source": "gov24", "source_id": "one"},
            {"source": "gov24", "source_id": "two"},
        ]
        chunks = [
            {"source": "gov24", "source_id": "one"},
            {"source": "gov24", "source_id": "two"},
        ]

        validate_chunk_coverage(policies, chunks)

    def test_rejects_policy_without_chunks(self):
        policies = [
            {"source": "gov24", "source_id": "one"},
            {"source": "gov24", "source_id": "two"},
        ]
        chunks = [{"source": "gov24", "source_id": "one"}]

        with self.assertRaisesRegex(SystemExit, "missing_chunks=1"):
            validate_chunk_coverage(policies, chunks)


if __name__ == "__main__":
    unittest.main()
