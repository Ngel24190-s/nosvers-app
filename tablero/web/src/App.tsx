import { lazy, Suspense, useEffect, useState } from 'react';
import { useIdentity } from './lib/auth';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';

const Cockpit = lazy(() => import('./pages/Cockpit'));
const AutomationListPage = lazy(() =>
  import('./components/automatizaciones/AutomationListPage').then((m) => ({ default: m.AutomationListPage })),
);

type Route = 'dashboard' | 'cockpit' | 'automatizaciones';

function routeFromLocation(): Route {
  if (typeof window === 'undefined') return 'dashboard';
  const path = window.location.pathname;
  const hash = window.location.hash;
  if (hash === '#cockpit/automatizaciones' || hash === '#/cockpit/automatizaciones') {
    return 'automatizaciones';
  }
  if (path.endsWith('/cockpit') || hash === '#cockpit' || hash === '#/cockpit') {
    return 'cockpit';
  }
  return 'dashboard';
}

export default function App() {
  const { identity, loading } = useIdentity();
  const [route, setRoute] = useState<Route>(routeFromLocation());

  useEffect(() => {
    const onChange = () => setRoute(routeFromLocation());
    window.addEventListener('hashchange', onChange);
    window.addEventListener('popstate', onChange);
    return () => {
      window.removeEventListener('hashchange', onChange);
      window.removeEventListener('popstate', onChange);
    };
  }, []);

  if (loading) {
    return (
      <main className="min-h-full flex items-center justify-center">
        <div className="skeleton w-40 h-8" aria-busy />
      </main>
    );
  }
  if (!identity) {
    return <Login />;
  }

  if (route === 'automatizaciones') {
    return (
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] text-[#9ca3af] font-mono text-xs">
            cargando editor…
          </div>
        }
      >
        <AutomationListPage
          onBack={() => {
            window.location.hash = 'cockpit';
          }}
        />
      </Suspense>
    );
  }

  if (route === 'cockpit') {
    const exitToDashboard = () => {
      const path = window.location.pathname;
      if (path.endsWith('/cockpit')) {
        window.history.pushState({}, '', path.replace(/\/cockpit$/, '/') || '/');
      }
      if (window.location.hash) {
        window.history.replaceState({}, '', window.location.pathname + window.location.search);
      }
      setRoute('dashboard');
    };
    return (
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] text-[#9ca3af] font-mono text-xs">
            cargando cockpit…
          </div>
        }
      >
        <Cockpit identitySub={identity.sub} onExit={exitToDashboard} />
      </Suspense>
    );
  }

  return (
    <>
      <Dashboard identitySub={identity.sub} />
      <button
        onClick={() => {
          window.location.hash = 'cockpit';
        }}
        className="fixed bottom-6 right-6 z-30 px-4 py-2 font-mono text-xs uppercase tracking-wider text-white hover:text-emerald-300 border border-white/20 rounded-lg shadow-2xl transition"
        style={{
          background: 'linear-gradient(135deg, rgba(52,211,153,0.25), rgba(167,139,250,0.25))',
          backdropFilter: 'blur(12px)',
        }}
        aria-label="Abrir Cockpit Mission Control"
      >
        ▶ COCKPIT
      </button>
    </>
  );
}
