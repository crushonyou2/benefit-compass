import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import embed


class EmbedCheckpointTest(unittest.TestCase):
    def test_resumes_only_matching_complete_chunks(self):
        chunks = [
            {"source": "gov24", "source_id": "one", "chunk_index": 0, "content": "a"},
            {"source": "gov24", "source_id": "two", "chunk_index": 0, "content": "b"},
        ]
        saved = {**chunks[0], "embedding": [0.0] * embed.DIMS}

        with tempfile.TemporaryDirectory() as directory:
            checkpoint = pathlib.Path(directory) / "chunks.jsonl.tmp"
            checkpoint.write_text(json.dumps(saved) + "\n", encoding="utf-8")
            with patch.object(embed, "TEMPFILE", checkpoint):
                self.assertEqual(1, embed.completed_chunks(chunks))

    def test_rejects_checkpoint_from_another_corpus(self):
        chunks = [
            {"source": "gov24", "source_id": "expected", "chunk_index": 0, "content": "a"}
        ]
        saved = {**chunks[0], "source_id": "different", "embedding": [0.0] * embed.DIMS}

        with tempfile.TemporaryDirectory() as directory:
            checkpoint = pathlib.Path(directory) / "chunks.jsonl.tmp"
            checkpoint.write_text(json.dumps(saved) + "\n", encoding="utf-8")
            with patch.object(embed, "TEMPFILE", checkpoint):
                with self.assertRaisesRegex(SystemExit, "현재 코퍼스와 다릅니다"):
                    embed.completed_chunks(chunks)

    def test_rejects_checkpoint_with_stale_content(self):
        chunks = [
            {"source": "gov24", "source_id": "same", "chunk_index": 0, "content": "new"}
        ]
        saved = {**chunks[0], "content": "old", "embedding": [0.0] * embed.DIMS}

        with tempfile.TemporaryDirectory() as directory:
            checkpoint = pathlib.Path(directory) / "chunks.jsonl.tmp"
            checkpoint.write_text(json.dumps(saved) + "\n", encoding="utf-8")
            with patch.object(embed, "TEMPFILE", checkpoint):
                with self.assertRaisesRegex(SystemExit, "현재 코퍼스와 다릅니다"):
                    embed.completed_chunks(chunks)


if __name__ == "__main__":
    unittest.main()
