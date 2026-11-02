"use client";

import { ArrowUpRight, Check, Terminal } from "lucide-react";
import CopyButton from "./copy-button";

export const APPLY_PROMPT = "Use cv-apply for application #42. Help me choose my CV and cover letter, then fill the application form using my confirmed profile. Save my progress, check the filled answers and attachments, and stop for my review. I'll submit it myself.";

export default function ApplicationAssistance() {
  return <section className="apply-section section" id="apply" aria-labelledby="apply-title">
    <div className="section-heading">
      <div><span className="eyebrow">APPLICATION FORM ASSISTANCE</span><h2 id="apply-title">Less retyping.<br />More time to review.</h2></div>
      <p>Let your agent fill an employer’s form from your confirmed profile and selected documents. It checks the answers and saves your place. You review and submit.</p>
    </div>
    <div className="apply-workflow">
      <ol className="apply-steps">
        <li><span className="step-number" aria-hidden="true">01</span><div><h3>Choose your application</h3><p>Save the job in your tracker and choose the CV and cover letter you want to use.</p></div></li>
        <li><span className="step-number" aria-hidden="true">02</span><div><h3>Ask your agent</h3><p>Copy the prompt, replace 42 with your application’s ID, and paste it into a browser-capable agent in the CV Tailor repository.</p></div></li>
        <li><span className="step-number" aria-hidden="true">03</span><div><h3>Review, then submit</h3><p>Check the filled answers and attachments. Handle sign-in or CAPTCHA when needed, then submit yourself. Tell your agent you submitted to update the tracker.</p></div></li>
      </ol>
      <div className="apply-prompt-panel">
        <div className="prompt-window">
          <div className="prompt-window-header"><span><Terminal size={13} />Try asking your agent</span><CopyButton text={APPLY_PROMPT} label="Copy application assistance prompt" caption="Copy prompt" /></div>
          <blockquote><span aria-hidden="true">›</span>{APPLY_PROMPT}</blockquote>
          <div className="prompt-result"><Check size={13} />Progress saved. The final click is yours.</div>
        </div>
        <p className="apply-dashboard-path"><strong>Using the dashboard?</strong> Choose Work with your CLI agent → Assist with application → your saved application → Copy agent prompt.</p>
      </div>
    </div>
    <div className="apply-notes"><p>Uses your agent’s browser tools. Without browser access, it prepares answers to copy. Saved checkpoints let you pick up where you left off.</p><a className="text-link" href="https://github.com/yabswannalearn/CV-Tailor/blob/main/docs/application_forms.md" target="_blank" rel="noreferrer">Read the application guide<ArrowUpRight size={14} /></a></div>
  </section>;
}
