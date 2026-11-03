import type { ResumeTemplate } from "./resumeTemplates";
import { queryOptions, useQuery, type QueryClient } from "@tanstack/react-query";
import { API_URL, getApiError } from "@/lib/api";

export type WorkspacePreferences = {
  revision: number;
  workspace_uuid: string;
  resume_template: ResumeTemplate;
  tracking_connection: { provider: string; config_path: string | null } | null;
};
export type Workspace = { name: string; email: string; profile_exists: boolean; data_dir: string; preferences?: WorkspacePreferences; ai: {mode: string; generation: boolean; assistant: boolean; research: boolean; ranking: boolean} };

export type ApplicationStatus = "Saved" | "Applied" | "Interview" | "Tech Test" | "Offer" | "Rejected" | "Ghosted";
export type ApplicationPriority = "High" | "Medium" | "Low";
export type { ResumeTemplate } from "./resumeTemplates";

export type Education = { school_name: string; course: string; location: string; description?: string; date_range?: string };
export type Experience = { job_title: string; company: string; location: string; description?: string; date_range?: string };
export type Project = { name: string; description?: string; date_range?: string; link?: string | null };
export type Certification = { name: string; issuer?: string; date_issued?: string };
export type Profile = {
  revision?: number;
  first_name: string;
  last_name: string;
  mobile_no: string;
  email: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
  education: Education[];
  experience: Experience[];
  projects: Project[];
  skills: { skill_name: string; is_confirmed?: boolean }[];
  certifications: Certification[];
  preset_slug?: string;
  preferred_template?: ResumeTemplate;
};

export type PresetSummary = {
  slug: string;
  display_name: string;
  recommended_template?: ResumeTemplate;
};

export type JobSummary = {
  revision?: number;
  id: number;
  company_name: string;
  job_title: string;
  job_url?: string;
  job_source?: string;
  is_archived?: boolean;
  short_description?: string;
  has_pdf: boolean;
  pdf_generated_at?: string;
  status: ApplicationStatus;
  date_applied?: string;
  follow_up_date?: string;
  job_type?: string;
  location?: string;
  salary_range?: string;
  priority: ApplicationPriority;
  template_id?: ResumeTemplate;
};

export type JobDetails = JobSummary & {
  job_description?: string;
  notes?: string;
  cover_letter?: string;
};

export type TrackerStats = { total: number; by_status: Partial<Record<ApplicationStatus, number>> };

export type ApplicationDocument = {
  id: number;
  conversation_id: number;
  type: "interview_plan" | "cheat_sheet" | "research";
  content: string;
  created_at: string;
  metadata: {
    parent_id?: number | null;
    sources?: { title: string; url: string }[];
  } | null;
};

export class ApiQueryError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiQueryError";
  }
}

export async function readJson<T>(path: string, fallback: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { credentials: "include" });
  if (!response.ok) throw new ApiQueryError(await getApiError(response, fallback), response.status);
  return response.json() as Promise<T>;
}

export const queryKeys = {
  workspaceData: ["workspace-data"] as const,
  workspace: ["workspace-data", "current-user"] as const,
  profile: ["workspace-data", "profile", "me"] as const,
  presets: ["presets"] as const,
  tracker: ["workspace-data", "tracker"] as const,
  trackerJobs: ["workspace-data", "tracker", "jobs"] as const,
  trackerStats: ["workspace-data", "tracker", "stats"] as const,
  trackerDetails: (id: number) => ["workspace-data", "tracker", "details", id] as const,
  applicationDocuments: (id: number) => ["workspace-data", "tracker", "documents", id] as const,
};

export const workspaceQueryOptions = () => queryOptions({
  queryKey: queryKeys.workspace,
  queryFn: () => readJson<Workspace>("/workspace", "Unable to load your local workspace."),
  retry: false,
});

export const profileQueryOptions = () => queryOptions({
  queryKey: queryKeys.profile,
  queryFn: () => readJson<Profile>("/profile/me", "Unable to load your profile."),
  retry: false,
});

export const presetsQueryOptions = () => queryOptions({
  queryKey: queryKeys.presets,
  queryFn: () => readJson<PresetSummary[]>("/presets", "Unable to load resume presets."),
  staleTime: 30 * 60_000,
});

export const trackerJobsQueryOptions = () => queryOptions({
  queryKey: queryKeys.trackerJobs,
  queryFn: () => readJson<JobSummary[]>("/tracker", "Unable to load your applications."),
});

export const trackerStatsQueryOptions = () => queryOptions({
  queryKey: queryKeys.trackerStats,
  queryFn: () => readJson<TrackerStats>("/tracker/stats", "Unable to load application statistics."),
});

export const trackerDetailsQueryOptions = (id: number) => queryOptions({
  queryKey: queryKeys.trackerDetails(id),
  queryFn: () => readJson<JobDetails>(`/tracker/${id}/details`, "Unable to load application details."),
});


export function useWorkspace() {
  return useQuery(workspaceQueryOptions());
}


export function useProfile() {
  return useQuery(profileQueryOptions());
}

export function usePresets() {
  return useQuery(presetsQueryOptions());
}

export function useTrackerJobs(enabled = true) {
  return useQuery({ ...trackerJobsQueryOptions(), enabled });
}

export function useTrackerStats(enabled = true) {
  return useQuery({ ...trackerStatsQueryOptions(), enabled });
}

export function useTrackerDetails(id: number | null) {
  return useQuery<JobDetails>({
    queryKey: id === null ? ["workspace-data", "tracker", "details", "none"] : queryKeys.trackerDetails(id),
    queryFn: () => readJson<JobDetails>(`/tracker/${id}/details`, "Unable to load application details."),
    enabled: id !== null,
  });
}

export function useApplicationDocuments(id: number) {
  return useQuery({
    queryKey: queryKeys.applicationDocuments(id),
    queryFn: () => readJson<ApplicationDocument[]>(`/tracker/${id}/documents`, "Unable to load application documents."),
  });
}

export function warmWorkspaceData(queryClient: QueryClient) {
  return Promise.allSettled([
    queryClient.prefetchQuery(workspaceQueryOptions()),
    queryClient.prefetchQuery(profileQueryOptions()),
    queryClient.prefetchQuery(presetsQueryOptions()),
    queryClient.prefetchQuery(trackerJobsQueryOptions()),
  ]);
}
