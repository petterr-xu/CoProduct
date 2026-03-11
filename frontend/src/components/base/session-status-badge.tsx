import { SESSION_STATUS_COLOR_MAP, SESSION_STATUS_LABEL_MAP } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { SessionStatus } from '@/types';

type Props = {
  status: SessionStatus;
};

export function SessionStatusBadge({ status }: Props) {
  return (
    <span
      className={cn(
        'inline-flex rounded-full border px-2 py-1 text-xs font-semibold',
        SESSION_STATUS_COLOR_MAP[status]
      )}
    >
      {SESSION_STATUS_LABEL_MAP[status]}
    </span>
  );
}

