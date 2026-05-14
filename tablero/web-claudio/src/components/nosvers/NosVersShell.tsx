import { useState } from 'react';
import { Sunrise, Sprout, Globe, Mail, Bot } from 'lucide-react';
import ContextSwitcher from '../ContextSwitcher';
import BottomTabs, { type Tab } from '../BottomTabs';
import Hoy from './tabs/Hoy';
import Granja from './tabs/Granja';
import Web from './tabs/Web';
import Mails from './tabs/Mails';
import Agentes from './tabs/Agentes';

const TABS: Tab[] = [
  { id: 'hoy', label: 'Hoy', Icon: Sunrise },
  { id: 'granja', label: 'Granja', Icon: Sprout },
  { id: 'web', label: 'Web', Icon: Globe },
  { id: 'mails', label: 'Mails', Icon: Mail },
  { id: 'agentes', label: 'Agentes', Icon: Bot },
];

export default function NosVersShell() {
  const [active, setActive] = useState('hoy');
  let panel: JSX.Element;
  switch (active) {
    case 'granja': panel = <Granja />; break;
    case 'web': panel = <Web />; break;
    case 'mails': panel = <Mails />; break;
    case 'agentes': panel = <Agentes />; break;
    default: panel = <Hoy />;
  }
  return (
    <div className="min-h-screen flex flex-col bg-bg text-fg">
      <ContextSwitcher title="NosVers" />
      <main className="flex-1 p-4 pb-24">{panel}</main>
      <BottomTabs tabs={TABS} active={active} onSelect={setActive} />
    </div>
  );
}
