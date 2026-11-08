import React from 'react';
import { Server, Users, ArrowRight, Play } from 'lucide-react';

export const ArchitectureSection: React.FC = () => {
  const steps = [
    {
      step: 'Step 1',
      title: 'Telegram Cloud Server',
      description: 'Your movie or file is stored safely on Telegram cloud servers around the world.',
      icon: <Server className="w-5 h-5 text-[#D97757]" />,
    },
    {
      step: 'Step 2',
      title: 'FlashFile Fast Lane',
      description: 'FlashFile opens multiple fast connections to Telegram at once instead of just one.',
      icon: <Users className="w-5 h-5 text-[#D97757]" />,
    },
    {
      step: 'Step 3',
      title: 'Direct Link Delivery',
      description: 'You get a clean HTTP link that works with any player, browser, or download app.',
      icon: <ArrowRight className="w-5 h-5 text-[#D97757]" />,
    },
    {
      step: 'Step 4',
      title: 'Instant Play on Your Device',
      description: 'Watch in VLC or MX Player, or download at full speed using IDM or 1DM.',
      icon: <Play className="w-5 h-5 text-[#D97757]" />,
    },
  ];

  return (
    <section id="architecture" className="py-24 bg-black border-t border-white/[0.08]">
      <div className="max-w-5xl mx-auto px-6">
        <div className="mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-[#D97757] font-medium block mb-3">
            Under The Hood
          </span>
          <h2 className="text-3xl sm:text-5xl font-normal text-white font-serif tracking-tight mb-4">
            How FlashFile Delivers Maximum Speed
          </h2>
          <p className="text-zinc-400 text-sm sm:text-base max-w-2xl leading-relaxed">
            Unlike other downloaders, FlashFile doesn't re-upload or store your personal files on third-party disks. It streams data directly from Telegram straight to your screen.
          </p>
        </div>

        {/* 4 Curved Step Boxes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-14">
          {steps.map((node, idx) => (
            <div
              key={idx}
              className="p-6 rounded-3xl border border-white/[0.08] bg-[#0A0A0A] flex flex-col justify-between hover:border-[#D97757]/30 transition-all hover:scale-[1.01]"
            >
              <div>
                <div className="w-9 h-9 rounded-2xl bg-[#D97757]/10 flex items-center justify-center mb-4">
                  {node.icon}
                </div>
                <div className="font-mono text-xs text-[#D97757] font-bold mb-1">
                  {node.step}
                </div>
                <h4 className="text-sm font-semibold text-white mb-2">
                  {node.title}
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  {node.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Two Highlights (Generously Curved Cards) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-8 rounded-3xl border border-white/[0.08] bg-[#0A0A0A]">
            <span className="font-sans text-xs text-[#D97757] uppercase tracking-wider font-semibold block mb-2">
              Instant Quality Check
            </span>
            <h3 className="text-xl font-semibold text-white mb-3">
              Verify Movie Print & Audio First
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Never waste data on the wrong movie version again. Tap play on your stream link to check if it has the correct language audio (Malayalam, Tamil, Hindi, English), clear audio dubbing, and proper 1080p/4K HDR video print before downloading.
            </p>
          </div>

          <div className="p-8 rounded-3xl border border-white/[0.08] bg-[#0A0A0A]">
            <span className="font-sans text-xs text-[#D97757] uppercase tracking-wider font-semibold block mb-2">
              Private & Direct
            </span>
            <h3 className="text-xl font-semibold text-white mb-3">
              Zero Login & 100% Private
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              FlashFile never asks for your Telegram login, phone number, or password. All you do is forward a file to the bot. Your files stream directly through secure encrypted links that only you possess.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ArchitectureSection;
