import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.semsearch import _DEFAULT_MODEL
from groundwork.tools.semsearch.embed import Embedder, model_available


def test_default_model_is_available_after_task1(tmp_path):
    # Task 1's benchmark pulled the default into the fastembed cache.
    assert model_available(_DEFAULT_MODEL) is True


def test_embedder_round_trip_dimensions():
    e = Embedder(_DEFAULT_MODEL)
    docs = e.embed_documents(["def retry(): ...", "def charge(): ..."])
    assert len(docs) == 2 and len(docs[0]) == e.dim
    q = e.embed_query("retry logic")
    assert len(q) == e.dim


def test_similar_text_scores_higher_than_unrelated():
    import numpy as np
    e = Embedder(_DEFAULT_MODEL)
    d = e.embed_documents(["def retry(fn): loop and try again",
                           "def charge_card(amount): bill the customer"])
    q = np.array(e.embed_query("retry the operation"))
    sims = [float(np.dot(q, np.array(x)) /
                  (np.linalg.norm(q) * np.linalg.norm(x))) for x in d]
    assert sims[0] > sims[1]


def test_uncached_model_raises_no_model():
    with pytest.raises(ToolError) as ei:
        Embedder("definitely/not-a-real-model-xyz")
    assert ei.value.code == "NO_MODEL" and ei.value.exit_code == 3
