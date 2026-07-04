import { useEffect, useRef, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Bot, Loader2, Send, WandSparkles } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import toast from "react-hot-toast";

import { generateAndPublishArticle, getArticleJob } from "../api/articles";
import { articleFormSchema, type ArticleFormValues } from "../schemas/articleSchema";
import type { ArticleJobResponse, ArticleJobStatus } from "../types/article";
import { KeywordInput } from "./KeywordInput";
import { ResultCard } from "./ResultCard";

const defaultValues: ArticleFormValues = {
  topic: "",
  keywords: [],
  target_audience: "",
  call_to_action: ""
};

const terminalStatuses = new Set<ArticleJobStatus>([
  "COMPLETED",
  "FAILED_LLM",
  "FAILED_VALIDATION",
  "FAILED_WORDPRESS"
]);

const articleExamples: ArticleFormValues[] = [
  {
    topic: "企業如何利用 AI 客服降低營運成本",
    keywords: ["AI 客服", "企業自動化", "客服效率"],
    target_audience: "中小企業經營者",
    call_to_action: "預約一次客服流程健檢，了解 AI 客服可以先從哪裡導入"
  },
  {
    topic: "WordPress 結合生成式 AI 自動發布文章的方法",
    keywords: ["WordPress", "AI 寫作", "自動發布", "REST API"],
    target_audience: "網站管理員、工程師",
    call_to_action: "開始規劃你的第一條 WordPress 自動發文流程"
  },
  {
    topic: "React、FastAPI 與 WordPress 如何分工與串接",
    keywords: ["React", "FastAPI", "WordPress", "REST API"],
    target_audience: "初中階網頁工程師",
    call_to_action: "下載架構檢查清單，檢視你的前後端串接設計"
  },
  {
    topic: "AI 文章如何兼顧 SEO 與內容品質",
    keywords: ["SEO", "AI 內容", "關鍵字", "搜尋排名"],
    target_audience: "行銷與內容人員",
    call_to_action: "建立一份 AI 內容品質規範，讓團隊產出更穩定"
  },
  {
    topic: "製造業如何利用 AI 提升生產效率",
    keywords: ["智慧製造", "AI", "數位轉型", "設備資料"],
    target_audience: "製造業主管",
    call_to_action: "盤點現有設備資料，找出第一個可導入 AI 的流程"
  },
  {
    topic: "中小企業導入生成式 AI 前應注意的資安問題",
    keywords: ["生成式 AI", "資料安全", "隱私", "企業資安"],
    target_audience: "企業資訊主管",
    call_to_action: "安排一次 AI 使用風險盤點，建立內部安全準則"
  },
  {
    topic: "自建 AI 系統與使用 SaaS 服務的差異",
    keywords: ["AI SaaS", "自建系統", "成本比較", "資料控制"],
    target_audience: "技術主管、創業者",
    call_to_action: "用成本表比較自建與 SaaS，選出最適合目前階段的方案"
  },
  {
    topic: "使用 FastAPI 建立 WordPress 自動發文 API",
    keywords: ["FastAPI", "WordPress API", "Python", "JWT"],
    target_audience: "Python 開發者",
    call_to_action: "依照教學建立第一支自動發文 API 並完成本機測試"
  },
  {
    topic: "電商如何利用 AI 推薦提升商品頁轉換率",
    keywords: ["電商推薦", "AI 推薦系統", "商品頁優化", "轉換率"],
    target_audience: "電商品牌經營者",
    call_to_action: "檢查你的商品頁資料，找出最適合導入推薦模型的位置"
  },
  {
    topic: "在地商家如何用 SEO 內容提高 Google 搜尋曝光",
    keywords: ["在地 SEO", "Google 搜尋", "商家曝光", "內容行銷"],
    target_audience: "餐飲與服務業店家",
    call_to_action: "建立一份在地關鍵字清單，開始規劃每週內容主題"
  },
  {
    topic: "診所如何利用 AI 內容提升衛教文章產出效率",
    keywords: ["診所行銷", "AI 內容", "衛教文章", "醫療 SEO"],
    target_audience: "診所經營者、醫療行銷人員",
    call_to_action: "先從常見病症 FAQ 開始，建立可審核的 AI 內容流程"
  },
  {
    topic: "補教產業如何導入 AI 助教改善課後服務",
    keywords: ["AI 助教", "補教產業", "課後服務", "學習成效"],
    target_audience: "補習班經營者、教育產品負責人",
    call_to_action: "盤點學生常見問題，設計第一版 AI 助教知識庫"
  },
  {
    topic: "房地產業如何用內容行銷建立專業信任",
    keywords: ["房地產行銷", "內容行銷", "SEO", "買房知識"],
    target_audience: "房仲品牌與代銷團隊",
    call_to_action: "整理客戶最常問的買房問題，轉成可搜尋的文章主題"
  },
  {
    topic: "旅遊業如何用 AI 快速產出行程推薦文章",
    keywords: ["旅遊內容", "AI 行程", "行程推薦", "SEO 文章"],
    target_audience: "旅行社、旅遊內容編輯",
    call_to_action: "選定一個目的地，建立第一批 AI 輔助行程文章"
  },
  {
    topic: "金融科技產品如何用 SEO 教育潛在客戶",
    keywords: ["金融科技", "SEO 教育內容", "理財工具", "信任建立"],
    target_audience: "FinTech 行銷與產品團隊",
    call_to_action: "建立內容漏斗，讓使用者先理解問題再認識產品"
  },
  {
    topic: "人資團隊導入 AI 履歷篩選時該注意什麼",
    keywords: ["AI 招募", "履歷篩選", "人資科技", "公平性"],
    target_audience: "人資主管、招募團隊",
    call_to_action: "制定 AI 招募使用規範，避免黑箱決策影響候選人"
  },
  {
    topic: "客服知識庫如何搭配生成式 AI 提升回覆品質",
    keywords: ["客服知識庫", "生成式 AI", "客服品質", "知識管理"],
    target_audience: "客服主管、營運團隊",
    call_to_action: "先整理前 50 個高頻問題，建立 AI 可引用的知識庫"
  },
  {
    topic: "SaaS 新產品上市前應如何規劃 SEO 內容",
    keywords: ["SaaS 行銷", "產品上市", "SEO 策略", "內容規劃"],
    target_audience: "SaaS 創辦人、產品行銷",
    call_to_action: "用目標客戶的搜尋問題，建立上市前 30 天內容清單"
  },
  {
    topic: "行銷團隊如何用 GA4 資料改善內容策略",
    keywords: ["GA4", "內容策略", "流量分析", "SEO 成效"],
    target_audience: "數位行銷人員、內容主管",
    call_to_action: "檢查前 10 篇高流量文章，找出可複製的內容模式"
  },
  {
    topic: "如何用 Docker 建立本機 WordPress 測試環境",
    keywords: ["Docker", "WordPress", "本機開發", "測試環境"],
    target_audience: "網頁工程師、技術 PM",
    call_to_action: "建立一個乾淨的本機 WordPress，讓 API 串接測試更穩定"
  },
  {
    topic: "品牌如何建立 AI 內容產製的審核流程",
    keywords: ["AI 內容策略", "品牌聲音", "內容審核", "行銷流程"],
    target_audience: "品牌行銷主管、內容團隊",
    call_to_action: "定義品牌語氣與審核標準，讓 AI 內容更符合品牌定位"
  },
  {
    topic: "Zapier、自建 API 與 AI Agent 自動化的差異",
    keywords: ["Zapier", "API 自動化", "AI Agent", "流程整合"],
    target_audience: "營運主管、自動化顧問",
    call_to_action: "列出現有重複流程，評估哪些適合工具串接或自建系統"
  },
  {
    topic: "法律服務業如何安全導入 AI 文件摘要",
    keywords: ["法律科技", "AI 摘要", "文件處理", "資料保密"],
    target_audience: "律師事務所、法務主管",
    call_to_action: "先從非敏感文件開始試點，建立 AI 文件處理規範"
  },
  {
    topic: "零售品牌如何用會員資料提升再行銷成效",
    keywords: ["會員資料", "再行銷", "零售數據", "顧客分群"],
    target_audience: "零售品牌、CRM 團隊",
    call_to_action: "盤點會員資料欄位，建立第一版顧客分群策略"
  },
  {
    topic: "企業 ESG 報告如何轉化為可搜尋的內容資產",
    keywords: ["ESG", "永續報告", "內容資產", "企業溝通"],
    target_audience: "企業永續部門、公關團隊",
    call_to_action: "選出 ESG 報告中的三個亮點，改寫成對外溝通文章"
  },
  {
    topic: "CRM 系統如何結合 AI 提升業務跟進效率",
    keywords: ["CRM", "AI 業務助理", "銷售流程", "客戶管理"],
    target_audience: "業務主管、CRM 管理者",
    call_to_action: "檢查 CRM 中的跟進紀錄，找出最適合 AI 提醒的節點"
  },
  {
    topic: "App 成長團隊如何用內容降低使用者教育成本",
    keywords: ["App Growth", "使用者教育", "內容行銷", "新手引導"],
    target_audience: "App 產品經理、成長行銷",
    call_to_action: "整理新手常見卡點，規劃一組可搜尋的教學內容"
  },
  {
    topic: "B2B 企業如何用技術文章建立銷售信任",
    keywords: ["B2B 行銷", "技術文章", "銷售漏斗", "專業信任"],
    target_audience: "B2B 行銷、售前團隊",
    call_to_action: "把售前常見問題整理成技術文章，縮短客戶評估時間"
  },
  {
    topic: "到府服務業如何設計能帶來詢問的 SEO 文章",
    keywords: ["到府服務", "SEO 文章", "詢問轉換", "在地關鍵字"],
    target_audience: "清潔、維修、居家服務業者",
    call_to_action: "挑選三個服務地區，建立對應的在地 SEO 文章主題"
  },
  {
    topic: "企業導入 AI 寫作後如何建立內容治理機制",
    keywords: ["AI 寫作", "內容治理", "審核流程", "企業知識"],
    target_audience: "內容主管、知識管理負責人",
    call_to_action: "制定 AI 內容治理清單，確保每篇文章都有來源與審核紀錄"
  }
];

