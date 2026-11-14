"""Approved T6 note-only input seam; no live model or infrastructure."""
from datetime import date
import pytest
from vaeil.domain import MemberIdentity
from vaeil.domain import Applicant, Verdict, vet

NOTE = "I seek a thoughtful long term relationship."


def test_vetting_port_receives_only_the_application_note():
    received = []

    class CapturingModel:
        def vet(self, application_note):
            received.append(application_note)
            return Verdict.APPROVED

    applicant = Applicant(date_of_birth=date(1987, 3, 14), application_note=NOTE)
    assert vet(applicant, CapturingModel()) is Verdict.APPROVED
    assert received == [NOTE]
    assert type(received[0]) is str
    assert "1987" not in received[0]
    assert NOTE not in repr(applicant) + str(applicant)



def owner(name="Mark Example"):
    return MemberIdentity("m1", name, "mark.example@example.invalid", None, date(1987, 3, 14))


@pytest.mark.parametrize("raw,expected", [
    ("a" * 20, "a" * 20), ("a" * 500, "a" * 500),
    ("  " + "a" * 20 + "  ", "a" * 20),
    ("Ａ" * 20, "A" * 20), ("e\u0301" * 20, "é" * 20),
    ("😀" * 20, "😀" * 20),
    ("I enjoy the local market and quiet walks.", "I enjoy the local market and quiet walks."),
], ids=["min", "max", "trim", "fullwidth", "combining", "emoji", "substring-safe"])
def test_note_normalization_and_accepted_boundaries(raw, expected):
    from vaeil.domain.admission import validate_application_note
    assert validate_application_note(raw, owner=owner()) == expected


@pytest.mark.parametrize("raw,reason", [
    (None, "shape"), ([], "shape"), ("", "length"), ("   ", "length"),
    ("a" * 19, "length"), ("a" * 501, "length"),
    ("é" * 501, "length"), ("😀" * 501, "length"),
    ("safe text with a null\x00inside", "control"),
    ("safe text with a new\nline", "control"),
    ("safe text with zero width\u200bjoiner", "control"),
    ("Please email me at secret@example.invalid", "identifier"),
    ("Please call 9876543210 about a meeting", "identifier"),
    ("I am Mark and I seek a good relationship", "self_name"),
    ("I am ＭＡＲＫ and seek a good relationship", "self_name"),
], ids=["none", "list", "empty", "whitespace", "below", "above", "unicode-above", "emoji-above",
        "null", "newline", "format-control", "email", "phone", "name", "fullwidth-name"])
def test_invalid_note_refused_without_echoing_input(raw, reason):
    from vaeil.domain.admission import ApplicationNoteError, validate_application_note
    with pytest.raises(ApplicationNoteError) as result:
        validate_application_note(raw, owner=owner())
    assert result.value.reason == reason
    message = str(result.value)
    assert "secret@example.invalid" not in message and "9876543210" not in message
    assert "Mark" not in message and "1987" not in message


def test_whole_word_note_false_positive_can_be_rephrased():
    from vaeil.domain.admission import ApplicationNoteError, validate_application_note
    with pytest.raises(ApplicationNoteError) as result:
        validate_application_note("I will enjoy meeting a thoughtful person.", owner=owner("Will Person"))
    assert result.value.reason == "self_name"
    assert result.value.can_rephrase is True


def test_invalid_or_missing_note_never_reaches_vetting():
    called = []
    class Model:
        def vet(self, note):
            called.append(note)
            return Verdict.APPROVED
    for applicant in (Applicant(date(1987, 3, 14)), Applicant(date(1987, 3, 14), "x"),
                      Applicant(date(1987, 3, 14), "Please email secret@example.invalid for more")):
        assert vet(applicant, Model()) is Verdict.NEEDS_REVIEW
    assert called == []
