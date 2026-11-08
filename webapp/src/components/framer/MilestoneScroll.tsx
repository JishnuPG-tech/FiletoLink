import React, { useRef } from 'react';
import { motion, useScroll, useSpring } from 'framer-motion';
import { Bot, Cpu, Network, Film } from 'lucide-react';

export interface Milestone {
  step: string;
  title: string;
  tagline: string;
  description: string;
  icon: React.ReactNode;
  specs: string[];
}

export interface MilestoneScrollProps {
  className?: string;
}

/**
 * MilestoneScroll
 * Ported from Framer: https://framer.com/m/MilestoneScroll-TvAMc9.js@kLeH8KcXfHpYAKSCeEM1
 * Interactive scroll-driven chapter timeline with glowing progress tracker.
 */
export const MilestoneScroll: React.FC<MilestoneScrollProps> = ({ className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start center', 'end center'],
  });

  const scaleY = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 20,
    restDelta: 0.001,
  });

  const milestones: Milestone[] = [
    {
      step: 'CHAPTER 01',
      title: 'Drop Any Telegram File or Channel Link',
      tagline: 'Instant Handshake in < 120ms',
      description:
        'Forward any video, audio, archive, or software file directly to the FlashFile Bot. No storage upload needed — FlashFile indexes the file ID directly from Telegram data centers.',
      icon: <Bot className="w-5 h-5 text-rose-500" />,
      specs: ['Up to 4.0 GB File Support', 'Private Channels & Public Posts', 'Zero Local Storage Consumption'],
    },
    {
      step: 'CHAPTER 02',
      title: '6x Pyrogram Parallel Worker Cluster',
      tagline: 'Multi-Client DC Routing',
      description:
        'Instead of a single throttled Telegram client, FlashFile spins up a cluster of 6 parallel MTProto workers across global Telegram DCs to eliminate speed bottlenecks.',
      icon: <Network className="w-5 h-5 text-sky-400" />,
      specs: ['Multi-DC Telegram Mesh', 'Automated FloodWait Balancing', '100 MB/s Aggregated Pipeline'],
    },
    {
      step: 'CHAPTER 03',
      title: 'Aiohttp ByteStreamer Synthesis',
      tagline: 'HTTP 206 Partial Content Proxy',
      description:
        'The streaming server splits the file into dynamic byte slices on-the-fly. It converts proprietary MTProto chunk streams into a standard, resumable HTTP 206 stream link.',
      icon: <Cpu className="w-5 h-5 text-purple-400" />,
      specs: ['100% IDM / 1DM Resumable', 'Instant Seeking & Range Headers', 'End-to-End SSL Encryption'],
    },
    {
      step: 'CHAPTER 04',
      title: 'Instant Cinema Playback & Max-Speed Download',
      tagline: 'Zero Phone Storage Needed',
      description:
        'Stream 4K MKV movies directly in Chrome, VLC, or MX Player without waiting for hours. Or copy the link into IDM / Aria2 for 16-thread maximum line-speed downloads.',
      icon: <Film className="w-5 h-5 text-emerald-400" />,
      specs: ['Multi-Audio & Subtitle Switching', 'Instant Bitrate & Audio Check', 'Zero Download Freezes'],
    },
  ];

  return (
    <div ref={containerRef} className={`relative max-w-4xl mx-auto py-12 ${className}`}>
      {/* Central Progress Line */}
      <div className="absolute left-6 md:left-1/2 top-0 bottom-0 w-[2px] bg-white/[0.08] -translate-x-1/2">
        <motion.div
          style={{ scaleY }}
          className="w-full bg-gradient-to-b from-rose-500 via-sky-400 to-purple-500 origin-top"
        />
      </div>

      {/* Milestone Cards */}
      <div className="space-y-16 relative z-10">
        {milestones.map((item, idx) => {
          const isEven = idx % 2 === 0;
          return (
            <div
              key={idx}
              className={`flex flex-col md:flex-row items-start gap-8 ${
                isEven ? 'md:flex-row-reverse' : ''
              }`}
            >
              {/* Card Content */}
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-80px' }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="w-full md:w-[calc(50%-3rem)] pl-14 md:pl-0"
              >
                <div className="rounded-2xl bg-[#090B11] border border-white/[0.08] p-6 shadow-xl hover:border-white/[0.15] transition-all duration-300 group">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono text-[10px] tracking-widest text-rose-500 font-semibold uppercase">
                      {item.step}
                    </span>
                    <span className="text-[11px] font-mono text-zinc-500">{item.tagline}</span>
                  </div>

                  <h4 className="text-base font-semibold text-white mb-2 group-hover:text-rose-400 transition-colors">
                    {item.title}
                  </h4>

                  <p className="text-xs text-zinc-400 leading-relaxed mb-4">
                    {item.description}
                  </p>

                  <div className="flex flex-wrap gap-1.5 pt-3 border-t border-white/[0.06]">
                    {item.specs.map((spec, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 rounded-md bg-white/[0.04] text-[10px] font-mono text-zinc-400"
                      >
                        ✓ {spec}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Node Center Dot */}
              <div className="absolute left-6 md:left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-[#08090D] border-2 border-white/[0.15] flex items-center justify-center shadow-lg shadow-black">
                {item.icon}
              </div>

              {/* Empty spacer for alternating balance */}
              <div className="hidden md:block w-[calc(50%-3rem)]" />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MilestoneScroll;
