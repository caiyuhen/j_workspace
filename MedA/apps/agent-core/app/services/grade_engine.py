from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

DOMAIN_LEVEL = Literal["no_concerns", "some_concerns", "major_concerns"]
CERTAINTY   = Literal["High", "Moderate", "Low", "VeryLow"]
START_LEVEL = Literal["High", "Moderate", "Low", "VeryLow"]

DOMAIN_SCORE: dict = {
    "no_concerns": 0,
    "some_concerns": 1,
    "major_concerns": 2,
}

DOMAIN_KEYS_5: tuple = (
    "risk_of_bias", "indirectness", "inconsistency", "imprecision", "publication_bias"
)

DOWNGRADE_TABLE_STR: dict = {
    "High":     ["High",   "Moderate", "Low",       "VeryLow"],
    "Moderate": ["Moderate","Low",     "VeryLow",   "VeryLow"],
    "Low":      ["Low",    "VeryLow",  "VeryLow",   "VeryLow"],
    "VeryLow":  ["VeryLow","VeryLow",  "VeryLow",   "VeryLow"],
}

UPGRADE_TABLE_STR: dict = {
    "VeryLow":  ["VeryLow", "Low",      "Moderate",  "High"],
    "Low":      ["Low",     "Moderate", "High",      "High"],
    "Moderate": ["Moderate","High",     "High",      "High"],
    "High":     ["High",    "High",     "High",      "High"],
}

@dataclass(frozen=True, slots=True)
class Grade5Domains:
    risk_of_bias: DOMAIN_LEVEL
    indirectness: DOMAIN_LEVEL
    inconsistency: DOMAIN_LEVEL
    imprecision: DOMAIN_LEVEL
    publication_bias: DOMAIN_LEVEL

    def items(self):
        return (
            ("risk_of_bias", self.risk_of_bias),
            ("indirectness", self.indirectness),
            ("inconsistency", self.inconsistency),
            ("imprecision", self.imprecision),
            ("publication_bias", self.publication_bias),
        )

    def total_downgrade_score(self) -> int:
        return sum(DOMAIN_SCORE[v] for _, v in self.items())

@dataclass(frozen=True, slots=True)
class Grade3Upgrades:
    large_effect: bool
    dose_response: bool
    confounders_reduce: bool

    def total_upgrade_count(self) -> int:
        return (1 if self.large_effect else 0) + (1 if self.dose_response else 0) + (1 if self.confounders_reduce else 0)

class GradeEngineError(Exception):
    pass

def _validate_domains(d: Grade5Domains) -> None:
    for _, v in d.items():
        if v not in DOMAIN_SCORE:
            raise GradeEngineError("grade_invalid_domain_value_not_in_3_level")

def compute_certainty_final(
    domains: Grade5Domains,
    upgrades: Grade3Upgrades,
    start: START_LEVEL = "High",
) -> CERTAINTY:
    _validate_domains(domains)
    td = domains.total_downgrade_score()
    bucket_td = min(td, 3)
    after_td: CERTAINTY = DOWNGRADE_TABLE_STR[start][bucket_td]
    tu = upgrades.total_upgrade_count()
    bucket_tu = min(tu, 3)
    final: CERTAINTY = UPGRADE_TABLE_STR[after_td][bucket_tu]
    return final
