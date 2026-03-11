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
import { UncertaintiesCard } from '@/components/business/uncertainties-card';
import { usePrereviewDetail, useRegeneratePrereview } from '@/hooks/use-prereview-api';
import { getApiErrorMessage, isApiClientError } from '@/lib/api-client';

type Props = {
  sessionId: string;
};

export function ReviewDetailLayout({ sessionId }: Props) {
  const router = useRouter();
  const detailQuery = usePrereviewDetail(sessionId);
  const regenerateMutation = useRegeneratePrereview(sessionId);

  if (detailQuery.isLoading) {
    return <LoadingSkeleton />;
  }

  if (detailQuery.error) {
    if (
      isApiClientError(detailQuery.error) &&
      (detailQuery.error.status === 'NOT_FOUND' || detailQuery.error.httpStatus === 404)
    ) {
      return <EmptyState title='任务不存在' description='该预审任务可能已被删除或 sessionId 无效。' />;
    }
    return <ErrorAlert message={getApiErrorMessage(detailQuery.error)} />;
  }

  if (!detailQuery.data) {
    return <EmptyState title='未找到预审结果' description='请确认 sessionId 是否正确。' />;
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
      {data.status === 'FAILED' ? (
        <ErrorAlert
          title='预审生成失败'
          message={data.errorMessage || '工作流执行失败，请补充输入后重试或稍后再试。'}
        />
      ) : null}

      <div className='grid gap-4 lg:grid-cols-2'>
        <SummaryCard summary={data.summary} />
        <CapabilityCard capability={data.capability} />
        <StructuredRequirementCard requirement={data.structuredRequirement} />
        <MissingInfoCard items={data.missingInfo} />
        <RiskListCard items={data.risks} />
        <ImpactScopeCard items={data.impactScope} />
        <NextActionsCard items={data.nextActions} />
        <UncertaintiesCard items={data.uncertainties} />
        <EvidencePanel evidence={data.evidence} />
      </div>

      <RegeneratePanel
        loading={regenerateMutation.isPending}
        onSubmit={async (additionalContext) => {
          const result = await regenerateMutation.mutateAsync({ additionalContext });
          router.push(`/prereview/${result.sessionId}`);
        }}
      />
      {regenerateMutation.error ? <ErrorAlert title='重新生成失败' message={getApiErrorMessage(regenerateMutation.error)} /> : null}
    </div>
  );
}
