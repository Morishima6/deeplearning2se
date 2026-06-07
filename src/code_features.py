"""Feature helpers for LOSVER-Light preprocessing."""

from __future__ import annotations

import re
from collections import Counter
from statistics import mean
from typing import Any


DANGEROUS_APIS = (
    "strcpy",
    "strncpy",
    "strcat",
    "sprintf",
    "vsprintf",
    "gets",
    "memcpy",
    "memmove",
    "malloc",
    "calloc",
    "realloc",
    "free",
    "scanf",
    "sscanf",
    "fscanf",
)

BRANCH_LOOP_KEYWORDS = ("if", "else", "for", "while", "switch", "case", "do")
ERROR_HANDLING_TOKENS = ("return", "goto", "NULL", "errno", "EINVAL", "ENOMEM")
SINK_PATTERNS = (
    "system",
    "popen",
    "exec",
    "open",
    "read",
    "write",
    "recv",
    "send",
)

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def split_code_lines(code: str) -> list[str]:
    return code.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _contains_word(line: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", line) is not None


def score_line(line: str) -> tuple[float, list[str]]:
    stripped = line.strip()
    if not stripped:
        return 0.0, []

    score = 0.0
    reasons: list[str] = []

    api_hits = [api for api in DANGEROUS_APIS if _contains_word(stripped, api)]
    if api_hits:
        score += 3.0 + 0.5 * (len(api_hits) - 1)
        reasons.append("dangerous_api")

    if any(symbol in stripped for symbol in ("->", "*", "[", "]")):
        score += 1.5
        reasons.append("pointer_or_array")

    if any(_contains_word(stripped, keyword) for keyword in BRANCH_LOOP_KEYWORDS):
        score += 1.0
        reasons.append("branch_or_loop")

    if any(token in stripped for token in ERROR_HANDLING_TOKENS):
        score += 0.8
        reasons.append("error_handling")

    if any(_contains_word(stripped, sink) for sink in SINK_PATTERNS):
        score += 0.8
        reasons.append("io_or_process_api")

    if len(stripped) >= 100:
        score += 0.8
        reasons.append("long_line")
    elif len(stripped) >= 80:
        score += 0.4
        reasons.append("medium_long_line")

    symbol_count = sum(1 for ch in stripped if not ch.isalnum() and not ch.isspace() and ch != "_")
    symbol_density = symbol_count / max(len(stripped), 1)
    if symbol_density >= 0.28:
        score += 0.8
        reasons.append("symbol_dense")
    elif symbol_density >= 0.20:
        score += 0.4
        reasons.append("moderately_symbol_dense")

    if api_hits and not any(token in stripped for token in ("if", "assert", "return", "NULL")):
        score += 0.7
        reasons.append("unchecked_sensitive_call")

    return round(score, 3), reasons


def rank_risk_lines(code: str, top_k: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for idx, line in enumerate(split_code_lines(code), start=1):
        score, reasons = score_line(line)
        if score <= 0:
            continue
        candidates.append(
            {
                "line_no": idx,
                "score": score,
                "text": line.strip(),
                "reasons": reasons,
            }
        )

    ranked = sorted(candidates, key=lambda item: (-item["score"], item["line_no"]))
    return ranked[:top_k]


def add_mod_tags(code: str, risk_lines: list[dict[str, Any]]) -> str:
    marked_line_numbers = {int(item["line_no"]) for item in risk_lines}
    output_lines = []
    for idx, line in enumerate(split_code_lines(code), start=1):
        if idx in marked_line_numbers:
            output_lines.append(f"<MOD> {line} </MOD>")
        else:
            output_lines.append(line)
    return "\n".join(output_lines)


def build_prefix(code: str, risk_lines: list[dict[str, Any]]) -> str:
    if not risk_lines:
        return "Risk lines: none\n\n" + code

    summary_lines = ["Risk lines:"]
    for item in risk_lines:
        reasons = ",".join(item["reasons"])
        text = item["text"].replace("\t", " ")
        summary_lines.append(f"- L{item['line_no']} score={item['score']} reasons={reasons}: {text}")
    return "\n".join(summary_lines) + "\n\n" + code


def extract_metrics(code: str, risk_lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    lines = split_code_lines(code)
    nonempty_lines = [line for line in lines if line.strip()]
    tokens = TOKEN_RE.findall(code)
    token_counts = Counter(tokens)

    dangerous_api_hits = sum(
        len(re.findall(rf"\b{re.escape(api)}\b", code)) for api in DANGEROUS_APIS
    )
    branch_loop_hits = sum(
        len(re.findall(rf"\b{re.escape(keyword)}\b", code)) for keyword in BRANCH_LOOP_KEYWORDS
    )
    pointer_array_hits = code.count("->") + code.count("*") + code.count("[") + code.count("]")
    error_handling_hits = sum(code.count(token) for token in ERROR_HANDLING_TOKENS)
    symbol_count = sum(1 for ch in code if not ch.isalnum() and not ch.isspace() and ch != "_")

    risk_lines = risk_lines or []
    risk_scores = [float(item["score"]) for item in risk_lines]

    return {
        "num_lines": len(lines),
        "num_nonempty_lines": len(nonempty_lines),
        "num_chars": len(code),
        "num_tokens": len(tokens),
        "num_unique_tokens": len(token_counts),
        "avg_line_length": round(mean([len(line) for line in nonempty_lines]), 3) if nonempty_lines else 0.0,
        "max_line_length": max([len(line) for line in lines], default=0),
        "num_dangerous_api": dangerous_api_hits,
        "num_branch_loop": branch_loop_hits,
        "num_pointer_array": pointer_array_hits,
        "num_error_handling": error_handling_hits,
        "symbol_density": round(symbol_count / max(len(code), 1), 5),
        "num_risk_lines": len(risk_lines),
        "max_risk_score": max(risk_scores, default=0.0),
        "avg_risk_score": round(mean(risk_scores), 3) if risk_scores else 0.0,
    }

