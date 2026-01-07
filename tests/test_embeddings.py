"""Tests for embedding functionality."""

import pytest


class TestModelNameValidation:
    """Tests for model name validation security."""

    def test_valid_model_names(self):
        """Valid model names should pass validation."""
        from omni_cortex.embeddings.local import _validate_model_name

        # These should not raise
        _validate_model_name("all-MiniLM-L6-v2")
        _validate_model_name("sentence-transformers/all-mpnet-base-v2")
        _validate_model_name("bert_base_uncased")
        _validate_model_name("BAAI/bge-small-en-v1.5".replace(".", ""))  # dots stripped
        _validate_model_name("model123")

    def test_invalid_model_names_quotes(self):
        """Model names with quotes should be rejected."""
        from omni_cortex.embeddings.local import _validate_model_name

        with pytest.raises(ValueError, match="Invalid model name"):
            _validate_model_name('model"; import os; os.system("ls")')

    def test_invalid_model_names_special_chars(self):
        """Model names with special characters should be rejected."""
        from omni_cortex.embeddings.local import _validate_model_name

        invalid_names = [
            "model$(whoami)",
            "model`id`",
            "model;ls",
            "model\nprint('evil')",
            "model\\path",
            "model<script>",
            "model'or'1=1",
        ]

        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid model name"):
                _validate_model_name(name)

    def test_empty_model_name(self):
        """Empty model names should be rejected."""
        from omni_cortex.embeddings.local import _validate_model_name

        with pytest.raises(ValueError, match="Invalid model name"):
            _validate_model_name("")

    def test_model_name_with_spaces(self):
        """Model names with spaces should be rejected."""
        from omni_cortex.embeddings.local import _validate_model_name

        with pytest.raises(ValueError, match="Invalid model name"):
            _validate_model_name("model with spaces")


class TestEmbeddingHelpers:
    """Tests for embedding helper functions."""

    def test_vector_to_blob_and_back(self):
        """Test converting vectors to blobs and back."""
        import numpy as np
        from omni_cortex.embeddings.local import vector_to_blob, blob_to_vector

        # Create a test vector
        original = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

        # Convert to blob and back
        blob = vector_to_blob(original)
        restored = blob_to_vector(blob)

        # Should be identical
        assert np.allclose(original, restored)

    def test_is_model_available(self):
        """Test checking if sentence-transformers is available."""
        from omni_cortex.embeddings.local import is_model_available

        # Should return bool without error
        result = is_model_available()
        assert isinstance(result, bool)
