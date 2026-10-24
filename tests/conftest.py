"""Keep collected test IDs bounded even when parameter values are large."""

import hashlib

import pytest

MAX_NODE_ID_LENGTH = 200


def pytest_make_parametrize_id(config, val, argname):
    if isinstance(val, (str, bytes)) and len(val) > 80:
        raw = val.encode("utf-8") if isinstance(val, str) else val
        digest = hashlib.sha256(raw).hexdigest()[:12]
        return f"{argname}-{len(val)}-{digest}"
    return None


def pytest_collection_modifyitems(items):
    long_ids = [item.nodeid for item in items if len(item.nodeid) > MAX_NODE_ID_LENGTH]
    if long_ids:
        preview = ", ".join(node_id[:100] + "..." for node_id in long_ids[:3])
        raise pytest.UsageError(f"Test IDs exceed {MAX_NODE_ID_LENGTH} characters; use short explicit ids: {preview}")
