from __future__ import annotations

"""FastAPI entrypoint for the AI Adoption DSS."""

import json
import logging
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pymysql.connections import Connection
import requests

from .config import get_settings
from .database import get_db, init_db
from .recommendations import RecommendationEngine
from .schemas import LikertScale
from .schemas import (
    RecommendationPayload,
    SurveyDefinitionResponse,
    SurveyResponseRead,
    SurveySubmission,
    SurveySubmissionResponse,
)
from .survey import get_survey_definition
from .webapp import render_webapp_html

settings = get_settings()
recommendation_engine = RecommendationEngine(settings=settings)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Adoption DSS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _probe_huggingface() -> dict[str, str]:
    if not settings.huggingface_token:
        return {
            "status": "misconfigured",
            "provider": "huggingface",
            "detail": "DSS_HF_TOKEN not set",
        }

    payload = {
        "model": settings.huggingface_model,
        "messages": [
            {"role": "user", "content": "Reply with valid JSON only: {\"ok\": true}"}
        ],
        "temperature": 0.0,
        "max_tokens": 32,
    }
    try:
        response = requests.post(
            settings.huggingface_api_url,
            headers={"Authorization": f"Bearer {settings.huggingface_token}"},
            json=payload,
            timeout=min(settings.timeout_seconds, 10),
        )
        response.raise_for_status()
        return {
            "status": "ok",
            "provider": "huggingface",
            "model": settings.huggingface_model,
        }
    except requests.RequestException as exc:
        return {
            "status": "error",
            "detail": str(exc),
            "provider": "huggingface",
            "model": settings.huggingface_model,
        }


def _probe_mistral() -> dict[str, str]:
    if not settings.mistral_api_key:
        return {
            "status": "misconfigured",
            "provider": "mistral",
            "detail": "DSS_MISTRAL_API_KEY not set",
        }

    payload = {
        "model": settings.mistral_model,
        "messages": [{"role": "user", "content": "Return JSON: {\"ok\": true}"}],
        "temperature": 0.0,
        "max_tokens": 32,
    }
    try:
        response = requests.post(
            settings.mistral_api_url,
            headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
            json=payload,
            timeout=min(settings.timeout_seconds, 10),
        )
        response.raise_for_status()
        return {"status": "ok", "provider": "mistral", "model": settings.mistral_model}
    except requests.RequestException as exc:
        return {
            "status": "error",
            "detail": str(exc),
            "provider": "mistral",
            "model": settings.mistral_model,
        }


def _probe_local() -> dict[str, str]:
    if not settings.local_model_id:
        return {
            "status": "misconfigured",
            "provider": "local",
            "detail": "DSS_LOCAL_MODEL_ID not set",
        }
    return {
        "status": "configured",
        "provider": "local",
        "model": settings.local_model_id,
    }


def _llm_status() -> dict[str, str]:
    provider_checks = {
        "huggingface": _probe_huggingface,
        "mistral": _probe_mistral,
        "local": _probe_local,
    }
    last_status = {"status": "skipped", "detail": "No LLM provider configured"}
    for provider in settings.preferred_llm_providers():
        check = provider_checks.get(provider)
        if check is None:
            return {
                "status": "error",
                "provider": provider,
                "detail": "Unsupported DSS_LLM_PROVIDER value",
            }
        status = check()
        if status["status"] in {"ok", "configured"}:
            return status
        last_status = status
        if settings.normalized_llm_provider() != "auto":
            return status
    return last_status


def compute_readiness_score(submission: SurveySubmission) -> int:
    likert_scores = {
        LikertScale.strongly_agree: 100,
        LikertScale.agree: 75,
        LikertScale.neutral: 50,
        LikertScale.disagree: 25,
        LikertScale.strongly_disagree: 0,
    }
    concern_scores = {
        LikertScale.strongly_agree: 0,
        LikertScale.agree: 25,
        LikertScale.neutral: 50,
        LikertScale.disagree: 75,
        LikertScale.strongly_disagree: 100,
    }
    score = 0.0
    score += likert_scores[submission.openness_to_ai] * 0.35
    score += 15 if submission.is_familiar_with_ai else 0
    score += min(len(submission.expected_benefits) * 4, 24)
    score += min(len(submission.ai_tasks) * 3, 21)
    score -= min(len(submission.concerns) * 3, 15)
    score += concern_scores[submission.job_replacement_concern] * 0.15
    score += min(len(submission.safeguards_needed) * 2, 10)
    return max(0, min(100, round(score)))


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    definition = get_survey_definition()
    return HTMLResponse(render_webapp_html(definition))


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/deps")
def health_dependencies(db: Connection = Depends(get_db)) -> dict[str, dict[str, str]]:
    db_status: dict[str, str]
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = {"status": "ok"}
    except Exception as exc:
        db_status = {"status": "error", "detail": str(exc)}

    llm_status = _llm_status()

    return {"db": db_status, "llm": llm_status}


@app.get("/survey", response_model=SurveyDefinitionResponse)
def fetch_survey_definition() -> SurveyDefinitionResponse:
    definition = get_survey_definition()
    return SurveyDefinitionResponse.model_validate(definition)


