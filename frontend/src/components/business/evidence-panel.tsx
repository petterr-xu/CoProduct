import { EvidenceSnippet } from '@/components/base/evidence-snippet';
import { SectionCard } from '@/components/base/section-card';
import { EvidenceItem } from '@/types';

type Props = {
  evidence: EvidenceItem[];
};

export function EvidencePanel({ evidence }: Props) {
  return (
    <SectionCard title='判断依据'>
      <div className='space-y-2'>
        {evidence.length === 0 ? <p className='text-sm text-muted'>暂无证据</p> : null}
        {evidence.map((item) => (
          <EvidenceSnippet key={`${item.doc_id}-${item.chunk_id}`} item={item} />
        ))}
      </div>
    </SectionCard>
  );
}
