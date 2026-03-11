import { CollapsibleText } from '@/components/base/collapsible-text';
import { SectionCard } from '@/components/base/section-card';

type Props = {
  summary: string;
};

export function SummaryCard({ summary }: Props) {
  return (
    <SectionCard title='需求摘要'>
      <CollapsibleText text={summary} emptyText='暂无摘要' className='text-sm leading-6 text-ink/90' />
    </SectionCard>
  );
}
