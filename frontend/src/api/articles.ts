import type {
  ApiErrorResponse,
  ArticleJobResponse,
  GenerateArticleAcceptedResponse,
  GenerateArticleRequest
} from "../types/article";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function generateAndPublishArticle(
  payload: GenerateArticleRequest
): Promise<GenerateArticleAcceptedResponse> {
  const response = await fetch(`${apiBaseUrl}/articles/generate-publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    const message = errorBody?.error?.message ?? "文章生成請求失敗，請稍後再試";
    throw new Error(message);
  }

  return response.json();
}

export async function getArticleJob(jobId: string): Promise<ArticleJobResponse> {
  const response = await fetch(`${apiBaseUrl}/articles/jobs/${jobId}`);

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    const message = errorBody?.error?.message ?? "無法取得文章任務狀態";
    throw new Error(message);
  }

  return response.json();
}
