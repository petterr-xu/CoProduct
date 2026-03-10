import { PageContainer } from '@/components/layout/page-container';
import { HistoryView } from '@/features/history/history-view';

export default function HistoryPage() {
  return (
    <PageContainer title='历史记录' subtitle='查看预审历史并快速进入详情'>
      <HistoryView />
    </PageContainer>
  );
}
