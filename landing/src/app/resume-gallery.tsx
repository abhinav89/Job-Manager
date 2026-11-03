"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import dynamic from "next/dynamic";
import { ArrowUpRight, Expand, X } from "lucide-react";
import { RESUME_TEMPLATES, type ResumeTemplate } from "../lib/resumeTemplates";
import CopyButton from "./copy-button";

const PdfPreview = dynamic(() => import("./pdf-preview"), { ssr: false, loading: () => <p role="status" className="pdf-preview-message">Loading PDF…</p> });

function promptFor(id: ResumeTemplate, name: string) {
  return `Use CV Tailor's cv-resume skill with the ${name} template (template_id: ${id}). Remember this as my default resume format using preferences get and preferences set with its current revision, unless I explicitly request an application-only choice. Ask which application to use if I haven't specified one. Save that template choice on the application using its current revision before exporting context. Tailor a one-page resume using only my confirmed profile facts and the job description. Save a draft, check the page count and extracted text, and export the PDF for my review.`;
}

export default function ResumeGallery() {
  const [selected, setSelected] = useState<(typeof RESUME_TEMPLATES)[number] | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);

  function preview(template: (typeof RESUME_TEMPLATES)[number]) {
    setSelected(template);
    dialog.current?.showModal();
  }

  return (
    <section id="templates" className="resume-gallery section" aria-labelledby="templates-title">
      <div className="section-heading">
        <div><span className="eyebrow">{RESUME_TEMPLATES.length} RESUME FORMATS</span><h2 id="templates-title">Find your format.</h2></div>
        <p>Every format uses Reinael Yabut’s resume. Preview the full PDF to compare.</p>
      </div>
      <div className="resume-gallery-grid">
        {RESUME_TEMPLATES.map(template => (
          <article className="resume-template-card" key={template.id}>
            <button type="button" className="resume-template-thumbnail" aria-label={`Enlarge ${template.name} resume PDF`} onClick={() => preview(template)}>
              <Image src={`/resume-templates/${template.id}.png`} alt={`Reinael Yabut’s resume in the ${template.name} format`} width={850} height={1100} />
              <span className="thumbnail-expand" aria-hidden="true"><Expand size={16} /></span>
            </button>
            <div className="resume-template-controls">
              <h3>{template.name}</h3>
              <div className="resume-template-actions">
                <CopyButton text={promptFor(template.id, template.name)} label={`Copy ${template.name} resume prompt`} caption="Copy prompt" />
                <button type="button" className="pdf-preview-button" aria-label={`Preview ${template.name} PDF`} onClick={() => preview(template)}><Expand size={13} />Preview PDF</button>
              </div>
            </div>
          </article>
        ))}
      </div>
      <dialog ref={dialog} className="pdf-preview-dialog" aria-labelledby="resume-preview-title" onClose={() => setSelected(null)} onClick={event => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
        <div className="pdf-preview-content">
          <header><h3 id="resume-preview-title">{selected?.name}</h3><button type="button" aria-label="Close PDF preview" onClick={() => dialog.current?.close()}><X size={20} /></button></header>
          {selected && <PdfPreview key={selected.id} file={`/resume-templates/${selected.id}.pdf`} />}
          <footer><span>Reinael Yabut’s resume</span>{selected && <a href={`/resume-templates/${selected.id}.pdf`} target="_blank" rel="noreferrer">Open PDF<ArrowUpRight size={13} /></a>}</footer>
        </div>
      </dialog>
    </section>
  );
}
