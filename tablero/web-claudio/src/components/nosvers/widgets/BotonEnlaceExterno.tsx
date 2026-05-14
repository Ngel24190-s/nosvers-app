import { ExternalLink, type LucideIcon } from 'lucide-react';

interface Props {
  href: string;
  label: string;
  Icon?: LucideIcon;
  accent?: 'emerald' | 'lime' | 'amber';
  sub?: string;
}

const ACCENT_BG = {
  emerald: 'bg-emerald-50 hover:bg-emerald-100 border-emerald-200/60 text-emerald-900',
  lime: 'bg-lime-50 hover:bg-lime-100 border-lime-200/60 text-lime-900',
  amber: 'bg-amber-50 hover:bg-amber-100 border-amber-200/60 text-amber-900',
};

export default function BotonEnlaceExterno({
  href, label, Icon, accent = 'emerald', sub,
}: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border transition-colors ${ACCENT_BG[accent]}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        {Icon && <Icon size={18} className="flex-shrink-0" />}
        <div className="min-w-0">
          <div className="text-sm font-medium truncate">{label}</div>
          {sub && <div className="text-[11px] opacity-70 truncate">{sub}</div>}
        </div>
      </div>
      <ExternalLink size={14} className="flex-shrink-0 opacity-60" />
    </a>
  );
}
