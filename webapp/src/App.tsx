import React from 'react';
import { SpiritBackground } from './components/canvas/SpiritBackground';
import { SiteHeader } from './components/layout/SiteHeader';
import { HeroSection } from './components/marketing/HeroSection';
import { WorkflowSection } from './components/marketing/WorkflowSection';
import { FeatureSection } from './components/marketing/FeatureSection';
import { ArchitectureSection } from './components/marketing/ArchitectureSection';
import { FaqSection } from './components/marketing/FaqSection';
import { FinalCtaSection } from './components/marketing/FinalCtaSection';
import { SiteFooter } from './components/layout/SiteFooter';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#08090D] text-ff-text relative selection:bg-ff-accent/20 selection:text-ff-accent overflow-x-hidden">
      {/* Exact The Spirit (particle-love.com) 3D Particle WebGL Engine Background */}
      <SpiritBackground />

      {/* Navigation Header */}
      <SiteHeader />

      {/* Main Content with Scrollable Reveal Sections */}
      <main className="relative z-10 flex-1">
        <HeroSection />
        <WorkflowSection />
        <FeatureSection />
        <ArchitectureSection />
        <FaqSection />
        <FinalCtaSection />
      </main>

      {/* Footer */}
      <SiteFooter />
    </div>
  );
};
