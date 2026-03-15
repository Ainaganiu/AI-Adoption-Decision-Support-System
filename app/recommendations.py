from __future__ import annotations

"""Recommendation generation utilities."""

import importlib.util
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

import logging
import requests
from requests import HTTPError

from .config import Settings, get_settings
from .schemas import (
    LikertScale,
    RecommendationPayload,
    SurveySubmission,
)
from .survey import BENEFIT_OPTIONS, CONCERN_OPTIONS, SAFEGUARD_OPTIONS, TASK_OPTIONS, YEARS_OPTIONS


class RecommendationError(Exception):
    """Raised when the remote API call fails."""


logger = logging.getLogger(__name__)


def _option_label_map(options: Iterable[dict[str, str]]) -> dict[str, str]:
    return {option["value"]: option["label"] for option in options}


TASK_LABELS = _option_label_map(TASK_OPTIONS)
CONCERN_LABELS = _option_label_map(CONCERN_OPTIONS)
BENEFIT_LABELS = _option_label_map(BENEFIT_OPTIONS)
SAFEGUARD_LABELS = _option_label_map(SAFEGUARD_OPTIONS)
YEAR_LABELS = _option_label_map(YEARS_OPTIONS)


def _label_for(value: str, mapping: dict[str, str]) -> str:
    key = value.strip()
    if not key:
        return ""
    if key in mapping:
        return mapping[key]
    lower_key = key.lower()
    if lower_key in mapping:
        return mapping[lower_key]
    return key.replace("_", " ")


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _map_list(values: Iterable[str], mapping: dict[str, str]) -> list[str]:
    mapped: list[str] = []
    for value in values:
        label = _label_for(str(value), mapping)
        if label:
            mapped.append(label)
    return mapped


def _display_list(values: Iterable[str]) -> list[str]:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return cleaned


def _humanize_likert(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _parse_json_text(text: str) -> Dict[str, Any]:
    try:
        json_start = text.index("{")
        json_end = text.rindex("}") + 1
        cleaned = text[json_start:json_end]
        return json.loads(cleaned)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RecommendationError("Failed to parse model output") from exc


def _apply_prompt_template(prompt: str, template: str | None) -> str:
    if not template:
        return prompt
    if "{prompt}" in template:
        return template.replace("{prompt}", prompt)
    return f"{template}{prompt}"


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _resolve_torch_dtype(value: str | None, torch_module: Any) -> Any | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"auto", "none"}:
        return None
    mapping = {
        "bfloat16": getattr(torch_module, "bfloat16", None),
        "float16": getattr(torch_module, "float16", None),
        "float32": getattr(torch_module, "float32", None),
    }
    return mapping.get(normalized)


