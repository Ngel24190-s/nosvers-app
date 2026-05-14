import { Inbox, type LucideIcon } from 'lucide-react';
import { type ReactNode } from 'react';

interface Props {
  Icon?: LucideIcon;
  text: ReactNode;
  hint?: ReactNode;
}

export default function EmptyState({ Icon = Inbox, text, hint }: Props) {
  return (
    <div className="py-6 px-4 flex flex-col items-center text-center gap-2">
      <Icon size={28} className="text-muted opacity-50" />
      <div className="text-sm text-muted">{text}</div>
      {hint && <div className="text-xs text-muted opacity-70">{hint}</div>}
    </div>
  );
}
