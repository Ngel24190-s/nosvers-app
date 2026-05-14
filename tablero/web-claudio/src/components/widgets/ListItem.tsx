import { ChevronRight, type LucideIcon } from 'lucide-react';
import { type ReactNode } from 'react';

interface Props {
  Icon?: LucideIcon;
  title: ReactNode;
  meta?: ReactNode;
  onClick?: () => void;
  chevron?: boolean;
  className?: string;
  accent?: 'neutral' | 'urgent' | 'success';
}

const ACCENT: Record<NonNullable<Props['accent']>, string> = {
  neutral: '',
  urgent: 'bg-amber-50 border-amber-200',
  success: 'bg-emerald-50 border-emerald-200',
};

export default function ListItem({
  Icon,
  title,
  meta,
  onClick,
  chevron = false,
  className = '',
  accent = 'neutral',
}: Props) {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-lg border border-border ${ACCENT[accent]} ${onClick ? 'active:scale-[0.99] transition-transform' : ''} ${className}`}
    >
      {Icon && (
        <span className="shrink-0 w-9 h-9 rounded-full bg-bg border border-border flex items-center justify-center text-fg">
          <Icon size={18} />
        </span>
      )}
      <div className="flex-1 text-left min-w-0">
        <div className="text-fg truncate">{title}</div>
        {meta && <div className="text-xs text-muted truncate mt-0.5">{meta}</div>}
      </div>
      {chevron && <ChevronRight size={18} className="text-muted shrink-0" />}
    </Tag>
  );
}
