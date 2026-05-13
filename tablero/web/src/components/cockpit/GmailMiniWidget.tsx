import { Mail, Lock } from 'lucide-react';
import { WidgetCard } from './WidgetCard';

// Gmail OAuth aún no configurado server-side (D-014 del 002 + brief Fase D).
// Placeholder elegante — la integración real entra cuando Angel suba el service-account.
export function GmailMiniWidget({ index }: { index: number }) {
  return (
    <WidgetCard title="Gmail" icon={<Mail size={14} />} accent="violet" index={index}>
      <div className="flex flex-col items-center justify-center h-full text-center gap-3 px-2">
        <div className="relative">
          <Mail size={32} className="text-cockpit-dim" />
          <Lock
            size={12}
            className="absolute -bottom-1 -right-1 text-accent-orange bg-cockpit-panel rounded-full p-0.5"
          />
        </div>
        <div>
          <div className="cockpit-mono text-[10px] uppercase tracking-wider text-cockpit-textDim">
            BLOCKED_OAUTH_HUMAN
          </div>
          <p className="text-[10px] text-cockpit-dim mt-1 leading-relaxed">
            Pendiente Google service-account
          </p>
        </div>
      </div>
    </WidgetCard>
  );
}
