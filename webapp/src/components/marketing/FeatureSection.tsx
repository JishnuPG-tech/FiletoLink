import React from 'react';
import { VERIFIED_CAPABILITIES } from '../../content/features';
import { ScrollReveal } from '../common/ScrollReveal';

export const FeatureSection: React.FC = () => {
  return (
    <section id="features" className="py-28 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="max-w-3xl mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-signal mb-3 block font-semibold">
              Verified Production Capabilities
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              Engineered for uncompromising speed.
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              Every capability is backed by the real-time Pyrogram Telegram MTProto cluster, MongoDB indexing engine, and streaming HTTP 206 infrastructure.
            </p>
          </div>
        </ScrollReveal>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {VERIFIED_CAPABILITIES.map((feat, idx) => (
            <ScrollReveal key={feat.id} delay={100 * (idx % 3 + 1)} direction="up">
              <div className="glass-panel rounded-2xl p-7 hover:border-ff-accent/40 hover:shadow-xl hover:shadow-ff-accent/5 transition-all duration-300 flex flex-col justify-between h-full group hover:-translate-y-1">
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <span className="text-xs font-mono font-medium px-3 py-1 rounded-full bg-white/[0.04] border border-white/10 text-ff-signal">
                      {feat.badge}
                    </span>
                    {feat.metric && (
                      <div className="text-right">
                        <span className="font-mono text-base font-bold text-white block leading-none">
                          {feat.metric}
                        </span>
                        <span className="text-[10px] font-mono text-ff-text-muted">
                          {feat.metricLabel}
                        </span>
                      </div>
                    )}
                  </div>

                  <h3 className="font-serif font-medium text-xl text-white mb-3 group-hover:text-ff-accent transition-colors">
                    {feat.title}
                  </h3>

                  <p className="text-sm text-ff-text-secondary leading-relaxed font-normal">
                    {feat.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-xs font-mono text-ff-text-muted">Production Node: Operational</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
};
