"""Fit the highest-ranked symbols to a token budget; emit a grouped text map."""
import math

from groundwork.tools.cartographer.extract import Symbol


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def _line(sym: Symbol) -> str:
    return f"  {sym.kind[:4]:>4} {sym.name}  ({sym.file}:{sym.line})"


def render_text(ranked: list[tuple[Symbol, float]], budget: int) -> dict:
    total = len(ranked)
    header = "# Repository map (ranked by reference centrality)\n"
    lines: list[str] = []
    shown = 0
    for sym, _score in ranked:
        candidate = "\n".join(lines + [_line(sym)])
        if estimate_tokens(header + candidate) > budget and shown > 0:
            break
        lines.append(_line(sym))
        shown += 1
    body = header + "\n".join(lines)
    return {"map": body, "symbols_shown": shown, "symbols_total": total,
            "est_tokens": estimate_tokens(body), "budget": budget,
            "truncated": shown < total}
