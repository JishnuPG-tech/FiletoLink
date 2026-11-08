import React from 'react';
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
    <div className="min-h-screen flex flex-col bg-ff-bg text-ff-text relative selection:bg-ff-accent/20 selection:text-ff-accent">
      <SiteHeader />
      <main className="flex-1">
        <HeroSection />
        <WorkflowSection />
        <FeatureSection />
        <ArchitectureSection />
        <FaqSection />
        <FinalCtaSection />
      </main>
      <SiteFooter />
    </div>
  );
};
