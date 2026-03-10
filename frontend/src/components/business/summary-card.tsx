import { SectionCard } from '@/components/base/section-card';

type Props = {
  summary: string;
};

export function SummaryCard({ summary }: Props) {
  return (
    <SectionCard title='需求摘要'>
      <p className='text-sm leading-6'>{summary || '暂无摘要'}</p>
    </SectionCard>
  );
}
