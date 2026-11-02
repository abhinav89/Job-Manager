"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

export default function CopyButton({ text, label, caption = "Copy" }: { text: string; label: string; caption?: string }) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true); setFailed(false);
      window.setTimeout(() => setCopied(false), 2200);
    } catch { setFailed(true); }
  }
  return <div className="copy-control"><button type="button" className="copy-button" aria-label={label} onClick={() => void copy()}>{copied ? <Check size={14} /> : <Copy size={14} />}{copied ? "Copied" : caption}</button><span className="sr-only" role="status">{copied ? "Copied to clipboard." : failed ? "Clipboard unavailable. Select and copy the text below." : ""}</span>{failed && <><span className="copy-error">Select the text below to copy.</span><textarea className="copy-fallback" aria-label={`${label}: text to copy`} readOnly value={text} rows={6} onFocus={event => event.currentTarget.select()} /></>}</div>;
}
