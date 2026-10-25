"""Refuse accidental private-record export; explicit persistence mapping is T5.

Opaque private text refuses native-string operations and generic export.
Private values refuse deepcopy so asdict cannot bypass the record guard.
Authorized extraction uses one noisy method, pinned to explicit production sites.
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


class _OpaquePrivateValue(PrivateRecord):
    __slots__ = ("__value",)
    __hash__ = None
    _plain_type = object

    def __new__(cls, value):
        return value if type(value) is cls else super().__new__(cls)

    def __init__(self, value):
        if value is self:
            return
        if hasattr(self, "_OpaquePrivateValue__value"):
            raise AttributeError("Private values are immutable.")
        if not isinstance(value, self._plain_type):
            raise TypeError("Use the expected private value type.")
        object.__setattr__(self, "_OpaquePrivateValue__value", value)

    def __setattr__(self, name, value):
        raise AttributeError("Private values are immutable.")

    def __delattr__(self, name):
        raise AttributeError("Private values are immutable.")

    def __repr__(self):
        return "<private>"

    def __str__(self):
        return "<private>"

    def __format__(self, spec):
        return "<private>"

    def __eq__(self, other):
        return type(self) is type(other) and self.__value == other.__value

    def UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE(self):
        """Deliberate extraction; production call sites are pinned by an AST test."""
        return self.__value


class PrivateText(_OpaquePrivateValue):
    __slots__ = ()
    _plain_type = str


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

