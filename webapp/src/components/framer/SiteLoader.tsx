import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap } from 'lucide-react';

export interface SiteLoaderProps {
  onComplete?: () => void;
  brandName?: string;
  duration?: number; // Duration in milliseconds (default 1200ms)
}

/**
 * SiteLoader
 * Ported from Framer: https://framer.com/m/MinimalPreloader-cc1jlH.js@90xfSUueigFLBdzFT7LN
 * Minimalist luxury preloader featuring count-up physics, pulsing insignia, and split-curtain exit reveal.
 */
export const SiteLoader: React.FC<SiteLoaderProps> = ({
  onComplete,
  brandName = 'FlashFile',
  duration = 1100,
}) => {
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const startTime = performance.now();

    const updateCounter = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const rawProgress = Math.min(100, Math.floor((elapsed / duration) * 100));

      // Ease-out progress counter
      setProgress(rawProgress);

      if (elapsed < duration) {
        requestAnimationFrame(updateCounter);
      } else {
        setProgress(100);
        setTimeout(() => {
          setIsVisible(false);
          onComplete?.();
        }, 250);
      }
    };

    requestAnimationFrame(updateCounter);
  }, [duration, onComplete]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="site-loader"
          initial={{ opacity: 1 }}
          exit={{
            y: '-100%',
            transition: { duration: 0.65, ease: [0.76, 0, 0.24, 1] },
          }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#04070E] text-white overflow-hidden pointer-events-auto"
        >
          {/* Subtle background ambient pulse */}
          <div className="absolute inset-0 bg-gradient-to-b from-sky-500/[0.04] via-transparent to-rose-500/[0.04] pointer-events-none" />

          {/* Central Logo & Insignia */}
          <div className="relative z-10 flex flex-col items-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 via-rose-500 to-sky-400 p-[1px] shadow-2xl shadow-rose-500/20 mb-6 flex items-center justify-center"
            >
              <div className="w-full h-full rounded-2xl bg-[#08090D] flex items-center justify-center">
                <Zap className="w-8 h-8 text-white fill-white" />
              </div>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
              className="text-2xl font-semibold tracking-tight text-white mb-2"
            >
              {brandName}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.25 }}
              className="text-xs uppercase tracking-widest text-zinc-500 mb-8"
            >
              Telegram Stream Acceleration Engine
            </motion.p>

            {/* Precision Loading Progress Bar */}
            <div className="w-48 h-1 bg-white/[0.08] rounded-full overflow-hidden relative mb-4">
              <motion.div
                className="h-full bg-gradient-to-r from-rose-500 via-purple-500 to-sky-400 rounded-full"
                style={{ width: `${progress}%` }}
                transition={{ ease: 'linear' }}
              />
            </div>

            {/* Numeric Percentage Readout */}
            <div className="font-mono text-xs text-zinc-400 tabular-nums tracking-wider">
              {progress.toString().padStart(3, '0')}%
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SiteLoader;
