"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDispatch } from "react-redux";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownToLine, ArrowUpRight, RefreshCw, Search } from "lucide-react";
import ApplicationFlow from "@/components/ApplicationFlow";
import { type ApplicationInsights, localDate, STATUS_COLORS } from "@/lib/applicationInsights";
import { readJson } from "@/lib/queries";
import { setExpandedJob, setFilterStatus, setSearchQuery } from "@/lib/store";

const actionClass = "inline-flex items-center justify-center gap-2 rounded-md border border-[#d4dcd9] px-3 py-2 text-xs font-medium text-[#3b5359] hover:bg-[#edf2ef] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#41756a] disabled:opacity-50";
const documentLabels: Record<string, string> = {
  resume: "CVs", cover_letter: "Cover letters", interview_plan: "Interview plans", cheat_sheet: "Cheat sheets",
  research: "Company research", job_fit: "Job fit reviews", application_form: "Form checkpoints",
  job_context: "Job descriptions", job_search: "Job searches", agent_activity: "Agent activity",
};

export default function InsightsPage() {
  const [includeArchived, setIncludeArchived] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [dueOnly, setDueOnly] = useState(false);
  const router = useRouter();
  const dispatch = useDispatch();
  const asOf = localDate();
  const query = useQuery({
    queryKey: ["workspace-data", "tracker", "insights", includeArchived, asOf],
    queryFn: () => readJson<ApplicationInsights>(`/tracker/insights?include_archived=${includeArchived}&as_of=${asOf}`, "Unable to load application insights."),
    staleTime: 0,
    refetchInterval: 30_000,
  });
  const data = query.data;
  const dueIds = new Set(data?.follow_ups_due.map(job => job.id));
  const needle = search.trim().toLocaleLowerCase();
  const jobs = (data?.applications || []).filter(job =>
    (!selectedStatus || job.status === selectedStatus) && (!dueOnly || dueIds.has(job.id)) &&
    (!needle || `${job.company_name} ${job.job_title} ${job.job_source || ""}`.toLocaleLowerCase().includes(needle)));

  function openApplication(id: number) {
    dispatch(setFilterStatus("All"));
    dispatch(setSearchQuery(""));
    dispatch(setExpandedJob(id));
    router.push("/tracker");
  }

  function downloadSnapshot() {
    if (!data) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `application-insights-${data.as_of}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <div className="min-h-full bg-[#f3f5f2] px-4 py-7 font-sans text-[#253a43] sm:px-8 sm:py-10">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#638176]">Application insights</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Where things stand.</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-[#728187]">Your application pipeline, drawn from your local tracker.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void query.refetch()} disabled={query.isFetching} className={actionClass}>
              <RefreshCw size={13} className={query.isFetching ? "animate-spin motion-reduce:animate-none" : ""} /> Refresh
            </button>
            <Link href="/tracker" className={actionClass}>Job tracker <ArrowUpRight size={14} /></Link>
          </div>
        </header>

        {query.isError && <div role="alert" className="rounded-lg border border-[#e0b4ac] bg-[#fff5f2] p-4 text-sm text-[#874e44]">
          <p>{query.error.message}</p>
          <button type="button" onClick={() => void query.refetch()} className="mt-2 underline underline-offset-4">Try again</button>
        </div>}

        {query.isPending && <div role="status" className="rounded-xl border border-[#dce3df] bg-white p-10 text-sm text-[#728187]">Loading your application pipeline…</div>}

        {data && <>
          <section aria-label="Pipeline summary" className="grid grid-cols-2 gap-y-5 border-y border-[#dce3df] py-5 sm:grid-cols-4">
            {[
              { label: "Tracked applications", count: data.total },
              { label: "Awaiting response", count: data.awaiting_response },
              { label: "Interview / tech test", count: data.interviewing },
              { label: "Offers", count: data.offers },
            ].map(item => <div key={item.label} className="pl-1 sm:border-r sm:border-[#dce3df] sm:pl-6 sm:first:pl-1 sm:last:border-0">
              <p className="text-[11px] text-[#728187]">{item.label}</p>
              <p className="mt-1 text-3xl font-semibold tabular-nums tracking-tight">{item.count}</p>
            </div>)}
          </section>

          <section aria-labelledby="flow-heading" className="overflow-hidden rounded-xl border border-[#dce3df] bg-white">
            <div className="flex flex-wrap items-start justify-between gap-4 px-5 pt-5 sm:px-7 sm:pt-6">
              <div>
                <h2 id="flow-heading" className="text-base font-semibold">Application flow</h2>
                <p className="mt-1 text-xs leading-5 text-[#728187]">Each branch shows a current status. Select one to explore its applications.</p>
              </div>
              <label className="flex cursor-pointer items-center gap-2 text-xs text-[#5e7177]">
                <input type="checkbox" checked={includeArchived} onChange={event => setIncludeArchived(event.target.checked)} className="accent-[#41756a]" /> Include archived
              </label>
            </div>
            {data.total > 0 ? <div className="px-3 pt-3 sm:px-5">
              <ApplicationFlow total={data.total} statuses={data.by_status} selected={selectedStatus} onSelect={setSelectedStatus} />
              <p className="px-2 pb-3 text-[11px] text-[#728187] sm:hidden">Swipe across the chart, or use the status filters below.</p>
            </div> : <div className="px-6 py-16 text-center">
              <p className="text-lg font-medium">Your pipeline starts with one application.</p>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#728187]">Save a job in your tracker to see it here{data.archived_excluded ? ", or include your archived applications" : ""}.</p>
              <Link href="/tracker" className={`${actionClass} mt-5`}>Open job tracker <ArrowUpRight size={14} /></Link>
            </div>}
            <div className="flex flex-wrap justify-between gap-2 border-t border-[#edf0ed] px-5 py-3 text-[11px] leading-5 text-[#728187] sm:px-7">
              <p>Current status snapshot · Interview rounds and past transitions are not recorded.</p>
              <p>{data.archived_excluded > 0 ? `${data.archived_excluded} archived excluded · ` : ""}As of {data.as_of}</p>
            </div>
          </section>

          <section aria-labelledby="applications-heading" className="rounded-xl border border-[#dce3df] bg-white">
            <div className="flex flex-wrap items-center justify-between gap-3 px-5 pt-5 sm:px-7">
              <div>
                <h2 id="applications-heading" className="text-base font-semibold">{selectedStatus ? `${selectedStatus} applications` : "Applications"}</h2>
                <p aria-live="polite" className="mt-1 text-xs text-[#728187]">{jobs.length} {jobs.length === 1 ? "application" : "applications"} shown{dueOnly ? " · Follow-up due" : ""}</p>
              </div>
              <label className="flex items-center gap-2 rounded-md border border-[#dce3df] px-3 py-2 text-[#728187]">
                <Search size={14} />
                <input aria-label="Search applications" placeholder="Company, role or source" value={search} onChange={event => setSearch(event.target.value)} className="w-44 bg-transparent text-xs text-[#253a43] outline-none placeholder:text-[#8b969a] sm:w-52" />
              </label>
            </div>
            <div className="flex flex-wrap gap-2 px-5 py-4 sm:px-7" aria-label="Filter by status">
              <button type="button" onClick={() => setSelectedStatus(null)} aria-pressed={selectedStatus === null} className={`rounded-full border px-3 py-1.5 text-[11px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#41756a] ${selectedStatus === null ? "border-[#48685d] bg-[#edf3ee] text-[#345748]" : "border-[#e2e7e3] text-[#728187]"}`}>All statuses</button>
              {data.by_status.map(item => <button key={item.status} type="button" onClick={() => setSelectedStatus(selectedStatus === item.status ? null : item.status)} aria-pressed={selectedStatus === item.status}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[11px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#41756a] ${selectedStatus === item.status ? "border-[#48685d] bg-[#edf3ee] text-[#345748]" : "border-[#e2e7e3] text-[#728187]"}`}>
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: STATUS_COLORS[item.status] || "#8b969a" }} />{item.status} <span className="tabular-nums">{item.count}</span>
              </button>)}
            </div>
            {jobs.length ? <div className="overflow-x-auto [contain:paint]">
              <table className="w-full min-w-[630px] text-left text-xs" aria-label="Applications in the selected status">
                <thead className="border-y border-[#e8ece8] bg-[#f8faf7] text-[10px] text-[#728187]">
                  <tr>{["Company / role", "Status", "Source", "Applied", ""].map((label, index) => <th key={index} scope="col" className="px-5 py-3 font-medium first:sm:pl-7"><span className={label ? "" : "sr-only"}>{label || "Open application"}</span></th>)}</tr>
                </thead>
                <tbody className="divide-y divide-[#edf0ed]">
                  {jobs.map(job => <tr key={job.id} className="hover:bg-[#fafbf8]">
                    <td className="max-w-[320px] px-5 py-4 sm:pl-7"><p className="font-semibold text-[#344b53]">{job.company_name}</p><p className="mt-1 text-[#728187]">{job.job_title}</p>{job.is_archived && <p className="mt-1 text-[10px] text-[#8b969a]">Archived</p>}</td>
                    <td className="px-5 py-4"><span className="inline-flex items-center gap-2 whitespace-nowrap"><span className="h-1.5 w-1.5 rounded-full" style={{ background: STATUS_COLORS[job.status] || "#8b969a" }} />{job.status}</span></td>
                    <td className="px-5 py-4 text-[#728187]">{job.job_source || "Unknown"}</td>
                    <td className="whitespace-nowrap px-5 py-4 font-mono text-[11px] text-[#728187]">{job.date_applied || "Not recorded"}</td>
                    <td className="px-5 py-4 text-right">{!job.is_archived ? <button type="button" aria-label={`Open ${job.company_name} in tracker`} onClick={() => openApplication(job.id)} className="inline-flex items-center gap-1 whitespace-nowrap text-[#41756a] underline-offset-4 hover:underline">Open <ArrowUpRight size={13} /></button> : <span className="text-[#8b969a]">Archived</span>}</td>
                  </tr>)}
                </tbody>
              </table>
            </div> : <p className="px-5 py-10 text-center text-sm text-[#728187]">No applications match these filters.</p>}
          </section>

          <div className="grid gap-5 lg:grid-cols-2">
            <section aria-labelledby="followups-heading" className="rounded-xl border border-[#dce3df] bg-white p-5 sm:p-7">
              <div className="flex items-center justify-between gap-3">
                <h2 id="followups-heading" className="text-sm font-semibold">Follow-ups due <span className="ml-2 text-[#8b969a]">{data.follow_ups_due.length}</span></h2>
                <button type="button" onClick={() => { setDueOnly(!dueOnly); setSelectedStatus(null); setSearch(""); }} aria-pressed={dueOnly} className="text-xs text-[#41756a] underline-offset-4 hover:underline">{dueOnly ? "Show all applications" : "Filter applications"}</button>
              </div>
              {data.follow_ups_due.length ? <ul className="mt-4 divide-y divide-[#edf0ed]">
                {data.follow_ups_due.slice(0, 5).map(job => <li key={job.id} className="flex items-center justify-between gap-3 py-3 text-xs">
                  <button type="button" onClick={() => openApplication(job.id)} className="text-left hover:underline"><span className="font-medium">{job.company_name}</span><span className="mt-1 block text-[#728187]">{job.job_title}</span></button>
                  <span className="shrink-0 font-mono text-[11px] text-[#b47759]">{job.follow_up_date}</span>
                </li>)}
                {data.follow_ups_due.length > 5 && <li className="pt-3 text-xs text-[#728187]">{data.follow_ups_due.length - 5} more · Use Filter applications to see all.</li>}
              </ul> : <p className="mt-4 text-xs leading-6 text-[#728187]">No scheduled follow-ups are due. Set a follow-up date in the tracker when you want to revisit an active application.</p>}
            </section>

            <section aria-labelledby="sources-heading" className="rounded-xl border border-[#dce3df] bg-white p-5 sm:p-7">
              <h2 id="sources-heading" className="text-sm font-semibold">Where your jobs came from</h2>
              {data.by_source.length ? <ul className="mt-5 space-y-4">
                {data.by_source.map(item => <li key={item.source}>
                  <div className="mb-2 flex justify-between gap-3 text-xs"><span className="break-words text-[#5e7177]">{item.source}</span><span className="tabular-nums">{item.count}</span></div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-[#edf1ed]"><div className="h-full rounded-full bg-[#8da995]" style={{ width: `${item.count / data.total * 100}%` }} /></div>
                </li>)}
              </ul> : <p className="mt-4 text-xs text-[#728187]">Job sources will appear as you add applications.</p>}
            </section>
          </div>

          <section aria-labelledby="workspace-heading" className="rounded-xl border border-[#dce3df] bg-[#eaf0e9] p-5 sm:p-7">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><h2 id="workspace-heading" className="text-sm font-semibold">Inside your local workspace</h2><p className="mt-1 text-xs leading-5 text-[#728187]">All saved records, including archived applications and earlier draft versions.</p></div>
              <button type="button" onClick={downloadSnapshot} className={actionClass}><ArrowDownToLine size={13} /> Download snapshot</button>
            </div>
            <dl className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-4">
              {[
                ["Applications", data.workspace.applications], ["Archived", data.workspace.archived_applications],
                ["Conversations", data.workspace.conversations], ["Saved drafts", data.workspace.drafts],
              ].map(([label, count]) => <div key={label}><dt className="text-[11px] text-[#728187]">{label}</dt><dd className="mt-1 text-xl font-semibold tabular-nums">{count}</dd></div>)}
            </dl>
            <div className="mt-5 border-t border-[#d5dfd4] pt-4 text-xs leading-6 text-[#5e7177]">
              {data.workspace.profile.exists ? <p>Profile · {data.workspace.profile.confirmed_skills} confirmed skills · {data.workspace.profile.experience} experience entries · {data.workspace.profile.projects} projects · {data.workspace.profile.education} education entries · {data.workspace.profile.certifications} certifications</p> : <p>No profile saved yet. <Link href="/dashboard" className="underline underline-offset-4">Set up your profile</Link></p>}
              {Object.keys(data.workspace.drafts_by_type).length > 0 && <p className="mt-1">{Object.entries(data.workspace.drafts_by_type).map(([type, count]) => `${documentLabels[type] || type.replaceAll("_", " ")}: ${count}`).join(" · ")}</p>}
            </div>
          </section>
        </>}
      </div>
    </div>
  );
}
