const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type DriftFeature = { psi: number; status: string };

export type DriftResults = {
  per_feature: Record<string, DriftFeature>;
  overall_psi: number;
  overall_status: string;
};

export type PerformanceMetrics = {
  status: "insufficient" | "limited" | "moderate" | "high";
  coverage: { total_rows: number; labeled_rows: number; coverage_pct: number };
  precision: number | null;
  recall: number | null;
  f1: number | null;
};

export type Report = {
  sections: Record<string, string>;
  drift_results: DriftResults;
  performance: PerformanceMetrics;
  model_health: "stable" | "attention" | "high_risk";
  bias_section: string;
  row_count_analyzed: number;
  normalized_rows: unknown[];
};

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail || JSON.stringify(body);
  } catch {
    return res.statusText;
  }
}

export async function generateReport(baselineFile: File, currentFile: File): Promise<Report> {
  const form = new FormData();
  form.append("baseline_file", baselineFile);
  form.append("current_file", currentFile);

  const res = await fetch(`${API_URL}/report/generate`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Report generation failed: ${await readError(res)}`);
  return res.json();
}

export async function downloadPdf(
  baselineFile: File,
  currentFile: File,
  institutionName: string
): Promise<Blob> {
  const form = new FormData();
  form.append("baseline_file", baselineFile);
  form.append("current_file", currentFile);

  const url = `${API_URL}/report/pdf?institution_name=${encodeURIComponent(institutionName)}`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) throw new Error(`PDF generation failed: ${await readError(res)}`);
  return res.blob();
}

export async function askQuestion(
  question: string,
  driftResults: DriftResults,
  normalizedRows: unknown[]
): Promise<string> {
  const res = await fetch(`${API_URL}/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      drift_results: driftResults,
      normalized_rows: normalizedRows,
    }),
  });
  if (!res.ok) throw new Error(`Question failed: ${await readError(res)}`);
  const data = await res.json();
  return data.answer as string;
}
