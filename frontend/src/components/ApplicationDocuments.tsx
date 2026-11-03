"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { BookOpen, FileText, Globe2, PencilLine, X } from "lucide-react";
import { toast } from "sonner";
import { API_URL, getApiError } from "@/lib/api";
import { queryKeys, useApplicationDocuments, type ApplicationDocument } from "@/lib/queries";
import FormattedOutput from "@/components/FormattedOutput";
import InlineQueryError from "@/components/InlineQueryError";

const kinds = {
  interview_plan: { label: "Interview plan", icon: BookOpen },
  cheat_sheet: { label: "Quick cheat sheet", icon: FileText },
  research: { label: "Company & role research", icon: Globe2 },
};
const buttonClass = "rounded-sm border border-[#d4cfc7] px-3 py-2 text-xs font-semibold text-[#4a4540] hover:bg-[#e8e4dd] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5a8a00] disabled:cursor-not-allowed disabled:opacity-50";

function savedDate(value: string) {
  return new Date(/(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`).toLocaleString();
}

export default function ApplicationDocuments({ applicationId }: { applicationId: number }) {
  const documents = useApplicationDocuments(applicationId);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const request = useRef<{ id: number; content: string; key: string } | null>(null);

  const groups = new Map<number, ApplicationDocument[]>();
  const roots = new Map<number, number>();
  for (const draft of [...(documents.data || [])].sort((a, b) => a.id - b.id)) {
    const root = roots.get(draft.metadata?.parent_id ?? -1) ?? draft.id;
    roots.set(draft.id, root);
    groups.set(root, [draft, ...(groups.get(root) || [])]);
  }
  const selectedGroup = [...groups.values()].find(versions => versions.some(draft => draft.id === selectedId));
  const selected = selectedGroup?.find(draft => draft.id === selectedId);
  const latest = selectedGroup?.[0];

  const save = useMutation({
    mutationFn: async ({ draft, content }: { draft: ApplicationDocument; content: string }) => {
      if (request.current?.id !== draft.id || request.current.content !== content) {
        request.current = { id: draft.id, content, key: crypto.randomUUID() };
      }
      const response = await fetch(`${API_URL}/tracker/${applicationId}/documents/${draft.id}/revise`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json", "Idempotency-Key": request.current.key },
        body: JSON.stringify({ content }),
      });
      if (!response.ok) throw new Error(await getApiError(response, "Unable to save this document. Your edits are still here."));
      return response.json() as Promise<ApplicationDocument>;
    },
    onSuccess: draft => {
      queryClient.setQueryData<ApplicationDocument[]>(queryKeys.applicationDocuments(applicationId), previous =>
        [draft, ...(previous || []).filter(item => item.id !== draft.id)]);
      setSelectedId(draft.id);
      setEditing(false);
      toast.success("Changes saved. Earlier versions are still available.");
    },
    onError: () => { void documents.refetch(); },
  });

  function download(draft: ApplicationDocument) {
    const url = URL.createObjectURL(new Blob([draft.content], { type: "text/markdown;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${draft.type.replaceAll("_", "-")}-${applicationId}.md`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <section aria-labelledby={`application-documents-${applicationId}`} className="mb-6 min-w-0">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 id={`application-documents-${applicationId}`} className="text-sm font-bold text-[#1a1814]">Application documents</h3>
          <p className="mt-1 text-xs text-[#7a7570]">Your saved interview preparation and research, ready to review and edit.</p>
        </div>
        {documents.data && <span className="text-[10px] text-[#7a7570]">{groups.size} saved {groups.size === 1 ? "document" : "documents"}</span>}
      </div>

      {documents.isPending ? <p role="status" className="py-4 text-xs text-[#7a7570]">Loading saved documents…</p>
        : documents.isError ? <InlineQueryError message={documents.error.message} onRetry={() => { void documents.refetch(); }} />
        : !groups.size ? <p className="rounded-sm border border-dashed border-[#d4cfc7] p-4 text-xs leading-6 text-[#7a7570]">Interview plans, cheat sheets, and research saved for this application will appear here.</p>
        : <div className="grid gap-2 md:grid-cols-3">
          {[...groups.entries()].map(([root, versions]) => {
            const draft = versions[0];
            const { label, icon: Icon } = kinds[draft.type];
            const active = selectedGroup === versions;
            const title = draft.content.split("\n").find(line => line.trim())?.replace(/^#+\s*/, "");
            return <button key={root} type="button" disabled={editing} aria-pressed={active}
              aria-label={`Open ${label.toLowerCase()}`} onClick={() => { setSelectedId(draft.id); save.reset(); }}
              className={`min-w-0 rounded-sm border p-4 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5a8a00] disabled:cursor-not-allowed ${active ? "border-[#8ab030] bg-[#f1f7e7]" : "border-[#d4cfc7] bg-[#f5f2ed] hover:border-[#8ab030]"}`}>
              <span className="mb-2 flex items-center gap-2 text-xs font-bold text-[#3d6600]"><Icon size={16} aria-hidden="true" />{label}</span>
              <span className="block line-clamp-2 break-words text-xs leading-5 text-[#4a4540]">{title}</span>
              <span className="mt-3 block text-[10px] leading-5 text-[#7a7570]">Saved {savedDate(draft.created_at)}</span>
            </button>;
          })}
        </div>}

      {selected && <div className="mt-3 overflow-hidden rounded-sm border border-[#d4cfc7] bg-[#fffdfa]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#d4cfc7] bg-[#f5f2ed] px-4 py-3">
          <h4 className="text-xs font-bold text-[#1a1814]">{kinds[selected.type].label}</h4>
          <div className="flex flex-wrap items-center gap-2">
            {selectedGroup && selectedGroup.length > 1 && <select aria-label="Document version" value={selected.id} disabled={editing}
              onChange={event => { setSelectedId(Number(event.target.value)); save.reset(); }}
              className="max-w-full rounded-sm border border-[#d4cfc7] bg-[#fffdfa] px-2 py-1.5 text-[10px] text-[#4a4540] focus-visible:outline-2 focus-visible:outline-[#5a8a00]">
              {selectedGroup.map((version, index) => <option key={version.id} value={version.id}>{index === 0 ? "Latest" : `Version ${selectedGroup.length - index}`} · {savedDate(version.created_at)}</option>)}
            </select>}
            {!editing && <button type="button" aria-label="Close document" onClick={() => setSelectedId(null)} className={buttonClass}><X size={14} /></button>}
          </div>
        </div>
        <div className="p-4 sm:p-6">
          {editing ? <>
            <label htmlFor={`document-editor-${applicationId}`} className="mb-2 block text-xs font-semibold text-[#4a4540]">Edit document <span className="font-normal text-[#7a7570]">· Markdown supported</span></label>
            <textarea id={`document-editor-${applicationId}`} value={text} maxLength={100000} disabled={save.isPending}
              onChange={event => setText(event.target.value)} rows={18}
              className="min-h-80 w-full resize-y rounded-sm border border-[#d4cfc7] bg-[#fffdfa] p-3 font-mono text-sm leading-6 text-[#1a1814] outline-none focus:border-[#5a8a00] focus:ring-1 focus:ring-[#5a8a00]" />
            {save.isError && <p role="alert" className="mt-3 text-xs leading-6 text-[#b83030]">{save.error.message}</p>}
          </> : <div className="max-h-[65vh] overflow-y-auto break-words font-sans text-sm leading-7 text-[#4a4540] [overflow-wrap:anywhere] [&_h1]:mb-4 [&_h1]:text-xl [&_h2]:mb-2 [&_h2]:mt-6 [&_h2]:text-lg [&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-base [&_table]:block [&_table]:overflow-auto">
            <FormattedOutput content={selected.content} copyLabel="Copy document" />
            {!!selected.metadata?.sources?.length && <div className="mt-5 border-t border-[#d4cfc7] pt-4">
              <p className="mb-1 text-xs font-semibold">Sources</p>
              {selected.metadata.sources.filter(source => /^https?:\/\//i.test(source.url)).map(source =>
                <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer" className="block text-xs text-[#3d6600] underline underline-offset-2">{source.title}</a>)}
            </div>}
          </div>}
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t border-[#d4cfc7] px-4 py-3">
          {editing ? <>
            <button type="button" disabled={save.isPending || !text.trim() || text === selected.content}
              onClick={() => save.mutate({ draft: selected, content: text })}
              className={`${buttonClass} border-[#315300] bg-[#3d6600] text-white hover:bg-[#315300]`}>{save.isPending ? "Saving…" : "Save changes"}</button>
            <button type="button" disabled={save.isPending} onClick={() => { setEditing(false); save.reset(); }} className={buttonClass}>Cancel</button>
            <span className="text-[10px] text-[#7a7570]">Saves a new version and keeps the earlier ones.</span>
          </> : <>
            {selected.id === latest?.id ? <button type="button" onClick={() => { setText(selected.content); setEditing(true); save.reset(); }} className={`${buttonClass} inline-flex items-center gap-2`}><PencilLine size={13} aria-hidden="true" />Edit document</button>
              : <span className="text-xs text-[#7a7570]">Earlier version. Select the latest version to edit.</span>}
            <button type="button" onClick={() => download(selected)} className={buttonClass}>Download Markdown</button>
          </>}
        </div>
      </div>}
    </section>
  );
}
