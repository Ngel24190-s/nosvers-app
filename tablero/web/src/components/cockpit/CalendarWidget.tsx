import { Calendar, Lock } from 'lucide-react';
import { WidgetCard } from './WidgetCard';

export function CalendarWidget({ index }: { index: number }) {
  return (
    <WidgetCard title="Calendar" icon={<Calendar size={14} />} accent="cyan" index={index}>
      <div className="flex flex-col items-center justify-center h-full text-center gap-3 px-2">
        <div className="relative">
          <Calendar size={32} className="text-cockpit-dim" />
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
