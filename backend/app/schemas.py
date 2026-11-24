"""Pydantic contracts for model output and HTTP request bodies."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExtractedTerm(BaseModel):
    """One grounded term. Extra fields are rejected deliberately."""

    model_config = ConfigDict(extra="forbid")

    term_type: Literal["base_rent_paise", "escalation_rate_bp", "maintenance_cap_paise"]
    value: int | None = Field(default=None, ge=0)
    source_quote: str = Field(min_length=3, max_length=1000)
    page: int = Field(ge=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    ambiguous: bool = False

    @model_validator(mode="after")
    def _plausible(self) -> ExtractedTerm:
        if self.term_type == "escalation_rate_bp" and self.value is not None and self.value > 10_000:
            raise ValueError("escalation above 100% is not plausible")
        return self


class ExtractedTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terms: list[ExtractedTerm] = Field(default_factory=list)


class ExtractedInvoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period_start: date
    rent_paise: int = Field(ge=0)
    maintenance_paise: int = Field(ge=0)


class LeaseCreate(BaseModel):
    property_label: str = Field(min_length=1, max_length=120)
    start_date: date


class LeaseUpdate(BaseModel):
    property_label: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None


class Decision(BaseModel):
    decision: Literal["approved", "rejected"]
