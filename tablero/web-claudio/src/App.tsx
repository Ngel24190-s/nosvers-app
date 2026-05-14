import { useEffect, useState } from 'react';
import { ClaudioContextContext, useContextState } from './lib/context';
import { getToken, setToken, isExpired } from './lib/auth';
import HomeScreen from './components/home/HomeScreen';
import CasaShell from './components/casa/CasaShell';
import NosVersShell from './components/nosvers/NosVersShell';
import TrabajoShell from './components/trabajo/TrabajoShell';
import PTTOverlay from './components/PTTOverlay';
import LoginPrompt from './components/LoginPrompt';

export default function App() {
  const ctx = useContextState();
  const [hasToken, setHasToken] = useState<boolean>(() => !!getToken() && !isExpired());

  // Permitir login via ?token=... en la URL (modo dev / qr-code)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const t = params.get('token');
    if (t) {
      setToken(t);
      setHasToken(true);
      const url = new URL(location.href);
      url.searchParams.delete('token');
      history.replaceState({}, '', url.toString());
    }
  }, []);

  if (!hasToken) {
    return (
      <LoginPrompt
        onToken={(t) => {
          setToken(t);
          setHasToken(true);
        }}
      />
    );
  }

  let screen: JSX.Element;
  switch (ctx.current) {
    case 'casa':
      screen = <CasaShell />;
      break;
    case 'nosvers':
      screen = <NosVersShell />;
      break;
    case 'trabajo':
      screen = <TrabajoShell />;
      break;
    default:
      screen = <HomeScreen />;
  }

  return (
    <ClaudioContextContext.Provider value={ctx}>
      <div className="min-h-screen flex flex-col">
        {screen}
        {ctx.current && <PTTOverlay context={ctx.current} />}
      </div>
    </ClaudioContextContext.Provider>
  );
}
