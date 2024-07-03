import pytest
import cbor2
import math
from datetime import datetime, timedelta, timezone
from binascii import unhexlify


@pytest.mark.parametrize(
    "data, expected",
    [
        ("00", 0),
        ("01", 1),
        ("0a", 10),
        ("17", 23),
        ("1818", 24),
        ("1819", 25),
        ("1864", 100),
        ("1903e8", 1000),
        ("1a000f4240", 1000000),
        ("1b000000e8d4a51000", 1000000000000),
        ("1bffffffffffffffff", 18446744073709551615),
        ("c249010000000000000000", 18446744073709551616),
        ("3bffffffffffffffff", -18446744073709551616),
        ("c349010000000000000000", -18446744073709551617),
        ("20", -1),
        ("29", -10),
        ("3863", -100),
        ("3903e7", -1000),
    ],
)
def test_integer(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, decoded, encoded",
    [
        ("f90000", 0.0, "fb0000000000000000"),
        ("f98000", -0.0, "fb8000000000000000"),
        ("f93c00", 1.0, "fb3ff0000000000000"),
        ("fb3ff199999999999a", 1.1, "fb3ff199999999999a"),
        ("f93e00", 1.5, "fb3ff8000000000000"),
        ("f97bff", 65504.0, "fb40effc0000000000"),
        ("fa47c35000", 100000.0, "fb40f86A0000000000"),
        ("fa7f7fffff", 3.4028234663852886e38, "fb47efffffe0000000"),
        ("fb7e37e43c8800759c", 1.0e300, "fb7e37e43c8800759c"),
        ("f90001", 5.960464477539063e-8, "fb3E70000000000000"),
        ("f90400", 0.00006103515625, "fb3f10000000000000"),
        ("f9c400", -4.0, "fbc010000000000000"),
        ("fbc010666666666666", -4.1, "fbc010666666666666"),
        ("f97c00", float("inf"), "f97c00"),
        ("f9fc00", float("-inf"), "f9fc00"),
        ("fa7f800000", float("inf"), "f97C00"),
        ("faff800000", float("-inf"), "f9fc00"),
        ("fb7ff0000000000000", float("inf"), "f97C00"),
        ("fbfff0000000000000", float("-inf"), "f9fc00"),
    ],
)
def test_float(data, decoded, encoded, helpers):
    helpers.assert_conformance_diff(data, decoded, encoded)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("f97e00", float("nan")),
    ],
)
def test_float_nan(data, expected, helpers):
    decoded = cbor2.loads(unhexlify(data))
    assert math.isnan(decoded)
    encoded = cbor2.dumps(decoded)
    assert encoded == unhexlify(data)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("f4", False), ("f5", True), ("f6", None), ("f7", "undefined"),
    ],
)
def test_special_values(data, expected, helpers):
    if expected == "undefined":
        expected = cbor2.undefined
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("60", ""),
        ("6161", "a"),
        ("6449455446", "IETF"),
        ("62225c", '"\\'),
        ("62c3bc", "\u00fc"),
        ("63e6b0b4", "\u6c34"),
    ],
)
def test_string(data, expected, helpers):
    helpers.assert_conformance(data, expected)

def test_invalid_integer_subtype():
    with pytest.raises(cbor2.CBORDecodeError) as exc:
        cbor2.loads(b"\x1c")
        assert str(exc.value).endswith("unknown unsigned integer subtype 0x1c")
        assert isinstance(exc, ValueError)

