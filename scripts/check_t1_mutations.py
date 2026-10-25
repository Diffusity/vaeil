"""Sequential T1 fault checks; restore exact source bytes after every run."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "src/vaeil/domain"


def main():
    mutations = []

    def add(name, module, before, after, tests=None):
        mutations.append((name, [(module, before, after)], tests))

    for reason in ("PHONE", "EMAIL", "HANDLE", "OBFUSCATED_EMAIL", "URL"):
        if reason == "PHONE":
            add("remove phone detection", "identifiers", "found.add(IdentifierReason.PHONE)", "pass")
        else:
            add("remove " + reason.lower() + " detection", "identifiers", "if reason in found)",
                "if reason in found and reason is not IdentifierReason." + reason + ")")
    for threshold in (9, 11):
        add("phone threshold " + str(threshold), "identifiers", "MIN_PHONE_DIGITS = 10", "MIN_PHONE_DIGITS = " + str(threshold))
    add("drop Pseudonym NFKC", "pseudonym", 'unicodedata.normalize("NFKC", candidate).strip()', "candidate.strip()")
    add("drop Pseudonym casefold", "pseudonym", "key = value.casefold()", "key = value")
    add("drop claim identifier check", "pseudonym", "if scan_identifiers(value).is_flagged:", "if False:")
    add("drop fixed-once guard", "pseudonym", "if member_id in self._members:", "if False:")
    add("drop reserved-name check", "pseudonym", "if key in RESERVED_PSEUDONYMS:", "if False:")
    add("make identity optional", "pseudonym", "*, identity: MemberIdentity)", "*, identity: MemberIdentity | None = None)")
    add("drop owner check", "pseudonym", "if not isinstance(identity, MemberIdentity) or identity.member_id != member_id:", "if False:")
    add("drop claim self-name check", "pseudonym", "if contains_self_name(value, identity=identity, mode=SelfNameMode.PSEUDONYM):", "if False:")
    add("use whole-word in claim", "pseudonym", "mode=SelfNameMode.PSEUDONYM", "mode=SelfNameMode.ABOUT")
    fixed = '        if member_id in self._members:\n            raise PseudonymAlreadySetError("Pseudonym is fixed once set.")\n\n'
    mutations.append(("move fixed-once after owner", [
        ("pseudonym", fixed, ""),
        ("pseudonym", '        if not isinstance(candidate, str):', fixed + '        if not isinstance(candidate, str):'),
    ], None))
    add("drop self-name NFKC", "self_name", 'unicodedata.normalize("NFKC", identity.legal_name.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE())', "identity.legal_name.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()")
    add("drop email-local NFKC", "self_name", 'unicodedata.normalize("NFKC", identity.email.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE())', "identity.email.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()")
    add("replace casefold with lower", "self_name", ".casefold()", ".lower()")
    add("drop text NFKC", "self_name", 'unicodedata.normalize("NFKC", text)', "text")
    for boundary in (2, 4):
        add("name token threshold " + str(boundary), "self_name", "len(token) >= 3", "len(token) >= " + str(boundary))
    add("do not split plus", "self_name", r'[\s._+\-]+', r'[\s._\-]+')
    add("do not split dot", "self_name", r'[\s._+\-]+', r'[\s_+\-]+')
    add("include email domain", "self_name", '.casefold().partition("@")[0]', '.casefold().replace("@", " ")')
    add("drop whole-word boundaries", "self_name", 'r"(?<!\w)(?:" + alternatives + r")(?!\w)"', 'r"(?:" + alternatives + r")"')
    add("drop About self-name", "profile", "if contains_self_name(text, identity=owner, mode=SelfNameMode.ABOUT):", "if False:")
    add("substring mode in About", "profile", "mode=SelfNameMode.ABOUT", "mode=SelfNameMode.PSEUDONYM")
    add("drop profile identifier check", "profile", "if scan_identifiers(text).is_flagged:", "if False:")
    add("drop controls", "profile", 'if any(unicodedata.category(char) == "Cc" for char in about):', "if False:")
    for cap in (279, 281):
        add("About limit " + str(cap), "profile", "MAX_ABOUT_CODE_POINTS = 280", "MAX_ABOUT_CODE_POINTS = " + str(cap))
    for cap in (4, 6):
        add("selection maximum " + str(cap), "profile", "MAX_PROFILE_SELECTIONS = 5", "MAX_PROFILE_SELECTIONS = " + str(cap))
    for lower in (0, 2):
        add("selection minimum " + str(lower), "profile", "MIN_PROFILE_SELECTIONS = 1", "MIN_PROFILE_SELECTIONS = " + str(lower))
    add("silently deduplicate", "profile", "len(set(items)) != len(items)", "False")
    add("mutable interests", "profile", 'interests=frozenset(selected["interests"])', 'interests=list(selected["interests"])')
    add("mutable values", "profile", 'values=frozenset(selected["values"])', 'values=list(selected["values"])')
    add("drop About normalization", "profile", 'unicodedata.normalize("NFKC", about).strip()', "about.strip()")
    add("drop About trim", "profile", 'unicodedata.normalize("NFKC", about).strip()', 'unicodedata.normalize("NFKC", about)')
    length = '    if len(text) > MAX_ABOUT_CODE_POINTS:\n        raise AboutTooLongError(field="about")\n'
    scan = '    if scan_identifiers(text).is_flagged:\n        raise ProfileIdentifierError(field="about")\n'
    self_name = '    if contains_self_name(text, identity=owner, mode=SelfNameMode.ABOUT):\n        raise ProfileSelfNameError(field="about")\n'
    add("scanner before length", "profile", length + scan, scan + length)
    add("self-name before scanner", "profile", scan + self_name, self_name + scan)
    add("controls before selection", "profile", '    for name, items in selected.items():',
        '    if any(unicodedata.category(char) == "Cc" for char in about):\n        raise AboutNormalizationError(field="about")\n    for name, items in selected.items():')
    controls = '    if any(unicodedata.category(char) == "Cc" for char in about):\n        raise AboutNormalizationError(field="about")\n'
    normalization = '    text = unicodedata.normalize("NFKC", about).strip()\n'
    add("length before controls", "profile", controls + normalization + length, normalization + length + controls)
    add("duplicate check before unknown codes", "profile", '    normalized = {}',
        '    for name, (items, _) in selections.items():\n        if len(set(items)) != len(items):\n            raise ProfileSelectionError(field=name)\n    normalized = {}')
    add("skip shape checks", "profile", '        if not isinstance(value, str):', '        if False:')
    add("accept Member Reveal flag", "member", '    values_profile: ValuesProfile\n\n    def __post_init__',
        '    values_profile: ValuesProfile\n    revealed: bool = False\n\n    def __post_init__')
    add("always reveal", "member", "if conversation.revealed:", "if True:")
    add("never reveal", "member", "if conversation.revealed:", "if False:")
    add("drop subject membership", "member", "if identity.member_id not in conversation.participant_ids:", "if False:")
    add("drop self-view check", "member", "if viewer_id == identity.member_id:", "if False:")
    add("drop viewer membership", "member", "if viewer_id not in conversation.participant_ids:", "if False:")
    add("accept duplicate participants", "member", "or pair[0] == pair[1]", "or False")
    mutations.append(("expose private pre-Reveal field", [
        ("member", 'class PreRevealMemberView:\n    pseudonym: Pseudonym\n    values_profile: ValuesProfile',
         'class PreRevealMemberView:\n    pseudonym: Pseudonym\n    values_profile: ValuesProfile\n    email: str'),
        ("member", 'return PreRevealMemberView(member.pseudonym, member.values_profile)',
         'return PreRevealMemberView(member.pseudonym, member.values_profile, identity.email)'),
    ], None))
    add("leak identity repr", "identity", '    def __post_init__(self) -> None:',
        '    def __repr__(self):\n        return "MemberIdentity(" + self.legal_name.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE() + ")"\n\n    def __post_init__(self) -> None:')
    add("leak Applicant repr", "applicant", '    def __post_init__(self) -> None:',
        '    def __repr__(self):\n        return "Applicant(" + self.date_of_birth.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE().isoformat() + ")"\n\n    def __post_init__(self) -> None:')
    add("echo rejected private About", "profile", '        raise ProfileSelfNameError(field="about")',
        '        error = ProfileSelfNameError(field="about")\n        error.args = (text,)\n        raise error')
    add("allow shallow private copy", "privacy", '    def __copy__(self):\n        raise PrivateSerializationError("Private records require explicit mapping; copying is disabled.")',
        '    def __copy__(self):\n        return self')
    add("allow deep private copy/asdict", "privacy", '    def __deepcopy__(self, memo):\n        raise PrivateSerializationError("Private records require explicit mapping; copying is disabled.")',
        '    def __deepcopy__(self, memo):\n        return self')
    add("allow private pickle", "privacy", '    def __reduce_ex__(self, protocol):\n        raise PrivateSerializationError("Private records require explicit mapping; generic serialization is disabled.")',
        '    def __reduce_ex__(self, protocol):\n        return str, ("wrongly serialized",)')
    add("allow direct private reduction", "privacy", '    def __reduce__(self):\n        raise PrivateSerializationError("Private records require explicit mapping; generic serialization is disabled.")',
        '    def __reduce__(self):\n        return str, ("wrongly serialized",)')
    add("SDK import in domain", "clock", 'from typing import Protocol', 'from typing import Protocol\nimport fastapi', ["tests/test_domain_purity.py"])
    add("real clock in domain", "clock", 'from typing import Protocol',
        'from typing import Protocol\nimport datetime\ndef accidental_now():\n    return datetime.datetime.now()', ["tests/test_domain_purity.py"])

    add("unwrap outside allowed function", "profile", "MAX_ABOUT_CODE_POINTS = 280",
        "MAX_ABOUT_CODE_POINTS = 280\ndef unsafe_log(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()")
    add("wrapper repr leaks", "privacy", '    def __repr__(self):\n        return "<private>"',
        '    def __repr__(self):\n        return repr(self._OpaquePrivateValue__value)')
    add("drop scalar str redaction", "privacy", '    def __str__(self):\n        return "<private>"',
        '    def __str__(self):\n        return str(self._OpaquePrivateValue__value)')
    add("drop scalar format redaction", "privacy", '    def __format__(self, spec):\n        return "<private>"',
        '    def __format__(self, spec):\n        return format(self._OpaquePrivateValue__value, spec)')
    add("private equality against plain value", "privacy", 'return type(self) is type(other) and self.__value == other.__value',
        'return self.__value == other.__value if type(self) is type(other) else self.__value == other')
    add("allow wrapper hashing", "privacy", '__hash__ = None', '__hash__ = lambda self: 0')
    add("expose PrivateDate year", "privacy", 'class PrivateDate(_OpaquePrivateValue):',
        'class PrivateDate(_OpaquePrivateValue):\n    @property\n    def year(self):\n        return self._OpaquePrivateValue__value.year')
    add("view holds plain private text", "member", 'object.__setattr__(self, "legal_name", PrivateText(self.legal_name))',
        'object.__setattr__(self, "legal_name", self.legal_name.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE())')
    add("global Reveal cache by Member", "member", '    if conversation.revealed:',
        '    if conversation.revealed or identity.member_id in _revealed_members:\n        _revealed_members.add(identity.member_id)')
    # This one mutation needs its backing cache declaration to stay executable.
    name, edits, tests = mutations[-1]
    mutations[-1] = (name, [("member", 'from dataclasses import dataclass, field',
                           'from dataclasses import dataclass, field\n_revealed_members = set()'), *edits], tests)

    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    paths = ["tests/test_member_identity_red.py", "tests/test_pseudonyms.py", "tests/test_identifier_detection.py", "tests/test_domain_purity.py", "tests/test_private_unwrap_boundary.py", "tests/test_opaque_private_values.py", "tests/test_invite_redemption.py"]
    results = []
    with tempfile.TemporaryDirectory(prefix="vaeil-t1-mutations-") as scratch:
        for index, (name, edits, tests) in enumerate(mutations, 1):
            originals = {DOMAIN / (module + ".py"): (DOMAIN / (module + ".py")).read_bytes() for module, _, _ in edits}
            sources = {path: raw.decode("utf-8").replace("\r\n", "\n") for path, raw in originals.items()}
            try:
                for module, before, after in edits:
                    path = DOMAIN / (module + ".py")
                    if before not in sources[path]:
                        raise RuntimeError("Changed mutation target: " + name)
                    sources[path] = sources[path].replace(before, after)
                for path, source in sources.items():
                    path.write_text(source, encoding="utf-8")
                xml = Path(scratch) / (str(index) + ".xml")
                run = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "--tb=no", "-rN", "--junitxml=" + str(xml), *(tests or paths)],
                                     cwd=ROOT, env=environment, capture_output=True, text=True, timeout=45)
                tree = ET.parse(xml)
                errors = list(tree.iter("error"))
                failed = [case.attrib["name"] for case in tree.iter("testcase") if case.find("failure") is not None]
                killed = run.returncode == 1 and bool(failed) and not errors
                result = {"mutation": name, "result": "KILLED" if killed else "SURVIVED/ERROR", "failed": len(failed), "witness": failed[0] if failed else run.stdout[-400:]}
                results.append(result)
                (ROOT / "docs/audit/t1-mutation-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(f"{index}/{len(mutations)} {name}: {result['result']} ({len(failed)} failed)", flush=True)
            finally:
                for path, original in originals.items():
                    path.write_bytes(original)
    output = ROOT / "docs/audit/t1-mutation-results.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Results:", output, flush=True)
    if any(result["result"] != "KILLED" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
