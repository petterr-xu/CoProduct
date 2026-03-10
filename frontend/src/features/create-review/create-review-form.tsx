'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';

import { ErrorAlert } from '@/components/base/error-alert';
import { FileUploader } from '@/components/base/file-uploader';
import { SubmitButton } from '@/components/base/submit-button';
import { useCreatePreReview } from '@/hooks/use-review-api';
import { createReviewSchema, CreateReviewSchema } from '@/schemas/create-review';
import { useCreateReviewDraftStore } from '@/stores/create-review-draft';

const DRAFT_KEY = 'coproduct:create-review:draft';

const EXAMPLE_TEXT =
  '运营希望按活动批量导出用户报名信息，不同角色导出的字段不一样，主管可以导出手机号。';

export function CreateReviewForm() {
  const router = useRouter();
  const mutation = useCreatePreReview();
  const draftStore = useCreateReviewDraftStore();

  const defaults = useMemo(
    () => ({
      requirementText: draftStore.requirementText,
      backgroundText: draftStore.backgroundText,
      businessDomain: draftStore.businessDomain,
      moduleHint: draftStore.moduleHint,
      attachments: []
    }),
    [draftStore.backgroundText, draftStore.businessDomain, draftStore.moduleHint, draftStore.requirementText]
  );

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<CreateReviewSchema>({
    resolver: zodResolver(createReviewSchema),
    defaultValues: defaults
  });

  const attachments = watch('attachments') ?? [];

  useEffect(() => {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as Partial<CreateReviewSchema>;
      if (parsed.requirementText) setValue('requirementText', parsed.requirementText);
      if (parsed.backgroundText) setValue('backgroundText', parsed.backgroundText);
      if (parsed.businessDomain) setValue('businessDomain', parsed.businessDomain);
      if (parsed.moduleHint) setValue('moduleHint', parsed.moduleHint);
    } catch {
      // ignore invalid local draft
    }
  }, [setValue]);

  useEffect(() => {
    const subscription = watch((values) => {
      const nextDraft = {
        requirementText: values.requirementText ?? '',
        backgroundText: values.backgroundText ?? '',
        businessDomain: values.businessDomain ?? '',
        moduleHint: values.moduleHint ?? ''
      };
      draftStore.setDraft(nextDraft);
      localStorage.setItem(DRAFT_KEY, JSON.stringify(nextDraft));
    });
    return () => subscription.unsubscribe();
  }, [draftStore, watch]);

  const onSubmit = handleSubmit(async (values) => {
    const result = await mutation.mutateAsync({
      requirementText: values.requirementText,
      backgroundText: values.backgroundText,
      businessDomain: values.businessDomain,
      moduleHint: values.moduleHint,
      attachments: values.attachments
    });
    router.push(`/review/${result.sessionId}`);
  });

  return (
    <form className='space-y-4' onSubmit={onSubmit}>
      {mutation.error ? <ErrorAlert message={mutation.error.message} /> : null}

      <div className='space-y-1'>
        <label className='text-sm font-medium'>需求描述 *</label>
        <textarea
          className='min-h-36 w-full rounded-md border border-black/20 bg-white p-3 text-sm outline-none focus:border-black/50'
          placeholder='请输入业务需求描述'
          {...register('requirementText')}
        />
        <p className='text-xs text-danger'>{errors.requirementText?.message}</p>
      </div>

      <div className='space-y-1'>
        <label className='text-sm font-medium'>背景说明</label>
        <textarea
          className='min-h-24 w-full rounded-md border border-black/20 bg-white p-3 text-sm outline-none focus:border-black/50'
          placeholder='补充背景、动因和现状'
          {...register('backgroundText')}
        />
      </div>

      <div className='grid gap-4 md:grid-cols-2'>
        <div className='space-y-1'>
          <label className='text-sm font-medium'>业务域</label>
          <input
            className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            placeholder='如 activity'
            {...register('businessDomain')}
          />
        </div>
        <div className='space-y-1'>
          <label className='text-sm font-medium'>模块提示</label>
          <input
            className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            placeholder='如 registration'
            {...register('moduleHint')}
          />
        </div>
      </div>

      <div className='space-y-1'>
        <label className='text-sm font-medium'>附件</label>
        <FileUploader files={attachments} onChange={(files) => setValue('attachments', files)} />
      </div>

      <div className='flex flex-wrap items-center gap-2'>
        <SubmitButton loading={mutation.isPending}>发起预审</SubmitButton>
        <button
          type='button'
          className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm'
          onClick={() => setValue('requirementText', EXAMPLE_TEXT)}
        >
          一键填充示例
        </button>
      </div>
    </form>
  );
}
