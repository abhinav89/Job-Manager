"use client";

import { toast } from "sonner";

type FormField = {
  key: string; label: string; section: string; kind: string;
  proposed_value: string | boolean | string[] | null;
  original_value: string | boolean | string[] | null;
  observed_value: string | boolean | string[] | null;
  observation: string; document_id: number | null;
  evidence: string;
};
type FormData = {
  company_name: string; job_title: string; form_url: string; step: string;
  documents: { draft_id: number; kind: string; filename: string; sha256: string }[];
  fields: FormField[];
};
type Validation = {
  state: string;
  issues: { field_key: string | null; message: string; severity: string }[];
  fields: { key: string; verified: boolean; used: number | null; maximum: number | null; unit: string | null }[];
};
type Props = { metadata?: { [key: string]: unknown } | null };

const states: Record<string, string> = {
  drafted: "Answers drafted", partially_filled: "Partially filled",
  verified_for_review: "Verified for your review", submission_confirmed: "Submission confirmed",
};
const display = (value: FormField["proposed_value"]) => value === null ? "No answer recorded" :
  typeof value === "boolean" ? value ? "Checked / Yes" : "Unchecked / No" : Array.isArray(value) ? value.join(", ") : value || "Blank";

export default function ApplicationFormDraft({ metadata }: Props) {
  const data = metadata?.structured_content as FormData | undefined;
  const validation = metadata?.validation as Validation | undefined;
  if (!data || !validation) return <p className="mt-4 text-sm">This form checkpoint could not be read. Reload it with your local agent.</p>;
  const copyAnswers = async () => {
    const text = data.fields.map(field => `${field.section ? `${field.section} · ` : ""}${field.label}\n${field.kind === "file" ? data.documents.find(doc => doc.draft_id === field.document_id)?.filename || "No selected attachment" : display(field.proposed_value ?? field.original_value)}`).join("\n\n");
    try { await navigator.clipboard.writeText(text); toast.success("Application answers copied."); }
    catch { toast.error("Could not copy the answers. Select and copy the text instead."); }
  };
  return <section aria-label="Application form checkpoint" className="mt-4 overflow-hidden rounded-xl border border-[#d8e3d3] bg-white text-[#303a32]">
    <div className="border-b border-[#e5e8df] px-4 py-3">
      <p className="text-xs font-semibold text-[#557442]">{states[validation.state] || "Form checkpoint"}</p>
      <h3 className="mt-1 text-sm font-semibold">{data.job_title} · {data.company_name}</h3>
      <p className="mt-1 text-xs text-[#71816b]">{data.step} · Saved observations from your agent</p>
    </div>
    <div className="space-y-4 p-4">
      {!!validation.issues.length && <ul aria-label="Form review items" className="space-y-2 rounded-lg bg-[#fbf7ec] p-3 text-xs leading-5 text-[#796140]">
        {validation.issues.map((issue, index) => <li key={index}>{issue.field_key && <span className="font-semibold">{data.fields.find(field => field.key === issue.field_key)?.label || "Field"}: </span>}{issue.message}</li>)}
      </ul>}
      <dl className="space-y-4">
        {data.fields.map(field => {
          const check = validation.fields.find(item => item.key === field.key);
          const document = data.documents.find(item => item.draft_id === field.document_id);
          return <div key={field.key}>
            <dt className="text-xs font-semibold">{field.section && <span className="font-normal text-[#71816b]">{field.section} · </span>}{field.label}</dt>
            <dd className="mt-1 whitespace-pre-wrap break-words text-sm">{field.kind === "file" ? document?.filename || "No selected attachment" : display(field.proposed_value ?? field.original_value)}</dd>
            {field.kind !== "file" && field.observation === "observed" && JSON.stringify(field.observed_value) !== JSON.stringify(field.proposed_value ?? field.original_value) && <dd className="mt-1 whitespace-pre-wrap break-words text-xs text-[#796140]">Observed: {display(field.observed_value)}</dd>}
            <dd className="mt-1 text-xs text-[#71816b]">{check?.verified ? "Value verified in saved observation" : "Needs live verification"}{check?.maximum !== null && check?.maximum !== undefined ? ` · ${check.used}/${check.maximum} ${check.unit === "utf16" ? "characters" : "words"}` : field.kind === "text" || field.kind === "textarea" ? " · Limit unknown" : ""}</dd>
            {field.evidence && <dd className="mt-1 text-xs text-[#71816b]">Source: {field.evidence}</dd>}
          </div>;
        })}
      </dl>
      {!!data.documents.length && <details className="text-xs text-[#71816b]"><summary className="cursor-pointer">Selected documents</summary><ul className="mt-2 space-y-2">{data.documents.map(doc => <li key={doc.draft_id} className="break-all">{doc.filename} · Draft #{doc.draft_id}<br />SHA-256: {doc.sha256}</li>)}</ul></details>}
      <button type="button" onClick={() => void copyAnswers()} className="rounded-lg border border-[#d7dfd2] px-3 py-2 text-xs font-semibold text-[#557442]">Copy application answers</button>
      <p className="text-xs leading-5 text-[#71816b]">{validation.state === "submission_confirmed" ? "You confirmed submission. These are the last values observed by your agent; later manual edits may differ." : "Resume with cv-apply to refresh this checkpoint. You review and submit in the employer’s form. Tracker status changes only after you confirm submission."}</p>
    </div>
  </section>;
}
