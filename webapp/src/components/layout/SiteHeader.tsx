import React, { useState, useEffect } from 'react';
import { Send, Menu, X, Activity } from 'lucide-react';
import { getSiteConfig, getTelegramBotLink } from '../../content/site-config';

export const SiteHeader: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const config = getSiteConfig();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-ff-bg/85 backdrop-blur-md border-b border-ff-border py-3.5 shadow-2xl shadow-black/50'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Brand */}
        <a href="#" className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring rounded-lg">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-ff-accent to-ff-accent-deep flex items-center justify-center text-white shadow-lg shadow-ff-accent/25 group-hover:scale-105 transition-transform">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1.5">
              <span className="font-display font-bold text-lg text-white tracking-tight">FlashFile</span>
              <span className="font-serif italic text-ff-accent text-lg">Pro</span>
            </div>
            <span className="text-[10px] uppercase font-mono tracking-wider text-ff-text-muted">By FileToLink</span>
          </div>
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a href="#how-it-works" className="text-sm font-medium text-ff-text-secondary hover:text-white transition-colors">
            How It Works
          </a>
          <a href="#features" className="text-sm font-medium text-ff-text-secondary hover:text-white transition-colors">
            Features
          </a>
          <a href="#architecture" className="text-sm font-medium text-ff-text-secondary hover:text-white transition-colors">
            Architecture
          </a>
          <a href="#faq" className="text-sm font-medium text-ff-text-secondary hover:text-white transition-colors">
            FAQ
          </a>
        </nav>

        {/* Actions */}
        <div className="hidden md:flex items-center gap-4">
          <a
            href={config.statusEndpoint}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-ff-surface border border-ff-border text-xs font-mono text-ff-text-secondary hover:text-white hover:border-ff-border-strong transition-all"
            title="Check live server status"
          >
            <span className="w-2 h-2 rounded-full bg-ff-success shadow-[0_0_8px_rgba(72,214,160,0.8)] animate-pulse" />
            <span>Online</span>
          </a>

          <a
            href={getTelegramBotLink('header_nav')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-ff-accent to-ff-accent-deep text-white text-sm font-semibold shadow-lg shadow-ff-accent/25 hover:shadow-ff-accent/40 hover:-translate-y-0.5 active:translate-y-0 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring"
          >
            <Send className="w-4 h-4" />
            <span>Open Bot</span>
          </a>
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg text-ff-text-secondary hover:text-white hover:bg-ff-surface focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-x-0 border-t mt-3 px-4 pt-4 pb-6 flex flex-col gap-4 animate-fade-in">
          <a
            href="#how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-ff-text-secondary hover:text-white py-1"
          >
            How It Works
          </a>
          <a
            href="#features"
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-ff-text-secondary hover:text-white py-1"
          >
            Features
          </a>
          <a
            href="#architecture"
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-ff-text-secondary hover:text-white py-1"
          >
            Architecture
          </a>
          <a
            href="#faq"
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-ff-text-secondary hover:text-white py-1"
          >
            FAQ
          </a>

          <div className="pt-2 flex flex-col gap-3">
            <a
              href={getTelegramBotLink('mobile_menu')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-gradient-to-r from-ff-accent to-ff-accent-deep text-white text-sm font-semibold shadow-lg shadow-ff-accent/30"
            >
              <Send className="w-4 h-4" />
              <span>Open FlashFile on Telegram</span>
            </a>
          </div>
        </div>
      )}
    </header>
  );
};
