import { Globe, Search, Link2, Heart, Camera, Wallet, ExternalLink } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState, Sparkbar } from '../../widgets';
import { BotonEnlaceExterno } from '../widgets';
import type {
  WebTrafficSnapshot,
  SearchConsoleSnapshot,
  AhrefsSnapshot,
  EngagementRedesSnapshot,
} from '../../../lib/api-types';

function WidgetVisitasNosVers() {
  const { data } = useChannel<WebTrafficSnapshot>('web_traffic');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Globe size={16} className="text-emerald-700" />
          Visitas nosvers.com · 30 días
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  const max = Math.max(...data.series.map((s) => s.visitas), 1);
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Globe size={16} className="text-emerald-700" />
          Visitas · 30 días
        </h3>
        <span className="text-[11px] text-muted">{data.fuente}</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Total" value={data.total_visitas} accent="emerald" size="sm" />
        <Stat label="Hoy" value={data.visitas_hoy} accent="lime" size="sm" />
        <Stat
          label="Δ ayer"
          value={`${data.delta_dia >= 0 ? '+' : ''}${data.delta_dia}`}
          accent={data.delta_dia >= 0 ? 'emerald' : 'amber'}
          size="sm"
        />
      </div>
      <div className="mt-3 flex items-end gap-[2px] h-12">
        {data.series.map((s) => (
          <div
            key={s.fecha}
            className="flex-1 bg-emerald-300 hover:bg-emerald-500 rounded-sm transition-colors"
            style={{ height: `${(s.visitas / max) * 100}%`, minHeight: '2px' }}
            title={`${s.fecha}: ${s.visitas}`}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-muted">
        <span>{data.series[0]?.fecha?.slice(5)}</span>
        <span>{data.series[data.series.length - 1]?.fecha?.slice(5)}</span>
      </div>
    </Card>
  );
}

function WidgetSearchConsole() {
  const { data } = useChannel<SearchConsoleSnapshot>('search_console');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Search size={16} className="text-emerald-700" />
          Search Console
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Search size={16} className="text-emerald-700" />
          Search Console · 28 d
        </h3>
        <span className="text-[11px] text-muted">{data.fuente}</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Impr." value={data.total_impresiones} accent="emerald" size="sm" />
        <Stat label="Clicks" value={data.total_clicks} accent="lime" size="sm" />
        <Stat label="CTR" value={`${data.ctr_pct}%`} accent="amber" size="sm" />
      </div>
      <div className="mt-3 text-[11px] text-muted uppercase tracking-wide">Top queries</div>
      <div className="mt-1 space-y-1">
        {data.queries_top.slice(0, 5).map((q) => (
          <div key={q.query} className="flex items-center justify-between gap-2 py-1 border-b border-emerald-100 last:border-0">
            <span className="text-sm text-fg truncate flex-1 min-w-0">{q.query}</span>
            <span className="text-[11px] text-muted">
              {q.clicks}/{q.impresiones}
            </span>
            <span className="text-[10px] text-muted ml-1">pos {q.posicion_media}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function WidgetAhrefs() {
  const { data } = useChannel<AhrefsSnapshot>('ahrefs');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Link2 size={16} className="text-emerald-700" />
          Ahrefs
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Link2 size={16} className="text-emerald-700" />
          Ahrefs
        </h3>
        <span className="text-[11px] text-muted">{data.fuente}</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="DR" value={data.domain_rating} accent="emerald" size="sm" />
        <Stat label="Backlinks" value={data.backlinks} accent="lime" size="sm" />
        <Stat label="Ref. domains" value={data.referring_domains} accent="amber" size="sm" />
      </div>
      <Sparkbar value={data.url_rating} max={50} accent="emerald" />
      <div className="mt-1 text-[11px] text-muted">URL rating {data.url_rating}/50</div>
      {data.top_backlinks.length > 0 && (
        <div className="mt-3 space-y-1">
          {data.top_backlinks.slice(0, 3).map((b) => (
            <div key={b.url} className="flex items-center justify-between gap-2 py-1 border-b border-emerald-100 last:border-0">
              <a href={b.url} target="_blank" rel="noopener noreferrer"
                 className="text-sm text-emerald-700 hover:underline truncate flex-1 min-w-0">
                {b.anchor || b.url}
              </a>
              <span className="text-[11px] text-muted">DR {b.dr}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetEngagementRedes() {
  const { data } = useChannel<EngagementRedesSnapshot>('engagement_redes');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Heart size={16} className="text-emerald-700" />
          Engagement redes · 7 días
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Heart size={16} className="text-emerald-700" />
          Redes · 7 días
        </h3>
        <span className="text-[11px] text-muted">{data.fuente}</span>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between py-1 border-b border-emerald-100">
          <span className="text-sm text-fg">Instagram</span>
          <span className="text-[11px] text-muted">
            {data.instagram.followers} foll · {data.instagram.engagement_rate_pct}% engagement
          </span>
        </div>
        <div className="flex items-center justify-between py-1 border-b border-emerald-100">
          <span className="text-sm text-fg">YouTube</span>
          <span className="text-[11px] text-muted">
            {data.youtube.subs} subs · {data.youtube.views_semana} views
          </span>
        </div>
        <div className="flex items-center justify-between py-1">
          <span className="text-sm text-fg">Facebook</span>
          <span className="text-[11px] text-muted">
            {data.facebook.page_likes} likes · {data.facebook.reach} reach
          </span>
        </div>
      </div>
    </Card>
  );
}

function WidgetEnlacesExternos() {
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <ExternalLink size={16} className="text-emerald-700" />
        Enlaces externos
      </h3>
      <div className="space-y-2">
        <BotonEnlaceExterno
          href="https://nosvers.com/panel-fotos/"
          label="Panel Fotos"
          sub="WP page 802 — gestión visuales"
          Icon={Camera}
          accent="emerald"
        />
        <BotonEnlaceExterno
          href="https://nosvers.com/wp-admin/"
          label="WP Admin"
          sub="Dashboard WordPress"
          Icon={Globe}
          accent="lime"
        />
        <BotonEnlaceExterno
          href="https://dashboard.stripe.com/"
          label="Stripe Dashboard"
          sub="Pagos · suscripciones · payouts"
          Icon={Wallet}
          accent="amber"
        />
      </div>
    </Card>
  );
}

export default function Web() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg flex items-center gap-2">
        <Globe size={22} className="text-emerald-700" />
        Web · nosvers.com
      </h2>
      <WidgetVisitasNosVers />
      <WidgetSearchConsole />
      <WidgetAhrefs />
      <WidgetEngagementRedes />
      <WidgetEnlacesExternos />
    </div>
  );
}
