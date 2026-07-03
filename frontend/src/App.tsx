import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileText,
  PenLine,
  Search,
  ShieldCheck,
  Sparkles
} from "lucide-react";

import { ArticleForm } from "./components/ArticleForm";

const navItems = ["工作流程", "Search API", "Producer", "Critique", "WordPress"];

const metrics = [
  ["1x", "Search Tool"],
  ["4x", "最多 LLM"],
  ["Draft", "WordPress"]
];

const workflowItems = [
  {
    icon: Search,
    title: "Search API",
    copy: "先取得搜尋脈絡與參考摘要，讓文章有外部資訊支撐，但不讓 LLM 任意瀏覽網頁。"
  },
  {
    icon: PenLine,
    title: "Producer",
    copy: "根據主題、關鍵字、受眾與 CTA，生成可發布的 WordPress HTML 草稿。"
  },
  {
    icon: BrainCircuit,
    title: "Critique",
    copy: "以 critic pattern 檢查 SEO、結構、內容完整度與發布品質。"
  },
  {
    icon: ShieldCheck,
    title: "Validator",
    copy: "最後由規則驗證與 HTML sanitizer 把關，再建立 WordPress draft。"
  }
];

export default function App() {
  return (
    <main className="min-h-screen bg-[#f7faf9] text-slate-950">
      <section className="relative overflow-hidden bg-[linear-gradient(120deg,#f8fffd_0%,#ffffff_48%,#fff8ef_100%)]">
        <div className="absolute inset-x-0 top-0 h-64 bg-white/60 backdrop-blur-sm" />
        <div className="absolute -right-24 top-28 h-96 w-96 rounded-full bg-cyan-100/70 blur-3xl" />
        <div className="absolute -left-24 bottom-16 h-80 w-80 rounded-full bg-orange-100/60 blur-3xl" />

        <div className="relative mx-auto flex min-h-screen w-full max-w-[1560px] flex-col px-5 sm:px-8 xl:px-10">
          <header className="flex h-20 items-center justify-between border-b border-slate-200/70">
            <a href="#generator" className="inline-flex items-center gap-3" aria-label="AI SEO Publisher">
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-md bg-[#5bc5c7] text-white shadow-sm shadow-cyan-100">
                <Sparkles className="h-5 w-5" />
              </span>
              <span className="text-sm font-semibold tracking-[0.18em] text-slate-700">
                AI SEO Publisher
              </span>
            </a>

            <nav className="hidden items-center gap-7 text-sm text-slate-500 lg:flex">
              {navItems.map((item) => (
                <a key={item} href="#pipeline" className="transition hover:text-slate-950">
                  {item}
                </a>
              ))}
            </nav>

            <a
              href="#generator"
              className="inline-flex h-11 items-center justify-center rounded-md bg-slate-950 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1f8f94]"
            >
              開始生成
            </a>
          </header>

          <div className="grid flex-1 items-center gap-8 py-10 lg:grid-cols-[0.42fr_0.58fr] xl:gap-12">
            <div className="relative z-10 max-w-2xl rounded-[1.5rem] bg-white/72 p-5 shadow-sm backdrop-blur sm:p-7 lg:bg-transparent lg:p-0 lg:shadow-none lg:backdrop-blur-0">
              <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-100 bg-white px-4 py-2 text-sm font-medium text-[#237f86] shadow-sm">
                <Sparkles className="h-4 w-4" />
                Search API + Critic Pattern
              </p>

              <h1 className="text-5xl font-semibold leading-[1.03] tracking-normal text-slate-950 md:text-6xl xl:text-7xl">
                AI SEO 自動發文工作台
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
                結合搜尋資料、Producer 生成與 Critique 反思，
                將 SEO 文章從研究到 WordPress 草稿建立串成同一條流程。
              </p>

              <div className="mt-8 grid max-w-xl grid-cols-3 gap-3">
                {metrics.map(([value, label]) => (
                  <div key={label} className="rounded-md border border-slate-200 bg-white/92 p-4 shadow-sm">
                    <div className="text-2xl font-semibold text-slate-950">{value}</div>
                    <div className="mt-1 text-sm text-slate-500">{label}</div>
                  </div>
                ))}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  href="#generator"
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#1f8f94] px-5 font-semibold text-white shadow-sm transition hover:bg-slate-950"
                >
                  建立文章任務
                  <ArrowRight className="h-5 w-5" />
                </a>
                <a
                  href="#pipeline"
                  className="inline-flex h-12 items-center justify-center rounded-md border border-slate-200 bg-white px-5 font-semibold text-slate-800 shadow-sm transition hover:border-cyan-200 hover:text-[#237f86]"
                >
                  查看流程
                </a>
              </div>
            </div>

            <div className="relative min-h-[360px] lg:min-h-[620px]">
              <div className="absolute inset-0 rounded-[2rem] bg-[#2b343c] opacity-95 shadow-2xl shadow-slate-300/60 lg:-right-28" />
              <div className="absolute inset-x-0 top-8 overflow-hidden rounded-[2rem] bg-white shadow-2xl shadow-slate-300/70 lg:-right-36 lg:left-0 lg:top-10">
                <img
                  src="/ai-seo-hero.png"
                  alt="AI SEO Publisher dashboard"
                  className="h-full min-h-[330px] w-full object-cover object-center lg:min-h-[540px]"
                />
              </div>
              <div className="absolute bottom-8 left-6 hidden rounded-md border border-white/60 bg-white/88 px-4 py-3 text-sm text-slate-700 shadow-xl backdrop-blur md:block">
                <div className="flex items-center gap-2 font-medium text-slate-950">
                  <CheckCircle2 className="h-4 w-4 text-[#1f8f94]" />
                  WordPress 草稿已準備
                </div>
                <p className="mt-1 text-slate-500">搜尋、生成、反思、建立草稿</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="generator" className="relative z-10 w-full px-5 py-16 sm:px-8 xl:px-10">
        <div className="mx-auto max-w-[1480px]">
          <ArticleForm />
        </div>
      </section>

      <section id="pipeline" className="w-full px-5 pb-20 sm:px-8 xl:px-10">
        <div className="mx-auto max-w-[1480px]">
          <div className="mb-8 flex flex-col gap-2">
            <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.16em] text-[#237f86]">
              <FileText className="h-4 w-4" />
              Agent Pipeline
            </p>
            <h2 className="text-3xl font-semibold tracking-normal text-slate-950">
              可追蹤的 SEO 發文代理流程
            </h2>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {workflowItems.map((item) => {
              const Icon = item.icon;
              return (
                <article key={item.title} className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-md bg-cyan-50 text-[#237f86] ring-1 ring-cyan-100">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-950">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.copy}</p>
                </article>
              );
            })}
          </div>

          <div className="mt-8 rounded-md border border-slate-200 bg-[#2b343c] p-6 text-white shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-200">
                  WordPress-ready
                </p>
                <h3 className="mt-2 text-2xl font-semibold tracking-normal">
                  將搜尋脈絡、文章生成、品質反思與草稿建立整合在同一個任務。
                </h3>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-200">
                <CheckCircle2 className="h-5 w-5 text-cyan-200" />
                Draft flow ready
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
