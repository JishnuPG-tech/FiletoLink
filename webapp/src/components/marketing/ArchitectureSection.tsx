import React from 'react';
import { Server, Cpu, Monitor, CheckCircle2, ShieldCheck } from 'lucide-react';
import { ScrollReveal } from '../common/ScrollReveal';

export const ArchitectureSection: React.FC = () => {
  return (
    <section id="architecture" className="py-28 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="max-w-3xl mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block font-semibold">
              System Topology & Pipeline
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              Under the hood.
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              A breakdown of how FlashFile proxies chunks directly between Telegram's MTProto global DC infrastructure and your browser.
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
                <p className="text-xs text-ff-text-secondary">Global document & video file stores</p>
              </div>

              {/* Node 2 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-ff-accent/10 border border-ff-accent/30 text-ff-accent flex items-center justify-center mb-4 shadow-lg shadow-ff-accent/10">
                  <Cpu className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">6x Worker Pool</h4>
                <p className="text-xs text-ff-text-secondary">Pyrogram sessions balancing chunk load</p>
              </div>

              {/* Node 3 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/10">
                  <Server className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">Aiohttp ByteStreamer</h4>
                <p className="text-xs text-ff-text-secondary">HTTP 206 partial content proxy</p>
              </div>

              {/* Node 4 */}
              <div className="glass-panel rounded-2xl p-6 flex flex-col items-center hover:scale-105 transition-transform duration-300">
                <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/10">
                  <Monitor className="w-7 h-7" />
                </div>
                <h4 className="font-serif text-lg font-medium text-white mb-1.5">Client Player</h4>
                <p className="text-xs text-ff-text-secondary">Web Cinema, VLC Mobile, or MX Player</p>
              </div>
            </div>
          </div>
        </ScrollReveal>

        {/* Compatibility Matrix & Codec Specifications */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <ScrollReveal delay={200} direction="left">
            <div className="glass-panel rounded-2xl p-8 h-full">
              <div className="flex items-center gap-3.5 mb-5">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                <h3 className="font-serif font-medium text-2xl text-white">Direct Web Playback</h3>
              </div>
              <p className="text-sm text-ff-text-secondary mb-6 leading-relaxed">
                Standard web containers stream natively at full 60 FPS in Chrome, Firefox, Safari, and Brave:
              </p>
              <ul className="space-y-3 font-mono text-xs text-ff-text-secondary">
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>MP4 (H.264 / AVC + AAC Audio) - 100% Native</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>WebM (VP8/VP9 + Opus Audio) - 100% Native</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>MP3, FLAC, WAV & OGG Lossless Audio</span>
                </li>
              </ul>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={300} direction="right">
            <div className="glass-panel rounded-2xl p-8 h-full">
              <div className="flex items-center gap-3.5 mb-5">
                <ShieldCheck className="w-6 h-6 text-ff-signal" />
                <h3 className="font-serif font-medium text-2xl text-white">MKV & Spatial Audio Fallback</h3>
              </div>
              <p className="text-sm text-ff-text-secondary mb-6 leading-relaxed">
                For heavy HEVC/H.265 video with Dolby AC-3 / EAC-3 / DTS 7.1 tracks, FlashFile auto-generates 1-tap external launcher links:
              </p>
              <ul className="space-y-3 font-mono text-xs text-ff-text-secondary">
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>VLC for Android / iOS intent (vlc://stream-url)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>MX Player / MX Player Pro mobile intent</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                  <span>1-Click M3U playlist file for Desktop PotPlayer & VLC</span>
                </li>
              </ul>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
};
