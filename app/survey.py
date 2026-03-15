from __future__ import annotations

"""Survey definition served to front-end clients."""

from typing import Any, Dict, List

from .schemas import (
    AiTaskChoice,
    BenefitChoice,
    ConcernChoice,
    LikertScale,
    SafeguardChoice,
    YearsInProfession,
)

LIKERT_OPTIONS = [item.value for item in LikertScale]
YEARS_OPTIONS = [
    {"value": YearsInProfession.less_than_1.value, "label": "Less than 1 year"},
    {"value": YearsInProfession.one_to_three.value, "label": "1 - 3 years"},
    {"value": YearsInProfession.four_to_seven.value, "label": "4 - 7 years"},
    {"value": YearsInProfession.eight_to_fifteen.value, "label": "8 - 15 years"},
    {"value": YearsInProfession.more_than_fifteen.value, "label": "More than 15 years"},
]

TASK_OPTIONS = [
    {"value": AiTaskChoice.data_analysis.value, "label": "Data analysis & reporting"},
    {"value": AiTaskChoice.customer_support.value, "label": "Customer support & success"},
    {"value": AiTaskChoice.workflow_automation.value, "label": "Workflow / process automation"},
    {"value": AiTaskChoice.forecasting.value, "label": "Forecasting & planning"},
    {"value": AiTaskChoice.quality_assurance.value, "label": "Quality assurance"},
    {"value": AiTaskChoice.decision_support.value, "label": "Decision support & insights"},
    {"value": AiTaskChoice.innovation_research.value, "label": "Innovation & research"},
    {"value": AiTaskChoice.other.value, "label": "Other (please specify)"},
]

CONCERN_OPTIONS = [
    {"value": ConcernChoice.job_loss.value, "label": "Job loss"},
    {"value": ConcernChoice.security_risks.value, "label": "Security risks"},
    {"value": ConcernChoice.privacy_issues.value, "label": "Privacy issues"},
    {"value": ConcernChoice.lack_of_control.value, "label": "Lack of control"},
    {"value": ConcernChoice.ethical_bias.value, "label": "Ethical bias"},
]

BENEFIT_OPTIONS = [
    {"value": BenefitChoice.increased_efficiency.value, "label": "Increased efficiency"},
    {"value": BenefitChoice.cost_savings.value, "label": "Cost savings"},
    {"value": BenefitChoice.better_decisions.value, "label": "Better decision-making"},
    {"value": BenefitChoice.improved_accuracy.value, "label": "Improved accuracy"},
    {"value": BenefitChoice.innovation.value, "label": "Faster innovation"},
    {"value": BenefitChoice.better_customer_experience.value, "label": "Better customer experience"},
]

SAFEGUARD_OPTIONS = [
    {"value": SafeguardChoice.transparency.value, "label": "Transparency"},
    {"value": SafeguardChoice.data_privacy.value, "label": "Data privacy"},
    {"value": SafeguardChoice.accountability.value, "label": "Accountability"},
    {"value": SafeguardChoice.human_in_the_loop.value, "label": "Human-in-the-loop"},
    {"value": SafeguardChoice.audit_trail.value, "label": "Audit trails"},
    {"value": SafeguardChoice.governance_policy.value, "label": "Governance policy"},
]


SURVEY_DEFINITION: Dict[str, Any] = {
    "title": "AI Adoption Readiness Survey",
    "introduction": (
        "We are researching how professionals evaluate and plan for AI adoption in "
        "their daily work. Your answers will only be used for aggregated insights and "
        "to generate an optional personalized recommendation."
    ),
    "sections": [
        {
            "section_id": "general_information",
            "title": "General Information",
            "description": "Tell us about your professional background.",
            "questions": [
                {
                    "id": "profession",
                    "type": "text",
                    "prompt": "What is your profession?",
                    "required": True,
                },
                {
                    "id": "years_in_profession",
                    "type": "multiple_choice",
                    "prompt": "How long have you worked in this profession?",
                    "options": YEARS_OPTIONS,
                    "required": True,
                },
            ],
        },
        {
            "section_id": "adoption_readiness",
            "title": "AI Adoption Readiness",
            "description": "Gauge familiarity and openness.",
            "questions": [
                {
                    "id": "is_familiar_with_ai",
                    "type": "boolean",
                    "prompt": "Are you familiar with Artificial Intelligence (AI)?",
                    "required": True,
                },
                {
                    "id": "openness_to_ai",
                    "type": "likert",
                    "prompt": "Would you be open to adopting AI in your work?",
                    "options": LIKERT_OPTIONS,
                    "required": True,
                },
            ],
        },
        {
            "section_id": "tasks",
            "title": "AI Task Relevance",
            "description": "Identify the work that could benefit from AI assistance.",
            "questions": [
                {
                    "id": "ai_tasks",
                    "type": "checkbox",
                    "prompt": "Which tasks could benefit from AI?",
                    "options": TASK_OPTIONS,
                    "required": True,
                },
                {
                    "id": "ai_tasks_other",
                    "type": "text",
                    "prompt": "If other, please describe.",
                    "required": False,
                },
            ],
        },
        {
            "section_id": "concerns",
            "title": "Concerns About AI",
            "questions": [
                {
                    "id": "concerns",
                    "type": "checkbox",
                    "prompt": "What are your concerns about AI adoption?",
                    "options": CONCERN_OPTIONS,
                },
                {
                    "id": "job_replacement_concern",
                    "type": "likert",
                    "prompt": "How concerned are you about AI replacing jobs in your field?",
                    "options": LIKERT_OPTIONS,
                    "required": True,
                },
            ],
        },
        {
            "section_id": "benefits",
            "title": "Expected Benefits",
            "questions": [
                {
                    "id": "expected_benefits",
                    "type": "checkbox",
                    "prompt": "What benefits do you expect from AI adoption?",
                    "options": BENEFIT_OPTIONS,
                }
            ],
        },
        {
            "section_id": "safeguards",
            "title": "AI Safety and Safeguards",
            "questions": [
                {
                    "id": "safeguards_needed",
                    "type": "checkbox",
                    "prompt": "What safeguards are necessary for safe AI adoption?",
                    "options": SAFEGUARD_OPTIONS,
                },
                {
                    "id": "safeguards_notes",
                    "type": "text",
                    "prompt": "Include any additional safety expectations.",
                },
            ],
        },
        {
            "section_id": "closing",
            "title": "Closing",
            "questions": [
                {
                    "id": "wants_recommendation",
                    "type": "boolean",
                    "prompt": "Would you like to receive a personalized recommendation on AI adoption?",
                    "required": True,
                    "default": True,
                },
                {
                    "id": "email",
                    "type": "text",
                    "prompt": "If yes, share an email for follow-up (optional).",
                },
                {
                    "id": "additional_notes",
                    "type": "text",
                    "prompt": "Any other comments or context to consider?",
                },
            ],
        },
    ],
}


def get_survey_definition() -> Dict[str, Any]:
    """Return a copy of the survey definition to prevent accidental mutation."""

    import copy

    return copy.deepcopy(SURVEY_DEFINITION)
