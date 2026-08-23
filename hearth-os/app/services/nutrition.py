from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

PLACEHOLDER_KG = 70.0
CANCER_PROTEIN_G_PER_KG = 1.2
CANCER_KCAL_PER_KG = 25.0


@dataclass(frozen=True)
class PersonNeed:
    protein_g: float
    kcal: float
    weight_kg: float
    weight_known: bool
    estimate: bool
    energy_first: bool
    soft_food: bool
    label: str


def person_need(
    *,
    weight_kg: Optional[float],
    cancer_track: bool = False,
    soft_food: bool = False,
    protein_target_g: Optional[float] = None,
    kcal_target: Optional[float] = None,
) -> PersonNeed:
    """Kitchen floors only. Not a diagnosis and not a treatment plan."""
    weight_known = weight_kg is not None
    weight = float(weight_kg) if weight_known else PLACEHOLDER_KG
    protein = float(protein_target_g or 0.0)
    kcal = float(kcal_target or 0.0)
    if cancer_track:
        protein = max(protein, CANCER_PROTEIN_G_PER_KG * weight)
        kcal = max(kcal, CANCER_KCAL_PER_KG * weight)
    bits = ["estimate"]
    if not weight_known:
        bits.append("weight unknown")
    return PersonNeed(
        protein_g=round(protein, 1),
        kcal=round(kcal, 1),
        weight_kg=weight,
        weight_known=weight_known,
        estimate=True,
        energy_first=cancer_track,
        soft_food=soft_food,
        label=", ".join(bits),
    )


def cook_verbs(*, cancer_track: bool, soft_food: bool) -> str:
    parts: list[str] = []
    if cancer_track:
        parts.append("Cook eggs and meat until fully done.")
    if soft_food:
        parts.append("Mash or simmer until soft. Shred meat.")
    return " ".join(parts)
