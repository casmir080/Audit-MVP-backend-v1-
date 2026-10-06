import type { Report } from "@/lib/api";

const SECTION_TITLES: Record<string, string> = {
  system_overview: "1. System Overview",
  data_and_inputs: "2. Data and Inputs",
  drift_summary: "3. Drift Summary",
  performance_summary: "4. Performance Summary",
  decision_logic_summary: "5. Decision Logic Summary",
};

const STATUS_STYLES: Record<string, string> = {
  stable: "text-stable border-stable",
  moderate_shift: "text-moderate border-moderate",
  significant_shift: "text-severe border-severe",
};

const HEALTH_STYLES: Record<string, { label: string; className: string }> = {
  stable: { label: "Stable", className: "text-stable border-stable" },
  attention: { label: "Attention required", className: "text-moderate border-moderate" },
  high_risk: { label: "High risk", className: "text-severe border-severe" },
};

export default function ReportView({
  report,
  onDownloadPdf,
  pdfBusy,
}: {
  report: Report;
  onDownloadPdf: () => void;
  pdfBusy: boolean;
}) {
  const { drift_results, sections, performance, model_health, row_count_analyzed } = report;
  const health = HEALTH_STYLES[model_health] || HEALTH_STYLES.attention;

  return (
    <div className="border border-rule bg-white/60 p-6">
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-muted mb-1">Step 2</p>
          <h2 className="font-serif text-xl font-semibold text-ink">Audit report</h2>
          <p className="text-sm text-muted mt-1">
            {row_count_analyzed} rows analyzed
            {` \u00b7 ${performance.coverage.labeled_rows} of ${performance.coverage.total_rows} with a confirmed outcome`}
          </p>
        </div>
        <button
          onClick={onDownloadPdf}
          disabled={pdfBusy}
          className="shrink-0 border border-ink text-ink px-3 py-2 text-sm font-medium disabled:opacity-40 hover:bg-ink hover:text-paper transition-colors"
        >
          {pdfBusy ? "Preparing\u2026" : "Download PDF"}
        </button>
      </div>

      <div className={`mb-8 border px-4 py-3 flex items-center justify-between ${health.className}`}>
        <span className="font-mono text-xs uppercase tracking-widest">Model health</span>
        <span className="font-serif text-lg font-semibold">{health.label}</span>
      </div>

      <div className="mb-8">
        <p className="font-mono text-xs uppercase tracking-widest text-muted mb-2">Drift detail</p>
        <div className="border border-rule divide-y divide-rule">
          <DriftRow
            label="Overall"
            psi={drift_results.overall_psi}
            status={drift_results.overall_status}
            emphasis
          />
          {Object.entries(drift_results.per_feature).map(([key, val]) => (
            <DriftRow key={key} label={key} psi={val.psi} status={val.status} />
          ))}
        </div>
      </div>

      <div className="space-y-6">
        {Object.entries(SECTION_TITLES).map(([key, title]) =>
          sections[key] ? (
            <div key={key}>
              <h3 className="font-serif text-base font-semibold text-ink mb-1">{title}</h3>
              <p className="text-sm leading-relaxed text-ink/90 whitespace-pre-wrap">{sections[key]}</p>
            </div>
          ) : null
        )}

        <div>
          <h3 className="font-serif text-base font-semibold text-ink mb-1">6. Bias / Fairness</h3>
          <p className="text-sm leading-relaxed text-muted italic">{report.bias_section}</p>
        </div>
      </div>
    </div>
  );
}

function DriftRow({
  label,
  psi,
  status,
  emphasis,
}: {
  label: string;
  psi: number;
  status: string;
  emphasis?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between px-4 py-2 ${emphasis ? "bg-paper/60" : ""}`}>
      <span className={`text-sm capitalize ${emphasis ? "font-semibold text-ink" : "text-ink/80"}`}>
        {label.replace(/_/g, " ")}
      </span>
      <div className="flex items-center gap-3">
        <span className="font-mono text-sm text-ink">{psi.toFixed(4)}</span>
        <span
          className={`font-mono text-[11px] uppercase tracking-wide border px-2 py-0.5 ${
            STATUS_STYLES[status] || "text-muted border-rule"
          }`}
        >
          {status.replace(/_/g, " ")}
        </span>
      </div>
    </div>
  );
}
