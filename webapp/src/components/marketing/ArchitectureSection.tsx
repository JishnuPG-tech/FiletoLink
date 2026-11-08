import React from 'react';
import { Server, Cpu, Monitor, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { ScrollReveal } from '../common/ScrollReveal';

export const ArchitectureSection: React.FC = () => {
  return (
    <section id="architecture" className="py-28 relative bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="max-w-3xl mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block font-semibold">
              High-Speed Architecture
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              Why FlashFile is so fast.
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              Standard Telegram apps throttle single-connection downloads. FlashFile uses a distributed 6-worker MTProto pool to pull media chunks in parallel and stream them straight to your browser or download manager.
            </p>
          </div>
        </ScrollReveal>

        {/* Diagram Flow */}
        <ScrollReveal delay={150} direction="up">
          <div className="glass-panel rounded-3xl p-8 md:p-12 mb-12 hover:border-white/20 transition-all duration-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 items-center text-center">
              {/* Node 1 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mb-4 shadow-lg shadow-sky-500/10">
                  <Server className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">Telegram DCs</h4>
                <p className="text-xs text-ff-text-secondary">Official global media & file servers</p>
              </div>

              {/* Node 2 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-ff-accent/10 border border-ff-accent/30 text-ff-accent flex items-center justify-center mb-4 shadow-lg shadow-ff-accent/10">
                  <Cpu className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">6x Worker Pool</h4>
                <p className="text-xs text-ff-text-secondary">Parallel Pyrogram clients beating throttles</p>
              </div>

              {/* Node 3 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/10">
                  <Zap className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">Aiohttp ByteStreamer</h4>
                <p className="text-xs text-ff-text-secondary">HTTP 206 chunk aggregator & proxy</p>
              </div>

              {/* Node 4 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/10">
                  <Monitor className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">Your Device</h4>
                <p className="text-xs text-ff-text-secondary">Web Cinema, IDM, 1DM, VLC or MX</p>
              </div>
            </div>
          </div>
        </ScrollReveal>

        {/* Playback & Verification Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <ScrollReveal delay={200} direction="left">
            <div className="glass-panel rounded-2xl p-8 h-full">
              <div className="flex items-center gap-3.5 mb-5">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                <h3 className="font-serif font-medium text-2xl text-white">Instant Audio & Print Preview</h3>
              </div>
              <p className="text-sm text-ff-text-secondary mb-6 leading-relaxed">
                Stream right in your browser or 1-tap mobile player to verify everything before saving:
              </p>
              <ul className="space-y-3 font-mono text-xs text-ff-text-secondary">
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Audio Language Check (Malayalam, Tamil, Telugu, Hindi, English)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Video Print Quality Check (1080p HQ HDRip vs low-res cam print)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Subtitle Sync & Audio Dubbing Clarity</span>
                </li>
              </ul>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={300} direction="right">
            <div className="glass-panel rounded-2xl p-8 h-full">
              <div className="flex items-center gap-3.5 mb-5">
                <ShieldCheck className="w-6 h-6 text-ff-signal" />
                <h3 className="font-serif font-medium text-2xl text-white">Download Manager Integration</h3>
              </div>
              <p className="text-sm text-ff-text-secondary mb-6 leading-relaxed">
                Every generated link is a standard HTTP URL compatible with all modern download tools:
              </p>
              <ul className="space-y-3 font-mono text-xs text-ff-text-secondary">
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>1DM & ADM (Android) — Full multi-threaded chunking</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>Internet Download Manager (IDM) on Windows / Mac</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>VLC Mobile, MX Player & PotPlayer M3U Playback</span>
                </li>
              </ul>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
};
