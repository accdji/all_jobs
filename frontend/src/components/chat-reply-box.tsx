"use client";

import { useState } from "react";
import { Mic, Paperclip, SendHorizonal } from "lucide-react";

type ChatReply = {
  intent: string;
  draft_reply: string;
  suggested_action: string;
  confidence: number;
};

export function ChatReplyBox() {
  const [input, setInput] = useState("");
  const [reply, setReply] = useState<ChatReply | null>(null);
  const [pending, setPending] = useState(false);

  async function generateReply() {
    if (!input.trim()) return;
    setPending(true);
    try {
      const response = await fetch(`/api/chat/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = (await response.json()) as ChatReply;
      setReply(data);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="rounded-md bg-[var(--color-soft)] p-4">
      <div className="flex items-center gap-3 rounded-md bg-white px-3 py-3 ring-1 ring-black/4">
        <Paperclip className="h-4 w-4 text-slate-400" />
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
          placeholder="输入 HR 的问题或你想发出的消息"
        />
        <Mic className="h-4 w-4 text-slate-400" />
        <button onClick={() => void generateReply()} className="rounded-md bg-[var(--color-primary)] p-3 text-white">
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>

      {pending ? <p className="mt-3 text-sm text-[var(--color-muted)]">正在生成回复...</p> : null}

      {reply ? (
        <div className="mt-4 rounded-md bg-white p-4 ring-1 ring-black/4">
          <div className="flex flex-wrap gap-3 text-xs text-[var(--color-muted)]">
            <span>意图：{reply.intent}</span>
            <span>动作：{reply.suggested_action}</span>
            <span>置信度：{reply.confidence}</span>
          </div>
          <p className="mt-3 text-sm leading-7 text-[var(--color-ink)]">{reply.draft_reply}</p>
        </div>
      ) : null}
    </div>
  );
}
