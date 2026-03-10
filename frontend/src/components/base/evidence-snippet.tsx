import { EvidenceItem } from '@/types';

type Props = {
  item: EvidenceItem;
};

export function EvidenceSnippet({ item }: Props) {
  return (
    <article className='rounded-md border border-black/10 bg-white p-3'>
      <p className='text-sm font-semibold'>{item.doc_title}</p>
      <p className='mt-1 text-xs text-muted'>
        {item.source_type} · trust={item.trust_level} · score={item.relevance_score}
      </p>
      <p className='mt-2 text-sm text-ink/90'>{item.snippet}</p>
    </article>
  );
}
