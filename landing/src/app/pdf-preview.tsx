"use client";

import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

export default function PdfPreview({ file }: { file: string }) {
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const observer = new ResizeObserver(entries => {
      setWidth(Math.max(100, Math.floor(entries[0].contentRect.width)));
    });
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);

  return <div className="pdf-document-scroll"><div className="pdf-document-inner" ref={container}>
    {failed ? <p role="alert" className="pdf-preview-message">Unable to load the preview. Use Open PDF below.</p> :
      <Document file={file} onLoadError={() => setFailed(true)} loading={<p role="status" className="pdf-preview-message">Loading PDF…</p>}>
        <Page pageNumber={1} width={width} renderAnnotationLayer={false} loading={<p role="status" className="pdf-preview-message">Rendering PDF…</p>} />
      </Document>}
  </div></div>;
}
