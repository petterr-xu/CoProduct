import { SectionCard } from '@/components/base/section-card';
import { PreReviewReportView } from '@/types';

type Props = {
  data: Pick<PreReviewReportView, 'sessionId' | 'version' | 'status' | 'parentSessionId'>;
};

export function ReviewHeader({ data }: Props) {
  return (
    <SectionCard title='预审任务'>
      <div className='grid gap-1 text-sm md:grid-cols-2'>
        <p>
          <span className='font-semibold'>Session:</span> {data.sessionId}
        </p>
        <p>
          <span className='font-semibold'>Version:</span> v{data.version}
        </p>
        <p>
          <span className='font-semibold'>Status:</span> {data.status}
        </p>
        <p>
          <span className='font-semibold'>Parent:</span> {data.parentSessionId ?? '-'}
        </p>
      </div>
    </SectionCard>
  );
}
