import type { ResumeTemplate } from "./resumeTemplates";
import { queryOptions, useQuery, type QueryClient } from "@tanstack/react-query";
import { API_URL, getApiError } from "@/lib/api";

export type WorkspacePreferences = {
  revision: number;
  workspace_uuid: string;
  resume_template: ResumeTemplate;
  tracking_connection: { provider: string; config_path: string | null } | null;
  calendar_connections: { provider: "googlecalendar" | "outlook"; config_path: string | null }[];
};
export type Workspace = { name: string; email: string; profile_exists: boolean; data_dir: string; preferences?: WorkspacePreferences; ai: {mode: string; generation: boolean; assistant: boolean; research: boolean; ranking: boolean} };

export type ApplicationStatus =
  | "To Review"
  | "To Apply"
  | "Applied"
  | "Interview"
  | "Tech Test"
  | "Offer"
  | "Rejected"
  | "Ghosted"
  | "Saved";
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
  target_roles?: string[];
  target_locations?: string[];
  target_work_modes?: string[];
  target_salary?: string;
};

export type PresetSummary = {
  slug: string;
  display_name: string;
  recommended_template?: ResumeTemplate;
};

export type MatchAnalysis = {
  score: number;
  score_percent: number;
  label: "STRONG" | "GOOD" | "FAIR" | "PARTIAL" | string;
  summary: string;
  pros: string[];
  cons: string[];
  matched_skills: string[];
  missing_skills: string[];
  experience_fit?: string;
  location_fit?: string;
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
  match_score?: number;
  match_analysis?: MatchAnalysis;
};

export type PipelineSummary = {
  total: number;
  to_review_count: number;
  to_apply_count: number;
  applied_count: number;
  interviewing_count: number;
  offers_count: number;
  rejected_count: number;
  follow_ups_due_count: number;
  follow_ups_due: JobSummary[];
  recent_applications: JobSummary[];
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

export type CareerTheme = {
  id: string;
  name: string;
  category: string;
  icon?: string;
  description: string;
  target_roles: string[];
  recommended_template: ResumeTemplate;
  is_custom?: boolean;
};

export type ResumeItem = {
  id: string;
  name: string;
  display_title: string;
  theme_id: string;
  theme_name: string;
  template_id: ResumeTemplate;
  target_roles: string[];
  experience_count: number;
  skills_count: number;
  education_count: number;
  last_updated: string;
  is_master: boolean;
  summary?: string;
  notes?: string;
  description?: string;
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
  pipelineSummary: ["workspace-data", "tracker", "pipeline-summary"] as const,
  repositoryJobs: (filters: Record<string, any>) => ["scraper", "jobs", filters] as const,
  trackedCompanies: ["scraper", "companies"] as const,
  trackerDetails: (id: number) => ["workspace-data", "tracker", "details", id] as const,
  applicationDocuments: (id: number) => ["workspace-data", "tracker", "documents", id] as const,
  resumes: ["workspace-data", "resumes"] as const,
  themes: ["workspace-data", "themes"] as const,
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

export function usePipelineSummary() {
  return useQuery<PipelineSummary>({
    queryKey: queryKeys.pipelineSummary,
    queryFn: () => readJson<PipelineSummary>("/tracker/pipeline-summary", "Unable to load pipeline summary."),
    refetchInterval: 10000,
  });
}

export function useRepositoryJobs(filters: {
  keyword?: string;
  location?: string;
  work_model?: string;
  seniority?: string;
  company?: string;
  source?: string;
  min_score?: number;
} = {}) {
  const queryParams = new URLSearchParams();
  if (filters.keyword) queryParams.set("keyword", filters.keyword);
  if (filters.location) queryParams.set("location", filters.location);
  if (filters.work_model && filters.work_model !== "all") queryParams.set("work_model", filters.work_model);
  if (filters.seniority && filters.seniority !== "all") queryParams.set("seniority", filters.seniority);
  if (filters.company) queryParams.set("company", filters.company);
  if (filters.source && filters.source !== "all") queryParams.set("source", filters.source);
  if (filters.min_score) queryParams.set("min_score", String(filters.min_score));

  return useQuery<{ status: string; total: number; jobs: any[] }>({
    queryKey: queryKeys.repositoryJobs(filters),
    queryFn: () => readJson<{ status: string; total: number; jobs: any[] }>(
      `/scraper/jobs?${queryParams.toString()}`,
      "Unable to load jobs from repository."
    ),
  });
}

export function useTrackedCompanies() {
  return useQuery<{ status: string; companies: any[] }>({
    queryKey: queryKeys.trackedCompanies,
    queryFn: () => readJson<{ status: string; companies: any[] }>("/scraper/companies", "Unable to load tracked companies."),
    staleTime: 60 * 60_000,
  });
}

export function useApplicationDocuments(id: number) {
  return useQuery({
    queryKey: queryKeys.applicationDocuments(id),
    queryFn: () => readJson<ApplicationDocument[]>(`/tracker/${id}/documents`, "Unable to load application documents."),
  });
}

export function useResumes() {
  return useQuery<{ status: string; total: number; resumes: ResumeItem[] }>({
    queryKey: queryKeys.resumes,
    queryFn: () => readJson<{ status: string; total: number; resumes: ResumeItem[] }>("/resumes", "Unable to load resumes."),
  });
}

export function useThemes() {
  return useQuery<{ status: string; themes: CareerTheme[] }>({
    queryKey: queryKeys.themes,
    queryFn: () => readJson<{ status: string; themes: CareerTheme[] }>("/resumes/themes", "Unable to load career themes."),
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
