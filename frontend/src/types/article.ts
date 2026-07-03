export type GenerateArticleRequest = {
  topic: string;
  keywords: string[];
  target_audience: string;
  call_to_action: string;
};

export type ArticleJobStatus =
  | "RECEIVED"
  | "GENERATING"
  | "VALIDATING"
  | "REPAIRING"
  | "PUBLISHING"
  | "COMPLETED"
  | "FAILED_LLM"
  | "FAILED_VALIDATION"
  | "FAILED_WORDPRESS";

export type GenerateArticleAcceptedResponse = {
  job_id: string;
  status: ArticleJobStatus;
  status_url: string;
};

export type ArticleJobError = {
  code: string;
  message: string;
  retryable: boolean;
};

export type ArticleJobResponse = {
  job_id: string;
  status: ArticleJobStatus;
  title: string | null;
  wordpress_post_id: number | null;
  wordpress_status: string | null;
  wordpress_edit_url: string | null;
  error: ArticleJobError | null;
};

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    details?: unknown;
  };
};
