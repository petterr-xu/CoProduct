import { redirect } from 'next/navigation';

type PageProps = {
  params: Promise<{ sessionId: string }>;
};

export default async function LegacyReviewDetailPage({ params }: PageProps) {
  const { sessionId } = await params;
  redirect(`/prereview/${sessionId}`);
}
