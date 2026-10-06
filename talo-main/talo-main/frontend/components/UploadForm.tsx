"use client";

import { useState } from "react";

type Props = {
  institutionName: string;
  onInstitutionNameChange: (v: string) => void;
  onSubmit: (baseline: File, current: File) => void;
  busy: boolean;
};

export default function UploadForm({ institutionName, onInstitutionNameChange, onSubmit, busy }: Props) {
  const [baseline, setBaseline] = useState<File | null>(null);
  const [current, setCurrent] = useState<File | null>(null);

  const canSubmit = baseline && current && !busy;

  return (
    <form
      className="border border-rule bg-white/60 p-6"
      onSubmit={(e) => {
        e.preventDefault();
        if (baseline && current) onSubmit(baseline, current);
      }}
    >
      <p className="font-mono text-xs uppercase tracking-widest text-muted mb-1">Step 1</p>
      <h2 className="font-serif text-xl font-semibold text-ink mb-4">Upload two periods</h2>

      <label className="block mb-4">
        <span className="text-sm text-ink">Institution name</span>
        <input
          type="text"
          value={institutionName}
          onChange={(e) => onInstitutionNameChange(e.target.value)}
          placeholder="Used on the PDF cover"
          className="mt-1 w-full border border-rule bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-ink"
        />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <FileField
          label="Baseline period"
          hint="An earlier, normal period"
          file={baseline}
          onChange={setBaseline}
        />
        <FileField
          label="Current period"
          hint="The period you're auditing"
          file={current}
          onChange={setCurrent}
        />
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className="bg-ink text-paper px-4 py-2 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ink"
      >
        {busy ? "Analyzing\u2026" : "Generate report"}
      </button>
    </form>
  );
}

function FileField({
  label,
  hint,
  file,
  onChange,
}: {
  label: string;
  hint: string;
  file: File | null;
  onChange: (f: File) => void;
}) {
  return (
    <label className="block border border-dashed border-rule p-4 cursor-pointer hover:border-ink transition-colors">
      <span className="block text-sm font-medium text-ink">{label}</span>
      <span className="block text-xs text-muted mb-2">{hint}</span>
      <span className="block font-mono text-xs text-ink truncate">
        {file ? file.name : "No file chosen"}
      </span>
      <input
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onChange(f);
        }}
      />
    </label>
  );
}
