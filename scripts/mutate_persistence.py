"""Ticket12 mutation checks. Run alone; source bytes are restored in finally."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "src/vaeil/adapters/persistence.py"
CONVERSATION = ROOT / "src/vaeil/domain/conversation.py"
CONTRACT = "tests/test_repository_contract.py::"
BOUNDARY = "tests/test_private_unwrap_boundary.py::test_production_unwrap_sites_are_exactly_the_approved_functions"


def replace_once(old, new):
    def mutate(source):
        if source.count(old) != 1:
            raise RuntimeError("Mutation anchor must occur exactly once")
        return source.replace(old, new, 1)
    return mutate


def disable_audit_operation(operation):
    other = "DELETE" if operation == "UPDATE" else "UPDATE"

    def mutate(source):
        source = source.replace('for operation in ("UPDATE", "DELETE"):', f'for operation in ("{other}",):')
        return source.replace('BEFORE UPDATE OR DELETE ON audit_events', f'BEFORE {other} ON audit_events')
    return mutate


MUTATIONS = [
    ("remove normalized unique index", ADAPTER,
     replace_once('Column("normalized_pseudonym", String, nullable=False, unique=True)',
                  'Column("normalized_pseudonym", String, nullable=False, unique=False)'),
     CONTRACT + "test_concurrent_normalized_claims_commit_exactly_one_owner"),
    ("remove normalized key", ADAPTER,
     replace_once('normalized_pseudonym=pseudonym.value.casefold()', 'normalized_pseudonym=member.pseudonym.value'),
     CONTRACT + "test_normalized_pseudonym_has_one_durable_owner"),
    ("allow second Pseudonym overwrite", ADAPTER,
     replace_once('            raise d.PseudonymAlreadySetError("Pseudonym is fixed once set.")',
                  '            self._execute(update(members).where(members.c.member_id == member.identity.member_id).values(**member_to_row(member)))\n            return'),
     CONTRACT + "test_normalized_pseudonym_has_one_durable_owner"),
    ("commit instead of rollback", ADAPTER,
     replace_once('                    connection.rollback()', '                    connection.commit()'),
     CONTRACT + "test_domain_and_audit_commit_or_rollback_together"),
    ("commit audit/domain early", ADAPTER,
     replace_once('    def list_audit(self, *, subject_id: str)',
                  '        self._connection.commit()\n\n    def list_audit(self, *, subject_id: str)'),
     CONTRACT + "test_constraint_failure_rolls_back_earlier_domain_and_audit_writes"),
    ("allow audit UPDATE", ADAPTER, disable_audit_operation("UPDATE"),
     CONTRACT + "test_database_refuses_audit_update_and_delete"),
    ("allow audit DELETE", ADAPTER, disable_audit_operation("DELETE"),
     CONTRACT + "test_database_refuses_audit_update_and_delete"),
    ("allow replacement of an audit event", ADAPTER,
     lambda source: disable_audit_operation("UPDATE")(source).replace('.execute_if(dialect="sqlite")', '.execute_if(dialect="no_database")'),
     CONTRACT + "test_database_cannot_replace_an_existing_audit_event"),
    ("omit active Conversation exclusion", CONVERSATION,
     replace_once('    if conversation.active and any(', '    if False and conversation.active and any('),
     CONTRACT + "test_concurrent_active_conversation_opens_have_one_winner"),
    ("omit monotonic Conversation guard", CONVERSATION,
     replace_once('    if previous is not None and (', '    if False and previous is not None and ('),
     CONTRACT + "test_durable_conversation_refuses_reversal_or_reassignment"),
    ("restore a plain private value", ADAPTER,
     replace_once('    return d.Member(identity, d.Pseudonym(row["pseudonym"]), d.build_values_profile(owner=identity, **row["profile"]))',
                  '    member = d.Member(identity, d.Pseudonym(row["pseudonym"]), d.build_values_profile(owner=identity, **row["profile"]))\n    object.__setattr__(member.identity, "legal_name", row["legal_name"])\n    return member'),
     CONTRACT + "test_member_round_trip_survives_new_repository_with_wrappers"),
    ("leak SQL bound parameters", ADAPTER,
     replace_once('hide_parameters=True', 'hide_parameters=False'),
     CONTRACT + "test_sql_logging_never_copies_private_parameters"),
    ("permit commit after database failure", ADAPTER,
     lambda source: source.replace('self._failed = True', 'self._failed = False'),
     CONTRACT + "test_failed_transaction_cannot_commit_even_if_caller_catches_the_error"),
    ("unwrap outside the approved mapper", ADAPTER,
     lambda source: source + '\n\ndef unsafe_mapper(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()\n', BOUNDARY),
]


def main(mutations=None, output_path="docs/audit/t5-mutations.json"):
    selected = MUTATIONS if mutations is None else mutations
    originals = {path: path.read_bytes() for _, path, _, _ in selected}
    mtimes = {path: path.stat().st_mtime for path in originals}
    backends = ["sqlite"] + (["postgres"] if os.environ.get("VAEIL_TEST_POSTGRES_URL") else [])
    results = []
    try:
        for number, (name, path, mutate, test) in enumerate(selected, 1):
            source = originals[path].decode().replace("\r\n", "\n")
            changed = mutate(source)
            if changed == source:
                raise RuntimeError("Mutation made no change")
            path.write_bytes(changed.encode())
            # Invalidate timestamp/size bytecode caches even for equal-size edits.
            os.utime(path, (mtimes[path] + number + 2, mtimes[path] + number + 2))
            try:
                is_database = "test_remote_postgres_uses_verified_tls" not in test and test.split("::", 1)[0] in {"tests/test_repository_contract.py", "tests/test_t6_repository.py", "tests/test_t6_application.py", "tests/test_t6_profiles.py", "tests/test_t6_http.py"}
                matrix = ["architecture"] if test == BOUNDARY else (backends if is_database else ["domain"])
                for backend in matrix:
                    command = [sys.executable, "-m", "pytest", test, "-q", "--tb=short"]
                    if backend in {"sqlite", "postgres"}:
                        command += ["-k", backend]
                    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
                    killed = run.returncode == 1 and " failed" in run.stdout and "ERROR collecting" not in run.stdout
                    results.append(dict(mutation=name, backend=backend, killed=killed, test=test))
                    print(f"{name} | {backend} | {'KILLED' if killed else 'SURVIVED/ERROR'}", flush=True)
                    if not killed:
                        print(run.stdout[-1800:] + run.stderr[-500:], flush=True)
            finally:
                path.write_bytes(originals[path])
                os.utime(path, (mtimes[path] + 100 + number, mtimes[path] + 100 + number))
    finally:
        for path, content in originals.items():
            path.write_bytes(content)
            os.utime(path, (mtimes[path] + 200, mtimes[path] + 200))
        assert all(path.read_bytes() == content for path, content in originals.items())
    output = dict(results=results, restored_sha256={str(path.relative_to(ROOT)): hashlib.sha256(content).hexdigest()
                                                  for path, content in originals.items()})
    (ROOT / output_path).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if not all(result["killed"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
