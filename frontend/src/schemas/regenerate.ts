import { z } from 'zod';

export const regenerateSchema = z.object({
  additionalContext: z.string().min(1, '补充说明不能为空').max(5000, '补充说明最多 5000 个字符')
});

export type RegenerateSchema = z.infer<typeof regenerateSchema>;
