import { useState } from 'react';
import { Calendar, ListChecks, Wallet, Bell, Home } from 'lucide-react';
import ContextSwitcher from '../ContextSwitcher';
import BottomTabs, { type Tab } from '../BottomTabs';
import HoyTab from './tabs/Hoy';
import ListasTab from './tabs/Listas';
import GastarTab from './tabs/Gastar';
import RecordarTab from './tabs/Recordar';
import CasaTab from './tabs/Casa';

const TABS: Tab[] = [
  { id: 'hoy', label: 'Hoy', Icon: Calendar },
  { id: 'listas', label: 'Listas', Icon: ListChecks },
  { id: 'gastar', label: 'Gastar', Icon: Wallet },
  { id: 'recordar', label: 'Recordar', Icon: Bell },
  { id: 'casa', label: 'Casa', Icon: Home },
];

export default function CasaShell() {
  const [active, setActive] = useState('hoy');
  let panel: JSX.Element;
  switch (active) {
    case 'listas': panel = <ListasTab />; break;
    case 'gastar': panel = <GastarTab />; break;
    case 'recordar': panel = <RecordarTab />; break;
    case 'casa': panel = <CasaTab />; break;
    default: panel = <HoyTab />;
  }
  return (
    <div className="min-h-screen flex flex-col bg-bg text-fg">
      <ContextSwitcher title="Casa" />
      <main className="flex-1 p-4 pb-24">{panel}</main>
      <BottomTabs tabs={TABS} active={active} onSelect={setActive} />
    </div>
  );
}