@app.post(
    "/survey/responses",
    response_model=SurveySubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_survey(
    submission: SurveySubmission, db: Connection = Depends(get_db)
) -> SurveySubmissionResponse:
    readiness_score = compute_readiness_score(submission)
    years_map = {
        "less_than_1": 0,
        "1_to_3": 1,
        "4_to_7": 2,
        "8_to_15": 3,
        "more_than_15": 4,
    }
    response_doc = {
        "created_at": datetime.utcnow(),
        "profession": submission.profession,
        "years_in_profession": years_map[submission.years_in_profession.value],
        "is_familiar_with_ai": int(submission.is_familiar_with_ai),
        "openness_to_ai": submission.openness_to_ai.value,
        "ai_tasks": json.dumps([choice.value for choice in submission.ai_tasks]),
        "ai_tasks_other": submission.ai_tasks_other,
        "concerns": json.dumps([choice.value for choice in submission.concerns]),
        "job_replacement_concern": submission.job_replacement_concern.value,
        "expected_benefits": json.dumps(
            [choice.value for choice in submission.expected_benefits]
        ),
        "safeguards_needed": json.dumps(
            [choice.value for choice in submission.safeguards_needed]
        ),
        "safeguards_notes": submission.safeguards_notes,
        "wants_recommendation": int(submission.wants_recommendation),
        "email": submission.email,
        "additional_notes": submission.additional_notes,
        "raw_payload": json.dumps(submission.model_dump(mode="json"), ensure_ascii=True),
        "recommendation": None,
        "readiness_score": readiness_score,
    }

    insert_sql = """
        INSERT INTO survey_submission_responses (
            created_at,
            profession,
            years_in_profession,
            is_familiar_with_ai,
            openness_to_ai,
            ai_tasks,
            ai_tasks_other,
            concerns,
            job_replacement_concern,
            expected_benefits,
            safeguards_needed,
            safeguards_notes,
            wants_recommendation,
            email,
            additional_notes,
            raw_payload,
            recommendation,
            readiness_score
        )
        VALUES (
            %(created_at)s,
            %(profession)s,
            %(years_in_profession)s,
            %(is_familiar_with_ai)s,
            %(openness_to_ai)s,
            %(ai_tasks)s,
            %(ai_tasks_other)s,
            %(concerns)s,
            %(job_replacement_concern)s,
            %(expected_benefits)s,
            %(safeguards_needed)s,
            %(safeguards_notes)s,
            %(wants_recommendation)s,
            %(email)s,
            %(additional_notes)s,
            %(raw_payload)s,
            %(recommendation)s,
            %(readiness_score)s
        )
    """
    with db.cursor() as cursor:
        cursor.execute(insert_sql, response_doc)
        response_id_int = int(cursor.lastrowid)
        response_id = str(response_id_int)

    recommendation_payload: RecommendationPayload | None = None
    if submission.wants_recommendation:
        try:
            recommendation_payload = recommendation_engine.generate(submission)
            recommendation_json = json.dumps(
                recommendation_payload.model_dump(mode="json"), ensure_ascii=True
            )
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE survey_submission_responses SET recommendation = %s WHERE id = %s",
                    (recommendation_json, response_id_int),
                )
        except Exception as exc:
            logger.exception("Recommendation generation failed: %s", exc)

    return SurveySubmissionResponse(
        response_id=response_id,
        recommendation=recommendation_payload,
        readiness_score=readiness_score,
    )


@app.get("/recommendations/{response_id}", response_model=SurveyResponseRead)
def fetch_submission(response_id: str, db: Connection = Depends(get_db)) -> SurveyResponseRead:
    try:
        response_id_int = int(response_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    select_sql = "SELECT * FROM survey_submission_responses WHERE id = %s"
    with db.cursor() as cursor:
        cursor.execute(select_sql, (response_id_int,))
        record = cursor.fetchone()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    years_reverse_map = {
        0: "less_than_1",
        1: "1_to_3",
        2: "4_to_7",
        3: "8_to_15",
        4: "more_than_15",
    }
    record["id"] = str(record.pop("id"))
    record["years_in_profession"] = years_reverse_map.get(
        record.get("years_in_profession"), "less_than_1"
    )
    record["is_familiar_with_ai"] = bool(record.get("is_familiar_with_ai"))
    record["wants_recommendation"] = bool(record.get("wants_recommendation"))
    record["ai_tasks"] = json.loads(record.get("ai_tasks") or "[]")
    record["concerns"] = json.loads(record.get("concerns") or "[]")
    record["expected_benefits"] = json.loads(record.get("expected_benefits") or "[]")
    record["safeguards_needed"] = json.loads(record.get("safeguards_needed") or "[]")
    raw_recommendation = record.get("recommendation")
    if raw_recommendation:
        try:
            record["recommendation"] = json.loads(raw_recommendation)
        except json.JSONDecodeError:
            record["recommendation"] = None
    else:
        record["recommendation"] = None

    return SurveyResponseRead.model_validate(record)
