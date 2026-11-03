import type { JobSummary } from "@/lib/queries";

export type ApplicationInsights = {
  as_of: string;
  total: number;
  include_archived: boolean;
  archived_excluded: number;
  by_status: { status: string; count: number }[];
  awaiting_response: number;
  interviewing: number;
  offers: number;
  dated_submissions: number;
  follow_ups_due: JobSummary[];
  by_source: { source: string; count: number }[];
  submissions_by_month: { month: string; count: number }[];
  applications: JobSummary[];
  flow: {
    kind: "current_status";
    nodes: { id: string; label: string; count: number }[];
    links: { source: string; target: string; value: number }[];
  };
  workspace: {
    applications: number;
    archived_applications: number;
    conversations: number;
    drafts: number;
    drafts_by_type: Record<string, number>;
    profile: { exists: boolean; confirmed_skills: number; experience: number; projects: number; education: number; certifications: number };
  };
};

export const STATUS_COLORS: Record<string, string> = {
  Saved: "#8b969a", Applied: "#5487b5", Interview: "#3b9a91", "Tech Test": "#a285bd",
  Offer: "#73934b", Rejected: "#d88276", Ghosted: "#b3a69b",
};

export function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}
