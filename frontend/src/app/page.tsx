import { PageContainer } from '@/components/layout/page-container';
import { HomeDashboard } from '@/features/home/home-dashboard';

export default function HomePage() {
  return (
    <PageContainer title='CoProduct 预审工作台' subtitle='从这里快速进入新建预审、历史记录与最近会话。'>
      <HomeDashboard />
    </PageContainer>
  );
}
