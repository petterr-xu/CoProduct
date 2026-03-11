'use client';

import { useState } from 'react';

import { SubmitButton } from '@/components/base/submit-button';
import { regenerateSchema } from '@/schemas/regenerate';

type Props = {
  onSubmit: (additionalContext: string) => Promise<void>;
  loading?: boolean;
};

export function RegeneratePanel({ onSubmit, loading }: Props) {
  const [text, setText] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const validate = (value: string) => {
    const parsed = regenerateSchema.safeParse({ additionalContext: value.trim() });
    return parsed.success ? null : parsed.error.issues[0]?.message ?? '输入不合法';
  };

  return (
    <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
      <h2 className='mb-3 text-base font-semibold'>补充信息再生成</h2>
      <textarea
        className='min-h-24 w-full rounded-md border border-black/20 p-3 text-sm outline-none ring-0 focus:border-black/50'
        placeholder='补充角色、范围、约束、性能要求等信息...'
        value={text}
        onChange={(e) => {
          const nextText = e.target.value;
          setText(nextText);
          if (errorMessage) {
            setErrorMessage(validate(nextText));
          }
        }}
      />
      {errorMessage ? <p className='mt-2 text-xs text-danger'>{errorMessage}</p> : null}
      <div className='mt-3'>
        <SubmitButton
          loading={loading}
          onClick={async (e) => {
            e.preventDefault();
            const validationError = validate(text);
            if (validationError) {
              setErrorMessage(validationError);
              return;
            }
            setErrorMessage(null);
            await onSubmit(text.trim());
          }}
        >
          重新生成
        </SubmitButton>
      </div>
    </section>
  );
}
