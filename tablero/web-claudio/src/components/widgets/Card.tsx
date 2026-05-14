import { useEffect, useState, type ReactNode } from 'react';

type Ctx = 'casa' | 'nosvers' | 'trabajo';
type Variant = Ctx | 'auto';

interface Props {
  variant?: Variant;
  className?: string;
  children: ReactNode;
}

function detectContext(): Ctx {
  if (typeof document === 'undefined') return 'casa';
  const c = document.documentElement.dataset.context;
  if (c === 'casa' || c === 'nosvers' || c === 'trabajo') return c;
  return 'casa';
}

const STYLES: Record<Ctx, string> = {
  casa: 'rounded-2xl bg-white border border-stone-200 shadow-sm',
  nosvers: 'rounded-2xl bg-white border border-emerald-200/60 shadow-sm',
  trabajo: 'di-card',
};

function resolveVariant(v: Variant): Ctx {
  return v === 'auto' ? detectContext() : v;
}

export default function Card({ variant = 'auto', className = '', children }: Props) {
  const [resolved, setResolved] = useState<Ctx>(() => resolveVariant(variant));
  useEffect(() => {
    setResolved(resolveVariant(variant));
  }, [variant]);
  return <div className={`${STYLES[resolved]} ${className}`}>{children}</div>;
}
