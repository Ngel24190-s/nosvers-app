import { useClaudioContext } from '../../lib/context';
import { getSub } from '../../lib/auth';
import CardCasa from './CardCasa';
import CardNosVers from './CardNosVers';
import CardTrabajo from './CardTrabajo';

function saludo(): string {
  const h = new Date().getHours();
  if (h >= 6 && h < 12) return 'Buenos días';
  if (h >= 12 && h < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

function nombre(sub: string): string {
  if (sub === 'africa') return 'África';
  return sub.charAt(0).toUpperCase() + sub.slice(1);
}

export default function HomeScreen() {
  const { available, setContext } = useClaudioContext();
  const sub = getSub();

  return (
    <main className="min-h-screen flex flex-col bg-bg text-fg p-5">
      <header className="pt-4 pb-6">
        <h1 className="font-display text-3xl">
          {saludo()}, {nombre(sub)}
        </h1>
        <p className="text-muted text-sm mt-1">¿Dónde estás ahora?</p>
      </header>

      <div className="flex-1 flex flex-col gap-4">
        {available.includes('casa') && <CardCasa onSelect={() => setContext('casa')} />}
        {available.includes('nosvers') && (
          <CardNosVers onSelect={() => setContext('nosvers')} />
        )}
        {available.includes('trabajo') && (
          <CardTrabajo onSelect={() => setContext('trabajo')} />
        )}
      </div>

      <footer className="pt-6 text-center text-muted text-xs">
        o di <span className="font-mono">"claudio"</span> desde el PC casa
      </footer>
    </main>
  );
}