function isTerminalStatus(status: ArticleJobStatus | undefined) {
  return status ? terminalStatuses.has(status) : false;
}

export function ArticleForm() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [lastExampleIndex, setLastExampleIndex] = useState<number | null>(null);
  const notifiedStatusRef = useRef<string | null>(null);
  const form = useForm<ArticleFormValues>({
    resolver: zodResolver(articleFormSchema),
    defaultValues
  });

  const mutation = useMutation({
    mutationFn: generateAndPublishArticle,
    onSuccess: (data) => {
      setJobId(data.job_id);
      toast.success("文章任務已送出");
    },
    onError: (error) => {
      toast.error(error.message);
    }
  });

  const jobQuery = useQuery({
    queryKey: ["article-job", jobId],
    queryFn: () => getArticleJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return isTerminalStatus(status) ? false : 1500;
    }
  });

  useEffect(() => {
    const job = jobQuery.data;
    if (!job || !isTerminalStatus(job.status)) {
      return;
    }

    const notificationKey = `${job.job_id}:${job.status}`;
    if (notifiedStatusRef.current === notificationKey) {
      return;
    }

    notifiedStatusRef.current = notificationKey;
    if (job.status === "COMPLETED") {
      toast.success("WordPress 草稿已建立");
      return;
    }

    toast.error(job.error?.message ?? "文章任務執行失敗");
  }, [jobQuery.data]);

  function onSubmit(values: ArticleFormValues) {
    mutation.reset();
    setJobId(null);
    notifiedStatusRef.current = null;
    mutation.mutate(values);
  }

  function applyRandomExample() {
    const nextIndex = pickRandomExampleIndex(lastExampleIndex);
    const nextExample = articleExamples[nextIndex];
    form.reset(nextExample);
    setLastExampleIndex(nextIndex);
    toast.success(`已套用隨機範例：${nextExample.topic}`);
  }

  const queuedJob: ArticleJobResponse | null = mutation.data
    ? {
        job_id: mutation.data.job_id,
        status: mutation.data.status,
        title: null,
        wordpress_post_id: null,
        wordpress_status: null,
        wordpress_edit_url: null,
        tool_status: null,
        error: null
      }
    : null;
  const currentJob = jobQuery.data ?? queuedJob;
  const disabled = mutation.isPending || Boolean(currentJob && !isTerminalStatus(currentJob.status));

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="rounded-md border border-slate-200 bg-white p-5 shadow-2xl shadow-slate-200/70 sm:p-7"
      >
        <div className="mb-6 flex flex-col gap-4 border-b border-slate-100 pb-6 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-sm font-medium text-[#237f86]">
              <Bot className="h-4 w-4" />
              Agent Writer
            </div>
            <h2 className="text-2xl font-semibold tracking-normal text-slate-950">
              建立 SEO 文章任務
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              填入文章 brief 後，系統會依序執行搜尋脈絡、生成、評論、修稿與 WordPress 草稿建立。
            </p>
          </div>
          <button
            type="button"
            onClick={applyRandomExample}
            disabled={disabled}
            className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-md border border-cyan-100 bg-cyan-50 px-3 text-sm font-medium text-[#237f86] transition hover:border-cyan-200 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            <WandSparkles className="h-4 w-4" />
            隨機範例（30 種）
          </button>
        </div>

        <div className="grid gap-5">
          <div className="flex flex-col gap-2">
            <label htmlFor="topic" className="text-sm font-medium text-slate-800">
              文章主題
            </label>
            <input
              id="topic"
              disabled={disabled}
              className="h-12 rounded-md border border-slate-200 bg-white px-4 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-[#5bc5c7] focus:ring-4 focus:ring-cyan-100 disabled:bg-slate-100"
              placeholder="例如：AI 文章如何兼顧 SEO 與內容品質"
              {...form.register("topic")}
            />
            {form.formState.errors.topic ? (
              <p className="text-sm text-red-600">{form.formState.errors.topic.message}</p>
            ) : null}
          </div>

          <Controller
            control={form.control}
            name="keywords"
            render={({ field, fieldState }) => (
              <KeywordInput
                value={field.value}
                onChange={field.onChange}
                disabled={disabled}
                error={fieldState.error?.message}
              />
            )}
          />

          <div className="grid gap-5 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label htmlFor="target_audience" className="text-sm font-medium text-slate-800">
                目標受眾
              </label>
              <input
                id="target_audience"
                disabled={disabled}
                className="h-12 rounded-md border border-slate-200 bg-white px-4 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-[#5bc5c7] focus:ring-4 focus:ring-cyan-100 disabled:bg-slate-100"
                placeholder="例如：行銷與內容人員"
                {...form.register("target_audience")}
              />
              {form.formState.errors.target_audience ? (
                <p className="text-sm text-red-600">
                  {form.formState.errors.target_audience.message}
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="call_to_action" className="text-sm font-medium text-slate-800">
                行動呼籲
              </label>
              <textarea
                id="call_to_action"
                disabled={disabled}
                rows={3}
                className="min-h-12 resize-none rounded-md border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-[#5bc5c7] focus:ring-4 focus:ring-cyan-100 disabled:bg-slate-100"
                placeholder="例如：建立一份 AI 內容品質規範，讓團隊產出更穩定"
                {...form.register("call_to_action")}
              />
              {form.formState.errors.call_to_action ? (
                <p className="text-sm text-red-600">
                  {form.formState.errors.call_to_action.message}
                </p>
              ) : null}
            </div>
          </div>
        </div>

        <div className="mt-7 flex flex-col gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="inline-flex items-center gap-2 text-sm text-slate-500">
            <WandSparkles className="h-4 w-4 text-[#237f86]" />
            最多 1 次搜尋工具，最多 4 次 LLM
          </div>
          <button
            type="submit"
            disabled={disabled}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-slate-950 px-5 font-semibold text-white transition hover:bg-[#1f8f94] disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {disabled ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            {disabled ? "任務執行中" : "開始生成草稿"}
            {!disabled ? <ArrowRight className="h-5 w-5" /> : null}
          </button>
        </div>
      </form>

      <aside>
        {currentJob ? (
          <ResultCard result={currentJob} />
        ) : (
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-2xl shadow-slate-200/70">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
              Live Preview
            </p>
            <h2 className="mt-2 text-xl font-semibold text-slate-950">等待文章任務</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              送出表單後，這裡會顯示 job 狀態、每個處理階段，以及 WordPress draft 連結。
            </p>
            <div className="mt-6 space-y-3">
              {["Search context", "Producer draft", "Critique review", "WordPress draft"].map(
                (label) => (
                  <div key={label} className="flex items-center gap-3 text-sm text-slate-500">
                    <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
                    {label}
                  </div>
                )
              )}
            </div>
          </section>
        )}
      </aside>
    </div>
  );
}

function pickRandomExampleIndex(previousIndex: number | null) {
  if (articleExamples.length <= 1) {
    return 0;
  }

  let nextIndex = previousIndex ?? 0;
  while (nextIndex === previousIndex) {
    nextIndex = Math.floor(Math.random() * articleExamples.length);
  }
  return nextIndex;
}
