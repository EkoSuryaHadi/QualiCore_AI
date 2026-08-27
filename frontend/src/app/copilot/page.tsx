"use client";

import { FormEvent, useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Citation = { finding_code: string; severity: string; workstream: string; project_id?: string | null; project_code?: string | null; evidence: Record<string, string | number | boolean | null>; };
type CopilotResponse = { mode: string; scope: string; project_id?: string | null; question: string; answer: string; assurance_index: number; health_status: string; finding_count: number; recommended_actions: string[]; citations: Citation[]; suggested_questions: string[]; disclaimer: string; };
type ChatItem = { question: string; response: CopilotResponse; };

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
    api<{ suggested_questions: string[] }>("/copilot/suggestions").then((data) => setSuggestions(data.suggested_questions || [])).catch(() => {});
  }, []);

  async function ask(value?: string) {
    const prompt = (value ?? question).trim();
    if (!prompt || loading) return;
    setLoading(true); setError("");
    try {
      const response = await api<CopilotResponse>("/copilot/ask", { method: "POST", body: JSON.stringify({ question: prompt, project_id: projectId || null }) });
      setHistory((items) => [...items, { question: prompt, response }]);
      setQuestion("");
      if (response.suggested_questions?.length) setSuggestions(response.suggested_questions);
    } catch (err) { setError(err instanceof Error ? err.message : "Copilot could not answer the question"); }
    finally { setLoading(false); }
  }

  function submit(e: FormEvent) { e.preventDefault(); void ask(); }
  const selected = projects.find((project) => project.id === projectId);

  return (
    <AuthGuard><Shell>
      <div className="page-head"><div><p className="eyebrow">Grounded Project Intelligence</p><h1>QualiCore Copilot</h1><p className="muted">Ask assurance questions using live QualiCore records and auditable assurance findings.</p></div><div className="health-pill health-good">GROUNDED</div></div>

      <div className="card copilot-scope"><label><span className="muted small">Context Scope</span><select value={projectId} onChange={(e) => { setProjectId(e.target.value); setHistory([]); }}><option value="">Portfolio — All Projects</option>{projects.map((project) => <option value={project.id} key={project.id}>{project.code} — {project.name}</option>)}</select></label><div><span className="muted small">Current Context</span><strong>{selected ? `${selected.code} — ${selected.name}` : "Portfolio Assurance"}</strong></div></div>

      {!history.length ? <div className="card section-card copilot-welcome"><h2>What would you like to know?</h2><p className="muted">Start with one of these grounded assurance questions.</p><div className="copilot-suggestions">{suggestions.map((suggestion) => <button key={suggestion} className="secondary-btn" onClick={() => void ask(suggestion)}>{suggestion}</button>)}</div></div> : null}

      <div className="copilot-thread">{history.map((item, index) => <div className="copilot-turn" key={`${item.question}-${index}`}><div className="copilot-user"><strong>You</strong><p>{item.question}</p></div><div className="card copilot-answer"><div className="copilot-answer-head"><div><strong>QualiCore Copilot</strong><div className="muted small">{item.response.scope} · {item.response.finding_count} active findings</div></div><div className={`health-pill ${item.response.health_status === "GOOD" ? "health-good" : item.response.health_status === "ATTENTION" ? "health-attention" : "health-critical"}`}>{item.response.assurance_index}</div></div><div className="copilot-answer-text">{item.response.answer.split("\n").map((line, i) => <p key={i}>{line || <br />}</p>)}</div>{item.response.recommended_actions.length ? <div className="copilot-actions"><h3>Recommended Actions</h3>{item.response.recommended_actions.map((action, i) => <div className="priority-row" key={`${action}-${i}`}><span className="priority-index">{i + 1}</span><span>{action}</span></div>)}</div> : null}{item.response.citations.length ? <details className="copilot-evidence"><summary>Evidence trace · {item.response.citations.length} finding(s)</summary><div className="copilot-citations">{item.response.citations.map((citation) => <div className="copilot-citation" key={`${citation.finding_code}-${citation.project_id}`}><div><span className={`severity severity-${citation.severity.toLowerCase()}`}>{citation.severity}</span> <strong>{citation.finding_code}</strong></div><div className="muted small">{citation.project_code || "Portfolio"} · {citation.workstream}</div><code>{JSON.stringify(citation.evidence)}</code></div>)}</div></details> : null}<div className="muted small copilot-disclaimer">{item.response.disclaimer}</div></div></div>)}</div>

      {error ? <div className="error">{error}</div> : null}
      <form className="card copilot-composer" onSubmit={submit}><textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about assurance risk, NCR priorities, vendor exposure, weekly meeting focus, or management summary..." rows={3} /><div className="copilot-composer-actions"><span className="muted small">Answers are grounded in current QualiCore records.</span><button className="btn-action" type="submit" disabled={loading || !question.trim()}>{loading ? "Analyzing..." : "Ask Copilot"}</button></div></form>

      <style jsx global>{`
        .copilot-scope{display:grid;grid-template-columns:minmax(280px,1fr) 1fr;gap:18px;align-items:end}.copilot-scope label,.copilot-scope>div{display:flex;flex-direction:column;gap:7px}.copilot-scope select{padding:11px 12px;border:1px solid #ccd5e0;border-radius:9px;background:white;color:#152235}.copilot-welcome h2{margin-top:0}.copilot-suggestions{display:flex;flex-wrap:wrap;gap:10px}.copilot-suggestions .secondary-btn{font-weight:600}.copilot-thread{display:flex;flex-direction:column;gap:20px;margin-top:18px}.copilot-turn{display:flex;flex-direction:column;gap:8px}.copilot-user{align-self:flex-end;max-width:72%;background:#17385f;color:white;border-radius:14px 14px 3px 14px;padding:12px 15px}.copilot-user p{margin:5px 0 0}.copilot-answer{max-width:940px;border-left:4px solid #1565c0}.copilot-answer-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.copilot-answer-text{line-height:1.58;margin-top:14px}.copilot-answer-text p{margin:6px 0}.copilot-actions{border-top:1px solid #edf1f5;margin-top:18px;padding-top:14px}.copilot-actions h3{margin:0 0 10px}.priority-row{display:flex;gap:10px;align-items:flex-start;padding:9px 0}.priority-index{display:grid;place-items:center;flex:0 0 25px;height:25px;border-radius:50%;background:#edf5ff;color:#1554a0;font-size:12px;font-weight:800}.copilot-evidence{margin-top:16px;border-top:1px solid #edf1f5;padding-top:12px}.copilot-evidence summary{cursor:pointer;font-weight:700;color:#315c87}.copilot-citations{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:12px}.copilot-citation{background:#f8fafc;border:1px solid #e2e7ee;border-radius:9px;padding:11px;display:flex;flex-direction:column;gap:7px;overflow:hidden}.copilot-citation code{white-space:pre-wrap;overflow-wrap:anywhere;color:#52657a;font-size:11px}.copilot-disclaimer{border-top:1px solid #edf1f5;margin-top:16px;padding-top:12px}.copilot-composer{position:sticky;bottom:14px;margin-top:20px;box-shadow:0 12px 30px #16283d18}.copilot-composer textarea{width:100%;resize:vertical;border:0;outline:0;font:inherit;color:#152235}.copilot-composer-actions{display:flex;justify-content:space-between;align-items:center;gap:14px;border-top:1px solid #edf1f5;padding-top:12px}.copilot-composer .btn-action{min-width:130px}@media(max-width:800px){.copilot-scope{grid-template-columns:1fr}.copilot-user{max-width:90%}.copilot-citations{grid-template-columns:1fr}}@media(max-width:520px){.copilot-composer-actions{align-items:stretch;flex-direction:column}.copilot-composer .btn-action{width:100%}}
      `}</style>
    </Shell></AuthGuard>
  );
}
