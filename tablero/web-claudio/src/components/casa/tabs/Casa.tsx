import { clearToken, getSub } from '../../../lib/auth';

export default function CasaTab() {
  return (
    <div className="space-y-4">
      <h2 className="font-display text-xl">Casa</h2>
      <div className="p-4 bg-bg border border-border rounded-xl">
        <div className="text-xs text-muted">Sesión</div>
        <div className="text-fg">Conectado como {getSub()}</div>
      </div>
      <button
        onClick={() => {
          clearToken();
          location.reload();
        }}
        className="w-full py-3 bg-primary text-on-primary rounded-lg font-display"
      >
        Cerrar sesión
      </button>
    </div>
  );
}
