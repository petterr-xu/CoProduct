import { SectionCard } from '@/components/base/section-card';
import { StatusBadge } from '@/components/base/status-badge';
import { PreReviewReportView } from '@/types';

type Props = {
  capability: PreReviewReportView['capability'];
};

export function CapabilityCard({ capability }: Props) {
  return (
    <SectionCard title='当前能力判断'>
      <div className='flex items-center justify-between'>
        <StatusBadge status={capability.status} />
        <span className='text-xs text-muted'>confidence: {capability.confidence}</span>
      </div>
      <p className='mt-3 text-sm'>{capability.reason || '暂无说明'}</p>
    </SectionCard>
  );
}
