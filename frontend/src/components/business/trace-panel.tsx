import { SectionCard } from '@/components/base/section-card';
import { RETRIEVAL_MODE_LABEL_MAP } from '@/lib/constants';
import { PreReviewReportView } from '@/types';

type Props = {
  modelTrace: PreReviewReportView['modelTrace'];
  retrievalTrace: PreReviewReportView['retrievalTrace'];
};

function TraceRow({ label, value }: { label: string; value: string }) {
  return (
    <div className='flex items-start justify-between gap-3 text-sm'>
      <span className='text-muted'>{label}</span>
      <span className='max-w-[60%] break-all text-right text-ink/90'>{value}</span>
    </div>
  );
}

export function TracePanel({ modelTrace, retrievalTrace }: Props) {
  const noTrace = !modelTrace && !retrievalTrace;

  return (
    <SectionCard title='Agent Trace'>
      {noTrace ? (
        <p className='text-sm text-muted'>未提供 trace（可在调试选项中开启 includeTrace）。</p>
      ) : null}

      {modelTrace ? (
        <div className='space-y-2 rounded-md border border-black/10 bg-white p-3'>
          <p className='text-sm font-semibold'>模型调用</p>
          <TraceRow label='Provider' value={modelTrace.provider} />
          <TraceRow label='Model' value={modelTrace.model} />
          <TraceRow label='Latency' value={`${modelTrace.latencyMs} ms`} />
          <TraceRow label='Tokens' value={String(modelTrace.totalTokens ?? '-')} />
          <TraceRow label='Cost (USD)' value={modelTrace.costUsd != null ? String(modelTrace.costUsd) : '-'} />
          <TraceRow
            label='Fallback Path'
            value={modelTrace.fallbackPath && modelTrace.fallbackPath.length > 0 ? modelTrace.fallbackPath.join(' -> ') : '-'}
          />
        </div>
      ) : null}

      {retrievalTrace ? (
        <div className='mt-3 space-y-2 rounded-md border border-black/10 bg-white p-3'>
          <p className='text-sm font-semibold'>检索调用</p>
          <TraceRow label='Mode' value={RETRIEVAL_MODE_LABEL_MAP[retrievalTrace.mode]} />
          <TraceRow label='Backend' value={retrievalTrace.backend} />
          <TraceRow label='Dense Hits' value={String(retrievalTrace.denseHits)} />
          <TraceRow label='Sparse Hits' value={String(retrievalTrace.sparseHits)} />
          <TraceRow label='Fused Hits' value={String(retrievalTrace.fusedHits)} />
          <TraceRow label='Reranker' value={retrievalTrace.reranker ?? '-'} />
          <TraceRow label='Latency' value={`${retrievalTrace.latencyMs} ms`} />
        </div>
      ) : null}
    </SectionCard>
  );
}

