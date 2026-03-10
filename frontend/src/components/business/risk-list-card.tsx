import { SectionCard } from '@/components/base/section-card';
import { cn } from '@/lib/utils';

type RiskItem = {
  title: string;
  description: string;
  level: 'high' | 'medium' | 'low';
};

type Props = {
  items: RiskItem[];
};

function levelClass(level: RiskItem['level']) {
  if (level === 'high') return 'border-danger/20 bg-red-50 text-danger';
  if (level === 'medium') return 'border-warning/20 bg-amber-50 text-warning';
  return 'border-black/10 bg-white text-muted';
}

export function RiskListCard({ items }: Props) {
  return (
    <SectionCard title='风险提示'>
      <div className='space-y-2'>
        {items.length === 0 ? <p className='text-sm text-muted'>暂无风险提示</p> : null}
        {items.map((item) => (
          <div key={`${item.title}-${item.level}`} className={cn('rounded-md border p-3 text-sm', levelClass(item.level))}>
            <p className='font-semibold'>{item.title}</p>
            <p className='mt-1'>{item.description || '-'}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
