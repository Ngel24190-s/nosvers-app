import { useEffect, useRef, useState } from 'react';
import { Search, X } from 'lucide-react';

interface Props {
  onSearch: (q: string) => void;
  placeholder?: string;
}

export function SearchBar({ onSearch, placeholder = 'Buscar en el vault…' }: Props) {
  const [value, setValue] = useState('');
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      onSearch(value.trim());
    }, 300);
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    };
  }, [value, onSearch]);

  return (
    <div className="relative flex-1 min-w-[200px] max-w-md">
      <Search
        size={16}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-tinta/40"
      />
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-full border border-tinta/15 bg-cream pl-9 pr-9 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-verde"
      />
      {value && (
        <button
          type="button"
          onClick={() => setValue('')}
          aria-label="limpiar búsqueda"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-tinta/40 hover:text-tinta"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
