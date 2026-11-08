import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, Printer, Sparkles } from 'lucide-react';

export interface CopierProps {
  label?: string;
  value: string;
  mark?: string;
  className?: string;
}

/**
 * Copier
 * Ported from Framer: https://framer.com/m/Copier-ARhUUy.js@9O0QWxGvNvlvWpkJ3Eka
 * Tactile Xerox copy machine component with animated laser scan beam,
 * rolling paper sheet output, audio synthesis, and clipboard copy.
 */
export const Copier: React.FC<CopierProps> = ({
  label = 'Stream Direct URL',
  value,
  mark = 'FLASHFILE·206 COPIER',
  className = '',
}) => {
  const [copied, setCopied] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // Play subtle web audio mechanical beep/click
  const playCopySound = () => {
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(580, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);

      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch {
      // AudioContext not available or blocked by autoplay
    }
  };

  const handleCopy = () => {
    if (isScanning) return;
    setIsScanning(true);
    playCopySound();

    navigator.clipboard.writeText(value);

    // Simulate scan pass
    setTimeout(() => {
      setIsScanning(false);
      setCopied(true);
      setTimeout(() => setCopied(false), 2400);
    }, 450);
  };

  return (
    <div
      className={`relative rounded-2xl bg-[#0B0D13] border border-white/[0.09] p-5 shadow-2xl overflow-hidden group select-none ${className}`}
    >
      {/* Laser Scan Beam Animation */}
      <AnimatePresence>
        {isScanning && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: '200%' }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: 'easeInOut' }}
            className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-sky-400/30 to-transparent pointer-events-none z-30 transform -skew-x-12"
          />
        )}
      </AnimatePresence>

      {/* Machine Header */}
      <div className="flex items-center justify-between mb-3 text-[11px] font-mono tracking-wider text-zinc-500 uppercase">
        <div className="flex items-center gap-1.5">
          <Printer className="w-3.5 h-3.5 text-rose-500" />
          <span>{mark}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>READY</span>
        </div>
      </div>

      {/* Tray & Paper Sheet */}
      <div className="relative rounded-xl bg-[#14161F] border border-white/[0.06] p-4 font-mono text-xs text-zinc-300 overflow-hidden mb-4 shadow-inner">
        <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1 font-sans">
          {label}
        </div>
        <div className="truncate text-white font-medium select-all py-1">
          {value}
        </div>

        {/* Paper texture subtle corner fold */}
        <div className="absolute top-0 right-0 w-4 h-4 bg-white/[0.04] border-l border-b border-white/[0.08]" />
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between gap-3">
        <div className="text-[11px] text-zinc-400 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>100% IDM / VLC Compatible</span>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={handleCopy}
          className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-all duration-200 ${
            copied
              ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-white text-zinc-950 hover:bg-zinc-100 shadow-md'
          }`}
        >
          {copied ? (
            <>
              <Check className="w-4 h-4" />
              <span>Copied Link!</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              <span>Copy Direct URL</span>
            </>
          )}
        </motion.button>
      </div>
    </div>
  );
};

export default Copier;
