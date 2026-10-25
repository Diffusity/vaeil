"""Opaque scalar contract: no native-string/date behavior can leak identity."""

from dataclasses import asdict, is_dataclass
from datetime import date, timedelta
import copy
import json
import logging
import pickle
import traceback

import pytest

from vaeil import domain as d
from vaeil.domain.privacy import PrivateDate, PrivateText
from test_member_identity_red import (
    CANARIES, CANARY_DOB, assert_no_canary, conversation, identity, inspect_graph, member, projected,
)

UNWRAP_METHOD = "UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE"


@pytest.mark.parametrize("field_name", ["legal_name", "email", "phone"])
def test_private_text_values_refuse_native_json(field_name):
    value = getattr(identity(), field_name)
    with pytest.raises(TypeError) as caught:
        json.dumps(value)
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))


def test_private_date_value_refuses_native_json():
    with pytest.raises(TypeError) as caught:
        json.dumps(identity().date_of_birth)
    assert_no_canary(str(caught.value))


@pytest.mark.parametrize("field_name", ["legal_name", "email", "phone", "date_of_birth"])
@pytest.mark.parametrize("render", ["repr", "str", "format", "f-string", "percent", "dot-format" ])
def test_all_scalar_rendering_is_redacted(field_name, render):
    value = getattr(identity(), field_name)
    if render == "repr":
        output = repr(value)
    elif render == "str":
        output = str(value)
    elif render == "format":
        output = format(value, "%Y-%m-%d" if field_name == "date_of_birth" else ">40")
    elif render == "f-string":
        output = f"{value:%Y-%m-%d}" if field_name == "date_of_birth" else f"{value:>40}"
    elif render == "percent":
        output = "%s" % value
    else:
        output = "{:%Y-%m-%d}".format(value) if field_name == "date_of_birth" else "{:>40}".format(value)
    assert_no_canary(output)
    assert "private" in output.casefold()


@pytest.mark.parametrize("field_name", ["legal_name", "email", "phone", "date_of_birth"])
def test_scalars_are_opaque_immutable_slotted_and_unhashable(field_name):
    value = getattr(identity(), field_name)
    assert not isinstance(value, (str, date))
    assert not is_dataclass(value)
    assert not hasattr(value, "__dict__")
    assert callable(getattr(value, UNWRAP_METHOD, None))
    with pytest.raises(TypeError):
        hash(value)
    with pytest.raises(AttributeError):
        value.additional_value = "not allowed"
    for cls in type(value).__mro__:
        for slot in cls.__dict__.get("__slots__", ()):
            if hasattr(value, slot):
                with pytest.raises(AttributeError):
                    setattr(value, slot, object())


@pytest.mark.parametrize("field_name,plain", [
    ("legal_name", CANARIES[0]), ("email", CANARIES[1]), ("phone", CANARIES[2]),
    ("date_of_birth", CANARY_DOB),
], ids=["name", "email", "phone", "dob"])
def test_equality_never_compares_equal_to_a_plain_value(field_name, plain):
    value = getattr(identity(), field_name)
    assert (value == plain) is False
    assert (plain == value) is False
    wrapped = PrivateDate(plain) if field_name == "date_of_birth" else PrivateText(plain)
    assert value == wrapped
    assert (value == object()) is False


@pytest.mark.parametrize("operation", ["int", "bytes", "iter", "slice", "len", "contains"])
@pytest.mark.parametrize("field_name", ["legal_name", "date_of_birth"])
def test_private_values_have_no_implicit_plain_value_operations(field_name, operation):
    value = getattr(identity(), field_name)
    with pytest.raises(TypeError) as caught:
        if operation == "int":
            int(value)
        elif operation == "bytes":
            bytes(value)
        elif operation == "iter":
            iter(value)
        elif operation == "slice":
            value[:1]
        elif operation == "len":
            len(value)
        else:
            "a" in value
    assert_no_canary(str(caught.value))
    assert_no_canary(repr(caught.value))


@pytest.mark.parametrize("attribute", ["isoformat", "strftime", "year", "month", "day"])
def test_private_date_exposes_no_calendar_accessors(attribute):
    value = identity().date_of_birth
    assert not hasattr(value, attribute)


@pytest.mark.parametrize("reverse", [False, True])
def test_private_date_arithmetic_is_not_available(reverse):
    value = identity().date_of_birth
    with pytest.raises(TypeError) as caught:
        if reverse:
            timedelta(days=1) + value
        else:
            value + timedelta(days=1)
    assert_no_canary(str(caught.value))


@pytest.mark.parametrize("field_name", ["legal_name", "date_of_birth"])
@pytest.mark.parametrize("route", ["pickle", "copy", "deepcopy", "reduce", "asdict"])
def test_opaque_scalars_refuse_generic_copy_and_export(field_name, route):
    value = getattr(identity(), field_name)
    with pytest.raises(TypeError) as caught:
        if route == "pickle":
            pickle.dumps(value)
        elif route == "copy":
            copy.copy(value)
        elif route == "deepcopy":
            copy.deepcopy(value)
        elif route == "reduce":
            value.__reduce__()
        else:
            asdict(value)
    assert_no_canary(str(caught.value))


def test_pre_reveal_graph_has_no_wrappers_or_private_record_references():
    view = projected()
    graph = inspect_graph(view, forbidden_types=(d.Member, d.MemberIdentity, PrivateText, PrivateDate))
    assert_no_canary(graph)


@pytest.mark.parametrize("kind", ["revealed", "own"])
def test_authorized_views_hold_wrappers_not_plain_private_fields(kind):
    subject = member()
    view = d.project_own_profile(subject) if kind == "own" else d.project_member_for_viewer(
        subject, viewer_id="viewer", conversation=conversation(revealed=True),
    )
    for field in ("legal_name", "email", "phone"):
        value = getattr(view, field)
        assert type(value) is PrivateText
        assert not isinstance(value, str)
    if kind == "own":
        assert type(view.date_of_birth) is PrivateDate
        assert not isinstance(view.date_of_birth, date)


def test_authorized_reveal_payload_keeps_exact_plain_values_and_only_allowed_fields():
    payload = d.serialize_member_view(projected(revealed=True))
    assert payload == {
        "pseudonym": "Comet",
        "values_profile": {
            "relationship_intent": "long_term", "life_stage": "undergraduate",
            "interests": ["reading"], "values": ["honesty"],
            "communication_style": "direct", "pace_and_lifestyle": "quiet_and_routine", "about": "",
        },
        "legal_name": CANARIES[0], "email": CANARIES[1], "phone": CANARIES[2],
    }
    assert json.loads(json.dumps(payload)) == payload


def test_logs_tracebacks_and_exception_text_never_print_canaries(caplog):
    record = identity()
    with caplog.at_level(logging.INFO, logger="vaeil.privacy-test"):
        logger = logging.getLogger("vaeil.privacy-test")
        logger.info("record=%s", record)
        for value in (record.legal_name, record.email, record.phone, record.date_of_birth):
            logger.info("value=%s formatted=%s", value, f"{value:>40}")
            try:
                raise ValueError(f"Private operation refused: {value:>40}")
            except ValueError as error:
                assert_no_canary(str(error))
                assert_no_canary(repr(error))
                assert_no_canary(traceback.format_exc())
    assert_no_canary(caplog.text)
