"use client";

import Image from "next/image";

const agents = [
  { name: "Claude", logo: "claude-color" },
  { name: "Codex / OpenAI", logo: "openai", monochrome: true },
  { name: "OpenCode", logo: "opencode", monochrome: true },
  { name: "Antigravity", logo: "antigravity-color" },
  { name: "Gemini", logo: "gemini-color" },
  { name: "Grok", logo: "grok", monochrome: true },
  { name: "DeepSeek", logo: "deepseek-color" },
  { name: "Qwen", logo: "qwen-color" },
  { name: "Mistral", logo: "mistral-color" },
  { name: "Kimi", logo: "kimi", monochrome: true },
];

export default function AgentCarousel() {
  return <div className="agent-strip section">
    <span>AT HOME IN YOUR AGENT</span>
    <div className="agent-carousel" role="region" aria-label="AI agents and model providers">
      <div className="agent-carousel-window" tabIndex={0} aria-label="Logo carousel. Focus or hover to pause.">
        <div className="agent-carousel-track">
          {[false, true].map(duplicate => <ul className="agent-carousel-group" key={String(duplicate)} aria-hidden={duplicate || undefined}>
            {agents.map(agent => <li className="agent-carousel-item" key={agent.name}>
              <Image className={agent.monochrome ? "agent-logo-monochrome" : undefined} src={`/ai-logos/${agent.logo}.svg`} alt="" width={30} height={30} loading="eager" />
              <span>{agent.name}</span>
            </li>)}
          </ul>)}
        </div>
      </div>
    </div>
    <p>Your agent. Your choice.</p>
  </div>;
}
