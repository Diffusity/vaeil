"""The minimum an Applicant must carry through the age gate and vetting."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Applicant:
    date_of_birth: date
