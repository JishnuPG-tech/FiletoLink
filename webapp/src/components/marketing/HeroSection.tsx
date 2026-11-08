import React from 'react';
import { ArrowUpRight, Play, Zap, ShieldCheck, Smartphone } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative min-h-[85vh] flex flex-col justify-center pt-36 pb-20 bg-black">
      <div className="max-w-4xl mx-auto px-6 text-left">
        {/* Friendly Eyebrow Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#D97757]/10 border border-[#D97757]/25 text-[#D97757] mb-6">
          <Zap className="w-3.5 h-3.5 fill-[#D97757]" />
          <span className="font-sans text-xs font-medium tracking-wide">
            High-Speed Telegram Download & Streaming Bot
          </span>
        </div>

        {/* Clear, Human Headline with Claude Orange */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-normal tracking-tight text-white leading-[1.08] mb-6 font-serif">
          Turn any Telegram file into a{' '}
          <span className="text-[#D97757] italic">high-speed link</span>.
        </h1>

        {/* User-Friendly Everyday Copy */}
        <p className="text-base sm:text-lg text-zinc-300 max-w-2xl leading-relaxed mb-10 font-normal">
          Downloading inside Telegram is painfully slow, stops if your screen locks, and eats up your phone storage. FlashFile gives you a clean direct link so you can <strong className="text-white font-medium">watch movies instantly in VLC or MX Player</strong> without waiting, or download files at your maximum Wi-Fi speed.
        </p>

        {/* Call to Actions with Smooth Curved Corners */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 mb-16">
          <a
            href={getTelegramBotLink('hero_primary')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-full bg-[#D97757] hover:bg-[#E58A69] text-white font-medium text-sm transition-all shadow-lg shadow-[#D97757]/20 hover:scale-[1.02] active:scale-[0.98] focus:outline-none"
          >
            <span>Start Free on Telegram</span>
            <ArrowUpRight className="w-4 h-4" />
          </a>

          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-full border border-white/[0.15] hover:border-white/[0.3] text-zinc-300 hover:text-white font-medium text-sm transition-all focus:outline-none"
          >
            <Play className="w-4 h-4 text-[#D97757] fill-[#D97757]" />
            <span>See How It Works</span>
          </a>
        </div>

        {/* 4 Everyday Benefits (Curved Edge Cards) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between hover:border-white/[0.18] transition-colors">
            <div className="w-8 h-8 rounded-xl bg-[#D97757]/10 flex items-center justify-center text-[#D97757] mb-3">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white text-sm mb-1">
                Full Internet Speed
              </div>
              <div className="text-xs text-zinc-400 leading-relaxed">
                Uses multiple connections at once to max out your Wi-Fi or 5G.
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between hover:border-white/[0.18] transition-colors">
            <div className="w-8 h-8 rounded-xl bg-[#D97757]/10 flex items-center justify-center text-[#D97757] mb-3">
              <Play className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white text-sm mb-1">
                Stream Without Saving
              </div>
              <div className="text-xs text-zinc-400 leading-relaxed">
                Play movies and songs right away in MX Player, VLC, or Chrome.
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between hover:border-white/[0.18] transition-colors">
            <div className="w-8 h-8 rounded-xl bg-[#D97757]/10 flex items-center justify-center text-[#D97757] mb-3">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white text-sm mb-1">
                Never Starts Over
              </div>
              <div className="text-xs text-zinc-400 leading-relaxed">
                If your internet drops, your download resumes from where it stopped.
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between hover:border-white/[0.18] transition-colors">
            <div className="w-8 h-8 rounded-xl bg-[#D97757]/10 flex items-center justify-center text-[#D97757] mb-3">
              <Smartphone className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white text-sm mb-1">
                Save Phone Memory
              </div>
              <div className="text-xs text-zinc-400 leading-relaxed">
                No huge hidden Telegram cache files filling up your phone.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
