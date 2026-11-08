import React from 'react';
import { getSiteConfig } from '../../content/site-config';

export const SiteFooter: React.FC = () => {
  const config = getSiteConfig();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-white/[0.08] bg-black py-12 text-xs text-zinc-400">
      <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white font-sans text-sm">FlashFile</span>
          <span className="text-zinc-600">/</span>
          <span className="text-zinc-400">HTTP 206 Streaming Engine</span>
        </div>

        <div className="flex items-center gap-6 font-mono text-[11px]">
          <a
            href={config.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            GitHub
          </a>
          <a
            href={config.channelUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            Telegram
          </a>
          <span className="text-zinc-600">|</span>
          <span className="text-zinc-500">&copy; {currentYear} FlashFile</span>
        </div>
      </div>
    </footer>
  );
};

export default SiteFooter;