@pytest.mark.parametrize(
    "data",
    [
        pytest.param("6198", id="short"),
        pytest.param("7a00010000" + "61" * 65535 + "c3", id="long"),
        pytest.param("7f6198ff", id="indefinite"),
    ],
)
def test_string_invalid_utf8(data: str) -> None:
    with pytest.raises(cbor2.CBORDecodeValueError, match="error decoding unicode string") as exc:
        cbor2.loads(unhexlify(data))

    assert isinstance(exc.value.__cause__, UnicodeDecodeError)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("80", []),
        ("83010203", [1, 2, 3]),
        ("8301820203820405", [1, [2, 3], [4, 5]]),
    ],
)
def test_array(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("a0",
        {}),
        ("a201020304", {1: 2, 3: 4})
    ]
)
def test_map(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, expected",
    [
        ("a26161016162820203", {"a": 1, "b": [2, 3]}),
        ("826161a161626163", ["a", {"b": "c"}]),
        (
            "a56161614161626142616361436164614461656145",
            {"a": "A", "b": "B", "c": "C", "d": "D", "e": "E"},
        ),
    ],
)
def test_mixed_array_map(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, decoded, encoded",
    [
        ("5f42010243030405ff", b"\x01\x02\x03\x04\x05", "450102030405"),
        ("7f657374726561646d696e67ff", "streaming", "6973747265616d696e67"),
        ("9fff", [], "80"),
        ("9f018202039f0405ffff", [1, [2, 3], [4, 5]], "8301820203820405"),
        ("9f01820203820405ff", [1, [2, 3], [4, 5]], "8301820203820405"),
        ("83018202039f0405ff", [1, [2, 3], [4, 5]], "8301820203820405"),
        ("83019f0203ff820405", [1, [2, 3], [4, 5]], "8301820203820405"),
        (
            "9f0102030405060708090a0b0c0d0e0f101112131415161718181819ff",
            list(range(1, 26)),
            "98190102030405060708090a0b0c0d0e0f101112131415161718181819",
        ),
        ("bf61610161629f0203ffff", {"a": 1, "b": [2, 3]}, "a26161016162820203"),
        ("826161bf61626163ff", ["a", {"b": "c"}], "826161a161626163"),
        ("bf6346756ef563416d7421ff", {"Fun": True, "Amt": -2}, "a26346756ef563416d7421"),
        ("d901029f010203ff", {1, 2, 3}, "d9010283010203"),
    ],
)
def test_streaming(data, decoded, encoded, helpers):
    helpers.assert_conformance_diff(data, decoded, encoded)

@pytest.mark.parametrize(
    "data, as_timestamp, expected",
    [
        (
            "c074323031332d30332d32315432303a30343a30305a",
            False,
            datetime(2013, 3, 21, 20, 4, 0, tzinfo=timezone.utc),
        ),
        (
            "c0781b323031332d30332d32315432303a30343a30302e3338303834315a",
            False,
            datetime(2013, 3, 21, 20, 4, 0, 380841, tzinfo=timezone.utc),
        ),
        (
            "c07819323031332d30332d32315432323a30343a30302b30323a3030",
            False,
            datetime(2013, 3, 21, 22, 4, 0, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "c11a514b67b0",
            True,
            datetime(2013, 3, 21, 20, 4, 0, tzinfo=timezone.utc),
        ),
        (
            "c1fb41d452d9ec07e6b4",
            True,
            datetime(2013, 3, 21, 20, 4, 0, 123456, tzinfo=timezone.utc),
        ),
        (
            "c11a514b67b0",
            True,
            datetime(2013, 3, 21, 22, 4, 0, tzinfo=timezone(timedelta(hours=2))),
        ),
    ],
)
def test_datetime(data, as_timestamp, expected):
        decoded = cbor2.loads(unhexlify(data))
        assert decoded == expected
        encoded = cbor2.dumps(decoded, datetime_as_timestamp=as_timestamp, timezone=timezone.utc)
        assert encoded == unhexlify(data)


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            # Example from RFC 8949 section 3.4.3.
            "c249010000000000000000",
            18446744073709551616,
        ),
    ],
)
def test_positive_bignum(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, expected",
    [
        (
            "c349010000000000000000",
            -18446744073709551617,
        ),
    ],
)
def test_negative_bignum(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data, expected",
    [
        (
            "c349010000000000000000",
            -18446744073709551617,
        ),
    ],
)
def test_negative_bignum(data, expected, helpers):
    helpers.assert_conformance(data, expected)

@pytest.mark.parametrize(
    "data",
    ["7f7bff0000000000000471717272ff", "5f5bff0000000000000471717272ff"],
    ids=["string", "bytes"],
)
def test_indefinite_overflow(data):
    with pytest.raises(cbor2.CBORDecodeValueError):
        cbor2.loads(unhexlify(data))
