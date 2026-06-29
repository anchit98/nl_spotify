"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { GlassCard } from "@/components/ui";
import { ApiError, sendPmBuddyMessage } from "@/lib/api";
import type { PmBuddyChatTurn } from "@/lib/types";

const STARTER_PROMPTS = [
  "Why do users struggle to discover new music?",
  "What are the most common frustrations with recommendations?",
  "What listening behaviors are users trying to achieve?",
  "What causes users to repeatedly listen to the same content?",
  "Which user segments experience different discovery challenges?",
  "What unmet needs emerge consistently across reviews?",
];

function MessageBubble({ turn }: { turn: PmBuddyChatTurn }) {
  const isUser = turn.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-primary/15 text-on-surface border border-primary/30"
            : "glass-panel text-on-surface-variant border border-border-subtle"
        }`}
      >
        {!isUser && (
          <p className="text-[11px] uppercase tracking-wider text-primary mb-2 font-semibold">
            PM Buddy
          </p>
        )}
        {turn.content}
      </div>
    </div>
  );
}

export function PmBuddyChat() {
  const [messages, setMessages] = useState<PmBuddyChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const historyRef = useRef<PmBuddyChatTurn[]>([]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  useEffect(() => {
    historyRef.current = messages;
  }, [messages]);

  useEffect(() => {
    scrollToBottom(messages.length <= 1 ? "auto" : "smooth");
  }, [messages, loading, scrollToBottom]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);
    setLoading(true);
    const userTurn: PmBuddyChatTurn = { role: "user", content: trimmed };
    const prior = historyRef.current;
    setMessages([...prior, userTurn]);
    setInput("");

    try {
      const result = await sendPmBuddyMessage(trimmed, prior);
      setMessages((current) => [...current, { role: "assistant", content: result.reply }]);
    } catch (e) {
      setMessages(prior);
      setInput(trimmed);
      setError(e instanceof ApiError ? e.message : "Failed to get a response");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GlassCard className="flex flex-col flex-1 min-h-0 p-4 md:p-5">
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto space-y-4 pr-1 overscroll-contain">
        {messages.length === 0 ? (
          <div className="space-y-6 py-2">
            <div className="text-center">
              <span
                className="material-symbols-outlined text-5xl text-primary mb-3 block"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                psychology
              </span>
              <h2 className="text-[20px] font-semibold text-on-surface mb-2">
                Ask PM Buddy anything about discovery &amp; repetition
              </h2>
              <p className="text-[14px] text-text-muted max-w-lg mx-auto">
                I synthesize answers from public reviews plus latest Groq insights, solely focused on music discovery & repetitive listening behavior.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => void send(prompt)}
                  className="text-left text-[13px] px-4 py-2 rounded-full border border-border-subtle bg-surface-low hover:bg-surface-high hover:border-primary/40 text-on-surface-variant hover:text-on-surface transition-colors max-w-md"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((turn, i) => <MessageBubble key={`${turn.role}-${i}`} turn={turn} />)
        )}
        {loading && (
          <div className="flex items-center gap-2 text-text-muted text-[13px] pb-1">
            <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
            Synthesizing answer from review data…
          </div>
        )}
      </div>

      {error && (
        <p className="text-status-error text-[13px] mt-3 shrink-0">{error}</p>
      )}

      <form
        className="flex gap-2 border-t border-border-subtle pt-4 mt-4 shrink-0"
        onSubmit={(e) => {
          e.preventDefault();
          void send(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about repetitive listening, segments, or discovery barriers…"
          disabled={loading}
          className="flex-1 bg-surface-low border border-border-subtle rounded-full px-5 py-3 text-[15px] text-on-surface placeholder:text-text-muted focus:outline-none focus:border-primary/50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="h-12 w-12 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center disabled:opacity-50 hover:bg-primary transition-colors shrink-0"
          aria-label="Send message"
        >
          <span className="material-symbols-outlined">send</span>
        </button>
      </form>
    </GlassCard>
  );
}
