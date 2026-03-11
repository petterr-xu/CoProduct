import { z } from 'zod';

const uploadedFileSchema = z.object({
  fileId: z.string(),
  fileName: z.string(),
  fileSize: z.number(),
  parseStatus: z.enum(['PENDING', 'PARSING', 'DONE', 'FAILED'])
});

export const regenerateSchema = z
  .object({
    additionalContext: z.string().max(5000, '补充说明最多 5000 个字符'),
    attachments: z.array(uploadedFileSchema).max(5, '最多上传 5 个附件').optional()
  })
  .superRefine((data, ctx) => {
    const context = data.additionalContext.trim();
    const attachmentCount = data.attachments?.length ?? 0;
    if (!context && attachmentCount === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['additionalContext'],
        message: '请至少补充说明或上传附件'
      });
    }
  });

export type RegenerateSchema = z.infer<typeof regenerateSchema>;
