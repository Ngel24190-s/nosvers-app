import { useIdentity } from './lib/auth';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';

export default function App() {
  const { identity, loading } = useIdentity();

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
  return <Dashboard identitySub={identity.sub} />;
}
