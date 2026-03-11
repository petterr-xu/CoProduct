import { SectionCard } from '@/components/base/section-card';

type Props = {
  items: string[];
};

export function UncertaintiesCard({ items }: Props) {
  return (
    <SectionCard title='不确定项'>
      <ul className='list-disc space-y-1 pl-4 text-sm'>
        {items.length === 0 ? <li className='text-muted'>暂无不确定项</li> : null}
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </SectionCard>
  );
}

