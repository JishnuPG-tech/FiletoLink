import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { FAQS } from '../../content/faq';
import { ScrollReveal } from '../common/ScrollReveal';

export const FaqSection: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="py-28 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <ScrollReveal delay={50} direction="up">
          <div className="text-center mb-20">
            <span className="text-xs uppercase font-mono tracking-widest text-ff-accent mb-3 block font-semibold">
              Questions & Architecture Details
            </span>
            <h2 className="font-serif text-3xl sm:text-5xl md:text-6xl font-normal text-white tracking-tight mb-5">
              Frequently Asked Questions
            </h2>
            <p className="font-sans text-ff-text-secondary text-base sm:text-lg leading-relaxed">
              Everything you need to know about streaming speed, MTProto worker pools, and supported media formats.
            </p>
          </div>
        </ScrollReveal>

        {/* Accordion */}
        <div className="space-y-4">
          {FAQS.map((faq, index) => {
            const isOpen = openIndex === index;
            return (
              <ScrollReveal key={faq.question} delay={80 * (index + 1)} direction="up">
                <div className="glass-panel rounded-2xl overflow-hidden transition-all duration-300 hover:border-white/20">
                  <button
                    type="button"
                    onClick={() => toggle(index)}
                    className="w-full px-7 py-6 flex items-center justify-between text-left focus:outline-none"
                    aria-expanded={isOpen}
                  >
                    <span className="font-serif font-medium text-lg sm:text-xl text-white pr-4">
                      {faq.question}
                    </span>
                    <ChevronDown
                      className={`w-5 h-5 text-ff-text-secondary flex-shrink-0 transition-transform duration-300 ${
                        isOpen ? 'rotate-180 text-ff-accent' : ''
                      }`}
                    />
                  </button>

                  {isOpen && (
                    <div className="px-7 pb-6 pt-2 text-sm text-ff-text-secondary leading-relaxed border-t border-white/5 font-normal">
                      {faq.answer}
                    </div>
                  )}
                </div>
              </ScrollReveal>
            );
          })}
        </div>
      </div>
    </section>
  );
};
