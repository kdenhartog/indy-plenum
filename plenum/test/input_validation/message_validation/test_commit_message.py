import pytest
from plenum.common.messages.node_messages import Commit
from collections import OrderedDict
from plenum.common.messages.fields import NonNegativeNumberField


EXPECTED_ORDERED_FIELDS = OrderedDict([
    ("instId", NonNegativeNumberField),
    ("viewNo", NonNegativeNumberField),
    ("ppSeqNo", NonNegativeNumberField),
])


def test_hash_expected_type():
    assert Commit.typename == "COMMIT"


def test_has_expected_fields():
    actual_field_names = OrderedDict(Commit.schema).keys()
    assert actual_field_names == EXPECTED_ORDERED_FIELDS.keys()


def test_has_expected_validators():
    schema = dict(Commit.schema)
    for field, validator in EXPECTED_ORDERED_FIELDS.items():
        assert isinstance(schema[field], validator)
