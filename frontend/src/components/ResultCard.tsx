import { AlertCircle, CheckCircle2, ExternalLink, Loader2, RadioTower } from "lucide-react";

import type { ArticleJobResponse, ArticleJobStatus } from "../types/article";

type ResultCardProps = {
  result: ArticleJobResponse;
};

const statusLabels: Record<ArticleJobStatus, string> = {
  RECEIVED: "已收到任務",
  GENERATING: "Producer 正在生成",
  VALIDATING: "正在驗證文章品質",
  REPAIRING: "Critique 正在反思修稿",
  PUBLISHING: "正在建立 WordPress 草稿",
  COMPLETED: "WordPress 草稿已建立",
  FAILED_LLM: "LLM 生成失敗",
  FAILED_VALIDATION: "文章驗證失敗",
  FAILED_WORDPRESS: "WordPress 發布失敗"
};

const stepOrder: ArticleJobStatus[] = [
  "RECEIVED",
  "GENERATING",
  "VALIDATING",
  "REPAIRING",
  "PUBLISHING",
  "COMPLETED"
];

const failedStatuses = new Set<ArticleJobStatus>([
  "FAILED_LLM",
  "FAILED_VALIDATION",
  "FAILED_WORDPRESS"
]);

export function ResultCard({ result }: ResultCardProps) {
  const isCompleted = result.status === "COMPLETED";
  const isFailed = failedStatuses.has(result.status);
  const StatusIcon = isCompleted ? CheckCircle2 : isFailed ? AlertCircle : Loader2;
  const activeIndex = Math.max(stepOrder.indexOf(result.status), 0);

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-2xl shadow-slate-200/70">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
            Job Status
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">
            {statusLabels[result.status]}
          </h2>
        </div>
        <span
          className={`inline-flex h-11 w-11 items-center justify-center rounded-md ${
            isCompleted
              ? "bg-emerald-50 text-emerald-700"
              : isFailed
                ? "bg-red-50 text-red-700"
                : "bg-cyan-50 text-[#237f86]"
          }`}
        >
          <StatusIcon className={`h-5 w-5 ${!isCompleted && !isFailed ? "animate-spin" : ""}`} />
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {stepOrder.slice(0, 5).map((status, index) => {
          const reached = isCompleted || activeIndex >= index;
          const current = result.status === status;

          return (
            <div key={status} className="flex items-center gap-3">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  reached ? "bg-[#5bc5c7]" : "bg-slate-200"
                } ${current ? "ring-4 ring-cyan-100" : ""}`}
              />
              <span className={`text-sm ${reached ? "text-slate-800" : "text-slate-400"}`}>
                {statusLabels[status]}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-6 rounded-md bg-slate-50 p-4">
        <dl className="grid gap-3 text-sm text-slate-600">
          <div>
            <dt className="font-medium text-slate-950">Job ID</dt>
            <dd className="mt-1 break-all font-mono text-xs">{result.job_id}</dd>
          </div>
          {result.title ? (
            <div>
              <dt className="font-medium text-slate-950">文章標題</dt>
              <dd className="mt-1">{result.title}</dd>
            </div>
          ) : null}
          {result.wordpress_post_id ? (
            <div>
              <dt className="font-medium text-slate-950">WordPress Post ID</dt>
              <dd className="mt-1">{result.wordpress_post_id}</dd>
            </div>
          ) : null}
        </dl>
      </div>

      {result.error ? (
        <p className="mt-4 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700">
          {result.error.message}
        </p>
      ) : null}

      {result.wordpress_edit_url ? (
        <a
          href={result.wordpress_edit_url}
          target="_blank"
          rel="noreferrer"
          className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-[#1f8f94]"
        >
          <ExternalLink className="h-4 w-4" />
          開啟 WordPress 草稿
        </a>
      ) : (
        <div className="mt-5 inline-flex items-center gap-2 text-sm text-slate-500">
          <RadioTower className="h-4 w-4" />
          等待下一次狀態更新
        </div>
      )}
    </section>
  );
}
