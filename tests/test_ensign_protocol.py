"""Tests for ensign-protocol."""
import pytest
from ensign_protocol import Ensign, EnsignHeader, EnsignField, ValidationError


def test_header_validation():
    h = EnsignHeader(name="nav")
    assert h.validate() == []

    bad = EnsignHeader(name="", compression="brotli")
    errs = bad.validate()
    assert len(errs) == 2


def test_field_validation():
    f = EnsignField(key="depth", value=100, weight=0.5)
    assert f.validate() == []

    bad = EnsignField(key="", value=None, weight=5.0)
    assert len(bad.validate()) == 2


def test_round_trip():
    ensign = Ensign(
        header=EnsignHeader(name="navigator", source_room="bridge"),
        fields=[
            EnsignField(key="avoid_shallow", value=True, weight=0.9),
            EnsignField(key="prefer_channel", value="north", weight=0.6),
        ],
    )
    data = ensign.save()
    loaded = Ensign.load(data)
    loaded.validate()
    assert loaded.header.name == "navigator"
    assert len(loaded.fields) == 2
    assert loaded.fields[0].value is True


def test_checksum_tamper_detection():
    ensign = Ensign(header=EnsignHeader(name="test"), fields=[
        EnsignField(key="k", value="v"),
    ])
    data = ensign.save()
    
    import json
    tampered = json.loads(data)
    tampered["fields"][0]["value"] = "TAMPERED"
    tampered_str = json.dumps(tampered)
    
    loaded = Ensign.load(tampered_str)
    with pytest.raises(ValidationError, match="checksum mismatch"):
        loaded.validate()


def test_builder_pattern():
    ensign = (Ensign(header=EnsignHeader(name="builder"))
              .add_field("a", 1, weight=0.5)
              .add_field("b", 2, weight=0.8, category="ops"))
    assert len(ensign.fields) == 2
    assert ensign.total_weight() == 1.3
    assert len(ensign.fields_by_category("ops")) == 1
