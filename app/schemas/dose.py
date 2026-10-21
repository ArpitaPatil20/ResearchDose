"""
ResearchDose — Dose Calculation Schemas.

Pydantic models for single conversion requests, multi-species comparisons,
liquid formulation volume checks, and study cohort calculations with full arithmetic provenance.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class ConversionMode(str, Enum):
    HUMAN_TO_ANIMAL = "human_to_animal"
    ANIMAL_TO_HUMAN = "animal_to_human"
    ANIMAL_TO_ANIMAL = "animal_to_animal"


class AdministrationRoute(str, Enum):
    ORAL_GAVAGE = "oral_gavage"
    IV_BOLUS = "iv_bolus"
    IP = "ip"
    SC = "sc"
    OTHER = "other"


class DoseCalculationRequest(BaseModel):
    source_species_id: str = Field(..., description="Species ID of the source dose (e.g., 'mouse')")
    target_species_id: str = Field(..., description="Species ID of the target recipient (e.g., 'human')")
    source_dose: Decimal = Field(..., gt=0, description="Source dose amount (must be positive)")
    source_dose_unit: str = Field("mg_kg", description="Unit of source dose: 'mg_kg', 'ug_kg', 'g_kg', 'total_mg', 'total_g'")
    
    source_weight: Optional[Decimal] = Field(
        None, gt=0, description="Source animal or human body weight. Uses reference weight if omitted."
    )
    source_weight_unit: str = Field("kg", description="Source weight unit: 'kg' or 'g'")
    
    target_weight: Optional[Decimal] = Field(
        None, gt=0, description="Target animal or human body weight. Uses reference weight if omitted."
    )
    target_weight_unit: str = Field("kg", description="Target weight unit: 'kg' or 'g'")
    
    concentration: Optional[Decimal] = Field(
        None, gt=0, description="Optional liquid formulation concentration (e.g., mg/mL)"
    )
    concentration_unit: str = Field("mg_ml", description="Concentration unit: 'mg_ml' or 'ug_ml'")
    
    administration_route: Optional[str] = Field("oral_gavage", description="Optional administration route for volume safety check")
    safety_factor: Optional[Decimal] = Field(Decimal("1.0"), ge=1, description="Safety factor for MRSD (e.g. 10 for human trials)")
    study_id: Optional[str] = Field(None, description="Optional study ID or project label")
    notes: Optional[str] = Field(None, description="Optional researcher notes")

    @model_validator(mode="after")
    def validate_inputs(self) -> "DoseCalculationRequest":
        return self


class DoseCalculationResult(BaseModel):
    mode: str
    source_species_id: str
    source_species_name: str
    target_species_id: str
    target_species_name: str
    
    # Source values
    source_dose_input: Decimal
    source_dose_unit: str
    source_dose_mg_kg: Decimal
    source_weight_kg: Decimal
    is_source_reference_weight: bool
    source_km: Decimal
    
    # Target factors
    target_km: Decimal
    km_ratio: Decimal  # Km(source) / Km(target)
    
    # Core results
    target_dose_mg_kg: Decimal
    target_weight_kg: Decimal
    is_reference_weight: bool
    total_dose_mg: Decimal
    total_dose_ug: Decimal
    
    # Clinical Safety Factor & MRSD (Maximum Recommended Starting Dose)
    safety_factor: Decimal = Decimal("1.0")
    mrsd_mg_kg: Optional[Decimal] = None
    mrsd_total_mg: Optional[Decimal] = None
    
    # Formulation & Volume (optional)
    concentration_mg_ml: Optional[Decimal] = None
    formulation_volume_ml: Optional[Decimal] = None
    formulation_volume_ul: Optional[Decimal] = None
    volume_per_kg_ml: Optional[Decimal] = None
    route_welfare_status: Optional[str] = None  # "safe", "warning", "exceeded"
    route_welfare_message: Optional[str] = None
    
    # Scientific comparison: BSA vs Direct mg/kg
    direct_unscaled_dose_mg_kg: Decimal
    scaling_differential_percent: Decimal
    
    # Provenance and steps
    formula_used: str
    arithmetic_steps: List[str]
    scientific_citation: str
    reference_url: Optional[str] = None
    limitations: List[str]
    timestamp: str
    algorithm_version: str


class MultiSpeciesComparisonItem(BaseModel):
    species_id: str
    common_name: str
    category: str
    km_factor: Decimal
    reference_weight_kg: Decimal
    equivalent_dose_mg_kg: Decimal
    total_dose_mg: Decimal
    fold_difference_vs_source: Decimal


class MultiSpeciesComparisonResponse(BaseModel):
    source_species_id: str
    source_species_name: str
    source_dose_mg_kg: Decimal
    comparisons: List[MultiSpeciesComparisonItem]
    methodology: str
    citation: str


class CohortCalculationRequest(BaseModel):
    species_id: str = Field(..., description="Species ID for cohort study (e.g. 'mouse', 'rat')")
    dose_mg_kg: Decimal = Field(..., gt=0, description="Dose in mg/kg")
    animal_count: int = Field(..., gt=0, description="Total number of animals in group")
    average_weight: Decimal = Field(..., gt=0, description="Average animal weight")
    weight_unit: str = Field("g", description="Weight unit: 'g' or 'kg'")
    frequency_per_day: int = Field(1, ge=1, le=6, description="Doses per day (e.g. 1 for QD, 2 for BID)")
    duration_days: int = Field(14, ge=1, description="Study duration in days")
    concentration_mg_ml: Optional[Decimal] = Field(None, gt=0, description="Optional liquid formulation concentration (mg/mL)")
    waste_margin_percent: Decimal = Field(Decimal("10.0"), ge=0, le=50, description="Syringe dead-volume / waste contingency margin (%)")


class CohortCalculationResult(BaseModel):
    species_id: str
    species_name: str
    dose_mg_kg: Decimal
    animal_count: int
    average_weight_kg: Decimal
    single_dose_per_animal_mg: Decimal
    single_dose_per_animal_ug: Decimal
    daily_total_all_animals_mg: Decimal
    study_total_active_compound_mg: Decimal
    study_total_active_compound_g: Decimal
    waste_contingency_mg: Decimal
    grand_total_compound_required_mg: Decimal
    grand_total_compound_required_g: Decimal
    single_volume_per_animal_ml: Optional[Decimal] = None
    single_volume_per_animal_ul: Optional[Decimal] = None
    total_formulation_volume_required_ml: Optional[Decimal] = None
    summary_text: str
    timestamp: str
