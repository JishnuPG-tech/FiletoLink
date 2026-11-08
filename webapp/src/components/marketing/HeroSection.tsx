import React from 'react';
import { Send, ArrowRight, Play, Shield, Cpu, Zap } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';
import { TransmissionCore } from '../canvas/TransmissionCore';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative min-h-[92vh] flex items-center justify-center pt-28 pb-16 overflow-hidden">
      {/* 3D Particle Backdrop */}
      <div className="absolute inset-0 z-0 flex items-center justify-center opacity-70 pointer-events-none">
        <TransmissionCore />
      </div>

      {/* Hero Foreground Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-ff-surface border border-ff-border text-xs font-mono text-ff-signal tracking-wide mb-6 shadow-xl shadow-black/40">
          <Zap className="w-3.5 h-3.5 text-ff-accent" />
          <span className="uppercase text-[11px] font-semibold tracking-wider">Telegram-Powered File & Streaming Engine</span>
        </div>

        {/* Headline */}
        <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl font-normal tracking-tight text-white max-w-4xl leading-[1.08] mb-6">
          Your files. Streamed at{' '}
          <span className="italic text-ff-accent bg-clip-text text-transparent bg-gradient-to-r from-ff-accent to-rose-400">
            wire speed
          </span>{' '}
          through Telegram.
        </h1>

        {/* Subtitle */}
        <p className="font-sans text-base sm:text-lg md:text-xl text-ff-text-secondary max-w-2xl mb-10 leading-relaxed font-normal">
          Direct HTTP byte-range video streaming, 6-worker load balancing, and 1-tap player integration powered by Telegram MTProto. Zero storage limits, instant seekability.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-14">
          <a
            href={getTelegramBotLink('hero_cta')}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-ff-accent to-ff-accent-deep text-white font-semibold text-base shadow-xl shadow-ff-accent/30 hover:shadow-ff-accent/50 hover:-translate-y-0.5 active:translate-y-0 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring"
          >
            <Send className="w-5 h-5" />
            <span>Open FlashFile on Telegram</span>
            <ArrowRight className="w-4 h-4" />
          </a>

          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-4 rounded-xl bg-ff-surface/80 border border-ff-border text-ff-text-secondary hover:text-white hover:border-ff-border-strong text-base font-medium transition-all"
          >
            <span>See How It Works</span>
          </a>
        </div>

        {/* Verified Capability Tags */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full max-w-2xl">
          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-lg bg-ff-surface/40 border border-ff-border text-xs text-ff-text-secondary justify-center sm:justify-start">
            <Zap className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="font-mono">HTTP 206 Partial Content</span>
          </div>

          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-lg bg-ff-surface/40 border border-ff-border text-xs text-ff-text-secondary justify-center sm:justify-start">
            <Cpu className="w-4 h-4 text-ff-signal flex-shrink-0" />
            <span className="font-mono">6x MTProto Worker Pool</span>
          </div>

          <div className="col-span-2 sm:col-span-1 flex items-center gap-2.5 px-3.5 py-2 rounded-lg bg-ff-surface/40 border border-ff-border text-xs text-ff-text-secondary justify-center sm:justify-start">
            <Play className="w-4 h-4 text-ff-accent flex-shrink-0" />
            <span className="font-mono">1-Tap VLC / MX Integration</span>
          </div>
        </div>
      </div>
    </section>
  );
};
