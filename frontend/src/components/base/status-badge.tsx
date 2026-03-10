import { CapabilityStatus } from '@/types';

import { STATUS_COLOR_MAP } from '@/lib/constants';
import { cn } from '@/lib/utils';

type Props = {
  status: CapabilityStatus;
};

export function StatusBadge({ status }: Props) {
  return (
    <span className={cn('inline-flex rounded-full border px-2 py-1 text-xs font-semibold', STATUS_COLOR_MAP[status])}>
      {status}
    </span>
  );
}
