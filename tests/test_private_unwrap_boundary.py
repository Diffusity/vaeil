"""The only production functions permitted to extract opaque private values."""

import ast
from pathlib import Path

import pytest

UNWRAP_METHOD = "UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE"
ALLOWED_UNWRAP_SITES = {
    ("vaeil.domain.member", "serialize_member_view"),
    ("vaeil.domain.self_name", "contains_self_name"),
    ("vaeil.domain.invite", "redeem_invite"),
}
SOURCE = Path(__file__).resolve().parents[1] / "src"


def unwrap_sites(source, module):
    sites = set()

    class Calls(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def visit_FunctionDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_Attribute(self, node):
            # Attribute loading also rejects binding an unwrap alias elsewhere.
            if node.attr == UNWRAP_METHOD:
                sites.add((module, ".".join(self.scope) or "<module>"))
            self.generic_visit(node)

        def visit_Call(self, node):
            if (isinstance(node.func, ast.Name) and node.func.id == "getattr"
                    and len(node.args) > 1 and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == UNWRAP_METHOD):
                sites.add((module, ".".join(self.scope) or "<module>"))
            self.generic_visit(node)

    Calls().visit(ast.parse(source))
    return sites


def assert_unwrap_boundary(sources, *, exact):
    found = set().union(*(unwrap_sites(source, module) for module, source in sources.items()))
    assert found <= ALLOWED_UNWRAP_SITES, f"Unauthorized private extraction sites: {found - ALLOWED_UNWRAP_SITES}"
    if exact:
        assert found == ALLOWED_UNWRAP_SITES, f"Missing expected extraction sites: {ALLOWED_UNWRAP_SITES - found}"


def test_production_unwrap_sites_are_exactly_the_approved_functions():
    sources = {
        ".".join(path.relative_to(SOURCE).with_suffix("").parts): path.read_text(encoding="utf-8")
        for path in sorted((SOURCE / "vaeil").rglob("*.py"))
    }
    assert sources
    assert_unwrap_boundary(sources, exact=True)


@pytest.mark.parametrize("source", [
    "def log_identity(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()\n",
    "def log_identity(value):\n    extract = value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE\n    return extract()\n",
    "def log_identity(value):\n    return getattr(value, 'UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE')()\n",
], ids=["direct", "alias", "getattr"])
def test_boundary_catches_a_deliberately_violating_fake_module(source):
    assert unwrap_sites(source, "vaeil.adapters.unsafe_logger") == {
        ("vaeil.adapters.unsafe_logger", "log_identity"),
    }
    with pytest.raises(AssertionError):
        assert_unwrap_boundary({"vaeil.adapters.unsafe_logger": source}, exact=False)
