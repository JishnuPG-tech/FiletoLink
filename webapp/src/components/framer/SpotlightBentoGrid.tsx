import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  DownloadCloud,
  Film,
  RotateCcw,
  Volume2,
  HardDrive,
  CheckCircle2,
  Play,
} from 'lucide-react';

interface BentoCardProps {
  title: string;
  tagline: string;
  description: string;
  icon: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  badge?: string;
}

const SpotlightCard: React.FC<BentoCardProps> = ({
  title,
  tagline,
  description,
  icon,
  children,
  className = '',
  badge,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`relative rounded-3xl bg-[#080A10] border border-white/[0.08] p-7 overflow-hidden transition-all duration-300 group ${className}`}
    >
      {/* Mouse-following Radial Spotlight Border */}
      <div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: isHovered
            ? `radial-gradient(450px circle at ${position.x}px ${position.y}px, rgba(244, 63, 94, 0.22), transparent 40%)`
            : '',
        }}
      />

      {/* Mouse-following Ambient Inner Light */}
      <div
        className="pointer-events-none absolute inset-0 rounded-3xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: isHovered
            ? `radial-gradient(350px circle at ${position.x}px ${position.y}px, rgba(56, 189, 248, 0.06), transparent 60%)`
            : '',
        }}
      />

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center group-hover:border-rose-500/30 transition-colors">
            {icon}
          </div>
          {badge && (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-wider bg-rose-500/15 border border-rose-500/25 text-rose-300 font-semibold uppercase">
              {badge}
            </span>
          )}
        </div>

        <div className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider mb-1">
          {tagline}
        </div>
        <h3 className="text-xl font-semibold text-white tracking-tight mb-2 group-hover:text-rose-400 transition-colors">
          {title}
        </h3>
        <p className="text-xs text-zinc-400 leading-relaxed mb-6">
          {description}
        </p>

        {children && <div className="mt-auto">{children}</div>}
      </div>
    </div>
  );
};

export const SpotlightBentoGrid: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
      {/* Card 1: 16-Thread Aiohttp ByteStreamer (Large 2-column card) */}
      <SpotlightCard
        className="md:col-span-2"
        badge="CORE ENGINE"
        icon={<DownloadCloud className="w-5 h-5 text-rose-500" />}
        tagline="Aiohttp ByteStreamer Chunk Engine"
        title="Parallel Multi-Part Acceleration"
        description="Splits large video and archive files into 16 concurrent HTTP byte streams. Connects multiple Pyrogram clients to distinct Telegram DCs simultaneously, beating bandwidth caps."
      >
        <div className="rounded-xl bg-[#0C0E17] border border-white/[0.06] p-4 font-mono text-xs">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span>CHUNKS: 16/16 ACTIVE</span>
            <span className="text-rose-400 font-semibold">124.6 MB/s</span>
          </div>
          <div className="grid grid-cols-8 gap-1.5 mb-3">
            {Array.from({ length: 16 }).map((_, i) => (
              <motion.div
                key={i}
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.08,
                }}
                className="h-2 rounded-sm bg-gradient-to-r from-rose-500 to-sky-400"
              />
            ))}
          </div>
          <div className="text-[11px] text-zinc-500 flex items-center justify-between">
            <span>Range: bytes=0-104857600/6871947673</span>
            <span className="text-emerald-400">HTTP 206 Partial</span>
          </div>
        </div>
      </SpotlightCard>

      {/* Card 2: In-Browser Cinema */}
      <SpotlightCard
        badge="INSTANT PLAY"
        icon={<Film className="w-5 h-5 text-sky-400" />}
        tagline="Web Cinema Player"
        title="Zero-Wait 4K Streaming"
        description="Stream heavy MKV files directly in browser or VLC with instant scrubbing without waiting for gigabytes to download."
      >
        <div className="rounded-xl bg-[#0C0E17] border border-white/[0.06] p-3 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/20 flex items-center justify-center text-sky-400">
            <Play className="w-4 h-4 fill-sky-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-white truncate">Oppenheimer.4K.IMAX.mkv</div>
            <div className="text-[10px] text-zinc-500 font-mono">0.0s Seek Latency</div>
          </div>
          <span className="text-xs font-mono text-sky-400 font-semibold">4K HDR</span>
        </div>
      </SpotlightCard>

      {/* Card 3: 100% Resume Guarantee */}
      <SpotlightCard
        badge="BULLETPROOF"
        icon={<RotateCcw className="w-5 h-5 text-emerald-400" />}
        tagline="Network Disconnect Shield"
        title="100% Resumable Links"
        description="Never lose a 3GB download again because your phone screen timed out or Telegram closed. Resumes down to the exact byte."
      >
        <div className="space-y-2">
          {['IDM & 1DM Multi-Thread', 'Aria2 & Wget Support', 'Zero Corrupted Chunks'].map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-zinc-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </SpotlightCard>

      {/* Card 4: Audio & Print Check */}
      <SpotlightCard
        badge="AUDIO CHECK"
        icon={<Volume2 className="w-5 h-5 text-purple-400" />}
        tagline="Sample Inspector"
        title="Audio & Subtitle Verify"
        description="Quickly verify multi-language audio tracks, FLAC bitrates, and embedded subtitles before burning data."
      >
        <div className="rounded-xl bg-[#0C0E17] border border-white/[0.06] p-3">
          <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 mb-2">
            <span>FLAC 24-Bit / 96kHz</span>
            <span className="text-purple-400">Dolby Atmos</span>
          </div>
          <div className="flex items-end gap-1 h-6">
            {[40, 75, 55, 90, 65, 80, 45, 95, 70, 85, 50, 65, 90, 60].map((h, i) => (
              <div
                key={i}
                className="flex-1 bg-purple-500/60 rounded-t-sm"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>
      </SpotlightCard>

      {/* Card 5: Zero Local Storage */}
      <SpotlightCard
        badge="SAVE STORAGE"
        icon={<HardDrive className="w-5 h-5 text-amber-400" />}
        tagline="Zero Phone Bloat"
        title="0 Phone Storage Consumed"
        description="Telegram caches gigabytes of video into your phone's internal memory. FlashFile streams directly into RAM without cluttering your disk."
      >
        <div className="rounded-xl bg-[#0C0E17] border border-white/[0.06] p-3">
          <div className="flex justify-between text-[11px] font-mono mb-1">
            <span className="text-zinc-400">Telegram Cache: 16.4 GB</span>
            <span className="text-rose-400 font-semibold">FlashFile: 0.0 MB</span>
          </div>
          <div className="w-full h-2 rounded-full bg-white/[0.06] overflow-hidden">
            <div className="h-full bg-emerald-400 rounded-full" style={{ width: '2%' }} />
          </div>
        </div>
      </SpotlightCard>
    </div>
  );
};

export default SpotlightBentoGrid;
