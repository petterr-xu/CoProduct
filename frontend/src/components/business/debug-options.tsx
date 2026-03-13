'use client';

import { RETRIEVAL_MODE_LABEL_MAP } from '@/lib/constants';
import { PreReviewDebugOptions, RetrievalMode } from '@/types';

type Props = {
  value?: PreReviewDebugOptions;
  disabled?: boolean;
  onChange: (nextValue?: PreReviewDebugOptions) => void;
};

const RETRIEVAL_MODES: RetrievalMode[] = ['hybrid', 'dense', 'sparse'];

function buildNextDebugOptions(base: PreReviewDebugOptions, patch: Partial<PreReviewDebugOptions>): PreReviewDebugOptions {
  return {
    includeTrace: patch.includeTrace ?? base.includeTrace ?? true,
    retrievalMode: patch.retrievalMode ?? base.retrievalMode ?? 'hybrid'
  };
}

export function DebugOptions({ value, disabled = false, onChange }: Props) {
  const enabled = Boolean(value);
  const current = value ?? { includeTrace: true, retrievalMode: 'hybrid' as RetrievalMode };

  return (
    <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
      <div className='flex items-center justify-between gap-4'>
        <div>
          <h3 className='text-sm font-semibold'>调试选项（管理员）</h3>
          <p className='text-xs text-muted'>用于联调阶段观测模型和检索行为，生产环境建议按需开启。</p>
        </div>
        <label className='inline-flex items-center gap-2 text-sm'>
          <input
            type='checkbox'
            checked={enabled}
            disabled={disabled}
            onChange={(event) => {
              if (event.target.checked) {
                onChange({ includeTrace: true, retrievalMode: 'hybrid' });
                return;
              }
              onChange(undefined);
            }}
          />
          启用
        </label>
      </div>

      {enabled ? (
        <div className='mt-3 grid gap-3 md:grid-cols-2'>
          <label className='inline-flex items-center gap-2 text-sm'>
            <input
              type='checkbox'
              checked={Boolean(current.includeTrace)}
              disabled={disabled}
              onChange={(event) =>
                onChange(buildNextDebugOptions(current, { includeTrace: event.target.checked }))
              }
            />
            返回 Trace 信息
          </label>

          <label className='space-y-1 text-sm'>
            <span className='font-medium'>检索模式</span>
            <select
              className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
              value={current.retrievalMode ?? 'hybrid'}
              disabled={disabled}
              onChange={(event) =>
                onChange(
                  buildNextDebugOptions(current, {
                    retrievalMode: event.target.value as RetrievalMode
                  })
                )
              }
            >
              {RETRIEVAL_MODES.map((mode) => (
                <option key={mode} value={mode}>
                  {RETRIEVAL_MODE_LABEL_MAP[mode]}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}
    </section>
  );
}

