import cbor2
import pytest
from binascii import unhexlify

class Helpers:
    @staticmethod
    def assert_roundtrip(data):
        # encode the data to CBOR
        encode_data = cbor2.dumps(data)
        # decode CBOR back to data
        decode_data = cbor2.loads(encode_data)
        assert data == decode_data

    @staticmethod
    def assert_conformance(data, expected):
        decoded = cbor2.loads(unhexlify(data))
        assert decoded == expected
        encoded = cbor2.dumps(decoded)
        assert encoded == unhexlify(data)

    @staticmethod
    def assert_conformance_diff(data, decoded, encoded):
        decoded_data = cbor2.loads(unhexlify(data))
        assert decoded_data == decoded
        encoded_data = cbor2.dumps(decoded_data)
        assert encoded_data == unhexlify(encoded)

@pytest.fixture
def helpers():
    return Helpers
