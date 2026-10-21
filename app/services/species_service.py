"""
ResearchDose — Species & Scientific Provenance Service.

Loads, validates, and serves verified laboratory species profiles and
corresponding literature references with strict data integrity guarantees.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.species import (
    SpeciesReference,
    ReferenceDocument,
    VerificationStatus,
)


class SpeciesService:
    def __init__(
        self,
        species_file: Path = settings.SPECIES_DATA_FILE,
        references_file: Path = settings.REFERENCES_DATA_FILE,
    ):
        self.species_file = species_file
        self.references_file = references_file
        self._species_cache: Dict[str, SpeciesReference] = {}
        self._references_cache: Dict[str, ReferenceDocument] = {}
        self._is_initialized = False

    def initialize(self) -> None:
        """Loads and strictly validates species and reference data from disk."""
        if not self.references_file.exists():
            raise FileNotFoundError(f"References data file not found at: {self.references_file}")
        if not self.species_file.exists():
            raise FileNotFoundError(f"Species data file not found at: {self.species_file}")

        # 1. Load and validate scientific references
        with open(self.references_file, "r", encoding="utf-8") as rf:
            raw_references = json.load(rf)
            for ref_item in raw_references:
                ref_doc = ReferenceDocument(**ref_item)
                self._references_cache[ref_doc.id] = ref_doc

        # 2. Load and validate species profiles
        with open(self.species_file, "r", encoding="utf-8") as sf:
            raw_species = json.load(sf)
            for sp_item in raw_species:
                species_obj = SpeciesReference(**sp_item)
                
                # Check reference integrity: If species is verified, its reference must exist
                if species_obj.verification_status == VerificationStatus.VERIFIED:
                    if species_obj.primary_reference_id not in self._references_cache:
                        raise ValueError(
                            f"Species '{species_obj.common_name}' references citation ID "
                            f"'{species_obj.primary_reference_id}', which does not exist in references.json."
                        )

                self._species_cache[species_obj.id] = species_obj

        self._is_initialized = True

    def _ensure_initialized(self) -> None:
        if not self._is_initialized:
            self.initialize()

    def get_all_species(self, include_unverified: bool = True) -> List[SpeciesReference]:
        """Returns all species, optionally filtering out unverified models."""
        self._ensure_initialized()
        if include_unverified:
            return list(self._species_cache.values())
        return [
            sp for sp in self._species_cache.values()
            if sp.verification_status == VerificationStatus.VERIFIED
        ]

    def get_verified_species(self) -> List[SpeciesReference]:
        """Returns only scientifically verified species with valid Km values."""
        return self.get_all_species(include_unverified=False)

    def get_species_by_id(self, species_id: str) -> Optional[SpeciesReference]:
        """Retrieves a species by its unique ID."""
        self._ensure_initialized()
        return self._species_cache.get(species_id.lower().strip())

    def get_all_references(self) -> List[ReferenceDocument]:
        """Returns all verified scientific reference documents."""
        self._ensure_initialized()
        return list(self._references_cache.values())

    def get_reference_by_id(self, reference_id: str) -> Optional[ReferenceDocument]:
        """Retrieves a scientific reference document by its citation key."""
        self._ensure_initialized()
        return self._references_cache.get(reference_id)

    def is_conversion_supported(
        self, source_id: str, target_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies if BSA/Km dose conversion between source and target species is scientifically valid.
        Returns (is_supported: bool, rejection_reason: Optional[str]).
        """
        source = self.get_species_by_id(source_id)
        if not source:
            return False, f"Source species '{source_id}' was not found in the laboratory dataset."

        target = self.get_species_by_id(target_id)
        if not target:
            return False, f"Target species '{target_id}' was not found in the laboratory dataset."

        if source.verification_status != VerificationStatus.VERIFIED or source.km_factor is None:
            return False, (
                f"Source species '{source.common_name}' does not have a verified Km factor. "
                "BSA normalization cannot be performed on unverified species."
            )

        if target.verification_status != VerificationStatus.VERIFIED or target.km_factor is None:
            return False, (
                f"Target species '{target.common_name}' does not have a verified Km factor. "
                "BSA normalization cannot be performed on unverified species."
            )

        return True, None


# Global singleton instance
species_service = SpeciesService()
