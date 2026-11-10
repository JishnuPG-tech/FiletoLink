import React, { useState, useEffect } from 'react';
import { Send, Menu, X, ArrowUpRight } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';

export const SiteHeader: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = (e: React.MouseEvent) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-black/95 backdrop-blur-md border-b border-white/[0.08] py-4'
          : 'bg-black py-5 border-b border-white/[0.05]'
      }`}
    >
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
        {/* Brand: Pure FlashFile Typography */}
        <a
          href="#"
          onClick={scrollToTop}
          className="flex items-center gap-2 focus:outline-none rounded-full group"
        >
          <span className="font-sans font-bold text-xl tracking-tight text-white group-hover:text-[#D97757] transition-colors">
            FlashFile
          </span>
          <span className="w-2 h-2 rounded-full bg-[#D97757]" />
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a
            href="#why-flashfile"
            className="text-xs font-medium text-zinc-400 hover:text-white transition-colors"
          >
            Why FlashFile
          </a>
          <a
            href="#how-it-works"
            className="text-xs font-medium text-zinc-400 hover:text-white transition-colors"
          >
            How It Works
          </a>
          <a
            href="#benefits"
            className="text-xs font-medium text-zinc-400 hover:text-white transition-colors"
          >
            Benefits
          </a>
          <a
            href="#faq"
            className="text-xs font-medium text-zinc-400 hover:text-white transition-colors"
          >
            FAQ
          </a>
          <a
            href="/admin"
            className="text-xs font-medium text-zinc-400 hover:text-[#D97757] transition-colors"
          >
            Admin
          </a>
        </nav>

        {/* Right CTA Button (Generously Curved Pill) */}
        <div className="hidden md:flex items-center gap-4">
          <a
            href={getTelegramBotLink('nav_button')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#D97757] hover:bg-[#E58A69] text-white font-medium text-xs transition-all hover:scale-[1.02] active:scale-[0.98] shadow-md shadow-[#D97757]/20 focus:outline-none"
          >
            <span>Open Telegram Bot</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Mobile menu toggle */}
        <div className="md:hidden flex items-center">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-zinc-400 hover:text-white focus:outline-none"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu (Curved Dropdown) */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-black/98 border-b border-white/[0.08] px-6 py-6 space-y-4 rounded-b-3xl">
          <a
            href="#why-flashfile"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm text-zinc-300 hover:text-white"
          >
            Why FlashFile
          </a>
          <a
            href="#how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm text-zinc-300 hover:text-white"
          >
            How It Works
          </a>
          <a
            href="#benefits"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm text-zinc-300 hover:text-white"
          >
            Benefits
          </a>
          <a
            href="#faq"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm text-zinc-300 hover:text-white"
          >
            FAQ
          </a>
          <a
            href="/admin"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm text-[#D97757] hover:text-[#ea6f4a] font-medium"
          >
            Admin Portal
          </a>
          <div className="pt-2">
            <a
              href={getTelegramBotLink('mobile_menu')}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-[#D97757] text-white font-medium text-xs"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Open Telegram Bot</span>
            </a>
          </div>
        </div>
      )}
    </header>
  );
};

export default SiteHeader;
