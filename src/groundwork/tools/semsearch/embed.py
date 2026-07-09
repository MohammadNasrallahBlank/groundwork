"""fastembed wrapper. Models are pulled explicitly; construction on an
uncached model exits 3 (no silent download in the query path)."""
import os

from groundwork.core.runner import ToolError


def _supported() -> dict:
    from fastembed import TextEmbedding
    return {m["model"]: m for m in TextEmbedding.list_supported_models()}


def model_available(name: str) -> bool:
    """True iff `name` is a known model already present in the local cache.

    Definitive check with no network: force HF_HUB_OFFLINE and try to
    construct. A missing snapshot raises; that means "not pulled".
    """
    if name not in _supported():
        return False
    from fastembed import TextEmbedding
    prev = os.environ.get("HF_HUB_OFFLINE")
    os.environ["HF_HUB_OFFLINE"] = "1"
    try:
        TextEmbedding(model_name=name)
        return True
    except Exception:
        return False
    finally:
        if prev is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = prev


def pull_model(name: str) -> dict:
    """Explicitly fetch a model into the fastembed cache; return model + dim."""
    from fastembed import TextEmbedding
    if name not in _supported():
        raise ToolError("USAGE", f"unknown model {name!r}", exit_code=2)
    m = TextEmbedding(model_name=name)          # fetches if absent
    dim = len(next(iter(m.embed(["probe"]))))
    return {"model": name, "dim": dim}


class Embedder:
    def __init__(self, name: str):
        if not model_available(name):
            raise ToolError(
                "NO_MODEL",
                f"embedding model {name!r} is not pulled; run: "
                f"groundwork semsearch models pull --model {name}",
                exit_code=3)
        from fastembed import TextEmbedding
        self.name = name
        self._m = TextEmbedding(model_name=name)
        self.dim = len(next(iter(self._m.embed(["probe"]))))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._m.embed(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._m.query_embed([text]))).tolist()
