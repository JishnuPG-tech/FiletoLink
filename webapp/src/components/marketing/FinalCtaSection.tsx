import React from 'react';
import { Send, ArrowRight } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';

export const FinalCtaSection: React.FC = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="relative rounded-3xl p-10 sm:p-16 text-center border border-ff-border-strong bg-gradient-to-b from-ff-surface-strong to-ff-surface overflow-hidden shadow-2xl shadow-black">
          {/* Ambient Glow */}
          <div
            className="absolute -top-32 left-1/2 -translate-x-1/2 w-96 h-96 bg-ff-accent/20 rounded-full blur-[100px] pointer-events-none"
            aria-hidden="true"
          />

          <span className="text-xs uppercase font-mono tracking-widest text-ff-signal mb-4 block">
            Start Streaming Today
          </span>

          <h2 className="font-serif text-3xl sm:text-5xl font-normal text-white max-w-2xl mx-auto leading-tight mb-6">
            Ready to access your Telegram media without limits?
          </h2>

          <p className="font-sans text-ff-text-secondary text-base sm:text-lg max-w-xl mx-auto mb-10 font-normal">
            Forward your first file to FlashFile on Telegram and experience zero-buffer HTTP byte-range playback right in your browser or favorite media player.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href={getTelegramBotLink('final_cta')}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-ff-accent to-ff-accent-deep text-white font-semibold text-base shadow-xl shadow-ff-accent/30 hover:shadow-ff-accent/50 hover:-translate-y-0.5 active:translate-y-0 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ff-focus-ring"
            >
              <Send className="w-5 h-5" />
              <span>Launch FlashFile on Telegram</span>
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
