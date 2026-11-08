import React from 'react';
import { Send, ArrowRight, Sparkles } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';
import { ScrollReveal } from '../common/ScrollReveal';

export const FinalCtaSection: React.FC = () => {
  return (
    <section className="py-28 relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <ScrollReveal delay={100} direction="up">
          <div className="relative rounded-3xl p-10 sm:p-20 text-center glass-panel-glow overflow-hidden shadow-2xl">
            {/* Ambient Background Glow */}
            <div
              className="absolute -top-32 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-gradient-to-b from-ff-accent/25 to-purple-600/10 rounded-full blur-[120px] pointer-events-none"
              aria-hidden="true"
            />

            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/10 text-xs font-mono text-ff-signal tracking-wide mb-6">
              <Sparkles className="w-3.5 h-3.5 text-ff-accent" />
              <span>Instant Cloud Access</span>
            </div>

            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white max-w-3xl mx-auto leading-tight mb-6">
              Ready to stream your files without limits?
            </h2>

            <p className="font-sans text-ff-text-secondary text-base sm:text-lg max-w-xl mx-auto mb-10 font-normal leading-relaxed">
              Forward any file up to 4GB to FlashFile on Telegram and experience zero-buffer HTTP byte-range playback right in your browser or favorite media player.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href={getTelegramBotLink('final_cta')}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-9 py-4 rounded-xl bg-gradient-to-r from-ff-accent via-rose-500 to-purple-600 text-white font-semibold text-base shadow-xl shadow-ff-accent/30 hover:shadow-ff-accent/50 hover:-translate-y-0.5 active:translate-y-0 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring"
              >
                <Send className="w-5 h-5" />
                <span>Launch FlashFile Bot</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
