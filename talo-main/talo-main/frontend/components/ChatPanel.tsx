"use client";

import { useState } from "react";
import { askQuestion, type DriftResults } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPanel({
  driftResults,
  normalizedRows,
}: {
  driftResults: DriftResults;
  normalizedRows: unknown[];
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const question = input.trim();
    if (!question || busy) return;

    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setBusy(true);
    setError(null);

    try {
      const answer = await askQuestion(question, driftResults, normalizedRows);
      setMessages((m) => [...m, { role: "assistant", content: answer }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="border border-rule bg-white/60 p-6">
      <p className="font-mono text-xs uppercase tracking-widest text-muted mb-1">Step 3</p>
      <h2 className="font-serif text-xl font-semibold text-ink mb-4">Ask about this data</h2>

      <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-muted italic">
            Try: &ldquo;why did drift spike in the current period&rdquo; or &ldquo;which transactions are riskiest&rdquo;
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block max-w-[85%] text-sm px-3 py-2 ${
                m.role === "user" ? "bg-ink text-paper" : "bg-paper text-ink border border-rule"
              }`}
            >
              {m.content}
            </span>
          </div>
        ))}
        {error && <p className="text-sm text-severe">{error}</p>}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask a question about this report"
          className="flex-1 border border-rule bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-ink"
        />
        <button
          onClick={send}
          disabled={busy || !input.trim()}
          className="bg-ink text-paper px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          {busy ? "\u2026" : "Ask"}
        </button>
      </div>
    </div>
  );
}
