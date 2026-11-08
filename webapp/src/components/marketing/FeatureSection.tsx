import React from 'react';
import { Film, Zap, RefreshCw, HardDrive, Smartphone, FileArchive } from 'lucide-react';

export const FeatureSection: React.FC = () => {
  const benefits = [
    {
      icon: <Film className="w-5 h-5 text-[#D97757]" />,
      title: 'Stream 4K Movies Instantly',
      badge: 'Zero Waiting',
      description: 'Tap play to start watching immediately in VLC, MX Player, or your web browser. No need to wait for 3GB files to finish downloading first.',
    },
    {
      icon: <Zap className="w-5 h-5 text-[#D97757]" />,
      title: 'Maximum Download Speed',
      badge: 'Full Bandwidth',
      description: 'Downloads your file through multiple parallel connections at the same time, using 100% of your Wi-Fi, 5G, or fiber internet speed.',
    },
    {
      icon: <RefreshCw className="w-5 h-5 text-[#D97757]" />,
      title: 'Never Loses Your Progress',
      badge: '100% Resumable',
      description: 'If your internet connection drops or your phone runs out of battery, your download picks right back up where it paused without starting over.',
    },
    {
      icon: <HardDrive className="w-5 h-5 text-[#D97757]" />,
      title: 'Zero Storage Wasted on Phone',
      badge: 'Storage Saver',
      description: 'Avoid Telegram caching gigabytes of temporary video files into your phone memory. Stream smoothly directly from the cloud.',
    },
    {
      icon: <Smartphone className="w-5 h-5 text-[#D97757]" />,
      title: 'Works on Phones, PCs & Smart TVs',
      badge: 'Universal',
      description: 'Compatible with Android, iPhone, Windows, Mac, iPad, and Smart TVs. Use your favorite video player or download manager.',
    },
    {
      icon: <FileArchive className="w-5 h-5 text-[#D97757]" />,
      title: 'Large Files Up to 4 GB',
      badge: 'All Media',
      description: 'Supports full-length 4K movies, season packs, high-resolution FLAC audio albums, software archives, and PC game files.',
    },
  ];

  return (
    <section id="benefits" className="py-24 bg-black border-t border-white/[0.08]">
      <div className="max-w-5xl mx-auto px-6">
        <div className="mb-16">
          <span className="font-mono text-xs uppercase tracking-widest text-[#D97757] font-medium block mb-3">
            Core Features
          </span>
          <h2 className="text-3xl sm:text-5xl font-normal text-white font-serif tracking-tight mb-4">
            Everything You Need to Enjoy Your Media
          </h2>
          <p className="text-zinc-400 text-sm sm:text-base max-w-2xl leading-relaxed">
            Designed for everyday movie lovers, binge-watchers, and power downloaders.
          </p>
        </div>

        {/* 6 Curved Benefit Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {benefits.map((item, idx) => (
            <div
              key={idx}
              className="p-7 rounded-3xl border border-white/[0.08] bg-[#0A0A0A] hover:border-[#D97757]/30 transition-all flex flex-col justify-between hover:scale-[1.01]"
            >
              <div>
                <div className="flex items-center justify-between mb-5">
                  <div className="w-10 h-10 rounded-2xl bg-[#D97757]/10 border border-[#D97757]/20 flex items-center justify-center">
                    {item.icon}
                  </div>
                  <span className="text-[10px] font-sans font-semibold px-3 py-1 rounded-full bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white mb-2">
                  {item.title}
                </h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeatureSection;
