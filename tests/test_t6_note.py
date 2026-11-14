"""Approved T6 note-only input seam; no live model or infrastructure."""
from datetime import date
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
