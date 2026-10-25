"""The minimum an Applicant must carry through the age gate and vetting."""

from dataclasses import dataclass, field

from vaeil.domain.privacy import PrivateRecord, PrivateDate, private_date


@dataclass(frozen=True, slots=True)
class Applicant(PrivateRecord):
    # Frozen/slotted dataclasses otherwise generate a generic state exporter.
    __getstate__ = PrivateRecord.__getstate__
    date_of_birth: PrivateDate = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "date_of_birth", private_date(self.date_of_birth))
