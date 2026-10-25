"""The minimum an Applicant must carry through the age gate and vetting."""

from dataclasses import dataclass, field
from datetime import date

from vaeil.domain.privacy import PrivateRecord, private_date


@dataclass(frozen=True, slots=True)
class Applicant(PrivateRecord):
    date_of_birth: date = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "date_of_birth", private_date(self.date_of_birth))
