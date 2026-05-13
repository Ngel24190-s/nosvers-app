import clsx from 'clsx';
import type { Autor } from '../lib/types';

interface Props {
  autor: Autor | 'desconocido';
  size?: 'sm' | 'md';
}

const LABELS: Record<string, string> = {
  angel: 'Angel',
  africa: 'África',
  desconocido: '¿?',
};

export function AuthorChip({ autor, size = 'sm' }: Props) {
  return (
    <span
      className={clsx(
        'chip text-white',
        autor === 'angel' && 'bg-angel',
        autor === 'africa' && 'bg-africa',
        autor === 'desconocido' && 'bg-tinta/40',
        size === 'md' && 'text-sm px-3 py-1',
      )}
    >
      {LABELS[autor] ?? '¿?'}
    </span>
  );
}
