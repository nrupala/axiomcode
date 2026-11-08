"""AxiomCode — untrusted-source policy screen (runs BEFORE Lean elaborates).

Why this exists
---------------
`lake env lean` elaborates the submitted file, and Lean runs code at
elaboration time: `#eval`, `run_cmd`, `initialize`, custom elaborators and
`IO` actions all execute on the host with the verifier's privileges. A
proof-checking service that elaborates untrusted text without a screen is a
remote-code-execution service. This module is the first line of defence; an
OS sandbox (see core/sandbox.py) is the second. Neither replaces the other.

It also blocks kernel-bypass and cheat constructs that the axiom audit alone
cannot see (e.g. `set_option debug.skipKernelTC true`), and declarations the
axiom audit would silently skip.

Fails closed: any BLOCK finding means the submission is rejected unproved,
with the reason and line number returned to the caller. The LLM repair loop
never sees a BLOCK — adversarial input is not a typo to fix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Bump whenever a rule is added, removed or changed. Recorded on every
#: certificate so a verdict can be traced to the exact rule set that ran.
POLICY_VERSION = "2026-10-29.1"

#: Imports an untrusted proof may use (AxiomCode = the house spec/tactic library). Anything else (notably `Lean`,
#: `Lean.Elab`, `Lean.Meta`, which unlock metaprogramming and IO) is blocked.
ALLOWED_IMPORT_ROOTS = ("AxiomCode", "Mathlib", "Std", "Batteries", "Init", "Aesop", "Qq", "Plausible")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # "BLOCK" or "WARN"
    line: int
    excerpt: str
    reason: str

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "line": self.line,
            "excerpt": self.excerpt,
            "reason": self.reason,
        }


# (rule id, severity, compiled pattern, reason)
_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    # ── host execution at elaboration time ─────────────────────────────────
    ("exec.eval", "BLOCK", re.compile(r"#eval!?\b"), "#eval runs code on the verifier host"),
    (
        "exec.run_cmd",
        "BLOCK",
        re.compile(r"\b(run_cmd|run_elab|run_meta|run_tac)\b"),
        "run_* commands execute metaprograms on the verifier host",
    ),
    (
        "exec.initialize",
        "BLOCK",
        re.compile(r"\b(builtin_)?initialize\b"),
        "initialize blocks run IO when the module loads",
    ),
    (
        "exec.io",
        "BLOCK",
        re.compile(r"\b(IO|System|EIO|BaseIO)\.[A-Za-z_]"),
        "IO/System calls can touch the host filesystem, network or processes",
    ),
    ("exec.extern", "BLOCK", re.compile(r"@\[\s*extern\b"), "@[extern] binds to native code"),
    ("exec.unsafe", "BLOCK", re.compile(r"\bunsafe\b"), "unsafe definitions bypass the kernel's guarantees"),
    ("exec.exit", "BLOCK", re.compile(r"#exit\b"), "#exit truncates elaboration; later declarations are never checked"),
    # ── metaprogramming that can rewrite what the kernel sees ──────────────
    (
        "meta.syntax",
        "BLOCK",
        re.compile(
            r"^[ \t]*(?:local\s+|scoped\s+)?(macro|macro_rules|syntax|elab|elab_rules|declare_syntax_cat|notation3?)\b",
            re.MULTILINE,
        ),
        "custom syntax/elaborators can disguise what a declaration actually proves",
    ),
    # ── kernel bypass / cheat options ──────────────────────────────────────
    (
        "cheat.skip_kernel",
        "BLOCK",
        re.compile(r"set_option\s+debug\.skipKernelTC\b"),
        "debug.skipKernelTC disables the kernel type check — nothing is proved",
    ),
    ("cheat.debug_option", "BLOCK", re.compile(r"set_option\s+debug\."), "debug.* options alter checking behaviour"),
    (
        "cheat.native_decide",
        "BLOCK",
        re.compile(r"\bnative_decide\b|\bLean\.ofReduceBool\b|\bLean\.trustCompiler\b"),
        "native_decide trusts the compiler, not the kernel (axiom Lean.ofReduceBool)",
    ),
    ("cheat.sorry_ax", "BLOCK", re.compile(r"\bsorryAx\b"), "direct use of sorryAx smuggles an unproved obligation"),
    (
        "cheat.axiom_decl",
        "BLOCK",
        re.compile(r"^[ \t]*(?:private\s+|protected\s+)?axiom\b", re.MULTILINE),
        "user-declared axioms can prove anything",
    ),
    ("cheat.opaque", "WARN", re.compile(r"\bopaque\b"), "opaque constants hide their definitions from the reader"),
    (
        "cheat.implemented_by",
        "WARN",
        re.compile(r"@\[\s*implemented_by\b"),
        "implemented_by: runtime code differs from the definition the proof is about",
    ),
    # ── declarations the axiom audit could skip ────────────────────────────
    (
        "audit.private_theorem",
        "BLOCK",
        re.compile(r"^[ \t]*(?:@\[[^\]]*\]\s*)*private\s+(?:theorem|lemma)\b", re.MULTILINE),
        "private theorems get mangled names that #print axioms cannot address",
    ),
    (
        "audit.example",
        "WARN",
        re.compile(r"^[ \t]*example\b", re.MULTILINE),
        "examples are anonymous and not covered by the certificate",
    ),
]

_IMPORT_RE = re.compile(r"^[ \t]*import\s+([A-Za-z_][A-Za-z0-9_.']*)", re.MULTILINE)


def _strip_comments(code: str) -> str:
    """Remove block (/- -/, nested) and line (--) comments, preserving line
    numbers so findings point at the right line. Doc comments are comments."""
    out: list[str] = []
    i, depth, n = 0, 0, len(code)
    in_string = False
    while i < n:
        two = code[i : i + 2]
        c = code[i]
        if depth == 0 and not in_string and c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(code[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if two == "/-":
            depth += 1
            i += 2
            continue
        if depth > 0:
            if two == "-/":
                depth -= 1
                i += 2
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if two == "--":
            while i < n and code[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def screen_source(code: str) -> list[Finding]:
    """Return every policy finding for the submitted Lean source."""
    clean = _strip_comments(code)
    lines = clean.splitlines()
    findings: list[Finding] = []

    def excerpt(line_no: int) -> str:
        return lines[line_no - 1].strip()[:160] if 0 < line_no <= len(lines) else ""

    for rule, severity, pattern, reason in _RULES:
        for m in pattern.finditer(clean):
            ln = _line_of(clean, m.start())
            findings.append(Finding(rule, severity, ln, excerpt(ln), reason))

    for m in _IMPORT_RE.finditer(clean):
        module = m.group(1)
        root = module.split(".", 1)[0]
        if root not in ALLOWED_IMPORT_ROOTS:
            ln = _line_of(clean, m.start())
            findings.append(
                Finding(
                    "import.disallowed",
                    "BLOCK",
                    ln,
                    excerpt(ln),
                    f"import {module} is outside the allowed roots {ALLOWED_IMPORT_ROOTS}",
                )
            )

    findings.sort(key=lambda f: (f.line, f.rule))
    return findings


def blocking(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "BLOCK"]


def format_findings(findings: list[Finding]) -> str:
    if not findings:
        return f"policy screen {POLICY_VERSION}: clean"
    rows = [f"  - [{f.severity}] {f.rule} (line {f.line}): {f.reason} :: {f.excerpt}" for f in findings]
    return f"policy screen {POLICY_VERSION}:\n" + "\n".join(rows)


# Declaration extractor used by the axiom audit. It must see every theorem a
# certificate will vouch for, including ones carrying attributes, docstrings
# or modifiers — a theorem the audit cannot see is a theorem nobody checked.
_DECL_RE = re.compile(
    r"^[ \t]*(?:@\[[^\]]*\]\s*)*"
    r"(?:(?:protected|noncomputable|nonrec|partial)\s+)*"
    r"(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
    re.MULTILINE,
)
_NS_RE = re.compile(r"^[ \t]*namespace\s+([A-Za-z_][A-Za-z0-9_.']*)")
_END_RE = re.compile(r"^[ \t]*end\b(?:\s+([A-Za-z_][A-Za-z0-9_.']*))?")
_SECTION_RE = re.compile(r"^[ \t]*(?:noncomputable\s+)?section\b")


def theorem_names(code: str) -> list[str]:
    """Fully-qualified theorem/lemma names, tracking namespaces and sections.

    Attributes (`@[simp]`), modifiers (`protected`, `noncomputable`) and
    docstrings no longer hide a declaration from the audit."""
    clean = _strip_comments(code)
    names: list[str] = []
    scopes: list[tuple[str, str | None]] = []  # ("ns", name) | ("sec", None)
    for line in clean.splitlines():
        m = _NS_RE.match(line)
        if m:
            scopes.append(("ns", m.group(1)))
            continue
        if _SECTION_RE.match(line):
            scopes.append(("sec", None))
            continue
        if _END_RE.match(line):
            if scopes:
                scopes.pop()
            continue
        d = _DECL_RE.match(line)
        if d:
            prefix = [n for kind, n in scopes if kind == "ns" and n]
            names.append(".".join([*prefix, d.group(1)]))
    return names
