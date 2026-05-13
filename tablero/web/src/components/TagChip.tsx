import clsx from 'clsx';
import type { Etiqueta } from '../lib/types';

interface Props {
  etiqueta: Etiqueta;
  active?: boolean;
  onClick?: () => void;
}

const LABELS: Record<Etiqueta, string> = {
  trabajo: 'trabajo',
  nosvers: 'nosvers',
  familia: 'familia',
  mental: 'mental',
  idea: 'idea',
  otro: 'otro',
};

export function TagChip({ etiqueta, active = false, onClick }: Props) {
  const isButton = Boolean(onClick);
  const Tag = isButton ? 'button' : 'span';
  return (
    <Tag
      type={isButton ? 'button' : undefined}
      onClick={onClick}
      className={clsx(
        'chip border',
        active
          ? 'bg-verde-dark text-cream border-verde-dark'
          : 'bg-cream text-tinta/80 border-tinta/15 hover:bg-tinta/5',
      )}
    >
      #{LABELS[etiqueta]}
    </Tag>
  );
}
