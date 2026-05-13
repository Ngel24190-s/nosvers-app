import { useState } from 'react';
import { X, Play, CheckCircle2, XCircle } from 'lucide-react';
import { apiAutomations, type Automation, type AutomationCreate, type ExecutionLog } from './lib/apiAutomations';

interface Props {
  automation: Automation | null | undefined;
  draftPayload: AutomationCreate | null;
  onClose: () => void;
}

export function TestRunModal({ automation, draftPayload, onClose }: Props) {
  const [payloadJson, setPayloadJson] = useState('{\n  "amount": 150,\n  "customer": "test@example.com"\n}');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ExecutionLog | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canTest = Boolean(automation);

  const run = async () => {
    setError(null);
    setResult(null);
    let payload: unknown = {};
    try {
      payload = JSON.parse(payloadJson);
    } catch (e) {
      setError('JSON inválido: ' + (e instanceof Error ? e.message : String(e)));
      return;
    }
    if (!automation) {
      setError('Guarda la automatización antes de hacer test (necesita id).');
      return;
    }
    setRunning(true);
    try {
      const r = await apiAutomations.test(automation.id, payload);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
      <div className="bg-cockpit-panel border border-cockpit-border rounded-lg max-w-2xl w-full max-h-[90vh] flex flex-col">
        <header className="flex items-center justify-between px-4 py-2 border-b border-cockpit-border">
          <div className="cockpit-mono text-xs text-cockpit-text">TEST RUN — DRY</div>
          <button onClick={onClose} className="text-cockpit-textDim hover:text-accent-orange p-1">
            <X size={16} />
          </button>
        </header>
        <div className="p-4 overflow-y-auto">
          <label className="block text-[11px] cockpit-mono text-cockpit-textDim mb-1">PAYLOAD MOCK (JSON)</label>
          <textarea
            value={payloadJson}
            onChange={(e) => setPayloadJson(e.target.value)}
            rows={6}
            className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 font-mono text-xs text-cockpit-text"
          />
          {!canTest && (
            <div className="mt-2 text-[11px] text-accent-orange cockpit-mono">
              Guarda primero para poder testear. {draftPayload ? '✓ payload válido' : ''}
            </div>
          )}
          {error && (
            <div className="mt-3 px-2 py-1.5 bg-accent-orange/20 border border-accent-orange/40 text-accent-orange text-xs cockpit-mono">
              {error}
            </div>
          )}
          {result && (
            <div className="mt-4">
              <div className="text-[11px] cockpit-mono text-cockpit-textDim mb-2">
                STATUS: <span className={result.status === 'ok' ? 'text-accent-green' : 'text-accent-orange'}>{result.status}</span>
                {' '}· DURATION {result.duration_ms}ms
              </div>
              <ol className="space-y-2">
                {result.steps.map((s) => (
                  <li
                    key={s.n}
                    className="px-3 py-2 border border-cockpit-border rounded bg-cockpit-bg/40 flex items-start gap-2"
                  >
                    {s.ok ? (
                      <CheckCircle2 size={14} className="text-accent-green mt-0.5" />
                    ) : (
                      <XCircle size={14} className="text-accent-orange mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="cockpit-mono text-[11px] text-cockpit-text">
                        #{s.n} {s.action_tipo} ({s.duration_ms}ms)
                      </div>
                      {s.would_do != null && (
                        <pre className="text-[10px] text-cockpit-textDim mt-1 whitespace-pre-wrap overflow-x-auto">
                          {JSON.stringify(s.would_do as unknown, null, 2)}
                        </pre>
                      )}
                      {s.error && (
                        <div className="text-[10px] text-accent-orange mt-1">{s.error}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
        <footer className="px-4 py-2 border-t border-cockpit-border flex justify-end">
          <button
            onClick={run}
            disabled={running || !canTest}
            className="px-3 py-1 rounded bg-accent-green/20 border border-accent-green/40 hover:bg-accent-green/30 text-[11px] cockpit-mono text-accent-green flex items-center gap-1.5 disabled:opacity-50"
          >
            <Play size={12} /> {running ? 'EJECUTANDO...' : 'EJECUTAR'}
          </button>
        </footer>
      </div>
    </div>
  );
}
