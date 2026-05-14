import { useChannel } from '../../../lib/ws';

interface HealthSnap {
  cpu_percent?: number;
  mem_percent?: number;
  disk_percent?: number;
  uptime_s?: number;
  empty?: boolean;
}

export default function CockpitMini() {
  const { data } = useChannel<HealthSnap>('health');
  const cpu = data?.cpu_percent ?? 0;
  const mem = data?.mem_percent ?? 0;
  const disk = data?.disk_percent ?? 0;
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl">Cockpit · mini</h2>
      <div className="grid grid-cols-3 gap-3">
        <KPI label="CPU" val={`${cpu.toFixed(0)}%`} />
        <KPI label="RAM" val={`${mem.toFixed(0)}%`} />
        <KPI label="Disco" val={`${disk.toFixed(0)}%`} />
      </div>
      <p className="text-xs text-muted">
        Resumen del VPS NosVers. Ver el cockpit completo en
        <a className="ml-1 underline text-primary" href="https://tablero.72.61.160.108.nip.io">tablero.*</a>.
      </p>
    </div>
  );
}

function KPI({ label, val }: { label: string; val: string }) {
  return (
    <div className="p-3 bg-bg border border-border rounded-lg">
      <div className="text-xs text-muted">{label}</div>
      <div className="font-mono text-xl mt-1">{val}</div>
    </div>
  );
}
