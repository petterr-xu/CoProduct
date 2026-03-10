import { PageContainer } from '@/components/layout/page-container';
import { ReviewDetailLayout } from '@/features/review-detail/review-detail-layout';

type PageProps = {
  params: Promise<{ sessionId: string }>;
};

export default async function ReviewDetailPage({ params }: PageProps) {
  const { sessionId } = await params;
  return (
    <PageContainer title='预审结果' subtitle='查看结构化结果、证据与后续建议'>
      <ReviewDetailLayout sessionId={sessionId} />
    </PageContainer>
  );
}
