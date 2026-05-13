import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { NoteFull } from './types';

interface Props {
  body: string;
  attachments?: NoteFull['attachments'];
}

function attachmentExistsMap(attachments: NoteFull['attachments'] | undefined): Map<string, boolean> {
  const m = new Map<string, boolean>();
  if (!attachments) return m;
  for (const a of attachments) m.set(a.src, a.exists);
  return m;
}

export function MarkdownBody({ body, attachments }: Props) {
  const existMap = attachmentExistsMap(attachments);

  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        urlTransform={(url) => {
          // Rewrite attachments/* → /attachments/* so nginx serves them.
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
        }}
      >
        {body}
      </ReactMarkdown>
    </div>
  );
}
