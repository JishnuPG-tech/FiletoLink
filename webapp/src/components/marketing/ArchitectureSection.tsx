import React from 'react';
import { Server, Cpu, Smartphone, Monitor, Info, CheckCircle2 } from 'lucide-react';

export const ArchitectureSection: React.FC = () => {
  return (
    <section id="architecture" className="py-24 bg-ff-bg-raised/70 border-t border-ff-border relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-16">
          <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block">
            System Topology
          </span>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight mb-4">
            Under the hood.
          </h2>
          <p className="font-sans text-ff-text-secondary text-base sm:text-lg">
            A look at how FlashFile proxies chunks directly between Telegram's MTProto DC infrastructure and your browser.
          </p>
        </div>

        {/* Diagram Flow */}
        <div className="glass-panel rounded-2xl p-8 md:p-12 mb-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-center text-center">
            {/* Node 1 */}
            <div className="bg-ff-surface border border-ff-border rounded-xl p-6 flex flex-col items-center">
              <div className="w-12 h-12 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mb-3">
                <Server className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-white mb-1">Telegram DCs</h4>
              <p className="text-xs text-ff-text-secondary">Global document & video file stores</p>
            </div>

            {/* Node 2 */}
            <div className="bg-ff-surface border border-ff-border rounded-xl p-6 flex flex-col items-center">
              <div className="w-12 h-12 rounded-lg bg-ff-accent/10 border border-ff-accent/20 text-ff-accent flex items-center justify-center mb-3">
                <Cpu className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-white mb-1">6x Worker Pool</h4>
              <p className="text-xs text-ff-text-secondary">Pyrogram sessions balancing chunk load</p>
            </div>

            {/* Node 3 */}
            <div className="bg-ff-surface border border-ff-border rounded-xl p-6 flex flex-col items-center">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3">
                <Server className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-white mb-1">Aiohttp ByteStreamer</h4>
              <p className="text-xs text-ff-text-secondary">HTTP 206 partial content proxy</p>
            </div>

            {/* Node 4 */}
            <div className="bg-ff-surface border border-ff-border rounded-xl p-6 flex flex-col items-center">
              <div className="w-12 h-12 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-3">
                <Monitor className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-white mb-1">Client Player</h4>
              <p className="text-xs text-ff-text-secondary">Browser, VLC Mobile, or PotPlayer</p>
            </div>
          </div>
        </div>

        {/* Compatibility Matrix & Real Limitations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-ff-surface border border-ff-border rounded-2xl p-7">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="font-display font-semibold text-lg text-white">Full In-Browser Compatibility</h3>
            </div>
            <p className="text-sm text-ff-text-secondary mb-4">
              Standard web containers stream natively at full 60 FPS without external apps:
            </p>
            <ul className="space-y-2 text-xs font-mono text-ff-text-muted">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>MP4 (H.264 / AVC + AAC / MP3)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>WebM (VP8 / VP9 / AV1 + Opus)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Audio (MP3, OGG, WAV, FLAC, AAC)</span>
              </li>
            </ul>
          </div>

          <div className="bg-ff-surface border border-ff-border rounded-2xl p-7">
            <div className="flex items-center gap-3 mb-4">
              <Info className="w-5 h-5 text-ff-signal" />
              <h3 className="font-display font-semibold text-lg text-white">MKV / Dolby AC-3 Fallback</h3>
            </div>
            <p className="text-sm text-ff-text-secondary mb-4">
              Browsers lack proprietary Dolby AC-3 decoders. FlashFile provides instant 1-tap launchers:
            </p>
            <ul className="space-y-2 text-xs font-mono text-ff-text-muted">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                <span>Android: 1-Tap VLC & MX Player Intent links</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                <span>iOS: Direct vlc:// and infuse:// deep links</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-ff-signal" />
                <span>Desktop: Instant M3U playlist launch for VLC / PotPlayer</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};
