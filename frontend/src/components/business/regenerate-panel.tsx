'use client';

import { useState } from 'react';

import { DebugOptions } from '@/components/business/debug-options';
import { ErrorAlert } from '@/components/base/error-alert';
import { FileUploader } from '@/components/base/file-uploader';
import { SubmitButton } from '@/components/base/submit-button';
import { regenerateSchema } from '@/schemas/regenerate';
import { PreReviewDebugOptions, UploadedFileRef } from '@/types';

type Props = {
  onSubmit: (payload: {
    additionalContext: string;
    attachments: UploadedFileRef[];
    debugOptions?: PreReviewDebugOptions;
  }) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  showDebugOptions?: boolean;
};

export function RegeneratePanel({ onSubmit, loading, disabled = false, showDebugOptions = false }: Props) {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<UploadedFileRef[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [debugOptions, setDebugOptions] = useState<PreReviewDebugOptions | undefined>(undefined);

  const validate = (value: string, files: UploadedFileRef[]) => {
    const parsed = regenerateSchema.safeParse({
      additionalContext: value.trim(),
      attachments: files
    });
    return parsed.success ? null : parsed.error.issues[0]?.message ?? '输入不合法';
  };

  return (
    <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
      <h2 className='mb-3 text-base font-semibold'>补充信息再生成</h2>
      <textarea
        className='min-h-24 w-full rounded-md border border-black/20 p-3 text-sm outline-none ring-0 focus:border-black/50'
        placeholder='补充角色、范围、约束、性能要求等信息...'
        value={text}
        disabled={disabled}
        onChange={(e) => {
          const nextText = e.target.value;
          setText(nextText);
          if (errorMessage) {
            setErrorMessage(validate(nextText, attachments));
          }
        }}
      />
      {errorMessage ? <p className='mt-2 text-xs text-danger'>{errorMessage}</p> : null}

      <div className='mt-3 space-y-1'>
        <p className='text-sm font-medium'>补充附件（可选）</p>
        <FileUploader
          files={attachments}
          disabled={disabled}
          onChange={(files) => {
            setAttachments(files);
            if (errorMessage) {
              setErrorMessage(validate(text, files));
            }
          }}
        />
      </div>

      {showDebugOptions ? (
        <div className='mt-3'>
          <DebugOptions value={debugOptions} disabled={disabled || loading} onChange={setDebugOptions} />
        </div>
      ) : null}

      <div className='mt-3'>
        {disabled ? <ErrorAlert title='当前账号只读' message='VIEWER 角色不可触发重新生成。' /> : null}
        <SubmitButton
          loading={loading}
          disabled={disabled}
          onClick={async (e) => {
            e.preventDefault();
            if (disabled) return;
            const validationError = validate(text, attachments);
            if (validationError) {
              setErrorMessage(validationError);
              return;
            }
            setErrorMessage(null);
            await onSubmit({ additionalContext: text.trim(), attachments, debugOptions: showDebugOptions ? debugOptions : undefined });
          }}
        >
          重新生成
        </SubmitButton>
      </div>
    </section>
  );
}
