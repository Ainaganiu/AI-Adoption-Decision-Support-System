from __future__ import annotations

"""HTML for the lightweight survey web UI."""

import json
from typing import Any, Dict

WEBAPP_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Adoption DSS</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap"
    rel="stylesheet"
  />
  <style>
    :root {
      color-scheme: light;
      --ink: #1b1a17;
      --muted: #5a5a53;
      --paper: #f5f1ea;
      --paper-strong: #e9e3d8;
      --accent: #d96b4a;
      --accent-dark: #b3563c;
      --leaf: #2f3f3a;
      --shadow: rgba(27, 26, 23, 0.12);
      --stroke: rgba(27, 26, 23, 0.18);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 20% 10%, rgba(217, 107, 74, 0.2), transparent 40%),
        radial-gradient(circle at 80% 0%, rgba(47, 63, 58, 0.18), transparent 40%),
        linear-gradient(160deg, #f7f2eb 0%, #efe7db 45%, #f4efe5 100%);
      color: var(--ink);
      min-height: 100vh;
    }

    .canvas {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
    }

    .canvas::before,
    .canvas::after {
      content: "";
      position: absolute;
      border-radius: 999px;
      background: rgba(217, 107, 74, 0.15);
      filter: blur(0px);
    }

    .canvas::before {
      width: 380px;
      height: 380px;
      top: 8%;
      left: -60px;
      background: rgba(217, 107, 74, 0.18);
    }

    .canvas::after {
      width: 320px;
      height: 320px;
      bottom: 8%;
      right: -40px;
      background: rgba(47, 63, 58, 0.18);
    }

    main {
      position: relative;
      z-index: 1;
      max-width: 1200px;
      margin: 0 auto;
      padding: 48px 24px 64px;
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
      gap: 28px;
    }

    header {
      grid-column: 1 / -1;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    h1 {
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      font-size: clamp(2rem, 3vw, 3.2rem);
      letter-spacing: -0.02em;
      margin: 0;
    }

    .subtitle {
      font-size: 1.05rem;
      color: var(--muted);
      max-width: 720px;
      line-height: 1.6;
    }

    .status-bar {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      font-size: 0.9rem;
      color: var(--leaf);
    }

    .status-pill {
      background: rgba(47, 63, 58, 0.12);
      padding: 6px 12px;
      border-radius: 999px;
      border: 1px solid rgba(47, 63, 58, 0.2);
    }

    .panel {
      background: var(--paper);
      border-radius: 20px;
      box-shadow: 0 24px 50px -30px rgba(27, 26, 23, 0.5);
      border: 1px solid var(--stroke);
    }

    .form-panel {
      padding: 28px;
    }

    .result-panel {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      position: sticky;
      top: 24px;
      height: fit-content;
    }

    .section-card {
      border: 1px solid rgba(27, 26, 23, 0.1);
      background: #fbf9f4;
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
      opacity: 0;
      transform: translateY(14px);
      animation: rise 0.5s ease forwards;
    }

    @keyframes rise {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .section-title {
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      font-size: 1.2rem;
      margin: 0 0 6px;
    }

    .section-desc {
      color: var(--muted);
      margin: 0 0 16px;
      font-size: 0.95rem;
    }

    .question {
      margin-bottom: 16px;
    }

    .question label {
      font-weight: 600;
      display: block;
      margin-bottom: 8px;
    }

    .input-grid {
      display: grid;
      gap: 10px;
    }

    .choice {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      background: #f2ece2;
      border-radius: 12px;
      border: 1px solid rgba(27, 26, 23, 0.1);
    }

    input[type="text"],
    input[type="email"],
    textarea,
    select {
      width: 100%;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(27, 26, 23, 0.2);
      background: #fffdf9;
      font-family: inherit;
      font-size: 0.98rem;
    }

    textarea {
      min-height: 90px;
      resize: vertical;
    }

    .submit-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 20px;
    }

    button {
      appearance: none;
      border: none;
      background: var(--accent);
      color: white;
      padding: 12px 20px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
      box-shadow: 0 18px 30px -20px rgba(217, 107, 74, 0.7);
    }

    button:hover { transform: translateY(-1px); background: var(--accent-dark); }
    button:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; }

    .error {
      color: #b63e2e;
      font-size: 0.9rem;
      margin-top: 6px;
    }

    .result-title {
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      font-size: 1.1rem;
      margin: 0;
    }

    .result-card {
      background: #fffdf9;
      border-radius: 14px;
      padding: 14px;
      border: 1px solid rgba(27, 26, 23, 0.12);
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .result-card h3 {
      margin: 0 0 8px;
      font-size: 1rem;
    }

    .muted {
      color: var(--muted);
    }

    @media (max-width: 980px) {
      main {
        grid-template-columns: 1fr;
      }

      .result-panel {
        position: static;
      }
    }
  </style>
</head>
<body>
  <div class="canvas"></div>
  <main>
    <header>
      <h1>AI Adoption Decision Support System</h1>
      <p class="subtitle" id="surveyIntro">
        Loading survey definition...
      </p>
      <div class="status-bar">
        <div class="status-pill">Powered by FastAPI + MySQL</div>
        <div class="status-pill">Optional Hugging Face insights</div>
      </div>
    </header>
    <section class="panel form-panel">
      <form id="surveyForm">
        <div id="formSections"></div>
        <div class="submit-row">
        <div class="muted" id="formStatus">Complete the survey and submit to receive recommendations.</div>
          <button type="submit" id="submitBtn">Submit Survey</button>
        </div>
        <div class="error" id="formError"></div>
      </form>
    </section>
    <aside class="panel result-panel">
      <h2 class="result-title">Recommendation</h2>
      <div class="result-card" id="resultCard">
        <div class="muted">Submit the survey to see the recommendation summary.</div>
      </div>
    </aside>
  </main>
  <script>
    window.SURVEY_DEFINITION = __SURVEY_JSON__;

    const surveyForm = document.getElementById("surveyForm");
    const formSections = document.getElementById("formSections");
    const formError = document.getElementById("formError");
    const submitBtn = document.getElementById("submitBtn");
    const resultCard = document.getElementById("resultCard");
    const surveyIntro = document.getElementById("surveyIntro");

    const questionMap = new Map();

    const labelize = (value) => value.replace(/_/g, " ").replace(/\\b\\w/g, (c) => c.toUpperCase());

    const isLongText = (id) =>
      ["additional_notes", "safeguards_notes", "ai_tasks_other"].includes(id);

    const buildChoices = (q, type) => {
      const wrapper = document.createElement("div");
      wrapper.className = "input-grid";
      const options = q.options || [];
      options.forEach((opt) => {
        const choice = document.createElement("label");
        choice.className = "choice";
        const input = document.createElement("input");
        input.type = type;
        input.name = q.id;
        input.value = opt.value || opt;
        choice.appendChild(input);
        const text = document.createElement("span");
        text.textContent = opt.label || labelize(opt);
        choice.appendChild(text);
        wrapper.appendChild(choice);
      });
      return wrapper;
    };

    const buildQuestion = (q) => {
      questionMap.set(q.id, q);
      const container = document.createElement("div");
      container.className = "question";

      const label = document.createElement("label");
      label.textContent = q.prompt;
      container.appendChild(label);

      if (q.type === "text") {
        const field = isLongText(q.id) ? document.createElement("textarea") : document.createElement("input");
        field.dataset.field = q.id;
        if (!isLongText(q.id)) {
          field.type = q.id === "email" ? "email" : "text";
        }
        if (q.required) {
          field.required = true;
        }
        container.appendChild(field);
      } else if (q.type === "boolean") {
        const wrapper = document.createElement("div");
        wrapper.className = "input-grid";
        ["true", "false"].forEach((value) => {
          const choice = document.createElement("label");
          choice.className = "choice";
          const input = document.createElement("input");
          input.type = "radio";
          input.name = q.id;
          input.value = value;
          if (q.default === true && value === "true") {
            input.checked = true;
          }
          choice.appendChild(input);
          const text = document.createElement("span");
          text.textContent = value === "true" ? "Yes" : "No";
          choice.appendChild(text);
          wrapper.appendChild(choice);
        });
        container.appendChild(wrapper);
      } else if (q.type === "multiple_choice") {
        container.appendChild(buildChoices(q, "radio"));
      } else if (q.type === "likert") {
        container.appendChild(buildChoices(q, "radio"));
      } else if (q.type === "checkbox") {
        container.appendChild(buildChoices(q, "checkbox"));
      }

      return container;
    };

    const buildSection = (section, index) => {
      const card = document.createElement("div");
      card.className = "section-card";
      card.style.animationDelay = `${index * 0.08}s`;

      const title = document.createElement("h2");
      title.className = "section-title";
      title.textContent = section.title;
      card.appendChild(title);

      if (section.description) {
        const desc = document.createElement("p");
        desc.className = "section-desc";
        desc.textContent = section.description;
        card.appendChild(desc);
      }

      section.questions.forEach((q) => {
        card.appendChild(buildQuestion(q));
      });

      return card;
    };

    const gatherSubmission = () => {
      const payload = {};
      const errors = [];

      questionMap.forEach((q) => {
        if (q.type === "text") {
          const field = surveyForm.querySelector(`[data-field="${q.id}"]`);
          let value = field.value.trim();
          if (!value) {
            value = null;
          }
          if (q.required && !value) {
            errors.push(`"${q.prompt}" is required.`);
          }
          payload[q.id] = value;
        } else if (q.type === "boolean") {
          const selected = surveyForm.querySelector(`input[name="${q.id}"]:checked`);
          if (!selected) {
            if (q.required) {
              errors.push(`"${q.prompt}" is required.`);
            }
            payload[q.id] = null;
          } else {
            payload[q.id] = selected.value === "true";
          }
        } else if (q.type === "multiple_choice" || q.type === "likert") {
          const selected = surveyForm.querySelector(`input[name="${q.id}"]:checked`);
          if (!selected) {
            if (q.required) {
              errors.push(`"${q.prompt}" is required.`);
            }
            payload[q.id] = null;
          } else {
            payload[q.id] = selected.value;
          }
        } else if (q.type === "checkbox") {
          const selected = Array.from(
            surveyForm.querySelectorAll(`input[name="${q.id}"]:checked`)
          ).map((input) => input.value);
          if (q.required && selected.length === 0) {
            errors.push(`"${q.prompt}" requires at least one selection.`);
          }
          payload[q.id] = selected;
        }
      });

      return { payload, errors };
    };

    const TASK_LABELS = {
      data_analysis: "Data analysis & reporting",
      customer_support: "Customer support & success",
      workflow_automation: "Workflow / process automation",
      forecasting: "Forecasting & planning",
      quality_assurance: "Quality assurance",
      decision_support: "Decision support & insights",
      innovation_research: "Innovation & research",
      other: "Other (please specify)",
    };

    const SAFEGUARD_LABELS = {
      transparency: "Transparency",
      data_privacy: "Data privacy",
      accountability: "Accountability",
      human_in_the_loop: "Human-in-the-loop",
      audit_trail: "Audit trails",
      governance_policy: "Governance policy",
    };

    const CONCERN_LABELS = {
      job_loss: "Job loss",
      security_risks: "Security risks",
      privacy_issues: "Privacy issues",
      lack_of_control: "Lack of control",
      ethical_bias: "Ethical bias",
    };

    const mapLabels = (values, mapping) => {
      if (!Array.isArray(values)) {
        return [];
      }
      return values
        .map((value) => mapping[value] || String(value).replace(/_/g, " "))
        .filter((value) => value);
    };

    const normalizeRiskAssessment = (text) => {
      if (!text) {
        return "";
      }
      let output = String(text);
      Object.entries(CONCERN_LABELS).forEach(([key, label]) => {
        output = output.replaceAll(key, label);
      });
      return output;
    };

    const renderResult = (data) => {
      const recommendation = data.recommendation;
      const responseId = data.response_id;
      if (!recommendation) {
        resultCard.innerHTML = `
          <h3>Submission saved</h3>
          <p class="muted">Response ID: ${responseId}</p>
          <p>No recommendation was generated (opted out).</p>
        `;
        return;
      }

      const helpfulTasks = mapLabels(recommendation.helpful_tasks, TASK_LABELS);
      const safeguards = mapLabels(recommendation.safeguards, SAFEGUARD_LABELS);
      const riskAssessment = normalizeRiskAssessment(recommendation.risk_assessment);

      resultCard.innerHTML = `
        <h3>${recommendation.adoption_decision}</h3>
        <p><strong>Helpful tasks:</strong> ${helpfulTasks.join(", ") || "None"}</p>
        <p><strong>Risk assessment:</strong> ${riskAssessment}</p>
        <p><strong>Safeguards:</strong> ${safeguards.join(", ") || "None"}</p>
        <p><strong>Confidence:</strong> ${(recommendation.confidence * 100).toFixed(0)}%</p>
        <p class="muted">Response ID: ${responseId}</p>
      `;
    };

    const showError = (message) => {
      formError.textContent = message;
    };

    const setBusy = (busy) => {
      submitBtn.disabled = busy;
      submitBtn.textContent = busy ? "Submitting..." : "Submit Survey";
    };

    const scaleLikert = (value) => {
      const map = {
        strongly_agree: 100,
        agree: 75,
        neutral: 50,
        disagree: 25,
        strongly_disagree: 0,
      };
      return map[value] ?? 50;
    };

    const scaleConcern = (value) => {
      const map = {
        strongly_agree: 0,
        agree: 25,
        neutral: 50,
        disagree: 75,
        strongly_disagree: 100,
      };
      return map[value] ?? 50;
    };

    const computeReadinessScore = (payload) => {
      let score = 0;
      score += scaleLikert(payload.openness_to_ai) * 0.35;
      score += (payload.is_familiar_with_ai ? 15 : 0);
      score += Math.min((payload.expected_benefits || []).length * 4, 24);
      score += Math.min((payload.ai_tasks || []).length * 3, 21);
      score -= Math.min((payload.concerns || []).length * 3, 15);
      score += scaleConcern(payload.job_replacement_concern) * 0.15;
      score += Math.min((payload.safeguards_needed || []).length * 2, 10);
      return Math.max(0, Math.min(100, Math.round(score)));
    };

    const renderReadiness = (payload, data) => {
      const score = data?.readiness_score ?? computeReadinessScore(payload);
      return `<p><strong>AI readiness score:</strong> ${score}%</p>`;
    };

    surveyForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      showError("");
      const { payload, errors } = gatherSubmission();
      if (errors.length) {
        showError(errors[0]);
        return;
      }
      setBusy(true);
      try {
        const res = await fetch("/survey/responses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const contentType = res.headers.get("content-type") || "";
        const isJson = contentType.includes("application/json");
        if (!res.ok) {
          let message = "Submission failed";
          if (isJson) {
            const err = await res.json();
            message = err.detail || message;
          } else {
            const text = await res.text();
            message = text || message;
          }
          throw new Error(message);
        }
        const data = isJson ? await res.json() : null;
        if (!data) {
          throw new Error("Unexpected response from server.");
        }
        renderResult(data);
        resultCard.insertAdjacentHTML("afterbegin", renderReadiness(payload, data));
      } catch (err) {
        showError(err.message || "Unable to submit survey.");
      } finally {
        setBusy(false);
      }
    });

    const renderSurvey = (definition) => {
      surveyIntro.textContent = definition.introduction || "Complete the survey.";
      formSections.innerHTML = "";
      definition.sections.forEach((section, index) => {
        formSections.appendChild(buildSection(section, index));
      });
    };

    const loadSurvey = async () => {
      try {
        if (window.SURVEY_DEFINITION) {
          renderSurvey(window.SURVEY_DEFINITION);
          return;
        }
        const res = await fetch("/survey");
        if (!res.ok) {
          throw new Error("Survey fetch failed");
        }
        const definition = await res.json();
        renderSurvey(definition);
      } catch (err) {
        surveyIntro.textContent = "Unable to load survey definition.";
      }
    };

    loadSurvey();
  </script>
</body>
</html>
"""


def render_webapp_html(survey_definition: Dict[str, Any]) -> str:
    """Render the web UI HTML with an embedded survey definition."""

    survey_json = json.dumps(survey_definition, ensure_ascii=True)
    return WEBAPP_TEMPLATE.replace("__SURVEY_JSON__", survey_json)
