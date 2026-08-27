"use client";

import { FormEvent, useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Citation = {
  finding_code: string;
  severity: string;
  workstream: string;
  project_id?: string | null;
  project_code?: string | null;
  evidence: Record<string, string | number | boolean | null>;
};
type CopilotResponse = {
  mode: string;
  scope: string;
  project_id?: string | null;
  question: string;
  answer: string;
  assurance_index: number;
  health_status: string;
  finding_count: number;
  recommended_actions: string[];
  citations: Citation[];
  suggested_questions: string[];
  disclaimer: string;
};

type ChatItem = {
  question: string;
  response: CopilotResponse;
};

export default function CopilotPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [question, setQuestion] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [history, setHistory] = useState<ChatItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setProjectId(params.get("project_id") || "");
    api<Project[]>("/projects").then(setProjects).catch(() => {});
    api<{ suggested_questions: string[] }>("/copilot/suggestions")
      .then((data) => setSuggestions(data.suggested_questions || []))
      .catch(() => {});
  }, []);

  async function ask(value?: string) {
    const prompt = (value ?? question).trim();
    if (!prompt || loading) return;
    setLoading(true);
    setError("");
    try {
      const response = await api<CopilotResponse>("/copilot/ask", {
        method: "POST",
        body: JSON.stringify({ question: prompt, project_id: projectId || null }),
      });
      setHistory((items) => [...items, { question: prompt, response }]);
      setQuestion("");
      if (response.suggested_questions?.length) setSuggestions(response.suggested_questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Copilot could not answer the question");
    } finally {
      setLoading(false);
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    void ask();
  }

  const selected = projects.find((project) => project.id === projectId);

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Grounded Project Intelligence</p>
            <h1>QualiCore Copilot</h1>
            <p className="muted">Ask assurance questions using live QualiCore records and auditable assurance findings.</p>
          </div>
          <div className="health-pill health-good">GROUNDED</div>
        </div>

        <div className="card copilot-scope">
          <label>
            <span className="muted small">Context Scope</span>
            <select value={projectId} onChange={(e) => { setProjectId(e.target.value); setHistory([]); }}>
              <option value="">Portfolio — All Projects</option>
              {projects.map((project) => <option value={project.id} key={project.id}>{project.code} — {project.name}</option>)}
            </select>
          </label>
          <div>
            <span className="muted small">Current Context</span>
            <strong>{selected ? `${selected.code} — ${selected.name}` : "Portfolio Assurance"}</strong>
          </div>
        </div>

        {!history.length ? (
          <div className="card section-card copilot-welcome">
            <h2>What would you like to know?</h2>
            <p className="muted">Start with one of these grounded assurance questions.</p>
            <div className="copilot-suggestions">
              {suggestions.map((suggestion) => (
                <button key={suggestion} className="secondary-btn" onClick={() => void ask(suggestion)}>{suggestion}</button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="copilot-thread">
          {history.map((item, index) => (
            <div className="copilot-turn" key={`${item.question}-${index}`}>
              <div className="copilot-user"><strong>You</strong><p>{item.question}</p></div>
              <div className="card copilot-answer">
                <div className="copilot-answer-head">
                  <div><strong>QualiCore Copilot</strong><div className="muted small">{item.response.scope} · {item.response.finding_count} active findings</div></div>
                  <div className={`health-pill ${item.response.health_status === "GOOD" ? "health-good" : item.response.health_status === "ATTENTION" ? "health-attention" : "health-critical"}`}>{item.response.assurance_index}</div>
                </div>
                <div className="copilot-answer-text">{item.response.answer.split("\n").map((line, i) => <p key={i}>{line || <br />}</p>)}</div>

                {item.response.recommended_actions.length ? (
                  <div className="copilot-actions">
                    <h3>Recommended Actions</h3>
                    {item.response.recommended_actions.map((action, i) => <div className="priority-row" key={`${action}-${i}`}><span className="priority-index">{i + 1}</span><span>{action}</span></div>)}
                  </div>
                ) : null}

                {item.response.citations.length ? (
                  <details className="copilot-evidence">
                    <summary>Evidence trace · {item.response.citations.length} finding(s)</summary>
                    <div className="copilot-citations">
                      {item.response.citations.map((citation) => (
                        <div className="copilot-citation" key={`${citation.finding_code}-${citation.project_id}`}>
                          <div><span className={`severity severity-${citation.severity.toLowerCase()}`}>{citation.severity}</span> <strong>{citation.finding_code}</strong></div>
                          <div className="muted small">{citation.project_code || "Portfolio"} · {citation.workstream}</div>
                          <code>{JSON.stringify(citation.evidence)}</code>
                        </div>
                      ))}
                    </div>
                  </details>
                ) : null}

                <div className="muted small copilot-disclaimer">{item.response.disclaimer}</div>
              </div>
            </div>
          ))}
        </div>

        {error ? <div className="error">{error}</div> : null}

        <form className="card copilot-composer" onSubmit={submit}>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about assurance risk, NCR priorities, vendor exposure, weekly meeting focus, or management summary..." rows={3} />
          <div className="copilot-composer-actions">
            <span className="muted small">Answers are grounded in current QualiCore records.</span>
            <button className="btn-action" type="submit" disabled={loading || !question.trim()}>{loading ? "Analyzing..." : "Ask Copilot"}</button>
          </div>
        </form>
      </Shell>
    </AuthGuard>
  );
}
