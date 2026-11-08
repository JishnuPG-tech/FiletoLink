import React from 'react';
import { X, Check, Send, Link, PlayCircle } from 'lucide-react';
import { getTelegramBotLink } from '../../content/site-config';

export const WorkflowSection: React.FC = () => {
  const telegramProblems = [
    {
      title: 'Downloads Crawl at Slow Speeds',
      description: 'Telegram restricts download speeds inside the app, so downloading a single 2GB movie can take hours even on fast Wi-Fi.',
    },
    {
      title: 'Stops Whenever Your Screen Locks',
      description: 'If you close the app, switch to WhatsApp, or lock your phone, your download pauses or silently fails in the background.',
    },
    {
      title: 'Fails at 90% and Restarts from Zero',
      description: 'If your connection glitches for even a second, the download often corrupts and forces you to restart the whole file from 0%.',
    },
    {
      title: 'Fills Up Your Phone Storage',
      description: 'Telegram secretly stores huge cache files inside your phone memory, giving you "Storage Full" warnings when you least expect it.',
    },
  ];

  const flashfileSolutions = [
    {
      title: 'Fastest Possible Download Speeds',
      description: 'FlashFile pulls files using multiple high-speed streams at once, letting download managers like IDM and 1DM max out your internet.',
    },
    {
      title: 'Plays Instantly in VLC or MX Player',
      description: 'No need to wait for a 3GB movie to download. Tap play to stream immediately with smooth seeking and full subtitle support.',
    },
    {
      title: 'Automatic Resume If Connection Drops',
      description: 'If your Wi-Fi disconnects, your download automatically continues from the exact percentage where it paused.',
    },
    {
      title: 'Zero Storage Space Wasted',
      description: 'Watch or check movies directly in your browser or video player without cluttering your phone with gigabytes of temporary data.',
    },
  ];

  const simpleSteps = [
    {
      step: 'Step 1',
      title: 'Send or Forward Any File',
      description: 'Forward any movie, series, audio track, or zip archive up to 4 GB to FlashFile on Telegram.',
      icon: <Send className="w-5 h-5 text-[#D97757]" />,
    },
    {
      step: 'Step 2',
      title: 'Get Your Direct Link in 1 Second',
      description: 'The bot instantly replies with your high-speed download link and an instant online streaming link.',
      icon: <Link className="w-5 h-5 text-[#D97757]" />,
    },
    {
      step: 'Step 3',
      title: 'Play Instantly or Download Fast',
      description: 'Open the link in VLC/MX Player to watch right away, or paste it into IDM/1DM to download at maximum speed.',
      icon: <PlayCircle className="w-5 h-5 text-[#D97757]" />,
    },
  ];

  return (
    <section id="why-flashfile" className="py-24 bg-black border-t border-white/[0.08]">
      <div className="max-w-5xl mx-auto px-6">
        {/* Section Header */}
        <div className="mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-[#D97757] font-medium block mb-3">
            Why Use FlashFile
          </span>
          <h2 className="text-3xl sm:text-5xl font-normal text-white font-serif tracking-tight mb-4">
            The Easiest Way to Handle Telegram Media
          </h2>
          <p className="text-zinc-400 text-sm sm:text-base max-w-2xl leading-relaxed">
            Telegram is great for chatting, but downloading large files inside the app is frustrating. Here is the difference FlashFile makes.
          </p>
        </div>

        {/* Side-by-Side Comparison with Generously Curved Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-24">
          {/* Telegram Limitations (Curved Card) */}
          <div className="rounded-3xl p-7 sm:p-9 border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.06]">
                <span className="font-sans text-xs text-zinc-400 uppercase tracking-wider font-semibold">
                  Inside The Telegram App
                </span>
                <span className="text-xs text-red-400 font-medium px-2.5 py-0.5 rounded-full bg-red-500/10 border border-red-500/20">
                  Slow & Frustrating
                </span>
              </div>

              <div className="space-y-6">
                {telegramProblems.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 flex-shrink-0 mt-0.5">
                      <X className="w-3 h-3" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white mb-1">
                        {item.title}
                      </h3>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* FlashFile Solution (Curved Card with Warm Claude Orange Accent) */}
          <div className="rounded-3xl p-7 sm:p-9 border border-[#D97757]/30 bg-[#0F0D0B] flex flex-col justify-between shadow-xl shadow-[#D97757]/5">
            <div>
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#D97757]/20">
                <span className="font-sans text-xs text-[#D97757] uppercase tracking-wider font-semibold">
                  With FlashFile
                </span>
                <span className="text-xs text-emerald-400 font-medium px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  Fast & Reliable
                </span>
              </div>

              <div className="space-y-6">
                {flashfileSolutions.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-[#D97757]/15 border border-[#D97757]/30 flex items-center justify-center text-[#D97757] flex-shrink-0 mt-0.5">
                      <Check className="w-3 h-3" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white mb-1">
                        {item.title}
                      </h3>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 3 Simple Steps (Curved Cards) */}
        <div id="how-it-works" className="pt-8">
          <div className="mb-14">
            <span className="font-mono text-xs uppercase tracking-widest text-[#D97757] font-medium block mb-2">
              Simple 3-Step Process
            </span>
            <h3 className="text-2xl sm:text-4xl font-normal text-white font-serif tracking-tight mb-3">
              How to Use FlashFile
            </h3>
            <p className="text-zinc-400 text-sm max-w-xl">
              No registration or setup required. Works in seconds right inside Telegram.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {simpleSteps.map((step, idx) => (
              <div
                key={idx}
                className="p-7 rounded-3xl border border-white/[0.08] bg-[#0A0A0A] hover:border-[#D97757]/30 transition-all hover:scale-[1.01]"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="w-10 h-10 rounded-2xl bg-[#D97757]/10 border border-[#D97757]/20 flex items-center justify-center">
                    {step.icon}
                  </div>
                  <span className="font-mono text-xs text-[#D97757] font-bold">
                    {step.step}
                  </span>
                </div>
                <h4 className="text-base font-semibold text-white mb-2">
                  {step.title}
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <a
              href={getTelegramBotLink('workflow_cta')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#D97757] hover:bg-[#E58A69] text-white font-medium text-xs transition-all shadow-md shadow-[#D97757]/20"
            >
              <span>Try It Right Now on Telegram</span>
              <Send className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default WorkflowSection;
