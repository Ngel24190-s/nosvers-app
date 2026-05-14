import { ArrowLeft } from 'lucide-react';
import { useClaudioContext } from '../lib/context';

interface Props {
  title: string;
  variant?: 'default' | 'di';
  subtitle?: string;
}

export default function ContextSwitcher({ title, variant = 'default', subtitle }: Props) {
  const { setContext } = useClaudioContext();

  if (variant === 'di') {
    return (
      <header className="di-header-stripe">
        <div className="bg-white p-3 flex items-center gap-2">
          <button
            onClick={() => setContext(null)}
            className="p-2 -ml-2 text-black"
            aria-label="Volver"
          >
            <ArrowLeft size={20} strokeWidth={3} />
          </button>
          <div className="font-black text-3xl text-black leading-none tracking-di">DI</div>
        </div>
        <div className="bg-[#D62828] p-3 text-white flex flex-col justify-center">
          <div className="text-[9px] font-black uppercase tracking-tight opacity-90">
            {subtitle ?? 'Cond. Travaux'}
          </div>
          <div className="font-black text-base uppercase tracking-tight leading-tight">
            {title}
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="px-5 pt-4 pb-3 flex items-center justify-between border-b border-border">
      <button onClick={() => setContext(null)} className="p-2 -ml-2 text-fg" aria-label="Volver">
        <ArrowLeft size={20} />
      </button>
      <div className="font-display text-lg text-fg">{title}</div>
      <div className="w-9" />
    </header>
  );
}
