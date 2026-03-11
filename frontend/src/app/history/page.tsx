import Link from 'next/link';

import { PageContainer } from '@/components/layout/page-container';
import { HistoryView } from '@/features/history/history-view';

export default function HistoryPage() {
  return (
    <PageContainer
      title='历史记录'
      subtitle='查看预审历史并快速进入详情'
      actions={
        <Link
          href='/prereview/new'
          className='rounded-md border border-black/20 bg-white px-3 py-1.5 text-sm hover:border-black/40'
        >
          发起预审
        </Link>
      }
    >
      <HistoryView />
    </PageContainer>
  );
}
