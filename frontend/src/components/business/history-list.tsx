import Link from 'next/link';

import { EmptyState } from '@/components/base/empty-state';
import { HistoryItem } from '@/types';

type Props = {
  items: HistoryItem[];
};

export function HistoryList({ items }: Props) {
  if (items.length === 0) {
    return <EmptyState title='暂无历史记录' description='可以先在新建预审页发起一个任务。' />;
  }

  return (
    <ul className='space-y-2'>
      {items.map((item) => (
        <li key={`${item.sessionId}-${item.version}`} className='rounded-card border border-black/10 bg-panel p-4'>
          <div className='flex flex-wrap items-center justify-between gap-2'>
            <p className='text-sm font-semibold'>{item.requestText || '未命名需求'}</p>
            <span className='text-xs text-muted'>v{item.version}</span>
          </div>
          <div className='mt-2 flex flex-wrap items-center gap-3 text-xs text-muted'>
            <span>{item.capabilityStatus}</span>
            <span>{item.createdAt}</span>
          </div>
          <div className='mt-3'>
            <Link className='text-sm text-info underline-offset-2 hover:underline' href={`/review/${item.sessionId}`}>
              查看详情
            </Link>
          </div>
        </li>
      ))}
    </ul>
  );
}
