import { useMemo, useEffect } from 'react';
import { ResponsiveGridLayout, useContainerWidth } from 'react-grid-layout';
import type { Layout } from 'react-grid-layout';
import { Toaster } from 'sonner';
import { motion } from 'framer-motion';
import { Radio, RotateCcw, ArrowLeft, Volume2, VolumeX } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useCockpitLayout, DEFAULT_LAYOUT } from '../hooks/useCockpitLayout';
import { getToken } from '../lib/auth';
import { ClaudeStatusWidget } from '../components/cockpit/ClaudeStatusWidget';
import { VpsHealthWidget } from '../components/cockpit/VpsHealthWidget';
import { RevenueWidget } from '../components/cockpit/RevenueWidget';
import { AegisBriefingWidget } from '../components/cockpit/AegisBriefingWidget';
import { ActivityStreamWidget } from '../components/cockpit/ActivityStreamWidget';
import { WakeWordWidget } from '../components/cockpit/WakeWordWidget';
import { VaultStatsWidget } from '../components/cockpit/VaultStatsWidget';
import { AgentesStatusWidget } from '../components/cockpit/AgentesStatusWidget';
import { GmailMiniWidget } from '../components/cockpit/GmailMiniWidget';
import { CalendarWidget } from '../components/cockpit/CalendarWidget';
import { FreqtradeWidget } from '../components/cockpit/FreqtradeWidget';
import { StripeToaster } from '../components/cockpit/StripeToaster';
import { AutomationsWidget } from '../components/cockpit/AutomationsWidget';
import { ShortcutsModal } from '../components/cockpit/ShortcutsModal';
// 006 — familia/admin
import { RecordatoriosWidget } from '../components/cockpit/RecordatoriosWidget';
import { GastosMesWidget } from '../components/cockpit/GastosMesWidget';
import { ComprasWidget } from '../components/cockpit/ComprasWidget';
import { MedicacionWidget } from '../components/cockpit/MedicacionWidget';
import { CocheStatusWidget } from '../components/cockpit/CocheStatusWidget';
import { MenuHoyWidget } from '../components/cockpit/MenuHoyWidget';
import { BrisWidget } from '../components/cockpit/BrisWidget';
import '../styles/cockpit.css';

