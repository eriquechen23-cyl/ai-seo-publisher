import { KeyboardEvent, useState } from "react";
import { Plus, X } from "lucide-react";

type KeywordInputProps = {
  value: string[];
  onChange: (keywords: string[]) => void;
  disabled?: boolean;
  error?: string;
};

export function KeywordInput({ value, onChange, disabled, error }: KeywordInputProps) {
  const [draft, setDraft] = useState("");

  function addKeyword() {
    const keyword = draft.trim();
    if (!keyword || value.includes(keyword) || value.length >= 10) {
      setDraft("");
      return;
    }

    onChange([...value, keyword]);
    setDraft("");
  }

  function removeKeyword(keyword: string) {
    onChange(value.filter((item) => item !== keyword));
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      addKeyword();
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-800">SEO 關鍵字</label>
      <div className="flex gap-2">
        <input
          className="h-12 min-w-0 flex-1 rounded-md border border-slate-200 bg-white px-4 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-[#5bc5c7] focus:ring-4 focus:ring-cyan-100 disabled:bg-slate-100"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="輸入後按 Enter，例如：AI SEO"
        />
        <button
          type="button"
          onClick={addKeyword}
          disabled={disabled}
          className="inline-flex h-12 w-12 items-center justify-center rounded-md bg-slate-950 text-white transition hover:bg-[#1f8f94] disabled:cursor-not-allowed disabled:bg-slate-300"
          aria-label="新增關鍵字"
          title="新增關鍵字"
        >
          <Plus className="h-5 w-5" />
        </button>
      </div>

      <div className="flex min-h-10 flex-wrap gap-2">
        {value.map((keyword) => (
          <span
            key={keyword}
            className="inline-flex h-9 items-center gap-2 rounded-md border border-cyan-100 bg-cyan-50 px-3 text-sm font-medium text-[#237f86]"
          >
            {keyword}
            <button
              type="button"
              onClick={() => removeKeyword(keyword)}
              disabled={disabled}
              className="inline-flex h-5 w-5 items-center justify-center rounded text-[#237f86] transition hover:bg-cyan-100 disabled:opacity-50"
              aria-label={`移除 ${keyword}`}
              title={`移除 ${keyword}`}
            >
              <X className="h-4 w-4" />
            </button>
          </span>
        ))}
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
