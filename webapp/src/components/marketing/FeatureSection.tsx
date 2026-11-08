import React from 'react';
import { VERIFIED_CAPABILITIES } from '../../content/features';

export const FeatureSection: React.FC = () => {
  return (
    <section id="features" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-16">
          <span className="text-xs uppercase font-mono tracking-widest text-ff-signal mb-3 block">
            Verified Production Features
          </span>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight mb-4">
            Engineered for high throughput.
          </h2>
          <p className="font-sans text-ff-text-secondary text-base sm:text-lg">
            Every capability listed here is substantiated by the production codebase and active Hugging Face / Python microservices.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {VERIFIED_CAPABILITIES.map((feat) => (
            <div
              key={feat.id}
              className="bg-ff-surface/60 border border-ff-border rounded-2xl p-7 hover:border-ff-border-strong hover:bg-ff-surface transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-medium px-2.5 py-1 rounded bg-ff-bg border border-ff-border text-ff-signal">
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

                <h3 className="font-display font-semibold text-xl text-white mb-2.5">
                  {feat.title}
                </h3>

                <p className="text-sm text-ff-text-secondary leading-relaxed font-normal">
                  {feat.description}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-ff-border/40 flex items-center justify-between">
                <span className="text-xs font-mono text-ff-text-muted">Status: Active</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
