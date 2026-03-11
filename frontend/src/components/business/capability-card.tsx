import { SectionCard } from '@/components/base/section-card';
import { StatusBadge } from '@/components/base/status-badge';
import { CONFIDENCE_LABEL_MAP } from '@/lib/constants';
import { PreReviewReportView } from '@/types';

type Props = {
  capability: PreReviewReportView['capability'];
};

export function CapabilityCard({ capability }: Props) {
  const confidenceText = capability.confidence
    ? `置信度：${CONFIDENCE_LABEL_MAP[capability.confidence]}`
    : '置信度：不可用（降级）';

  return (
    <SectionCard title='当前能力判断'>
      <div className='flex items-center justify-between'>
        <StatusBadge status={capability.status} />
        <span className='text-xs text-muted'>{confidenceText}</span>
      </div>
      <p className='mt-3 text-sm'>{capability.reason || '暂无说明'}</p>
    </SectionCard>
  );
}
