"""
Unit tests for Laboratory Species Dataset and Pydantic Schemas.

Validates data integrity, FDA 2005 Table 1 reference compliance,
and enforcement against inventing arbitrary or unverified Km values.
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas.species import (
    SpeciesReference,
    ReferenceDocument,
    VerificationStatus,
    SpeciesCategory,
)
from app.services.species_service import SpeciesService


def test_references_data_integrity(service: SpeciesService):
    """Ensure all references in references.json load cleanly with valid metadata."""
    references = service.get_all_references()
    assert len(references) >= 5, "Must contain all foundational scientific reference documents"

    fda_ref = service.get_reference_by_id("fda-2005-starting-dose")
    assert fda_ref is not None
    assert fda_ref.organization.startswith("U.S. Food and Drug Administration")
    assert fda_ref.verification_status == VerificationStatus.VERIFIED

    reagan_ref = service.get_reference_by_id("reagan-shaw-2008")
    assert reagan_ref is not None
    assert reagan_ref.doi == "10.1096/fj.07-9574LSF"


def test_verified_species_fda_compliance(service: SpeciesService):
    """
    Ensure core laboratory species match FDA 2005 Table 1 benchmarks:
    - Human: 60 kg, Km 37
    - Mouse: 0.02 kg (20 g), Km 3
    - Rat: 0.15 kg (150 g), Km 6
    - Hamster: 0.08 kg (80 g), Km 5
    - Guinea pig: 0.4 kg (400 g), Km 8
    - Ferret: 0.3 kg (300 g), Km 7
    - Rabbit: 1.8 kg, Km 12
    - Dog: 10 kg, Km 20
    - Mini-pig: 20 kg, Km 27
    """
    human = service.get_species_by_id("human")
    assert human is not None
    assert human.reference_weight_kg == Decimal("60.0")
    assert human.km_factor == Decimal("37.0")
    assert human.verification_status == VerificationStatus.VERIFIED

    mouse = service.get_species_by_id("mouse")
    assert mouse is not None
    assert mouse.reference_weight_kg == Decimal("0.02")
    assert mouse.km_factor == Decimal("3.0")

    rat = service.get_species_by_id("rat")
    assert rat is not None
    assert rat.reference_weight_kg == Decimal("0.15")
    assert rat.km_factor == Decimal("6.0")

    hamster = service.get_species_by_id("hamster")
    assert hamster is not None
    assert hamster.km_factor == Decimal("5.0")

    guinea_pig = service.get_species_by_id("guinea_pig")
    assert guinea_pig is not None
    assert guinea_pig.km_factor == Decimal("8.0")

    ferret = service.get_species_by_id("ferret")
    assert ferret is not None
    assert ferret.km_factor == Decimal("7.0")

    rabbit = service.get_species_by_id("rabbit")
    assert rabbit is not None
    assert rabbit.km_factor == Decimal("12.0")

    dog = service.get_species_by_id("dog")
    assert dog is not None
    assert dog.km_factor == Decimal("20.0")

    mini_pig = service.get_species_by_id("mini_pig")
    assert mini_pig is not None
    assert mini_pig.km_factor == Decimal("27.0")


def test_custom_species_unverified_rule(service: SpeciesService):
    """Verify that custom species profile has None for Km (never guessed or assumed)."""
    custom = service.get_species_by_id("custom")
    assert custom is not None
    assert custom.verification_status == VerificationStatus.UNVERIFIED
    assert custom.km_factor is None
    assert custom.reference_weight_kg is None


def test_conversion_support_logic(service: SpeciesService):
    """Verify that conversion between verified species is allowed, but blocked for unverified."""
    is_ok, reason = service.is_conversion_supported("mouse", "human")
    assert is_ok is True
    assert reason is None

    # Conversion involving unverified species must be rejected
    is_ok_custom, custom_reason = service.is_conversion_supported("mouse", "custom")
    assert is_ok_custom is False
    assert "verified Km" in custom_reason

    # Unknown species ID must be cleanly rejected
    is_ok_fake, fake_reason = service.is_conversion_supported("mouse", "dragon")
    assert is_ok_fake is False
    assert "was not found" in fake_reason


def test_schema_rejects_verified_without_km():
    """Ensure Pydantic schema validation rejects marking a species as verified if Km is missing."""
    with pytest.raises(ValidationError) as excinfo:
        SpeciesReference(
            id="test_species",
            common_name="Test Species",
            category=SpeciesCategory.RODENT,
            reference_weight_kg=Decimal("0.5"),
            km_factor=None,  # Missing Km
            verification_status=VerificationStatus.VERIFIED,  # Claiming verified
            primary_reference_id="fda-2005-starting-dose",
            source_citation="Test citation",
        )
    assert "lacks a verified positive Km factor" in str(excinfo.value)


def test_schema_rejects_negative_weight_or_km():
    """Ensure negative weights or Km factors are rejected at the schema level."""
    with pytest.raises(ValidationError):
        SpeciesReference(
            id="bad_weight",
            common_name="Bad Weight",
            category=SpeciesCategory.RODENT,
            reference_weight_kg=Decimal("-1.0"),
            km_factor=Decimal("5.0"),
            verification_status=VerificationStatus.VERIFIED,
            primary_reference_id="fda-2005-starting-dose",
            source_citation="Test citation",
        )

    with pytest.raises(ValidationError):
        SpeciesReference(
            id="bad_km",
            common_name="Bad Km",
            category=SpeciesCategory.RODENT,
            reference_weight_kg=Decimal("1.0"),
            km_factor=Decimal("-5.0"),
            verification_status=VerificationStatus.VERIFIED,
            primary_reference_id="fda-2005-starting-dose",
            source_citation="Test citation",
        )
