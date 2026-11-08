import React from 'react';
import { motion } from 'framer-motion';
import { Zap, ShieldCheck, HardDrive, Gauge, Globe, Flame } from 'lucide-react';

export const VelocityMarquee: React.FC = () => {
  const items = [
    { icon: <Zap className="w-4 h-4 text-rose-500" />, text: '124 MB/s Multi-Thread Throughput' },
    { icon: <HardDrive className="w-4 h-4 text-sky-400" />, text: '0 MB Phone Storage Consumed' },
    { icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />, text: '100% Resumable HTTP 206 Chunking' },
    { icon: <Gauge className="w-4 h-4 text-amber-400" />, text: 'Instant 4K Video & Audio Seeking' },
    { icon: <Globe className="w-4 h-4 text-purple-400" />, text: '6x Global Telegram DC Parallel Workers' },
    { icon: <Flame className="w-4 h-4 text-rose-400" />, text: 'Bypasses Official Telegram Rate Limits' },
  ];

  return (
    <div className="relative w-full overflow-hidden py-4 border-y border-white/[0.06] bg-[#05070D]/70 backdrop-blur-md">
      {/* Edge gradient masks */}
      <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#04070E] to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#04070E] to-transparent z-10 pointer-events-none" />

      <motion.div
        animate={{ x: ['0%', '-50%'] }}
        transition={{ duration: 25, ease: 'linear', repeat: Infinity }}
        className="flex items-center gap-8 whitespace-nowrap will-change-transform"
      >
        {[...items, ...items, ...items, ...items].map((item, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-xs font-mono text-zinc-300"
          >
            {item.icon}
            <span>{item.text}</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
};

export default VelocityMarquee;
