"""Application-note policy shared by admission writes and the note-only port."""
import unicodedata
from vaeil.domain.identifiers import scan_identifiers
from vaeil.domain.identity import MemberIdentity
from vaeil.domain.self_name import SelfNameMode, contains_self_name

MIN_APPLICATION_NOTE_CODE_POINTS = 20
MAX_APPLICATION_NOTE_CODE_POINTS = 500


class ApplicationNoteError(Exception):
    can_rephrase = True

    def __init__(self, reason):
        self.reason = reason
        super().__init__("Remove contact details or rephrase the application note.")


def normalize_application_note(raw: str) -> str:
    if not isinstance(raw, str):
        raise ApplicationNoteError("shape")
    text = unicodedata.normalize("NFKC", raw.strip())
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in text):
        raise ApplicationNoteError("control")
    if not MIN_APPLICATION_NOTE_CODE_POINTS <= len(text) <= MAX_APPLICATION_NOTE_CODE_POINTS:
        raise ApplicationNoteError("length")
    if scan_identifiers(text).reasons:
        raise ApplicationNoteError("identifier")
    return text


def validate_application_note(raw: str, *, owner: MemberIdentity) -> str:
    text = normalize_application_note(raw)
    if contains_self_name(text, identity=owner, mode=SelfNameMode.ABOUT):
        raise ApplicationNoteError("self_name")
    return text
