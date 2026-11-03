"use client";

import { STATUS_COLORS } from "@/lib/applicationInsights";

type Props = {
  total: number;
  statuses: { status: string; count: number }[];
  selected: string | null;
  onSelect: (status: string | null) => void;
};

export default function ApplicationFlow({ total, statuses, selected, onSelect }: Props) {
  const branches = statuses.filter(item => item.count > 0);
  if (!total) return null;
  const gap = 48;
  // One common scale preserves the count proportions even for small branches.
  const height = Math.max(450, 64 + branches.length * 52);
  const usable = height - 64 - Math.max(0, branches.length - 1) * gap;
  const scale = usable / total;
  const sourceTop = (height - usable) / 2;
  const paths = branches.map((branch, index) => {
    const offset = branches.slice(0, index).reduce((sum, item) => sum + item.count * scale, 0);
    return { ...branch, thickness: branch.count * scale, y0: sourceTop + offset, y1: 32 + offset + index * gap };
  });
  return (
    <div className="overflow-x-auto pb-1">
      <svg viewBox={`0 0 960 ${height}`} className="w-full min-w-[650px]" role="group" aria-label="Application status flow">
        <title>Current application statuses</title>
        <desc>Each application appears once in its recorded current status. Select a status to see its applications.</desc>
        <text x="20" y={height / 2 - 12} fill="#384b52" fontSize="15">Applications</text>
        <text x="20" y={height / 2 + 31} fill="#253a43" fontSize="40" fontWeight="600">{total}</text>
        <rect x="168" y={sourceTop} width="10" height={usable} rx="2" fill="#a4afb2" />
        {paths.map(branch => {
          const color = STATUS_COLORS[branch.status] || "#8b969a";
          const active = selected === null || selected === branch.status;
          const d = `M 178 ${branch.y0} C 390 ${branch.y0}, 505 ${branch.y1}, 706 ${branch.y1} L 706 ${branch.y1 + branch.thickness} C 505 ${branch.y1 + branch.thickness}, 390 ${branch.y0 + branch.thickness}, 178 ${branch.y0 + branch.thickness} Z`;
          return (
            <g key={branch.status} role="button" tabIndex={0}
              aria-label={`${branch.status}: ${branch.count} ${branch.count === 1 ? "application" : "applications"}`}
              aria-pressed={selected === branch.status}
              onClick={() => onSelect(selected === branch.status ? null : branch.status)}
              onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(selected === branch.status ? null : branch.status); } }}
              className="group cursor-pointer outline-none">
              <title>{branch.status}: {branch.count} ({Math.round(branch.count / total * 100)}%)</title>
              <path d={d} fill={color} opacity={active ? 0.38 : 0.09} className="group-hover:opacity-60 group-focus-visible:opacity-60" />
              <rect x="706" y={branch.y1} width="10" height={branch.thickness} rx="1" fill={color} opacity={active ? 1 : 0.3} />
              <rect x="727" y={branch.y1 + branch.thickness / 2 - 24} width="210" height="48" rx="5" fill="transparent" className="group-focus-visible:stroke-[#253a43]" />
              <text x="739" y={branch.y1 + branch.thickness / 2 - 3} fill={active ? "#253a43" : "#89969a"} fontSize="16">{branch.status}</text>
              <text x="739" y={branch.y1 + branch.thickness / 2 + 18} fill={color} fontSize="18" fontWeight="600">{branch.count}<tspan dx="12" fontSize="12" fill="#89969a" fontWeight="400">{Math.round(branch.count / total * 100)}%</tspan></text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
