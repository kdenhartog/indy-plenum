import pytest

from collections import OrderedDict
from plenum.common.messages.fields import NonNegativeNumberField, \
    LedgerIdField, IterableField, TimestampField, HexField, MerkleRootField, AnyValueField
from plenum.common.messages.node_messages import Ordered

EXPECTED_ORDERED_FIELDS = OrderedDict([
    ("instId", NonNegativeNumberField),
    ("viewNo", NonNegativeNumberField),
    ("reqIdr", IterableField),
    ("ppSeqNo", NonNegativeNumberField),
    ("ppTime", TimestampField),
    ("ledgerId", LedgerIdField),
    ("stateRootHash", MerkleRootField),
    ("txnRootHash", MerkleRootField),
])


def test_hash_expected_type():
    assert Ordered.typename == "ORDERED"


def test_has_expected_fields():
    actual_field_names = OrderedDict(Ordered.schema).keys()
    assert actual_field_names == EXPECTED_ORDERED_FIELDS.keys()


def test_has_expected_validators():
    schema = dict(Ordered.schema)
    for field, validator in EXPECTED_ORDERED_FIELDS.items():
        assert isinstance(schema[field], validator)
