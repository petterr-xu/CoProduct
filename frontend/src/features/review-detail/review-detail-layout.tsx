'use client';

import { useRouter } from 'next/navigation';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { CapabilityCard } from '@/components/business/capability-card';
import { EvidencePanel } from '@/components/business/evidence-panel';
import { ImpactScopeCard } from '@/components/business/impact-scope-card';
import { MissingInfoCard } from '@/components/business/missing-info-card';
import { NextActionsCard } from '@/components/business/next-actions-card';
import { RegeneratePanel } from '@/components/business/regenerate-panel';
import { ReviewHeader } from '@/components/business/review-header';
import { RiskListCard } from '@/components/business/risk-list-card';
import { StructuredRequirementCard } from '@/components/business/structured-requirement-card';
import { SummaryCard } from '@/components/business/summary-card';
import { useRegenerateReview, useReviewDetail } from '@/hooks/use-review-api';

type Props = {
  sessionId: string;
};

export function ReviewDetailLayout({ sessionId }: Props) {
  const router = useRouter();
  const detailQuery = useReviewDetail(sessionId);
  const regenerateMutation = useRegenerateReview(sessionId);

  if (detailQuery.isLoading) {
    return <LoadingSkeleton />;
  }

  if (detailQuery.error) {
    return <ErrorAlert message={detailQuery.error.message} />;
  }

  if (!detailQuery.data) {
    return <EmptyState title='未找到预审结果' description='请确认 sessionId 是否正确。' />;
  }

  if (detailQuery.data.status === 'NOT_FOUND') {
    return <EmptyState title='任务不存在' description='该预审任务可能已被删除或 sessionId 无效。' />;
  }

  const data = detailQuery.data;

  return (
    <div className='space-y-4'>
      <ReviewHeader data={data} />
      {data.status === 'PROCESSING' ? (
        <section className='rounded-card border border-blue-200 bg-blue-50 p-3 text-sm text-info'>
          正在生成中，页面会自动轮询刷新结果。
        </section>
      ) : null}

      <div className='grid gap-4 lg:grid-cols-2'>
        <SummaryCard summary={data.summary} />
        <CapabilityCard capability={data.capability} />
        <StructuredRequirementCard requirement={data.structuredRequirement} />
        <MissingInfoCard items={data.missingInfo} />
        <RiskListCard items={data.risks} />
        <ImpactScopeCard items={data.impactScope} />
        <NextActionsCard items={data.nextActions} />
        <EvidencePanel evidence={data.evidence} />
      </div>

      <RegeneratePanel
        loading={regenerateMutation.isPending}
        onSubmit={async (additionalContext) => {
          const result = await regenerateMutation.mutateAsync({ additionalContext });
          router.push(`/review/${result.sessionId}`);
        }}
      />
    </div>
  );
}
