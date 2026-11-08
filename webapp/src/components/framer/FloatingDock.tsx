import React, { useRef, useState } from 'react';
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  AnimatePresence,
} from 'framer-motion';
import {
  Home,
  Play,
  Layers,
  Cpu,
  HelpCircle,
  Send,
  Ticket,
} from 'lucide-react';
import { SystemThemeToggle } from './SystemThemeToggle';

export interface DockItem {
  title: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
}

export interface FloatingDockProps {
  className?: string;
}

/**
 * FloatingDock
 * Ported from Framer: https://framer.com/m/Floating-Dock-Native-gmGyg8.js@Pcp3rLgxRHRHvjauCH4S
 * macOS-style expanding bottom floating dock with spring-magnified icon physics.
 */
export const FloatingDock: React.FC<FloatingDockProps> = ({ className = '' }) => {
  const mouseX = useMotionValue(Infinity);

  const defaultItems: DockItem[] = [
    {
      title: 'Home',
      icon: <Home className="w-5 h-5" />,
      href: '#',
    },
    {
      title: 'Stream Simulator',
      icon: <Play className="w-5 h-5" />,
      href: '#simulator',
    },
    {
      title: 'VIP Pass',
      icon: <Ticket className="w-5 h-5" />,
      href: '#vip-pass',
    },
    {
      title: 'Features (Bento)',
      icon: <Layers className="w-5 h-5" />,
      href: '#features',
    },
    {
      title: 'Architecture',
      icon: <Cpu className="w-5 h-5" />,
      href: '#architecture',
    },
    {
      title: 'FAQ',
      icon: <HelpCircle className="w-5 h-5" />,
      href: '#faq',
    },
    {
      title: 'Open Telegram Bot',
      icon: <Send className="w-5 h-5 text-rose-400" />,
      href: 'https://t.me/FiletoLinkBot',
    },
  ];

  return (
    <div
      className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40 hidden md:flex items-center gap-3 px-3 py-2 rounded-2xl bg-[#08090D]/85 backdrop-blur-2xl border border-white/[0.08] shadow-2xl shadow-black/60 ${className}`}
      onMouseMove={(e) => mouseX.set(e.pageX)}
      onMouseLeave={() => mouseX.set(Infinity)}
    >
      <div className="flex items-end gap-2">
        {defaultItems.map((item, idx) => (
          <DockIcon key={idx} mouseX={mouseX} item={item} />
        ))}
      </div>

      <div className="h-6 w-[1px] bg-white/[0.1] mx-0.5" />

      {/* Embedded Compact Theme Toggle */}
      <SystemThemeToggle look="button" />
    </div>
  );
};

interface DockIconProps {
  mouseX: any;
  item: DockItem;
}

const DockIcon: React.FC<DockIconProps> = ({ mouseX, item }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);

  const distance = useTransform(mouseX, (val: number) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
    return val - bounds.x - bounds.width / 2;
  });

  const widthSync = useTransform(distance, [-140, 0, 140], [42, 64, 42]);
  const width = useSpring(widthSync, { mass: 0.1, stiffness: 160, damping: 14 });

  return (
    <a
      href={item.href}
      onClick={item.onClick}
      className="relative flex flex-col items-center group focus:outline-none"
    >
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.85 }}
            animate={{ opacity: 1, y: -8, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.85 }}
            transition={{ duration: 0.15 }}
            className="absolute -top-7 whitespace-nowrap px-2.5 py-1 rounded-md bg-zinc-900 border border-white/[0.12] text-white text-[11px] font-medium shadow-xl pointer-events-none z-50"
          >
            {item.title}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        ref={ref}
        style={{ width, height: width }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className="rounded-xl flex items-center justify-center bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-zinc-300 hover:text-white transition-colors duration-150 relative cursor-pointer"
      >
        {item.icon}
      </motion.div>
    </a>
  );
};

export default FloatingDock;
