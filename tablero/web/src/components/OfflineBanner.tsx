import { WifiOff } from 'lucide-react';

interface Props {
  visible: boolean;
}

export function OfflineBanner({ visible }: Props) {
  if (!visible) return null;
  return (
    <div className="bg-africa/15 border-y border-africa/30 px-4 py-2 text-sm text-tinta/80 flex items-center gap-2">
      <WifiOff size={14} />
      <span>Sin conexión — mostrando la última copia en caché. Algunos datos pueden estar desactualizados.</span>
    </div>
  );
}
