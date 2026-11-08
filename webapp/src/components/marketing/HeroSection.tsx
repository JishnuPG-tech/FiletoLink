import React from 'react';
import { Send, ArrowRight, Play, DownloadCloud, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';
import { ScrollReveal } from '../common/ScrollReveal';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative min-h-[96vh] flex items-center justify-center pt-32 pb-20 overflow-hidden bg-transparent">
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
        {/* Eyebrow Pill */}
        <ScrollReveal delay={50} direction="down">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full glass-panel text-xs font-mono text-ff-signal tracking-wide mb-8 shadow-2xl">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="uppercase text-[11px] font-semibold tracking-wider text-slate-300">
              High-Speed Telegram-to-Link & Instant Streaming Engine
            </span>
            <Zap className="w-3.5 h-3.5 text-ff-accent animate-pulse" />
          </div>
        </ScrollReveal>

        {/* Main Headline */}
        <ScrollReveal delay={150} direction="up">
          <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-normal tracking-tight text-white max-w-4xl leading-[1.06] mb-8">
            Never get stuck downloading on{' '}
            <span className="italic text-ff-accent bg-clip-text text-transparent bg-gradient-to-r from-ff-accent via-rose-400 to-purple-400">
              Telegram
            </span>{' '}
            again.
          </h1>
        </ScrollReveal>

        {/* Core Subtitle addressing user's real pain points */}
        <ScrollReveal delay={250} direction="up">
          <p className="font-sans text-base sm:text-lg md:text-xl text-ff-text-secondary max-w-2xl mb-12 leading-relaxed font-normal">
            Downloading directly inside Telegram is slow, stops if you close the chat, and often freezes halfway. FlashFile converts any Telegram file into a <span className="text-white font-medium">high-speed, 100% resumable direct link</span> — and lets you <span className="text-white font-medium">stream instantly</span> to verify print, voice, and multi-audio without wasting storage.
          </p>
        </ScrollReveal>

        {/* Primary Action Buttons */}
        <ScrollReveal delay={350} direction="up">
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-16">
            <a
              href={getTelegramBotLink('hero_cta')}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-ff-accent to-ff-accent-deep text-white font-semibold text-base shadow-xl shadow-ff-accent/30 hover:shadow-ff-accent/50 hover:-translate-y-0.5 active:translate-y-0 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring"
            >
              <Send className="w-5 h-5" />
              <span>Convert Telegram File to Link</span>
              <ArrowRight className="w-4 h-4" />
            </a>

            <a
              href="#problem-solution"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-4 rounded-xl glass-panel text-ff-text-secondary hover:text-white hover:border-ff-border-strong text-base font-medium transition-all hover:-translate-y-0.5"
            >
              <span>See Comparison & Features</span>
            </a>
          </div>
        </ScrollReveal>

        {/* 3 Main Value Props */}
        <ScrollReveal delay={450} direction="up">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-3xl">
            <div className="flex items-center gap-3 px-4 py-3.5 rounded-xl glass-panel text-xs text-ff-text-secondary justify-center sm:justify-start hover:border-white/20 transition-colors">
              <DownloadCloud className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <div className="text-left">
                <div className="font-semibold text-white">Full-Speed HTTP Links</div>
                <div className="text-[11px] text-ff-text-muted">IDM, 1DM & ADM multi-threading</div>
              </div>
            </div>

            <div className="flex items-center gap-3 px-4 py-3.5 rounded-xl glass-panel text-xs text-ff-text-secondary justify-center sm:justify-start hover:border-white/20 transition-colors">
              <Play className="w-5 h-5 text-ff-accent flex-shrink-0" />
              <div className="text-left">
                <div className="font-semibold text-white">Stream Without Download</div>
                <div className="text-[11px] text-ff-text-muted">Instant playback, 0 phone storage</div>
              </div>
            </div>

            <div className="flex items-center gap-3 px-4 py-3.5 rounded-xl glass-panel text-xs text-ff-text-secondary justify-center sm:justify-start hover:border-white/20 transition-colors">
              <CheckCircle2 className="w-5 h-5 text-ff-signal flex-shrink-0" />
              <div className="text-left">
                <div className="font-semibold text-white">Audio & Print Check</div>
                <div className="text-[11px] text-ff-text-muted">Verify voice, dubbing & quality</div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