@dataclass
class RecommendationEngine:
    settings: Settings = field(default_factory=get_settings)
    _local_model: Any = field(init=False, default=None, repr=False)
    _local_tokenizer: Any = field(init=False, default=None, repr=False)

    def generate(self, submission: SurveySubmission) -> RecommendationPayload:
        prompt = self._build_prompt(submission)
        for provider in self.settings.preferred_llm_providers():
            if provider == "huggingface" and self.settings.huggingface_token:
                return self._call_huggingface(prompt)
            if provider == "mistral" and self.settings.mistral_api_key:
                return self._call_mistral(prompt)
            if provider == "local" and self.settings.local_model_id:
                return self._call_local_transformers(prompt)

        requested_providers = ", ".join(self.settings.preferred_llm_providers())
        raise RecommendationError(
            "No configured text-generation provider is available for "
            f"{requested_providers}. Set DSS_HF_TOKEN, DSS_MISTRAL_API_KEY, or "
            "DSS_LOCAL_MODEL_ID to match DSS_LLM_PROVIDER."
        )

    def _build_prompt(self, submission: SurveySubmission) -> str:
        tasks = _map_list([choice.value for choice in submission.ai_tasks], TASK_LABELS)
        if submission.ai_tasks_other:
            tasks.append(submission.ai_tasks_other.strip())

        concerns = _map_list([choice.value for choice in submission.concerns], CONCERN_LABELS)
        benefits = _map_list(
            [choice.value for choice in submission.expected_benefits],
            BENEFIT_LABELS,
        )
        safeguards = _map_list(
            [choice.value for choice in submission.safeguards_needed],
            SAFEGUARD_LABELS,
        )
        if submission.safeguards_notes:
            safeguards.append(submission.safeguards_notes.strip())

        survey_context = {
            "profession": submission.profession,
            "years_in_profession": _label_for(
                submission.years_in_profession.value, YEAR_LABELS
            ),
            "familiar_with_ai": "Yes" if submission.is_familiar_with_ai else "No",
            "openness_to_ai": _humanize_likert(submission.openness_to_ai.value),
            "possible_ai_tasks": _display_list(tasks),
            "expected_benefits": _display_list(benefits),
            "main_concerns": _display_list(concerns),
            "job_replacement_concern": _humanize_likert(
                submission.job_replacement_concern.value
            ),
            "required_safeguards": _display_list(safeguards),
            "additional_notes": (submission.additional_notes or "").strip(),
        }
        instructions = (
            "You are an AI adoption advisor reviewing one workplace survey response. "
            "Return exactly one valid JSON object and nothing else. "
            "Use this schema: "
            "{\"adoption_decision\":\"string\",\"helpful_tasks\":[\"string\"],"
            "\"risk_assessment\":\"string\",\"safeguards\":[\"string\"],"
            "\"explanation\":\"string\",\"confidence\":0.0}. "
            "Rules: adoption_decision must be a short recommendation title; "
            "helpful_tasks must contain 2 to 5 concise work tasks tailored to the respondent; "
            "risk_assessment must be 1 to 2 sentences tied to the respondent's concerns; "
            "safeguards must contain 2 to 5 practical controls; "
            "explanation must be a short paragraph referencing profession, openness, and benefits; "
            "confidence must be a number between 0 and 1; "
            "do not include markdown, commentary, or code fences."
        )
        return f"{instructions}\nSURVEY_RESPONSE:\n{json.dumps(survey_context, indent=2)}"

    def _apply_defaults(
        self, data: Dict[str, Any], raw_text: str, model: str, source: str
    ) -> Dict[str, Any]:
        required_keys = {
            "adoption_decision",
            "helpful_tasks",
            "risk_assessment",
            "safeguards",
            "explanation",
            "confidence",
        }
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise RecommendationError(
                f"Model response missing fields: {', '.join(sorted(missing))}"
            )
        normalized = dict(data)
        normalized["helpful_tasks"] = _map_list(
            _coerce_list(normalized.get("helpful_tasks")), TASK_LABELS
        )
        normalized["safeguards"] = _map_list(
            _coerce_list(normalized.get("safeguards")), SAFEGUARD_LABELS
        )
        try:
            normalized["confidence"] = float(normalized.get("confidence"))
        except (TypeError, ValueError) as exc:
            raise RecommendationError("Model response returned non-numeric confidence") from exc
        normalized.setdefault("model", model)
        normalized.setdefault("source", source)
        normalized.setdefault("raw_text", raw_text)
        return normalized

    def _call_mistral(self, prompt: str) -> RecommendationPayload:
        headers = {
            "Authorization": f"Bearer {self.settings.mistral_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.mistral_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 450,
        }
        try:
            response = requests.post(
                self.settings.mistral_api_url,
                headers=headers,
                json=payload,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
        except HTTPError as exc:
            raise RecommendationError(str(exc)) from exc
        except requests.RequestException as exc:
            raise RecommendationError("Network error") from exc

        parsed = self._parse_mistral_body(response.json())
        return RecommendationPayload(**parsed)

    def _get_local_model(self) -> tuple[Any, Any]:
        if self._local_model is not None and self._local_tokenizer is not None:
            return self._local_model, self._local_tokenizer
        if not self.settings.local_model_id:
            raise RecommendationError("Local model ID not configured.")
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError as exc:
            raise RecommendationError(
                "Local model dependencies missing. Install torch, transformers, and accelerate."
            ) from exc

        model_kwargs: dict[str, Any] = {}
        dtype = _resolve_torch_dtype(self.settings.local_torch_dtype, torch)
        if dtype is not None:
            if not torch.cuda.is_available() and dtype in {
                getattr(torch, "float16", None),
                getattr(torch, "bfloat16", None),
            }:
                logger.warning(
                    "Requested dtype %s on CPU; using float32 instead.",
                    self.settings.local_torch_dtype,
                )
                model_kwargs["dtype"] = torch.float32
            else:
                model_kwargs["dtype"] = dtype
        if self.settings.local_use_flash_attention:
            if _module_available("flash_attn"):
                model_kwargs["use_flash_attention_2"] = True
            else:
                logger.warning("flash-attn not available; disabling flash attention.")
        if self.settings.local_device_map:
            if _module_available("accelerate"):
                model_kwargs["device_map"] = self.settings.local_device_map
            else:
                logger.warning(
                    "device_map=%s requires accelerate; running without device_map.",
                    self.settings.local_device_map,
                )

        tokenizer = AutoTokenizer.from_pretrained(self.settings.local_model_id)
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.settings.local_model_id, **model_kwargs
            )
        except TypeError as exc:
            if "dtype" in model_kwargs:
                legacy_kwargs = dict(model_kwargs)
                legacy_kwargs["torch_dtype"] = legacy_kwargs.pop("dtype")
                model = AutoModelForCausalLM.from_pretrained(
                    self.settings.local_model_id, **legacy_kwargs
                )
            else:
                raise RecommendationError("Failed to load local model") from exc

        model.eval()
        self._local_model = model
        self._local_tokenizer = tokenizer
        return model, tokenizer

    def _call_local_transformers(self, prompt: str) -> RecommendationPayload:
        model, tokenizer = self._get_local_model()
        try:
            import torch
        except ImportError as exc:
            raise RecommendationError(
                "Local model dependencies missing. Install torch and transformers."
            ) from exc

        use_chat_template = bool(
            self.settings.local_use_chat_template
            and hasattr(tokenizer, "apply_chat_template")
        )
        if use_chat_template:
            messages = [{"role": "user", "content": prompt}]
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )
        else:
            prompt_text = _apply_prompt_template(
                prompt, self.settings.local_prompt_template
            )
            inputs = tokenizer(prompt_text, return_tensors="pt")

        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        generation_kwargs = {
            "max_new_tokens": self.settings.local_max_new_tokens,
            "do_sample": False,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if tokenizer.eos_token_id is not None:
            generation_kwargs["pad_token_id"] = tokenizer.eos_token_id

        try:
            with torch.inference_mode():
                outputs = model.generate(**inputs, **generation_kwargs)
        except Exception as exc:
            raise RecommendationError("Local model inference failed") from exc

        input_length = inputs["input_ids"].shape[-1]
        generated = tokenizer.decode(
            outputs[0][input_length:], skip_special_tokens=True
        )
        if not generated:
            raise RecommendationError("Local model returned no text")

        data = _parse_json_text(generated)
        return RecommendationPayload(
            **self._apply_defaults(
                data, generated, self.settings.local_model_id, "local"
            )
        )

    def _call_huggingface(self, prompt: str) -> RecommendationPayload:
        headers = {
            "Authorization": f"Bearer {self.settings.huggingface_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.huggingface_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.settings.huggingface_temperature,
            "max_tokens": self.settings.huggingface_max_new_tokens,
        }
        try:
            response = requests.post(
                self.settings.huggingface_api_url,
                headers=headers,
                json=payload,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
        except HTTPError as exc:
            raise RecommendationError(str(exc)) from exc
        except requests.RequestException as exc:
            raise RecommendationError("Network error") from exc

        parsed = self._parse_hf_body(response.json())
        return RecommendationPayload(**parsed)

    def _parse_hf_body(self, body: Any) -> Dict[str, Any]:
        if isinstance(body, dict) and body.get("error"):
            error = body["error"]
            if isinstance(error, dict):
                message = error.get("message") or str(error)
            else:
                message = str(error)
            raise RecommendationError(f"Hugging Face API error: {message}")

        if isinstance(body, dict):
            choices = body.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                generated = message.get("content")
            else:
                generated = None
        else:
            generated = None

        if not generated:
            raise RecommendationError("Unexpected Hugging Face response format")

        data = _parse_json_text(generated)
        return self._apply_defaults(
            data, generated, self.settings.huggingface_model, "huggingface"
        )

    def _parse_mistral_body(self, body: Any) -> Dict[str, Any]:
        if isinstance(body, dict):
            choices = body.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                content = message.get("content")
            else:
                content = None
        else:
            content = None

        if not content:
            raise RecommendationError("Unexpected Mistral response format")

        data = _parse_json_text(content)
        return self._apply_defaults(
            data, content, self.settings.mistral_model, "mistral"
        )

    def _heuristic(self, submission: SurveySubmission) -> RecommendationPayload:
        score = 0.0
        likert_scores = {
            LikertScale.strongly_agree: 2.0,
            LikertScale.agree: 1.25,
            LikertScale.neutral: 0.0,
            LikertScale.disagree: -1.0,
            LikertScale.strongly_disagree: -2.0,
        }
        score += likert_scores[submission.openness_to_ai]
        score += 0.8 if submission.is_familiar_with_ai else -0.3
        score += 0.25 * len(submission.expected_benefits)
        score += 0.2 * len(submission.ai_tasks)
        score -= 0.25 * len(submission.concerns)
        score += -likert_scores[submission.job_replacement_concern] * 0.3

        if submission.safeguards_needed:
            score += 0.1

        if submission.ai_tasks_other:
            score += 0.1

        adoption_decision: str
        if score >= 2.5:
            adoption_decision = "Adopt AI in priority workflows"
        elif score >= 1.5:
            adoption_decision = "Run targeted AI pilots"
        else:
            adoption_decision = "Hold adoption until risks addressed"

        helpful_tasks = _map_list(
            [choice.value for choice in submission.ai_tasks], TASK_LABELS
        )
        if submission.ai_tasks_other:
            helpful_tasks.append(submission.ai_tasks_other)

        if not helpful_tasks:
            helpful_tasks = ["Workflow documentation", "Data preparation"]

        if submission.concerns:
            primary_concern = _label_for(submission.concerns[0].value, CONCERN_LABELS)
        else:
            primary_concern = "uncertainty"
        risk_assessment = (
            f"Primary concern: {primary_concern}. Ensure you run discovery workshops and "
            "define KPIs before scaling."
        )
        safeguards = _map_list(
            [choice.value for choice in submission.safeguards_needed], SAFEGUARD_LABELS
        )
        if submission.safeguards_notes:
            safeguards.append(submission.safeguards_notes)
        if not safeguards:
            safeguards = ["Human-in-the-loop", "Risk & compliance review"]

        explanation = (
            "Recommendation derived from rule-based scoring that balances openness, "
            "benefits, and risk concerns."
        )
        confidence = max(0.3, min(0.85, 0.4 + (score / 5)))
        return RecommendationPayload(
            adoption_decision=adoption_decision,
            helpful_tasks=helpful_tasks,
            risk_assessment=risk_assessment,
            safeguards=safeguards,
            explanation=explanation,
            confidence=round(confidence, 2),
            model="rule-based",
            source="heuristic",
        )
