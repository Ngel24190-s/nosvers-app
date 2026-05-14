interface Props {
  value: number;
  max: number;
  accent?: 'primary' | 'di' | 'emerald' | 'amber' | 'danger';
  height?: number;
}

const TONE: Record<NonNullable<Props['accent']>, string> = {
  primary: 'bg-primary',
  di: 'bg-[#D62828]',
  emerald: 'bg-emerald-600',
  amber: 'bg-amber-500',
  danger: 'bg-red-600',
};

export default function Sparkbar({
  value,
  max,
  accent = 'primary',
  height = 6,
}: Props) {
  const pct = max <= 0 ? 0 : Math.max(0, Math.min(1, value / max));
  return (
    <div
      className="w-full rounded-full bg-border/40 overflow-hidden"
      style={{ height }}
    >
      <div
        className={`h-full ${TONE[accent]} transition-[width] duration-500`}
        style={{ width: `${(pct * 100).toFixed(1)}%` }}
      />
    </div>
  );
}
