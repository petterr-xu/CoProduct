import { EvidenceSnippet } from '@/components/base/evidence-snippet';
import { SectionCard } from '@/components/base/section-card';
import { EvidenceItem } from '@/types';

type Props = {
  evidence: EvidenceItem[];
};

export function EvidencePanel({ evidence }: Props) {
  const sortedEvidence = [...evidence].sort((a, b) => b.relevance_score - a.relevance_score);

  return (
    <SectionCard title='判断依据'>
      <div className='space-y-2'>
        {sortedEvidence.length === 0 ? (
          <p className='text-sm text-muted'>暂无证据，建议补充更具体的目标、范围和约束信息后重新生成。</p>
        ) : (
          <p className='text-xs text-muted'>共 {sortedEvidence.length} 条证据，按相关性排序展示。</p>
        )}
        {sortedEvidence.map((item) => (
          <EvidenceSnippet key={`${item.doc_id}-${item.chunk_id}`} item={item} />
        ))}
      </div>
    </SectionCard>
  );
}
