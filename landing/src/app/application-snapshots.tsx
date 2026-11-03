import { ArrowUpRight, Check, FileText, Terminal } from "lucide-react";
import CopyButton from "./copy-button";
import styles from "./application-snapshots.module.css";

export const SNAPSHOT_PROMPT = "Use cv-snapshot to create a snapshot of my job applications from my local CV Tailor database. Show the current status counts and save the chart, HTML report, and source JSON locally. Leave my application records unchanged.";

const example = [
  { status: "Saved", count: 6, color: "#8b969a" },
  { status: "Applied", count: 10, color: "#5487b5" },
  { status: "Interview", count: 4, color: "#3b9a91" },
  { status: "Offer", count: 1, color: "#8b9f50" },
  { status: "Rejected", count: 3, color: "#d88276" },
];
const total = example.reduce((sum, item) => sum + item.count, 0);

function SnapshotPreview() {
  const height = 416;
  const usable = height - 48 - (example.length - 1) * 36;
  const scale = usable / total;
  const sourceTop = (height - usable) / 2;
  return <figure className={styles.preview}>
    <div className={styles.previewHeader}><span><span className={styles.dot} />Application flow</span><span>Illustrative data</span></div>
    <div className={styles.chartScroll} tabIndex={0} role="region" aria-label="Sample snapshot chart; scroll horizontally on small screens">
      <svg viewBox={`0 0 760 ${height}`} role="img" aria-labelledby="snapshot-chart-title" aria-describedby="snapshot-chart-description">
        <title id="snapshot-chart-title">Sample application snapshot</title>
        <desc id="snapshot-chart-description">24 sample applications: 6 Saved, 10 Applied, 4 Interview, 1 Offer, and 3 Rejected. Each application appears once at its current status.</desc>
        <text x="18" y={height / 2 - 12} className={styles.chartLabel}>Applications</text>
        <text x="18" y={height / 2 + 30} className={styles.total}>{total}</text>
        <rect x="142" y={sourceTop} width="8" height={usable} rx="2" fill="#a4afb2" />
        {example.map((item, index) => {
          const offset = example.slice(0, index).reduce((sum, previous) => sum + previous.count * scale, 0);
          const y0 = sourceTop + offset;
          const y1 = 24 + offset + index * 36;
          const thickness = item.count * scale;
          const path = `M150 ${y0} C305 ${y0} 385 ${y1} 546 ${y1} L546 ${y1 + thickness} C385 ${y1 + thickness} 305 ${y0 + thickness} 150 ${y0 + thickness} Z`;
          return <g key={item.status}>
            <path d={path} fill={item.color} opacity="0.35" />
            <rect x="546" y={y1} width="8" height={thickness} rx="1" fill={item.color} />
            <text x="574" y={y1 + thickness / 2 - 3} className={styles.chartLabel}>{item.status}</text>
            <text x="574" y={y1 + thickness / 2 + 20} fill={item.color} className={styles.count}>{item.count}<tspan dx="12" className={styles.percentage}>{Math.round(item.count / total * 100)}%</tspan></text>
          </g>;
        })}
      </svg>
    </div>
    <figcaption>Sample applications · Each branch shows a current recorded status.</figcaption>
    <p className={styles.mobileHint}>Swipe across the chart to see every status.</p>
  </figure>;
}

export default function ApplicationSnapshots() {
  return <section className={`section ${styles.section}`} id="snapshots" aria-labelledby="snapshots-title">
    <div className="section-heading">
      <div><span className="eyebrow">APPLICATION SNAPSHOTS</span><h2 id="snapshots-title">See where<br />your search stands.</h2></div>
      <p>Turn the applications in your local tracker into a clear status flow. Ask your agent for a snapshot, or explore your pipeline in the dashboard’s Insights view.</p>
    </div>
    <div className={styles.layout}>
      <SnapshotPreview />
      <div className={styles.guide}>
        <span className="eyebrow">HOW TO USE CV-SNAPSHOT</span>
        <h3>Just ask your agent.</h3>
        <ol className={styles.steps}>
          <li>Open your AI agent in the CV Tailor repository.</li>
          <li>Copy this prompt and send it to your agent.</li>
          <li>Open the generated chart or HTML report.</li>
        </ol>
        <div className={`prompt-window ${styles.prompt}`}>
          <div className="prompt-window-header"><span><Terminal size={13} />Ready to send</span><CopyButton text={SNAPSHOT_PROMPT} label="Copy application snapshot prompt" caption="Copy prompt" /></div>
          <blockquote><span aria-hidden="true">›</span>{SNAPSHOT_PROMPT}</blockquote>
          <div className="prompt-result"><Check size={13} />No dashboard required. Your tracker records stay intact.</div>
        </div>
        <p className={styles.archiveNote}>Want older jobs included? Add <strong>“include archived applications”</strong> to your request.</p>
      </div>
    </div>
    <div className={styles.details}>
      <div><FileText size={16} /><p><strong>SVG chart · Offline HTML report · Source JSON</strong><span>Saved in your local workspace’s snapshots folder. Generate a fresh snapshot whenever your tracker changes.</span></p></div>
      <a className="text-link" href="https://github.com/yabswannalearn/CV-Tailor/blob/main/.agents/skills/cv-snapshot/SKILL.md" target="_blank" rel="noreferrer">Read the skill instructions<ArrowUpRight size={14} /></a>
    </div>
  </section>;
}
