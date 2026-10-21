"""
ResearchDose — Unit Conversion Service.

Provides exact Decimal-based conversions for weights, pharmacological dose rates,
formulation concentrations, and liquid volumes.
"""

from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Union


class WeightUnit(str, Enum):
    KG = "kg"
    G = "g"


class DoseUnit(str, Enum):
    MG_KG = "mg_kg"
    UG_KG = "ug_kg"
    G_KG = "g_kg"
    TOTAL_MG = "total_mg"
    TOTAL_G = "total_g"
    TOTAL_UG = "total_ug"


class ConcentrationUnit(str, Enum):
    MG_ML = "mg_ml"
    UG_ML = "ug_ml"


class UnitConverter:
    """Handles unit conversions with zero binary floating-point rounding drift."""

    # Conversion multipliers to canonical base units:
    # Base weight: kg
    WEIGHT_TO_KG = {
        WeightUnit.KG: Decimal("1.0"),
        WeightUnit.G: Decimal("0.001"),
    }

    # Base dose rate: mg/kg
    DOSE_TO_MG_KG = {
        DoseUnit.MG_KG: Decimal("1.0"),
        DoseUnit.UG_KG: Decimal("0.001"),
        DoseUnit.G_KG: Decimal("1000.0"),
    }

    # Base concentration: mg/mL
    CONC_TO_MG_ML = {
        ConcentrationUnit.MG_ML: Decimal("1.0"),
        ConcentrationUnit.UG_ML: Decimal("0.001"),
    }

    @classmethod
    def to_decimal(cls, value: Union[str, float, int, Decimal]) -> Decimal:
        """Converts arbitrary numeric input safely into Decimal."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid numeric value: '{value}'")

    @classmethod
    def normalize_weight_to_kg(
        cls, weight_value: Union[str, float, int, Decimal], unit: Union[WeightUnit, str]
    ) -> Decimal:
        """Normalizes any weight to kilograms (kg)."""
        dec_val = cls.to_decimal(weight_value)
        if dec_val <= 0:
            raise ValueError("Body weight must be strictly positive (> 0).")
        
        unit_enum = WeightUnit(unit.lower() if isinstance(unit, str) else unit)
        multiplier = cls.WEIGHT_TO_KG[unit_enum]
        return dec_val * multiplier

    @classmethod
    def normalize_dose_to_mg_kg(
        cls, dose_value: Union[str, float, int, Decimal], unit: Union[DoseUnit, str]
    ) -> Decimal:
        """Normalizes any dose to milligrams per kilogram (mg/kg)."""
        dec_val = cls.to_decimal(dose_value)
        if dec_val <= 0:
            raise ValueError("Dose value must be strictly positive (> 0).")

        unit_str = str(unit).lower().replace("/", "_")
        unit_enum = DoseUnit(unit_str)
        multiplier = cls.DOSE_TO_MG_KG[unit_enum]
        return dec_val * multiplier

    @classmethod
    def normalize_concentration_to_mg_ml(
        cls, conc_value: Union[str, float, int, Decimal], unit: Union[ConcentrationUnit, str] = ConcentrationUnit.MG_ML
    ) -> Decimal:
        """Normalizes concentration to mg/mL."""
        dec_val = cls.to_decimal(conc_value)
        if dec_val <= 0:
            raise ValueError("Formulation concentration must be strictly positive (> 0).")

        unit_str = str(unit).lower().replace("/", "_")
        unit_enum = ConcentrationUnit(unit_str)
        multiplier = cls.CONC_TO_MG_ML[unit_enum]
        return dec_val * multiplier

    @classmethod
    def convert_from_mg_kg(
        cls, mg_kg_value: Decimal, target_unit: Union[DoseUnit, str]
    ) -> Decimal:
        """Converts mg/kg into target dose unit."""
        unit_str = str(target_unit).lower().replace("/", "_")
        unit_enum = DoseUnit(unit_str)
        multiplier = cls.DOSE_TO_MG_KG[unit_enum]
        return mg_kg_value / multiplier
