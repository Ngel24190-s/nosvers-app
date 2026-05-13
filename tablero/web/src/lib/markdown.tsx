import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { NoteFull } from './types';

interface Props {
  body: string;
  attachments?: NoteFull['attachments'];
  /** Callback opcional al hacer clic en un wiki-link [[slug]]. */
  onWikiLink?: (slug: string) => void;
}

function attachmentExistsMap(attachments: NoteFull['attachments'] | undefined): Map<string, boolean> {
  const m = new Map<string, boolean>();
  if (!attachments) return m;
  for (const a of attachments) m.set(a.src, a.exists);
  return m;
}

// Wiki-link regex: [[slug]] o [[slug|texto]]
const WIKILINK_RE = /\[\[([^\]\|]+)(?:\|([^\]]*))?\]\]/g;

/**
 * Transform pre-render: convertir [[slug]] en algo que react-markdown pueda
 * renderizar como link clickeable. Usamos un placeholder de etiqueta HTML
 * personalizada con un componente React mapeado.
 *
 * Estrategia: reemplazar [[slug]] por una marca markdown link especial
 *   [texto](wiki:slug)
 * y luego en components.a interceptar href que empieza con "wiki:".
 */
function preprocessWikilinks(body: string): string {
  return body.replace(WIKILINK_RE, (_, slug, label) => {
    const visible = label ?? slug;
    return `[${visible}](wiki:${slug})`;
  });
}

export function MarkdownBody({ body, attachments, onWikiLink }: Props) {
  const existMap = attachmentExistsMap(attachments);
  const processedBody = preprocessWikilinks(body);

  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        urlTransform={(url) => {
          // Preservar wiki:* esquema custom
          if (url.startsWith('wiki:')) return url;
          if (url.startsWith('attachments/')) {
            return '/' + url;
          }
          return url;
        }}
        components={{
          img: ({ src, alt }) => {
            const original = typeof src === 'string' ? src : '';
            const isAttachment = original.startsWith('/attachments/') || original.startsWith('attachments/');
            const lookup = isAttachment
              ? (original.startsWith('/') ? original.slice(1) : original)
              : original;
            const exists = !isAttachment || existMap.get(lookup) !== false;
            if (!exists) {
              return (
                <span className="inline-block rounded border border-dashed border-tinta/30 px-2 py-1 text-xs text-tinta/60">
                  imagen no disponible: {alt || lookup}
                </span>
              );
            }
            const finalSrc = isAttachment && !original.startsWith('/') ? '/' + original : original;
            return <img src={finalSrc} alt={alt ?? ''} loading="lazy" />;
          },
          a: ({ href, children, ...rest }) => {
            if (typeof href === 'string' && href.startsWith('wiki:')) {
              const slug = href.slice('wiki:'.length);
              return (
                <button
                  type="button"
                  onClick={() => onWikiLink?.(slug)}
                  className="inline-block rounded bg-emerald-50 px-1 font-medium text-emerald-700 underline decoration-dotted hover:bg-emerald-100"
                >
                  {children}
                </button>
              );
            }
            return <a href={href} {...rest}>{children}</a>;
          },
        }}
      >
        {processedBody}
      </ReactMarkdown>
    </div>
  );
}
