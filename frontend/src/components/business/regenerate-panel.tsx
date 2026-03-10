'use client';

import { useState } from 'react';

import { SubmitButton } from '@/components/base/submit-button';

type Props = {
  onSubmit: (additionalContext: string) => Promise<void>;
  loading?: boolean;
};

export function RegeneratePanel({ onSubmit, loading }: Props) {
  const [text, setText] = useState('');

  return (
    <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
      <h2 className='mb-3 text-base font-semibold'>补充信息再生成</h2>
      <textarea
        className='min-h-24 w-full rounded-md border border-black/20 p-3 text-sm outline-none ring-0 focus:border-black/50'
        placeholder='补充角色、范围、约束、性能要求等信息...'
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className='mt-3'>
        <SubmitButton
          loading={loading}
          onClick={async (e) => {
            e.preventDefault();
            if (!text.trim()) return;
            await onSubmit(text.trim());
          }}
        >
          重新生成
        </SubmitButton>
      </div>
    </section>
  );
}
