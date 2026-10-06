"use client";

import { useState } from "react";
import UploadForm from "@/components/UploadForm";
import ReportView from "@/components/ReportView";
import ChatPanel from "@/components/ChatPanel";
import { generateReport, downloadPdf, type Report } from "@/lib/api";

export default function Home() {
  const [institutionName, setInstitutionName] = useState("");
  const [files, setFiles] = useState<{ baseline: File; current: File } | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(baseline: File, current: File) {
    setFiles({ baseline, current });
    setBusy(true);
    setError(null);
    setReport(null);
    try {
      const result = await generateReport(baseline, current);
      setReport(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong generating the report");
    } finally {
      setBusy(false);
    }
  }

  async function handleDownloadPdf() {
    if (!files) return;
    setPdfBusy(true);
    setError(null);
    try {
      const blob = await downloadPdf(files.baseline, files.current, institutionName || "Institution");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_report.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong generating the PDF");
    } finally {
      setPdfBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8">
          <p className="font-mono text-xs uppercase tracking-widest text-muted mb-2">
            AI system audit
          </p>
          <h1 className="font-serif text-3xl font-semibold text-ink">
            Compliance-ready, in the time it takes to upload two files.
          </h1>
          <p className="text-sm text-muted mt-2 max-w-xl">
            Upload a baseline period and a current period from your fraud, AML,
            or KYC system&rsquo;s decision logs. Get a report mapped to CBN and
            NITDA&rsquo;s documentation requirements, and ask questions about
            what it found.
          </p>
        </header>

        <div className="space-y-6">
          <UploadForm
            institutionName={institutionName}
            onInstitutionNameChange={setInstitutionName}
            onSubmit={handleSubmit}
            busy={busy}
          />

          {error && (
            <div className="border border-severe bg-white/60 p-4">
              <p className="font-mono text-xs uppercase tracking-widest text-severe mb-1">
                Something went wrong
              </p>
              <p className="text-sm text-ink">{error}</p>
            </div>
          )}

          {report && (
            <>
              <ReportView report={report} onDownloadPdf={handleDownloadPdf} pdfBusy={pdfBusy} />
              <ChatPanel driftResults={report.drift_results} normalizedRows={report.normalized_rows} />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
