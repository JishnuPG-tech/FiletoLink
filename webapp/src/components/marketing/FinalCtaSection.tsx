import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';

export const FinalCtaSection: React.FC = () => {
  return (
    <section className="py-24 bg-black border-t border-white/[0.08]">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <div className="p-10 sm:p-16 rounded-3xl border border-white/[0.1] bg-[#0A0A0A] shadow-2xl">
          <span className="font-mono text-xs uppercase tracking-widest text-[#D97757] font-medium block mb-3">
            Start Right Now
          </span>

          <h2 className="text-3xl sm:text-5xl font-normal text-white font-serif tracking-tight mb-4 max-w-2xl mx-auto leading-tight">
            Ready to download at full speed?
          </h2>

          <p className="text-zinc-400 text-sm sm:text-base max-w-lg mx-auto mb-8 leading-relaxed">
            Forward any movie, series, or file to FlashFile on Telegram. It takes 5 seconds and requires zero setup.
          </p>

          <a
            href={getTelegramBotLink('final_cta')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-[#D97757] hover:bg-[#E58A69] text-white font-medium text-sm transition-all shadow-lg shadow-[#D97757]/20 hover:scale-[1.02] active:scale-[0.98] focus:outline-none"
          >
            <span>Launch FlashFile on Telegram</span>
            <ArrowUpRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </section>
  );
};

export default FinalCtaSection;
