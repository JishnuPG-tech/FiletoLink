import React from 'react';
import { Send, Activity } from 'lucide-react';
import { getSiteConfig } from '../../content/site-config';

export const SiteFooter: React.FC = () => {
  const config = getSiteConfig();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-ff-border bg-ff-bg-raised py-12 text-sm text-ff-text-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand */}
        <div className="flex flex-col items-center md:items-start gap-1">
          <div className="flex items-center gap-2">
            <span className="font-display font-bold text-white text-base">FlashFile</span>
            <span className="font-serif italic text-ff-accent text-sm">Engine</span>
          </div>
          <p className="text-xs text-ff-text-muted">
            High-speed Telegram media proxy & byte-stream server.
          </p>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6 text-xs font-mono">
          <a
            href={config.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition-colors"
          >
            <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
              <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5c.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34c-.46-1.16-1.11-1.47-1.11-1.47c-.91-.62.07-.6.07-.6c1 .07 1.53 1.03 1.53 1.03c.87 1.52 2.34 1.07 2.91.83c.09-.65.35-1.09.63-1.34c-2.22-.25-4.55-1.11-4.55-4.92c0-1.11.38-2 1.03-2.71c-.1-.25-.45-1.29.1-2.64c0 0 .84-.27 2.75 1.02c.79-.22 1.65-.33 2.5-.33s1.71.11 2.5.33c1.91-1.29 2.75-1.02 2.75-1.02c.55 1.35.2 2.39.1 2.64c.65.71 1.03 1.6 1.03 2.71c0 3.82-2.34 4.66-4.57 4.91c.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2" />
            </svg>
            <span>GitHub</span>
          </a>

          <a
            href={config.channelUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition-colors"
          >
            <Send className="w-3.5 h-3.5 text-ff-accent" />
            <span>Telegram Channel</span>
          </a>

          <a
            href={config.statusEndpoint}
            className="flex items-center gap-1.5 hover:text-white transition-colors"
          >
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Status</span>
          </a>
        </div>

        {/* Copyright */}
        <div className="text-xs text-ff-text-muted text-center md:text-right">
          &copy; {currentYear} FlashFile • Built on open-source FileToLink architecture.
        </div>
      </div>
    </footer>
  );
};