function wsUrl(): string {
  if (typeof window === 'undefined') return '';
  const apiBase = (import.meta.env.VITE_API_BASE as string) ?? '';
  if (apiBase.startsWith('http')) {
    return apiBase.replace(/^http/, 'ws') + '/tablero/api/v2/ws';
  }
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}/tablero/api/v2/ws`;
}

const STATUS_LABEL: Record<string, string> = {
  connecting: 'CONNECTING',
  connected: 'LIVE',
  reconnecting: 'RECONNECTING',
  failed: 'OFFLINE',
};

const STATUS_LED: Record<string, string> = {
  connecting: 'cockpit-led--listening animate-pulse-led',
  connected: 'cockpit-led--online animate-pulse-led',
  reconnecting: 'cockpit-led--listening animate-pulse-led',
  failed: 'cockpit-led--error',
};

interface CockpitProps {
  identitySub: string;
  onExit: () => void;
}

export default function Cockpit({ identitySub, onExit }: CockpitProps) {
  const token = getToken() ?? '';
  const ws = useWebSocket({ token, url: wsUrl() });
  const { layout, onLayoutChange, reset } = useCockpitLayout(identitySub);
  const { width, containerRef } = useContainerWidth({ initialWidth: 1280 });

  // dark mode forzado mientras estamos en cockpit
  useEffect(() => {
    document.documentElement.classList.add('dark');
    return () => {
      document.documentElement.classList.remove('dark');
    };
  }, []);

  const layouts = useMemo(() => ({ lg: layout, md: layout, sm: layout }), [layout]);

  const toggleSound = () => {
    const cur = localStorage.getItem('cockpit_sound') === 'on';
    localStorage.setItem('cockpit_sound', cur ? 'off' : 'on');
    // forzar re-render con un dispatch storage (opcional). Sin estado, suficiente.
    window.dispatchEvent(new Event('storage'));
  };
  const soundOn = typeof window !== 'undefined' && localStorage.getItem('cockpit_sound') === 'on';

  return (
    <div className="cockpit-root cockpit-grid-bg min-h-screen">
      <motion.header
        className="flex items-center justify-between px-6 py-3 border-b border-cockpit-border bg-cockpit-panel/40 backdrop-blur-xl"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3">
          <button
            onClick={onExit}
            className="cockpit-mono text-[11px] text-cockpit-textDim hover:text-accent-green flex items-center gap-1"
            aria-label="volver al dashboard"
          >
            <ArrowLeft size={14} />
            DASHBOARD
          </button>
          <span className="text-cockpit-border">|</span>
          <div className="flex items-center gap-2">
            <Radio size={14} className="text-accent-green" />
            <h1 className="cockpit-mono text-sm font-bold tracking-[0.18em] text-cockpit-text">
              NOSVERS · MISSION CONTROL
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="cockpit-status-pill">
            <span className={`cockpit-led ${STATUS_LED[ws.status]}`} />
            <span>{STATUS_LABEL[ws.status]}</span>
          </span>
          <span className="cockpit-mono text-[10px] text-cockpit-textDim hidden sm:inline">
            sub: {identitySub}
          </span>
          <button
            onClick={toggleSound}
            className="cockpit-mono text-[10px] text-cockpit-textDim hover:text-accent-green flex items-center gap-1"
            aria-label="toggle sound"
          >
            {soundOn ? <Volume2 size={14} /> : <VolumeX size={14} />}
          </button>
          <button
            onClick={reset}
            className="cockpit-mono text-[10px] text-cockpit-textDim hover:text-accent-orange flex items-center gap-1"
            aria-label="restaurar layout"
          >
            <RotateCcw size={14} />
            RESET
          </button>
        </div>
      </motion.header>

      <main className="px-3 sm:px-4 py-4">
        <div ref={containerRef as unknown as React.RefObject<HTMLDivElement>}>
        <ResponsiveGridLayout
          className="cockpit-layout"
          layouts={layouts}
          breakpoints={{ lg: 1200, md: 768, sm: 480 }}
          cols={{ lg: 12, md: 8, sm: 4 }}
          rowHeight={80}
          margin={[12, 12]}
          containerPadding={[0, 0]}
          width={width}
          onLayoutChange={(curr: Layout) => onLayoutChange([...curr])}
          dragConfig={{ handle: '.cockpit-glass' }}
        >
          <div key="claude" data-widget="claude">
            <ClaudeStatusWidget ws={ws} index={0} />
          </div>
          <div key="vps" data-widget="vps">
            <VpsHealthWidget ws={ws} index={1} />
          </div>
          <div key="revenue" data-widget="revenue">
            <RevenueWidget ws={ws} index={2} />
          </div>
          <div key="aegis">
            <AegisBriefingWidget ws={ws} index={3} />
          </div>
          <div key="activity">
            <ActivityStreamWidget ws={ws} index={4} />
          </div>
          <div key="wake">
            <WakeWordWidget ws={ws} index={5} />
          </div>
          <div key="vault">
            <VaultStatsWidget index={6} />
          </div>
          <div key="agentes">
            <AgentesStatusWidget ws={ws} index={7} />
          </div>
          <div key="gmail">
            <GmailMiniWidget index={8} />
          </div>
          <div key="calendar">
            <CalendarWidget index={9} />
          </div>
          <div key="freqtrade">
            <FreqtradeWidget index={10} />
          </div>
          <div key="automation">
            <AutomationsWidget ws={ws} index={11} />
          </div>
          {/* 006 — familia/admin */}
          <div key="recordatorios">
            <RecordatoriosWidget ws={ws} index={12} />
          </div>
          <div key="compras">
            <ComprasWidget ws={ws} index={13} />
          </div>
          <div key="menu_dia">
            <MenuHoyWidget ws={ws} index={14} />
          </div>
          <div key="gastos">
            <GastosMesWidget ws={ws} index={15} />
          </div>
          <div key="coche">
            <CocheStatusWidget ws={ws} index={16} />
          </div>
          <div key="medicacion">
            <MedicacionWidget ws={ws} index={17} />
          </div>
          <div key="bris">
            <BrisWidget ws={ws} index={18} />
          </div>
        </ResponsiveGridLayout>
        </div>
        <div className="text-center cockpit-mono text-[9px] text-cockpit-dim mt-4">
          drag para mover · esquina inferior derecha para resize · reset al default arriba
          · {DEFAULT_LAYOUT.length} widgets
        </div>
      </main>

      <StripeToaster ws={ws} />
      <ShortcutsModal />
      <Toaster
        position="bottom-right"
        theme="dark"
        toastOptions={{
          className: 'cockpit-glass !p-4',
          duration: 8000,
        }}
      />
    </div>
  );
}
