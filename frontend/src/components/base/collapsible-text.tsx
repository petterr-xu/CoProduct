'use client';

import { useMemo, useState } from 'react';

type Props = {
  text: string;
  maxLength?: number;
  emptyText?: string;
  className?: string;
};

export function CollapsibleText({ text, maxLength = 160, emptyText = '-', className }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { displayText, collapsed } = useMemo(() => {
    if (!text) return { displayText: emptyText, collapsed: false };
    if (text.length <= maxLength) return { displayText: text, collapsed: false };
    if (expanded) return { displayText: text, collapsed: false };
    return { displayText: `${text.slice(0, maxLength)}...`, collapsed: true };
  }, [text, maxLength, expanded, emptyText]);

  return (
    <div className={className}>
      <p className='whitespace-pre-wrap'>{displayText}</p>
      {collapsed ? (
        <button className='mt-1 text-xs text-info underline-offset-2 hover:underline' onClick={() => setExpanded(true)}>
          展开全文
        </button>
      ) : null}
      {expanded && text.length > maxLength ? (
        <button className='mt-1 text-xs text-muted underline-offset-2 hover:underline' onClick={() => setExpanded(false)}>
          收起
        </button>
      ) : null}
    </div>
  );
}

