import React, { useState } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import confetti from 'canvas-confetti';
import { Zap, CheckCircle2, Scissors } from 'lucide-react';

export interface TearTicketProps {
  edition?: string;
  title?: string;
  subtitle?: string;
  code?: string;
  className?: string;
}

/**
 * TearTicket
 * Ported from Framer: https://framer.com/m/TearTicket-LlpAvl.js@zoMGqZbPZlw7fRB5m1mO
 * Interactive tear-away VIP pass with perforated edge tearing physics,
 * sound synthesis, confetti blast, and secret access token reveal.
 */
export const TearTicket: React.FC<TearTicketProps> = ({
  edition = 'NO. 0081',
  title = 'FLASHFILE UNLIMITED VIP PASS',
  subtitle = '16-Thread Multi-Part Acceleration & Direct Cinema Streaming',
  code = '/stream --threads=16 --buffer=ram',
  className = '',
}) => {
  const [isTorn, setIsTorn] = useState(false);
  const y = useMotionValue(0);
  const rotate = useTransform(y, [0, 150], [0, 12]);
  const opacity = useTransform(y, [0, 140, 200], [1, 0.8, 0]);

  // Audio synthesis for procedural paper tear sound
  const playTearSound = () => {
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const bufferSize = ctx.sampleRate * 0.18;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);

      for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.3));
      }

      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.value = 1800;

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.18);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      noise.start();
    } catch {
      // AudioContext not allowed without gesture
    }
  };

  const triggerTear = () => {
    if (isTorn) return;
    setIsTorn(true);
    playTearSound();

    confetti({
      particleCount: 55,
      spread: 60,
      origin: { y: 0.65 },
      colors: ['#F43F5E', '#38BDF8', '#FFFFFF', '#A855F7'],
    });
  };

  return (
    <div className={`relative max-w-xl mx-auto ${className}`}>
      <div className="relative rounded-2xl bg-gradient-to-b from-[#10121A] to-[#0A0C12] border border-white/[0.09] p-6 shadow-2xl overflow-hidden">
        {/* Holographic Watermark */}
        <div className="absolute right-4 -top-8 text-white/[0.03] font-mono text-8xl font-black select-none pointer-events-none">
          206
        </div>

        {/* Ticket Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center">
              <Zap className="w-4 h-4 text-rose-500 fill-rose-500" />
            </div>
            <div>
              <div className="text-xs font-semibold tracking-wider text-white uppercase">
                FlashFile VIP Pass
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">{edition}</div>
            </div>
          </div>

          <div className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-zinc-400">
            {isTorn ? 'PASS ACTIVATED' : 'TEAR STUB TO ACTIVATE'}
          </div>
        </div>

        {/* Body Details */}
        <div className="mb-6">
          <h3 className="text-lg font-bold text-white tracking-tight mb-1">
            {title}
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">{subtitle}</p>
        </div>

        {/* Perforated Tear Line */}
        <div className="relative my-4 flex items-center justify-between">
          <div className="w-4 h-4 rounded-full bg-[#04070E] -ml-8 border-r border-white/[0.09]" />
          <div className="flex-1 border-b-2 border-dashed border-white/[0.12] mx-2 relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#0E1017] px-2 text-[9px] font-mono text-zinc-500 flex items-center gap-1">
              <Scissors className="w-2.5 h-2.5" /> TEAR ALONG PERFORATION
            </span>
          </div>
          <div className="w-4 h-4 rounded-full bg-[#04070E] -mr-8 border-l border-white/[0.09]" />
        </div>

        {/* Ticket Stub (Tearable or Revealed) */}
        {!isTorn ? (
          <motion.div
            style={{ y, rotate, opacity }}
            drag="y"
            dragConstraints={{ top: 0, bottom: 160 }}
            dragElastic={0.4}
            onDragEnd={(_, info) => {
              if (info.offset.y > 70 || info.velocity.y > 350) {
                triggerTear();
              }
            }}
            className="rounded-xl bg-white/[0.04] hover:bg-white/[0.06] border border-white/[0.08] p-4 flex items-center justify-between cursor-grab active:cursor-grabbing transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full border border-dashed border-rose-400 animate-spin" />
              <div>
                <div className="text-xs font-medium text-white">
                  Pull Down to Tear Stub
                </div>
                <div className="text-[10px] text-zinc-500">
                  Unlocks 16-stream parallel acceleration
                </div>
              </div>
            </div>

            <button
              onClick={triggerTear}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-medium transition-all"
            >
              Click to Tear
            </button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 flex flex-col sm:flex-row items-center justify-between gap-3"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <div className="text-xs font-semibold text-emerald-300">
                  VIP Mode Activated!
                </div>
                <div className="font-mono text-[11px] text-zinc-400 select-all">
                  {code}
                </div>
              </div>
            </div>

            <a
              href="https://t.me/FiletoLinkBot"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg bg-emerald-500 text-black text-xs font-semibold hover:bg-emerald-400 transition-colors"
            >
              Send to Bot
            </a>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TearTicket;
