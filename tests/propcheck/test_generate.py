import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.propcheck.generate import generate_property


def test_roundtrip_source_compiles_and_has_shape():
    src = generate_property(invariant="roundtrip", module="mypkg.codec",
                            func="encode", inverse="mypkg.codec.decode",
                            strategy="text")
    compile(src, "<gen>", "exec")               # must be valid Python
    assert "from hypothesis import given" in src
    assert "st.text()" in src
    assert "decode(encode(x)) == x" in src
    assert "derandomize=True" in src              # deterministic committed property


def test_idempotent_source():
    src = generate_property(invariant="idempotent", module="m", func="norm",
                            strategy="text")
    assert "norm(norm(x)) == norm(x)" in src


def test_oracle_requires_reference():
    with pytest.raises(ToolError) as ei:
        generate_property(invariant="oracle", module="m", func="fast",
                          strategy="int")
    assert ei.value.code == "USAGE"
    src = generate_property(invariant="oracle", module="m", func="fast",
                            reference="m.slow", strategy="int")
    assert "fast(x) == slow(x)" in src


def test_never_raises_source():
    src = generate_property(invariant="never_raises", module="m", func="parse",
                            strategy="text")
    assert "parse(x)" in src and "given" in src


def test_roundtrip_requires_inverse():
    with pytest.raises(ToolError) as ei:
        generate_property(invariant="roundtrip", module="m", func="enc",
                          strategy="int")
    assert ei.value.code == "USAGE"


def test_unknown_invariant_rejected():
    with pytest.raises(ToolError) as ei:
        generate_property(invariant="magic", module="m", func="f", strategy="int")
    assert ei.value.code == "USAGE"
