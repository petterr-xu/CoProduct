import { z } from 'zod';

export const createReviewSchema = z.object({
  requirementText: z
    .string()
    .min(10, '需求描述至少 10 个字符')
    .max(5000, '需求描述最多 5000 个字符'),
  backgroundText: z.string().max(5000, '背景说明最多 5000 个字符').optional().or(z.literal('')),
  businessDomain: z.string().max(100, '业务域长度过长').optional().or(z.literal('')),
  moduleHint: z.string().max(100, '模块提示长度过长').optional().or(z.literal('')),
  attachments: z
    .array(
      z.object({
        fileId: z.string(),
        fileName: z.string(),
        fileSize: z.number(),
        parseStatus: z.string().optional()
      })
    )
    .max(5, '最多上传 5 个附件')
    .optional()
});

export type CreateReviewSchema = z.infer<typeof createReviewSchema>;
