import type { TimelineEntry } from '../lib/types';
import { TimelineItem } from './TimelineItem';
import { EmptyState } from './EmptyState';

interface Props {
  entries: TimelineEntry[];
  onSelect: (entry: TimelineEntry) => void;
}

export function TimelineList({ entries, onSelect }: Props) {
  if (entries.length === 0) {
    return <EmptyState />;
  }
  return (
    <ul className="flex flex-col gap-3">
      {entries.map((e) => (
        <li key={e.path}>
          <TimelineItem entry={e} onSelect={onSelect} />
        </li>
      ))}
    </ul>
  );
}
