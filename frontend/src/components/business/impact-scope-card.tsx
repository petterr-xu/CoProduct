import { SectionCard } from '@/components/base/section-card';

type Props = {
  items: string[];
};

export function ImpactScopeCard({ items }: Props) {
  return (
    <SectionCard title='影响范围'>
      <ul className='list-disc space-y-1 pl-4 text-sm'>
        {items.length === 0 ? <li className='text-muted'>暂无</li> : null}
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </SectionCard>
  );
}
