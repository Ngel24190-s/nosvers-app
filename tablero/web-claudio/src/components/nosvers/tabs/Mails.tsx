import { Mail, Send, MessageSquare } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, EmptyState } from '../../widgets';
import { BotonEnlaceExterno } from '../widgets';
import type {
  TelegramResumenSnapshot,
  ComentariosWpSnapshot,
} from '../../../lib/api-types';

const LABELS = [
  { name: 'NosVers/Infraestructura', sub: 'VPS · Hostinger · alertas' },
  { name: 'NosVers/SEO', sub: 'Search Console · backlinks' },
  { name: 'NosVers/Facturas', sub: 'Stripe · clientes · MSA' },
  { name: 'Lectura/Tech', sub: 'Boletines técnicos' },
];

function gmailUrl(label: string): string {
  // Gmail soporta deep-link a label: encode con %2F y %20
  const encoded = label.replace(/\//g, '%2F').replace(/ /g, '%20');
  return `https://mail.google.com/mail/u/0/#label/${encoded}`;
}

function WidgetGmailEnlaces() {
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Mail size={16} className="text-emerald-700" />
        Gmail · labels NosVers
      </h3>
      <div className="space-y-2">
        {LABELS.map((l) => (
          <BotonEnlaceExterno
            key={l.name}
            href={gmailUrl(l.name)}
            label={l.name}
            sub={l.sub}
            Icon={Mail}
            accent="emerald"
          />
        ))}
      </div>
      <div className="mt-3 text-[11px] text-muted">
        OAuth Gmail desconectado · enlaces deep-link al cliente Gmail web.
      </div>
    </Card>
  );
}

function WidgetTelegramResumen() {
  const { data } = useChannel<TelegramResumenSnapshot>('telegram_resumen');
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Send size={16} className="text-emerald-700" />
          Telegram · resumen
        </h3>
        <span className="text-[11px] text-muted">{data?.fuente ?? '…'}</span>
      </div>
      {!data || data.items.length === 0 ? (
        <EmptyState text="Sin mensajes recientes." />
      ) : (
        <div className="space-y-2">
          {data.items.slice(0, 6).map((m, i) => (
            <div key={i} className="flex gap-2 py-1.5 border-b border-emerald-100 last:border-0">
              <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full self-start ${
                m.autor.toLowerCase() === 'angel'
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-lime-100 text-lime-800'
              }`}>
                {m.autor.slice(0, 8)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-fg leading-snug">{m.texto}</div>
                <div className="text-[10px] text-muted">{m.ts}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetComentariosWP() {
  const { data } = useChannel<ComentariosWpSnapshot>('comentarios_wp');
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <MessageSquare size={16} className="text-emerald-700" />
          Comentarios WP · pendientes
        </h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
          {data?.pendientes ?? 0}
        </span>
      </div>
      {!data || data.items.length === 0 ? (
        <EmptyState text="Sin comentarios pendientes." />
      ) : (
        <div className="space-y-2">
          {data.items.slice(0, 5).map((c) => (
            <div key={c.id} className="py-1.5 border-b border-emerald-100 last:border-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-fg truncate">{c.autor}</span>
                <span className="text-[10px] text-muted flex-shrink-0">{c.fecha}</span>
              </div>
              <div className="text-[11px] text-muted truncate">{c.post}</div>
              <div className="text-sm text-fg mt-1 leading-snug line-clamp-2">
                {c.extracto}
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="mt-3">
        <BotonEnlaceExterno
          href="https://nosvers.com/wp-admin/edit-comments.php?comment_status=moderated"
          label="Moderar en WP Admin"
          sub="Aprobar / responder / spam"
          Icon={MessageSquare}
          accent="lime"
        />
      </div>
    </Card>
  );
}

export default function Mails() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg flex items-center gap-2">
        <Mail size={22} className="text-emerald-700" />
        Mails y comunicación
      </h2>
      <WidgetGmailEnlaces />
      <WidgetTelegramResumen />
      <WidgetComentariosWP />
    </div>
  );
}
