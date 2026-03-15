# AI Adoption Decision Support System

## 1. Goals & Requirements
- **Objective:** Provide professionals with actionable, personalized recommendations about adopting AI in their workplace.
- **Key Capabilities:**
  1. Collect survey input describing the participant, their readiness, perceived AI-relevant tasks, concerns, safeguards, and desired benefits.
  2. Generate tailored recommendations by calling a Hugging Face text-generation model with the survey context.
  3. Capture survey submissions and the resulting recommendations in a persistent database for later analysis.
  4. Expose the functionality through a Python-first API layer that can power a future web/mobile UI.

## 2. Survey Inventory
The API serves a structured survey with the following sections:
1. **Introduction** – explains purpose and use of data.
2. **General Information** – profession (text/dropdown) and tenure (multiple choice buckets).
3. **AI Adoption Readiness** – familiarity (yes/no) and openness (Likert scale).
4. **AI Task Relevance** – select applicable tasks such as data analysis, customer support, workflow automation, quality assurance, forecasting, or "other" text.
5. **Concerns About AI** – checkbox (job loss, security risks, privacy, loss of control) plus a Likert question on job replacement risk.
6. **Expected Benefits** – checkbox (efficiency, cost savings, decision quality, innovation, compliance).
7. **AI Safety & Safeguards** – checkbox/text for transparency, privacy, accountability, human-in-the-loop, governance, plus free-text notes.
8. **Closing** – consent to receive personalized recommendations (yes/no) and optional email for follow-up.

Each question is captured in the backend with friendly labels and canonical keys to keep storage consistent.

## 3. System Architecture
- **API Layer (FastAPI):**
  - `GET /survey` returns question metadata so any UI can render the form.
  - `POST /survey/responses` accepts user submissions, triggers recommendation generation (if opted-in), persists data, and responds with the recommendation payload.
  - `GET /recommendations/{id}` retrieves a stored submission + recommendation for audit/testing.
- **Recommendation Service:**
  - Formats survey responses into a compact context block.
  - Sends prompt to Hugging Face Inference API (model configurable via env) requesting JSON output with adoption decision, helpful tasks, risk summary, safeguards, and confidence.
  - Falls back to a rule-based heuristic when the remote call fails or no API token is configured.
- **Persistence:**
  - MySQL via `DSS_MYSQL_HOST`/`DSS_MYSQL_PORT`/`DSS_MYSQL_USER`/`DSS_MYSQL_PASSWORD`/`DSS_MYSQL_DB` or `DSS_MYSQL_URI`.
  - Collections: `survey_responses` storing all raw answers and metadata, `recommendations` storing structured AI output linked to a response.

## 4. Data Flow
1. Client fetches survey definition; renders UI.
2. User submits responses to API.
3. API validates payload, persists submission, and when allowed calls the recommendation service.
4. Generated recommendation (AI or fallback) is saved and returned to the caller.
5. Analytics / exports can review stored rows for user-testing insights.

## 5. Testing Approach
- Unit tests focus on schema validation, recommendation prompt formatting, and fallback heuristics.
- Manual testing with `uvicorn app.main:app --reload` and cURL/HTTPie or the included Postman collection (future addition).
- User testing: recruit professionals to walk through the survey, verify clarity, and review whether generated advice feels actionable; capture feedback and update heuristics/prompting.

## 6. Next Steps
1. Implement FastAPI endpoints, MySQL persistence, and Hugging Face integration (current task).
2. Add auth/observability layers once core flow works.
3. Build UI client (Streamlit/React) to improve data collection experience.
4. Schedule user-testing sessions and document findings.
