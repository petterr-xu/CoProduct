import { SectionCard } from '@/components/base/section-card';

type Props = {
  items: string[];
};

export function NextActionsCard({ items }: Props) {
  return (
    <SectionCard title='下一步建议'>
      <ol className='list-decimal space-y-1 pl-4 text-sm'>
        {items.length === 0 ? <li className='text-muted'>暂无</li> : null}
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ol>
    </SectionCard>
  );
}
