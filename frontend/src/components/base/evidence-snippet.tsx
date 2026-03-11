import { EvidenceItem } from '@/types';

type Props = {
  item: EvidenceItem;
};

export function EvidenceSnippet({ item }: Props) {
  return (
    <article className='rounded-md border border-black/10 bg-white p-3'>
      <p className='text-sm font-semibold'>{item.doc_title || '未知来源文档'}</p>
      <p className='mt-1 text-xs text-muted'>
        {item.source_type} · trust={item.trust_level} · score={item.relevance_score.toFixed(2)}
      </p>
      <details className='mt-2'>
        <summary className='cursor-pointer text-sm text-ink/90'>查看证据片段</summary>
        <p className='mt-2 whitespace-pre-wrap text-sm text-ink/90'>{item.snippet || '暂无证据片段'}</p>
      </details>
    </article>
  );
}
