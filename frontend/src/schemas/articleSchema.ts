import { z } from "zod";

export const articleFormSchema = z.object({
  topic: z.string().trim().min(3, "請至少輸入 3 個字的文章主題"),
  keywords: z
    .array(z.string().trim().min(1))
    .min(1, "請至少輸入 1 個 SEO 關鍵字")
    .max(10, "最多可輸入 10 個關鍵字"),
  target_audience: z.string().trim().min(2, "請描述目標受眾"),
  call_to_action: z.string().trim().min(2, "請輸入行動呼籲")
});

export type ArticleFormValues = z.infer<typeof articleFormSchema>;
