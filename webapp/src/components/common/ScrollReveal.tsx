import React, { useEffect, useRef, useState } from 'react';

interface ScrollRevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number; // ms
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  threshold?: number;
  once?: boolean;
}

/**
 * ScrollReveal: High-performance IntersectionObserver wrapper for smooth scroll-driven reveals.
 * Automatically adds smooth blur-to-clear and translate transitions when entering the viewport.
 */
export const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  className = '',
  delay = 0,
  direction = 'up',
  threshold = 0.12,
  once = true,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const current = domRef.current;
    if (!current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            if (once) observer.unobserve(entry.target);
          } else if (!once) {
            setIsVisible(false);
          }
        });
      },
      {
        threshold,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    observer.observe(current);

    return () => {
      observer.disconnect();
    };
  }, [threshold, once]);

  const getDirectionClasses = () => {
    if (!isVisible) {
      switch (direction) {
        case 'up':
          return 'opacity-0 translate-y-8 blur-[3px] scale-[0.985]';
        case 'down':
          return 'opacity-0 -translate-y-8 blur-[3px] scale-[0.985]';
        case 'left':
          return 'opacity-0 translate-x-8 blur-[3px] scale-[0.985]';
        case 'right':
          return 'opacity-0 -translate-x-8 blur-[3px] scale-[0.985]';
        case 'none':
          return 'opacity-0 blur-[3px] scale-[0.985]';
      }
    }
    return 'opacity-100 translate-y-0 translate-x-0 blur-0 scale-100';
  };

  return (
    <div
      ref={domRef}
      style={{
        transitionDuration: '800ms',
        transitionDelay: `${delay}ms`,
        transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
      }}
      className={`transition-all will-change-[transform,opacity,filter] ${getDirectionClasses()} ${className}`}
    >
      {children}
    </div>
  );
};
