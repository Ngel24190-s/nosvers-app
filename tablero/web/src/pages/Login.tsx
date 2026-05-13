import { useState } from 'react';
import { setToken } from '../lib/auth';

export function Login() {
  const [jwt, setJwt] = useState('');
  const [err, setErr] = useState<string | null>(null);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const v = jwt.trim();
    if (!v) {
      setErr('Pega un JWT válido emitido por voz.auth.emitir_token.');
      return;
    }
    setToken(v);
    window.location.reload();
  }

  return (
    <main className="min-h-full flex items-center justify-center px-4 py-10">
      <form onSubmit={onSubmit} className="card w-full max-w-md p-6 bg-white">
        <h1 className="font-display text-2xl mb-2">Tablero · NosVers</h1>
        <p className="text-sm text-tinta/60 mb-4">
          Pega tu token JWT (emitido por <code className="bg-tinta/5 px-1 rounded">voz.auth.emitir_token</code>) para entrar.
        </p>
        <label className="block text-sm text-tinta/70 mb-1" htmlFor="jwt">Token JWT</label>
        <textarea
          id="jwt"
          value={jwt}
          onChange={(e) => setJwt(e.target.value)}
          rows={5}
          className="w-full rounded-md border border-tinta/15 bg-cream px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-verde"
          placeholder="eyJhbGciOiJIUzI1NiIs..."
        />
        {err && <p className="mt-2 text-sm text-africa">{err}</p>}
        <button
          type="submit"
          className="mt-4 w-full rounded-md bg-verde px-4 py-2 text-cream font-medium hover:bg-verde-dark transition-colors"
        >
          Entrar
        </button>
      </form>
    </main>
  );
}
