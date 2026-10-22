"""Fitness functions for the two domain rules that are easy to erode:

1. The domain imports only the standard library and `vaeil.domain`, so it
   cannot quietly depend on frameworks, databases, LLM SDKs, or sibling
   `vaeil` packages such as `vaeil.adapters`.
2. The domain never reads the system clock directly, so the injected Clock
   port cannot be bypassed.
"""

import ast
import sys
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[1] / "src" / "vaeil" / "domain"


def domain_files() -> list[Path]:
    return sorted(DOMAIN.rglob("*.py"))


def imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return modules


def allowed_import(module: str) -> bool:
    root = module.split(".", 1)[0]
    if root in sys.stdlib_module_names:
        return True
    return module == "vaeil.domain" or module.startswith("vaeil.domain.")


def test_domain_imports_only_the_standard_library_and_its_own_package() -> None:
    files = domain_files()
    assert files, "purity guard scanned no domain files"

    offenders = [
        f"{path.relative_to(DOMAIN)} imports {module}"
        for path in files
        for module in imported_modules(ast.parse(path.read_text(encoding="utf-8")))
        if not allowed_import(module)
    ]

    assert offenders == []


FORBIDDEN_CLOCK_CALLS = {
    "datetime.date.today",
    "datetime.datetime.now",
    "datetime.datetime.today",
    "time.time",
}


def dotted_name(node: ast.expr) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def imported_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"datetime", "time"}:
                    aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module in {"datetime", "time"}:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def forbidden_clock_calls(tree: ast.AST) -> list[str]:
    aliases = imported_aliases(tree)
    calls: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        path = dotted_name(node.func)
        if path is None:
            continue

        root, separator, rest = path.partition(".")
        resolved_root = aliases.get(root, root)
        resolved = f"{resolved_root}.{rest}" if separator else resolved_root

        if resolved in FORBIDDEN_CLOCK_CALLS:
            calls.append(resolved)

    return calls


def test_domain_does_not_read_the_system_clock() -> None:
    files = domain_files()
    assert files, "clock guard scanned no domain files"

    offenders = [
        f"{path.relative_to(DOMAIN)} calls {call}"
        for path in files
        for call in forbidden_clock_calls(
            ast.parse(path.read_text(encoding="utf-8"))
        )
    ]

    assert offenders == []
