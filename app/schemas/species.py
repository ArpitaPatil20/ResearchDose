"""
ResearchDose — Species & Scientific Reference Schemas.

Defines Pydantic models for laboratory species profiles, body surface area (BSA)
Km normalization factors, and verified scientific literature citations.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator, HttpUrl


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PROVISIONAL = "provisional"
    UNVERIFIED = "unverified"


class SpeciesCategory(str, Enum):
    HUMAN = "human"
    RODENT = "rodent"
    CARNIVORE = "carnivore"
    LAGOMORPH = "lagomorph"
    NONHUMAN_PRIMATE = "nonhuman_primate"
    NON_RODENT_UNGULATE = "non_rodent_ungulate"
    CUSTOM = "custom"


class ReferenceDocument(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier for citation")
    title: str = Field(..., description="Full publication or guidance title")
    organization: str = Field(..., description="Publishing body, journal, or regulatory agency")
    publication_date: str = Field(..., description="Publication date or version stamp (YYYY-MM)")
    url: Optional[str] = Field(None, description="Direct URL to official regulatory or publisher page")
    doi: Optional[str] = Field(None, description="Digital Object Identifier if applicable")
    method_supported: str = Field(..., description="Conversion or pharmacological method supported")
    summary: str = Field(..., description="Contextual explanation of relevance")
    verification_status: VerificationStatus = Field(
        VerificationStatus.VERIFIED,
        description="Editorial & scientific verification state"
    )
    notes: Optional[str] = Field(None, description="Scope and experimental limitations")


class SpeciesReference(BaseModel):
    id: str = Field(..., description="Canonical species key, e.g. 'mouse', 'rat', 'human'")
    common_name: str = Field(..., description="Standard common name")
    scientific_name: Optional[str] = Field(None, description="Binomial nomenclature (italicized)")
    category: SpeciesCategory = Field(..., description="Taxonomic or lab category")
    reference_weight_kg: Optional[Decimal] = Field(
        None, gt=0, description="Standard guidance reference body weight in kg"
    )
    reference_weight_display: Optional[str] = Field(
        None, description="Human-readable reference weight description"
    )
    reference_bsa_m2: Optional[Decimal] = Field(
        None, gt=0, description="Reference Body Surface Area in m^2"
    )
    km_factor: Optional[Decimal] = Field(
        None, gt=0, description="Conversion factor Km = Body Weight (kg) / BSA (m^2)"
    )
    verification_status: VerificationStatus = Field(
        ..., description="Verification state of this species and its Km factor"
    )
    primary_reference_id: Optional[str] = Field(
        None, description="ID referencing verified citation in references.json"
    )
    source_citation: str = Field(..., description="Formal citation text")
    source_url: Optional[str] = Field(None, description="Direct reference access URL")
    publication_date: Optional[str] = Field(None, description="Guidance or publication date")
    notes: Optional[str] = Field(None, description="Specific limitations, strains, and clinical notes")

    @model_validator(mode="after")
    def validate_scientific_integrity(self) -> "SpeciesReference":
        # Strict rule: Verified species must have a confirmed positive Km factor
        if self.verification_status == VerificationStatus.VERIFIED:
            if self.km_factor is None or self.km_factor <= 0:
                raise ValueError(
                    f"Species '{self.common_name}' is marked as 'verified', "
                    f"but lacks a verified positive Km factor."
                )
            if self.reference_weight_kg is None or self.reference_weight_kg <= 0:
                raise ValueError(
                    f"Species '{self.common_name}' is marked as 'verified', "
                    f"but lacks a reference body weight."
                )
            if not self.primary_reference_id:
                raise ValueError(
                    f"Verified species '{self.common_name}' must link to a valid primary_reference_id."
                )

        # Strict rule: Custom or unverified species cannot have arbitrary unverified Km factors
        if self.verification_status == VerificationStatus.UNVERIFIED and self.id == "custom":
            if self.km_factor is not None:
                raise ValueError(
                    "Default custom species template cannot invent an unverified Km factor."
                )

        return self


class SpeciesListResponse(BaseModel):
    species: List[SpeciesReference]
    total_count: int
    verified_count: int
    dataset_version: str
