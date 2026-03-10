import { SectionCard } from '@/components/base/section-card';
import { PreReviewReportView } from '@/types';

type Props = {
  requirement: PreReviewReportView['structuredRequirement'];
};

export function StructuredRequirementCard({ requirement }: Props) {
  return (
    <SectionCard title='结构化需求草案'>
      <div className='space-y-2 text-sm'>
        <p>
          <span className='font-semibold'>目标：</span>
          {requirement.goal || '-'}
        </p>
        <p>
          <span className='font-semibold'>参与角色：</span>
          {requirement.actors.join('、') || '-'}
        </p>
        <p>
          <span className='font-semibold'>范围：</span>
          {requirement.scope.join('、') || '-'}
        </p>
        <p>
          <span className='font-semibold'>约束：</span>
          {requirement.constraints.join('、') || '-'}
        </p>
        <p>
          <span className='font-semibold'>期望输出：</span>
          {requirement.expectedOutput || '-'}
        </p>
      </div>
    </SectionCard>
  );
}
