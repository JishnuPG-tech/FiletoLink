import React, { useEffect, useState } from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';

export type ThemeMode = 'system' | 'light' | 'dark';

export interface SystemThemeToggleProps {
  look?: 'switch' | 'button' | 'segmented';
  defaultMode?: ThemeMode;
  className?: string;
  onThemeChange?: (theme: 'dark' | 'light') => void;
}

/**
 * SystemThemeToggle
 * Ported from Framer: https://framer.com/m/SystemThemeToggle-jM5bNp.js@vcYk6tmtvZukHtQi14Qo
 * Supports switch, button, and segmented looks with system preference detection and localStorage persistence.
 */
export const SystemThemeToggle: React.FC<SystemThemeToggleProps> = ({
  look = 'segmented',
  defaultMode = 'dark',
  className = '',
  onThemeChange,
}) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return defaultMode;
    const stored = localStorage.getItem('ff_theme_mode');
    return (stored as ThemeMode) || defaultMode;
  });

  const [activeTheme, setActiveTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const root = document.documentElement;

    const applyTheme = () => {
      let resolved: 'dark' | 'light' = 'dark';

      if (mode === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        resolved = prefersDark ? 'dark' : 'light';
      } else {
        resolved = mode;
      }

      setActiveTheme(resolved);

      if (resolved === 'dark') {
        root.classList.add('dark');
        root.classList.remove('light');
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
      }

      onThemeChange?.(resolved);
    };

    applyTheme();
    localStorage.setItem('ff_theme_mode', mode);

    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemChange = () => {
      if (mode === 'system') applyTheme();
    };

    mql.addEventListener('change', handleSystemChange);
    return () => mql.removeEventListener('change', handleSystemChange);
  }, [mode, onThemeChange]);

  const cycleTheme = () => {
    if (mode === 'dark') setMode('light');
    else if (mode === 'light') setMode('system');
    else setMode('dark');
  };

  if (look === 'button') {
    return (
      <button
        onClick={cycleTheme}
        className={`p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-ff-muted hover:text-white transition-all duration-200 flex items-center justify-center ${className}`}
        title={`Theme: ${mode} (click to toggle)`}
        aria-label="Toggle Theme"
      >
        {activeTheme === 'dark' ? (
          <Moon className="w-4 h-4 text-sky-400" />
        ) : (
          <Sun className="w-4 h-4 text-amber-400" />
        )}
      </button>
    );
  }

  if (look === 'switch') {
    const isDark = activeTheme === 'dark';
    return (
      <button
        onClick={() => setMode(isDark ? 'light' : 'dark')}
        className={`relative w-12 h-6 rounded-full p-0.5 bg-white/[0.06] border border-white/[0.1] transition-colors duration-300 focus:outline-none ${className}`}
        aria-label="Switch Theme"
      >
        <div
          className={`w-5 h-5 rounded-full bg-white flex items-center justify-center transform transition-transform duration-300 shadow-md ${
            isDark ? 'translate-x-6 bg-slate-900 text-sky-400' : 'translate-x-0 bg-white text-amber-500'
          }`}
        >
          {isDark ? <Moon className="w-3 h-3" /> : <Sun className="w-3 h-3" />}
        </div>
      </button>
    );
  }

  // Segmented control look (Default & most versatile)
  return (
    <div
      className={`inline-flex items-center p-0.5 rounded-full bg-black/40 backdrop-blur-md border border-white/[0.08] ${className}`}
    >
      <button
        onClick={() => setMode('light')}
        className={`p-1.5 px-2.5 rounded-full text-xs font-medium transition-all duration-200 flex items-center gap-1.5 ${
          mode === 'light'
            ? 'bg-white text-black shadow-sm'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="Light Mode"
      >
        <Sun className="w-3.5 h-3.5" />
      </button>

      <button
        onClick={() => setMode('system')}
        className={`p-1.5 px-2.5 rounded-full text-xs font-medium transition-all duration-200 flex items-center gap-1.5 ${
          mode === 'system'
            ? 'bg-white/20 text-white shadow-sm'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="System Auto"
      >
        <Monitor className="w-3.5 h-3.5" />
      </button>

      <button
        onClick={() => setMode('dark')}
        className={`p-1.5 px-2.5 rounded-full text-xs font-medium transition-all duration-200 flex items-center gap-1.5 ${
          mode === 'dark'
            ? 'bg-white/[0.15] text-white shadow-sm border border-white/[0.1]'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="Dark Mode"
      >
        <Moon className="w-3.5 h-3.5 text-sky-400" />
      </button>
    </div>
  );
};

export default SystemThemeToggle;
