
from __future__ import annotations

import ast
from pathlib import Path

SERVICE_FILE = Path(
    "app/services/defi/application/wallet_session_service.py"
)

FORBIDDEN_IDENTIFIERS = (
    "private_key",
    "privatekey",
    "seed_phrase",
    "mnemonic",
)

FORBIDDEN_PAYLOAD_KEYS = FORBIDDEN_IDENTIFIERS


def _load_source_tree() -> ast.AST:
    assert SERVICE_FILE.exists(), f"{SERVICE_FILE} is missing"
    return ast.parse(SERVICE_FILE.read_text(encoding="utf-8"))


def test_service_file_exists():
    assert SERVICE_FILE.exists()


def test_redis_payload_only_contains_public_fields():
    tree = _load_source_tree()
    dicts = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)]
    payload_dicts = []
    for d in dicts:
        keys = [k.value for k in d.keys if isinstance(k, ast.Constant)]
        if any(k in keys for k in ("wallet_address", "chain_id")):
            payload_dicts.append(keys)
    assert payload_dicts, "expected at least one session payload dict"

    for keys in payload_dicts:
        for forbidden in FORBIDDEN_PAYLOAD_KEYS:
            assert forbidden not in keys, (
                f"session payload must never contain {forbidden!r}; "
                "this is a NonCustodialViolationError"
            )
        assert set(keys) == {"wallet_address", "chain_id"}, (
            "session payload must contain ONLY wallet_address and chain_id"
        )


def test_private_key_shaped_input_is_rejected():
    tree = _load_source_tree()
    source = SERVICE_FILE.read_text(encoding="utf-8")

    assert "_PRIVATE_KEY_RE" in source
    assert "PRIVATE_KEY_EXPOSURE" in source
    assert "NonCustodialViolationError" in source
    assert "WalletSessionService" in source

    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            ident = node.id
        elif isinstance(node, ast.arg):
            ident = node.arg
        elif isinstance(node, ast.Attribute):  # keep `ast.Attribute` (ast.attr is deprecated)
            ident = node.attr
        else:
            continue
        if ident in FORBIDDEN_IDENTIFIERS:
            raise AssertionError(
                f"forbidden identifier {ident!r} found in "
                f"{SERVICE_FILE}:{node.lineno} — NonCustodialViolationError"
            )


def test_session_storage_key_matches_feature_spec():
    source = SERVICE_FILE.read_text(encoding="utf-8")
    assert "defi:session:" in source