import React from 'react';
import { XCircle, CheckCircle2, MessageSquare, Link2, PlaySquare, ArrowRight } from 'lucide-react';
import { ScrollReveal } from '../common/ScrollReveal';

export const WorkflowSection: React.FC = () => {
  const steps = [
    {
      step: '01',
      icon: <MessageSquare className="w-6 h-6 text-ff-accent" />,
      title: 'Forward Any File to the Bot',
      description: 'Send any video, movie, audio, or archive up to 4 GB to @flashfilezbot. Zero upload wait — it registers instantly from Telegram cloud storage.',
      badge: 'Zero Upload Wait',
    },
    {
      step: '02',
      icon: <Link2 className="w-6 h-6 text-ff-signal" />,
      title: 'Get Fast Link & Stream URL',
      description: 'The bot replies in under 1 second with your direct HTTP download link, online web streaming link, and 1-tap mobile player buttons.',
      badge: '< 1s Response Time',
    },
    {
      step: '03',
      icon: <PlaySquare className="w-6 h-6 text-emerald-400" />,
      title: 'Stream to Verify or Download',
      description: 'Tap play to instantly verify video print, multi-audio language tracks, and dubbing — or paste the direct link into IDM / 1DM for max speed.',
      badge: '100% Resumable',
    },
  ];

  return (
    <section id="problem-solution" className="py-28 relative bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block font-semibold">
              The Problem & Our Solution
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              Why We Built FlashFile
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              Anyone who downloads media on Telegram knows the frustration of slow speeds, failed downloads, and wrong prints. Here is how FlashFile fixes it for good.
            </p>
          </div>
        </ScrollReveal>

        {/* Side-by-Side Comparison: Telegram vs FlashFile */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-24">
          {/* Telegram App Problems */}
          <ScrollReveal delay={150} direction="left">
            <div className="glass-panel rounded-3xl p-8 sm:p-10 border-rose-500/20 bg-rose-950/10 h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                    <XCircle className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-serif text-xl sm:text-2xl font-medium text-white">Downloading Inside Telegram</h3>
                    <span className="text-xs font-mono text-rose-400">Slow, fragile & frustrating</span>
                  </div>
                </div>

                <ul className="space-y-4 text-sm text-slate-300 font-sans">
                  <li className="flex items-start gap-3">
                    <span className="text-rose-400 font-bold mt-0.5">✕</span>
                    <div>
                      <strong className="text-white block font-medium">Severely Throttled Download Speeds</strong>
                      <span className="text-slate-400 text-xs">Single-thread downloads capped by the app, taking hours to download a standard 2GB movie.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-rose-400 font-bold mt-0.5">✕</span>
                    <div>
                      <strong className="text-white block font-medium">App Close / Chat Switch Aborts</strong>
                      <span className="text-slate-400 text-xs">Closing Telegram, switching chats, or locking your screen often silently halts the download.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-rose-400 font-bold mt-0.5">✕</span>
                    <div>
                      <strong className="text-white block font-medium">Download Stuck at 50% or 90%</strong>
                      <span className="text-slate-400 text-xs">Any network glitch corrupts the file cache, forcing you to delete and restart from 0%.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-rose-400 font-bold mt-0.5">✕</span>
                    <div>
                      <strong className="text-white block font-medium">Blind 3GB Downloads</strong>
                      <span className="text-slate-400 text-xs">No way to check if the movie has the right voice dubbing, correct print, or synced audio until it finishes.</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </ScrollReveal>

          {/* FlashFile Solution */}
          <ScrollReveal delay={250} direction="right">
            <div className="glass-panel-glow rounded-3xl p-8 sm:p-10 border-emerald-500/20 bg-emerald-950/10 h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-serif text-xl sm:text-2xl font-medium text-white">With FlashFile Bot</h3>
                    <span className="text-xs font-mono text-emerald-400">Fast, resumable & streamable</span>
                  </div>
                </div>

                <ul className="space-y-4 text-sm text-slate-300 font-sans">
                  <li className="flex items-start gap-3">
                    <span className="text-emerald-400 font-bold mt-0.5">✓</span>
                    <div>
                      <strong className="text-white block font-medium">Direct HTTP Multi-Threaded Links</strong>
                      <span className="text-slate-400 text-xs">Paste links into IDM, 1DM, or ADM to download with parallel connections at your full ISP speed.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-emerald-400 font-bold mt-0.5">✓</span>
                    <div>
                      <strong className="text-white block font-medium">Complete Background Independence</strong>
                      <span className="text-slate-400 text-xs">Close Telegram completely, turn off your screen — your download keeps running in your browser or download app.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-emerald-400 font-bold mt-0.5">✓</span>
                    <div>
                      <strong className="text-white block font-medium">100% Resumable (HTTP 206 Byte-Range)</strong>
                      <span className="text-slate-400 text-xs">Pause, disconnect, reconnect, or restart anytime. Your download picks up right where it left off.</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-emerald-400 font-bold mt-0.5">✓</span>
                    <div>
                      <strong className="text-white block font-medium">Stream to Verify Voice, Audio & Print</strong>
                      <span className="text-slate-400 text-xs">Instantly preview the movie in 5 seconds to confirm audio clarity, Malayalam/Tamil dubbing, and video quality before downloading.</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </ScrollReveal>
        </div>

        {/* 3-Step Simple Workflow */}
        <div id="how-it-works" className="pt-10">
          <ScrollReveal delay={50} direction="up">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs uppercase font-mono tracking-widest text-ff-signal mb-2 block font-semibold">
                Simple 3-Step Process
              </span>
              <h3 className="font-serif text-2xl sm:text-4xl font-normal text-white">
                From Telegram File to Direct Stream in Seconds
              </h3>
            </div>
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {steps.map((item, idx) => (
              <ScrollReveal key={item.step} delay={150 * (idx + 1)} direction="up">
                <div className="glass-panel rounded-2xl p-8 relative flex flex-col justify-between hover:border-ff-accent/40 hover:shadow-2xl hover:shadow-ff-accent/10 transition-all duration-300 group hover:-translate-y-1 h-full">
                  <div>
                    <div className="flex items-center justify-between mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/10 flex items-center justify-center shadow-inner group-hover:scale-110 group-hover:border-ff-accent/50 transition-all duration-300">
                        {item.icon}
                      </div>
                      <span className="font-mono text-4xl font-black text-white/10 group-hover:text-ff-accent/30 transition-colors">
                        {item.step}
                      </span>
                    </div>

                    <h4 className="font-serif font-medium text-2xl text-white mb-3">
                      {item.title}
                    </h4>

                    <p className="text-sm text-ff-text-secondary leading-relaxed mb-6 font-normal">
                      {item.description}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                    <span className="text-xs font-mono font-medium text-ff-text-muted">
                      {item.badge}
                    </span>
                    <span className="w-2 h-2 rounded-full bg-ff-accent/30 group-hover:bg-ff-accent transition-colors shadow-sm" />
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
