import type { LucideIcon } from 'lucide-react';

export interface Tab {
  id: string;
  label: string;
  Icon: LucideIcon;
}

interface Props {
  tabs: Tab[];
  active: string;
  onSelect: (id: string) => void;
  variant?: 'default' | 'di';
}

export default function BottomTabs({ tabs, active, onSelect, variant = 'default' }: Props) {
  if (variant === 'di') {
    return (
      <nav className="sticky bottom-0 border-t-2 border-black bg-white grid"
           style={{ gridTemplateColumns: `repeat(${tabs.length}, 1fr)` }}>
        {tabs.map((t) => {
          const isActive = t.id === active;
          return (
            <button
              key={t.id}
              onClick={() => onSelect(t.id)}
              className={`py-3 flex flex-col items-center gap-1 text-[10px] font-black uppercase tracking-tight ${
                isActive ? 'bg-[#D62828] text-white' : 'bg-white text-black'
              }`}
            >
              <t.Icon size={18} strokeWidth={3} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>
    );
  }
  return (
    <nav
      className="sticky bottom-0 border-t border-border bg-bg/95 backdrop-blur-sm grid"
      style={{ gridTemplateColumns: `repeat(${tabs.length}, 1fr)` }}
    >
      {tabs.map((t) => {
        const isActive = t.id === active;
        return (
          <button
            key={t.id}
            onClick={() => onSelect(t.id)}
            className={`py-3 flex flex-col items-center gap-1 text-xs ${
              isActive ? 'text-primary' : 'text-muted'
            }`}
          >
            <t.Icon size={20} />
            <span>{t.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
