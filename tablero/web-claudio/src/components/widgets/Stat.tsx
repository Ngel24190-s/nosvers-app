import { type ReactNode } from 'react';

interface Props {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: 'primary' | 'di' | 'emerald' | 'amber' | 'neutral' | 'lime';
  size?: 'sm' | 'md' | 'lg';
}

const VALUE_TONE: Record<NonNullable<Props['accent']>, string> = {
  primary: 'text-primary',
  di: 'text-[#D62828]',
  emerald: 'text-emerald-700',
  amber: 'text-amber-700',
  neutral: 'text-fg',
  lime: 'text-lime-700',
};

const VALUE_SIZE: Record<NonNullable<Props['size']>, string> = {
  sm: 'text-xl',
  md: 'text-3xl',
  lg: 'text-5xl',
};

export default function Stat({
  label,
  value,
  sub,
  accent = 'primary',
  size = 'md',
}: Props) {
  return (
    <div>
      <div className="text-xs text-muted uppercase tracking-wide">{label}</div>
      <div
        className={`font-display font-bold mt-1 leading-none ${VALUE_SIZE[size]} ${VALUE_TONE[accent]}`}
      >
        {value}
      </div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </div>
  );
}
