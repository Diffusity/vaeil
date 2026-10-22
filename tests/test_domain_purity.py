import ast
import sys
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[1] / "src" / "vaeil" / "domain"


def test_domain_imports_only_the_standard_library_and_itself() -> None:
    allowed = set(sys.stdlib_module_names) | {"vaeil"}
    offenders: list[str] = []

    for path in sorted(DOMAIN.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots = [node.module.split(".")[0]]
            else:
                continue

            offenders.extend(
                f"{path.relative_to(DOMAIN)} imports {root}"
                for root in roots
                if root not in allowed
            )

    assert offenders == []
