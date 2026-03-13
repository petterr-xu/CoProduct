'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import { DebugOptions } from '@/components/business/debug-options';
import { ErrorAlert } from '@/components/base/error-alert';
import { FileUploader } from '@/components/base/file-uploader';
import { SubmitButton } from '@/components/base/submit-button';
import { useCreatePrereview } from '@/hooks/use-prereview-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { createReviewSchema, CreateReviewSchema } from '@/schemas/create-review';
import { isAdminRole, isWriteRole, useAuthStore } from '@/stores/auth-store';
import { PreReviewDebugOptions } from '@/types';
import { useCreateReviewDraftStore } from '@/stores/create-review-draft';

const DRAFT_KEY = 'coproduct:create-review:draft';

const EXAMPLE_TEXT =
  '运营希望按活动批量导出用户报名信息，不同角色导出的字段不一样，主管可以导出手机号。';

type SubmissionPhase = 'IDLE' | 'SUBMITTING' | 'ACCEPTED';

export function CreateReviewForm() {
  const router = useRouter();
  const mutation = useCreatePrereview();
  const draftStore = useCreateReviewDraftStore();
  const role = useAuthStore((state) => state.user?.role);
  const canWrite = isWriteRole(role);
  const canUseDebugOptions = isAdminRole(role);
  const [debugOptions, setDebugOptions] = useState<PreReviewDebugOptions | undefined>(undefined);
  const [submissionPhase, setSubmissionPhase] = useState<SubmissionPhase>('IDLE');
  const [submissionHint, setSubmissionHint] = useState<string | null>(null);
  const isSubmitting = mutation.isPending || submissionPhase !== 'IDLE';

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
    if (!canWrite) return;
    if (submissionPhase === 'ACCEPTED') {
      setSubmissionHint('任务已受理，请在详情页查看进度。');
      return;
    }
    if (mutation.isPending) return;

    setSubmissionHint(null);
    setSubmissionPhase('SUBMITTING');
    try {
      const result = await mutation.mutateAsync({
        requirementText: values.requirementText,
        backgroundText: values.backgroundText,
        businessDomain: values.businessDomain,
        moduleHint: values.moduleHint,
        attachments: values.attachments,
        debugOptions: canUseDebugOptions ? debugOptions : undefined
      });
      setSubmissionPhase('ACCEPTED');
      setSubmissionHint('任务已受理，正在跳转详情页并进入轮询。');
      router.push(`/prereview/${result.sessionId}`);
    } catch {
      setSubmissionPhase('IDLE');
    }
  });

  return (
    <form className='space-y-4' onSubmit={onSubmit}>
      {mutation.error ? <ErrorAlert message={getApiErrorMessage(mutation.error)} /> : null}
      {submissionHint ? (
        <section className='rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-info'>{submissionHint}</section>
      ) : null}
      {!canWrite ? <ErrorAlert title='当前账号只读' message='VIEWER 角色不可发起预审，请联系管理员分配写权限。' /> : null}

      <div className='space-y-1'>
        <label className='text-sm font-medium'>需求描述 *</label>
        <textarea
          className='min-h-36 w-full rounded-md border border-black/20 bg-white p-3 text-sm outline-none focus:border-black/50'
          placeholder='请输入业务需求描述'
          disabled={!canWrite || isSubmitting}
          {...register('requirementText')}
        />
        <p className='text-xs text-danger'>{errors.requirementText?.message}</p>
      </div>

      <div className='space-y-1'>
        <label className='text-sm font-medium'>背景说明</label>
        <textarea
          className='min-h-24 w-full rounded-md border border-black/20 bg-white p-3 text-sm outline-none focus:border-black/50'
          placeholder='补充背景、动因和现状'
          disabled={!canWrite || isSubmitting}
          {...register('backgroundText')}
        />
      </div>

      <div className='grid gap-4 md:grid-cols-2'>
        <div className='space-y-1'>
          <label className='text-sm font-medium'>业务域</label>
          <input
            className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            placeholder='如 activity'
            disabled={!canWrite || isSubmitting}
            {...register('businessDomain')}
          />
        </div>
        <div className='space-y-1'>
          <label className='text-sm font-medium'>模块提示</label>
          <input
            className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            placeholder='如 registration'
            disabled={!canWrite || isSubmitting}
            {...register('moduleHint')}
          />
        </div>
      </div>

      <div className='space-y-1'>
        <label className='text-sm font-medium'>附件</label>
        <FileUploader
          files={attachments}
          onChange={(files) => setValue('attachments', files)}
          disabled={!canWrite || isSubmitting}
        />
      </div>

      {canUseDebugOptions ? (
        <DebugOptions value={debugOptions} disabled={!canWrite || isSubmitting} onChange={setDebugOptions} />
      ) : null}

      <div className='flex flex-wrap items-center gap-2'>
        <SubmitButton loading={isSubmitting} disabled={!canWrite || isSubmitting}>
          发起预审
        </SubmitButton>
        <button
          type='button'
          className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm disabled:opacity-60'
          disabled={!canWrite || isSubmitting}
          onClick={() => setValue('requirementText', EXAMPLE_TEXT)}
        >
          一键填充示例
        </button>
      </div>
    </form>
  );
}
