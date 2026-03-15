# AI Adoption Decision Support System

Python-first backend that collects survey responses, calls the Hugging Face Inference API for text generation, and stores the resulting AI adoption recommendations.

## Requirements
- Python 3.10+
- Hugging Face account + Inference API token for live recommendations

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create or update `.env` with your MySQL settings and Hugging Face token:

```bash
DSS_LLM_PROVIDER=huggingface
DSS_HF_MODEL=meta-llama/Llama-3.1-8B-Instruct:fastest
DSS_HF_API_URL=https://router.huggingface.co/v1/chat/completions
DSS_HF_TOKEN=hf_your_token_here
```

Set `DSS_MYSQL_HOST`/`DSS_MYSQL_PORT`/`DSS_MYSQL_USER`/`DSS_MYSQL_PASSWORD`/`DSS_MYSQL_DB` (or `DSS_MYSQL_URI`) to point at your MySQL instance.

The recommendation prompt is built from the survey answers and asks the model to return one JSON object with:
- `adoption_decision`
- `helpful_tasks`
- `risk_assessment`
- `safeguards`
- `explanation`
- `confidence`

## Local model (optional)
To run recommendations with a local Transformers model (SmolLM2 135M Instruct), install dependencies:

```bash
pip install torch
pip install transformers==4.34.0
pip install flash-attn==2.3.1.post1 --no-build-isolation
pip install accelerate==0.23.0
```

Then set (CPU-friendly defaults):

```bash
DSS_LLM_PROVIDER=local
DSS_LOCAL_MODEL_ID=HuggingFaceTB/SmolLM2-135M-Instruct
DSS_LOCAL_USE_CHAT_TEMPLATE=true
DSS_LOCAL_PROMPT_TEMPLATE=<|prompter|>{prompt}</s><|assistant|>
DSS_LOCAL_MAX_TOKENS=400
DSS_LOCAL_TORCH_DTYPE=auto
DSS_LOCAL_DEVICE_MAP=
```

## Running the API
```bash
uvicorn app.main:app --reload
```

## Deploying To AWS App Runner
This repository is ready for App Runner source-code deployment with [apprunner.yaml](/mnt/c/Users/ainag/Documents/AI Adoption System/apprunner.yaml).

1. Push the repository to GitHub.
2. In AWS App Runner, create a service from source code.
3. Connect the GitHub repository and choose the branch to deploy.
4. Use the configuration file in the repo (`apprunner.yaml`).
5. Set these environment variables in App Runner:

```text
DSS_LLM_PROVIDER=huggingface
DSS_HF_MODEL=meta-llama/Llama-3.1-8B-Instruct:fastest
DSS_HF_API_URL=https://router.huggingface.co/v1/chat/completions
DSS_MYSQL_HOST=your-db-host
DSS_MYSQL_PORT=3306
DSS_MYSQL_USER=your-db-user
DSS_MYSQL_DB=aiadoption
```

6. Set these as App Runner secrets, not plain-text env vars:

```text
DSS_HF_TOKEN
DSS_MYSQL_PASSWORD
```

7. Set the health check path to `/health`.
8. Deploy the service.

Notes:
- App Runner will run `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080`.
- The service must be able to reach your MySQL host from the public internet or through your network design.
- This app creates the target database and table on startup, so the configured MySQL user needs permission to create the database if it does not already exist.

## Deploying To Render
This repository is also ready for Render with [render.yaml](/mnt/c/Users/ainag/Documents/AI Adoption System/render.yaml).

If you deploy manually in Render, use:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Render should use Python 3.12.3 for this repo via [.python-version](/mnt/c/Users/ainag/Documents/AI Adoption System/.python-version).

Set these environment variables in Render:

```text
DSS_LLM_PROVIDER=huggingface
DSS_HF_MODEL=meta-llama/Llama-3.1-8B-Instruct:fastest
DSS_HF_API_URL=https://router.huggingface.co/v1/chat/completions
DSS_HF_MAX_NEW_TOKENS=450
DSS_HF_TEMPERATURE=0.2
DSS_HF_TOKEN=...
DSS_MYSQL_HOST=...
DSS_MYSQL_PORT=...
DSS_MYSQL_USER=...
DSS_MYSQL_PASSWORD=...
DSS_MYSQL_DB=...
```

Key endpoints:
- `GET /health` – service check.
- `GET /survey` – returns the structured survey definition.
- `POST /survey/responses` – submit survey data and receive an optional recommendation.
- `GET /recommendations/{id}` – retrieve a stored survey + recommendation for QA/user testing.

## Recommendation Flow
1. Validate survey payload with Pydantic.
2. Persist submission in MySQL.
3. If the participant opts in, build a survey-specific JSON prompt and call the configured provider (`DSS_LLM_PROVIDER`, default `huggingface`).
4. Parse JSON returned by the model and store the recommendation alongside the submission.
5. Return the recommendation to the caller.

## Testing / QA
- Automated: `python3 -m compileall app` verifies syntax; add pytest/unit tests as the project grows.
- Manual: use `uvicorn` locally and hit the endpoints with cURL or the FastAPI docs (`/docs`).
- User testing: recruit professionals, have them complete the survey, review the generated recommendation, and capture qualitative feedback for prompt or heuristic adjustments.

## Next Steps
1. Build a Streamlit or React survey UI that consumes `GET /survey` and posts responses.
2. Expand analytics/export tooling for stored responses.
3. Add authentication + rate limiting before rolling out widely.
4. Iterate on prompts or fine-tune models based on real submissions.
