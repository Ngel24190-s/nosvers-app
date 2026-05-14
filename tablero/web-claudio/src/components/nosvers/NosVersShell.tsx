import { useState } from 'react';
import { Sprout, Leaf, ShoppingBag, Fish, Activity } from 'lucide-react';
import ContextSwitcher from '../ContextSwitcher';
import BottomTabs, { type Tab } from '../BottomTabs';
import HoyGranja from './tabs/HoyGranja';
import Huerto from './tabs/Huerto';
import Tienda from './tabs/Tienda';
import AAPPMA from './tabs/AAPPMA';
import CockpitMini from './tabs/CockpitMini';

const TABS: Tab[] = [
  { id: 'hoy', label: 'Granja', Icon: Sprout },
  { id: 'huerto', label: 'Huerto', Icon: Leaf },
  { id: 'tienda', label: 'Tienda', Icon: ShoppingBag },
  { id: 'aappma', label: 'AAPPMA', Icon: Fish },
  { id: 'cockpit', label: 'Cockpit', Icon: Activity },
];

export default function NosVersShell() {
  const [active, setActive] = useState('hoy');
  let panel: JSX.Element;
  switch (active) {
    case 'huerto': panel = <Huerto />; break;
    case 'tienda': panel = <Tienda />; break;
    case 'aappma': panel = <AAPPMA />; break;
    case 'cockpit': panel = <CockpitMini />; break;
    default: panel = <HoyGranja />;
  }
  return (
    <div className="min-h-screen flex flex-col bg-bg text-fg">
      <ContextSwitcher title="NosVers" />
      <main className="flex-1 p-4 pb-24">{panel}</main>
      <BottomTabs tabs={TABS} active={active} onSelect={setActive} />
    </div>
  );
}
