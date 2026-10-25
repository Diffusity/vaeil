"""Refuse accidental private-record export; explicit persistence mapping is T5.

Private scalar subclasses retain str/date behavior for domain operations, but
refuse deepcopy so dataclasses.asdict/astuple cannot bypass the record guard.
Authorized view encoders deliberately unwrap values; generic serializers cannot.
This is an export boundary, not protection from code already holding private data.
"""

from datetime import date


class PrivateSerializationError(TypeError):
    """Private data requires an explicit, authorized mapping."""


class PrivateRecord:
    __slots__ = ()

    def __reduce__(self):
        raise PrivateSerializationError("Private records require explicit mapping; generic serialization is disabled.")

    def __reduce_ex__(self, protocol):
        raise PrivateSerializationError("Private records require explicit mapping; generic serialization is disabled.")

    def __copy__(self):
        raise PrivateSerializationError("Private records require explicit mapping; copying is disabled.")

    def __deepcopy__(self, memo):
        raise PrivateSerializationError("Private records require explicit mapping; copying is disabled.")

    def __getstate__(self):
        raise PrivateSerializationError("Private records require explicit mapping; generic serialization is disabled.")


class PrivateText(PrivateRecord, str):
    __slots__ = ()

    def __new__(cls, value: str):
        if not isinstance(value, str):
            raise TypeError("Private text must be text.")
        return str.__new__(cls, str.__str__(value))

    def __repr__(self):
        return "<private>"

    def __str__(self):
        return "<private>"


class PrivateDate(PrivateRecord, date):
    __slots__ = ()

    def __repr__(self):
        return "<private>"

    def __str__(self):
        return "<private>"


def private_date(value: date) -> PrivateDate:
    if not isinstance(value, date):
        raise TypeError("Private date must be a date.")
    return PrivateDate(value.year, value.month, value.day)


def reveal_text(value: str) -> str:
    """Use only in an authorized explicit view/persistence mapper."""
    return str.__str__(value)
