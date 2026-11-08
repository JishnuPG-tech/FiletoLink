import React from 'react';
import { MessageSquare, Network, PlaySquare } from 'lucide-react';
import { ScrollReveal } from '../common/ScrollReveal';

export const WorkflowSection: React.FC = () => {
  const steps = [
    {
      step: '01',
      icon: <MessageSquare className="w-6 h-6 text-ff-accent" />,
      title: 'Send File to Telegram Bot',
      description: 'Forward any video, audio, or document up to 4 GB directly to FlashFile bot. The bot registers the media reference in milliseconds.',
      tag: 'Zero Upload Wait',
    },
    {
      step: '02',
      icon: <Network className="w-6 h-6 text-ff-signal" />,
      title: '6-Worker Load Balancing',
      description: 'Your file is indexed with a secure canonical hash. When requested, streaming byte-ranges are balanced across 6 MTProto worker clients.',
      tag: 'FloodWait Immunity',
    },
    {
      step: '03',
      icon: <PlaySquare className="w-6 h-6 text-emerald-400" />,
      title: 'Direct Stream or 1-Tap Play',
      description: 'Watch instantly in the web cinema player or tap one button to launch VLC Mobile, MX Player, or Desktop PotPlayer via M3U playlist.',
      tag: 'Full Hardware Decode',
    },
  ];

  return (
    <section id="how-it-works" className="py-28 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block font-semibold">
              End-To-End Architecture
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              How FlashFile Works
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              No cloud storage intermediaries. Raw Telegram byte chunks delivered directly to your device via streaming HTTP 206 pipelines.
            </p>
          </div>
        </ScrollReveal>

        {/* Steps Grid */}
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

                  <h3 className="font-serif font-medium text-2xl text-white mb-3">
                    {item.title}
                  </h3>

                  <p className="text-sm text-ff-text-secondary leading-relaxed mb-6 font-normal">
                    {item.description}
                  </p>
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-ff-text-muted">
                    {item.tag}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-ff-accent/30 group-hover:bg-ff-accent transition-colors shadow-sm" />
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
};
