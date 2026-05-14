import { useState } from 'react';

export default function LoginPrompt({ onToken }: { onToken: (t: string) => void }) {
  const [val, setVal] = useState('');
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-bg">
      <div className="max-w-md w-full space-y-6">
        <h1 className="text-3xl font-display text-fg">Claudio</h1>
        <p className="text-muted text-sm">
          Pega aquí tu JWT (Angel: con scope trabajo · África: solo casa/nosvers).
          También puedes abrir la app con <code className="bg-border/40 px-1">?token=...</code> en la URL.
        </p>
        <textarea
          value={val}
          onChange={(e) => setVal(e.target.value)}
          placeholder="eyJ..."
          rows={6}
          className="w-full p-3 bg-bg border-2 border-border rounded font-mono text-xs"
        />
        <button
          onClick={() => val.trim() && onToken(val.trim())}
          disabled={!val.trim()}
          className="w-full py-3 bg-primary text-on-primary font-display text-lg rounded
                     disabled:opacity-40 active:scale-[0.98] transition-transform"
        >
          Entrar
        </button>
      </div>
    </div>
  );
}
