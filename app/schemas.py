from __future__ import annotations

"""Pydantic schemas shared across the DSS."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class YearsInProfession(str, Enum):
    less_than_1 = "less_than_1"
    one_to_three = "1_to_3"
    four_to_seven = "4_to_7"
    eight_to_fifteen = "8_to_15"
    more_than_fifteen = "more_than_15"


class LikertScale(str, Enum):
    strongly_agree = "strongly_agree"
    agree = "agree"
    neutral = "neutral"
    disagree = "disagree"
    strongly_disagree = "strongly_disagree"


class AiTaskChoice(str, Enum):
    data_analysis = "data_analysis"
    customer_support = "customer_support"
    workflow_automation = "workflow_automation"
    forecasting = "forecasting"
    quality_assurance = "quality_assurance"
    decision_support = "decision_support"
    innovation_research = "innovation_research"
    other = "other"


class ConcernChoice(str, Enum):
    job_loss = "job_loss"
    security_risks = "security_risks"
    privacy_issues = "privacy_issues"
    lack_of_control = "lack_of_control"
    ethical_bias = "ethical_bias"


class BenefitChoice(str, Enum):
    increased_efficiency = "increased_efficiency"
    cost_savings = "cost_savings"
    better_decisions = "better_decisions"
    improved_accuracy = "improved_accuracy"
    innovation = "innovation"
    better_customer_experience = "better_customer_experience"


class SafeguardChoice(str, Enum):
    transparency = "transparency"
    data_privacy = "data_privacy"
    accountability = "accountability"
    human_in_the_loop = "human_in_the_loop"
    audit_trail = "audit_trail"
    governance_policy = "governance_policy"


class RecommendationPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Structured response returned to the caller and stored in the DB."""

    adoption_decision: str
    helpful_tasks: List[str]
    risk_assessment: str
    safeguards: List[str]
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    model: str
    source: str
    raw_text: Optional[str] = None


class SurveySubmission(BaseModel):
    profession: str = Field(min_length=2, max_length=120)
    years_in_profession: YearsInProfession
    is_familiar_with_ai: bool
    openness_to_ai: LikertScale
    ai_tasks: List[AiTaskChoice] = Field(default_factory=list)
    ai_tasks_other: Optional[str] = Field(
        default=None, description="Free-text tasks not covered by canned options"
    )
    concerns: List[ConcernChoice] = Field(default_factory=list)
    job_replacement_concern: LikertScale
    expected_benefits: List[BenefitChoice] = Field(default_factory=list)
    safeguards_needed: List[SafeguardChoice] = Field(default_factory=list)
    safeguards_notes: Optional[str] = None
    wants_recommendation: bool = True
    email: Optional[EmailStr] = Field(
        default=None, description="Optional contact if the user wants follow-up"
    )
    additional_notes: Optional[str] = None


class SurveySubmissionResponse(BaseModel):
    response_id: str
    recommendation: Optional[RecommendationPayload] = None
    readiness_score: int


class SurveyResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    profession: str
    years_in_profession: YearsInProfession
    is_familiar_with_ai: bool
    openness_to_ai: LikertScale
    ai_tasks: List[AiTaskChoice]
    ai_tasks_other: Optional[str]
    concerns: List[ConcernChoice]
    job_replacement_concern: LikertScale
    expected_benefits: List[BenefitChoice]
    safeguards_needed: List[SafeguardChoice]
    safeguards_notes: Optional[str]
    wants_recommendation: bool
    email: Optional[str]
    additional_notes: Optional[str]
    recommendation: Optional[RecommendationPayload]
    readiness_score: Optional[int] = None


class SurveyDefinitionSection(BaseModel):
    section_id: str
    title: str
    description: Optional[str]
    questions: List[dict]


class SurveyDefinitionResponse(BaseModel):
    title: str
    introduction: str
    sections: List[SurveyDefinitionSection]
