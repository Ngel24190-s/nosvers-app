import { useState } from 'react';
import { Sun, HardHat, Users, FileText } from 'lucide-react';
import ContextSwitcher from '../ContextSwitcher';
import BottomTabs, { type Tab } from '../BottomTabs';
import Aujourdhui from './tabs/Aujourdhui';
import Chantiers from './tabs/Chantiers';
import Equipe from './tabs/Equipe';
import Docs from './tabs/Docs';

const TABS: Tab[] = [
  { id: 'today', label: "Aujourd'hui", Icon: Sun },
  { id: 'chantiers', label: 'Chantiers', Icon: HardHat },
  { id: 'equipe', label: 'Équipe', Icon: Users },
  { id: 'docs', label: 'Docs', Icon: FileText },
];

export default function TrabajoShell() {
  const [active, setActive] = useState('today');
  let panel: JSX.Element;
  switch (active) {
    case 'chantiers': panel = <Chantiers />; break;
    case 'equipe': panel = <Equipe />; break;
    case 'docs': panel = <Docs />; break;
    default: panel = <Aujourdhui />;
  }
  return (
    <div className="min-h-screen flex flex-col bg-white text-black font-body">
      <ContextSwitcher title="Cond. Travaux" variant="di" subtitle="Angel · Chef d'équipe" />
      <main className="flex-1 p-4 pb-24">{panel}</main>
      <BottomTabs tabs={TABS} active={active} onSelect={setActive} variant="di" />
    </div>
  );
}
