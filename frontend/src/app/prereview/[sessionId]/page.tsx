import Link from 'next/link';

import { WriteAccess } from '@/components/auth/write-access';
import { PageContainer } from '@/components/layout/page-container';
import { ReviewDetailLayout } from '@/features/review-detail/review-detail-layout';

type PageProps = {
  params: Promise<{ sessionId: string }>;
};

export default async function PrereviewDetailPage({ params }: PageProps) {
  const { sessionId } = await params;
  return (
    <PageContainer
      title='预审结果'
      subtitle='查看结构化结果、证据与后续建议'
      actions={
        <>
          <Link
            href='/history'
            className='rounded-md border border-black/20 bg-white px-3 py-1.5 text-sm hover:border-black/40'
          >
            返回历史
          </Link>
          <WriteAccess>
            <Link
              href='/prereview/new'
              className='rounded-md border border-black/20 bg-white px-3 py-1.5 text-sm hover:border-black/40'
            >
              新建预审
            </Link>
          </WriteAccess>
        </>
      }
    >
      <ReviewDetailLayout sessionId={sessionId} />
    </PageContainer>
  );
}
