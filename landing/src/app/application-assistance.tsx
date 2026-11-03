"use client";

import { ArrowUpRight, Check, Terminal } from "lucide-react";
import CopyButton from "./copy-button";

export const APPLY_PROMPT = "Use cv-apply. Help me choose a saved application, CV, and cover letter, then fill the application form using my confirmed profile. Save my progress, check the filled answers and attachments, and stop for my review. I'll submit it myself.";

export default function ApplicationAssistance() {
  return <section className="apply-section section" id="apply" aria-labelledby="apply-title">
    <div className="section-heading">
      <div><span className="eyebrow">APPLICATION FORM ASSISTANCE</span><h2 id="apply-title">Apply with your agent.</h2></div>
    </div>
    <div className="apply-workflow">
      <ol className="apply-steps">
        <li><span className="step-number" aria-hidden="true">01</span><div><h3>Pick an application</h3><p>Choose a saved job, CV, and cover letter.</p></div></li>
        <li><span className="step-number" aria-hidden="true">02</span><div><h3>Ask your agent</h3><p>Copy the prompt into your browser-capable agent.</p></div></li>
        <li><span className="step-number" aria-hidden="true">03</span><div><h3>Review and submit</h3><p>Check the answers and attachments, then submit yourself. Tell your agent to update the tracker.</p></div></li>
      </ol>
      <div className="apply-prompt-panel">
        <div className="prompt-window">
          <div className="prompt-window-header"><span><Terminal size={13} />Try asking your agent</span><CopyButton text={APPLY_PROMPT} label="Copy application assistance prompt" caption="Copy prompt" /></div>
          <blockquote><span aria-hidden="true">›</span>{APPLY_PROMPT}</blockquote>
          <div className="prompt-result"><Check size={13} />Progress saved. The final click is yours.</div>
        </div>
      </div>
    </div>
    <div className="apply-notes"><a className="text-link" href="https://github.com/yabswannalearn/CV-Tailor/blob/main/docs/application_forms.md" target="_blank" rel="noreferrer">Read the application guide<ArrowUpRight size={14} /></a></div>
  </section>;
}
