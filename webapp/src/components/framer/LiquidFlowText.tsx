import React, { useId } from 'react';

export interface LiquidFlowTextProps {
  text: string;
  className?: string;
  baseColor?: string;
  waveColor1?: string;
  waveColor2?: string;
  waveColor3?: string;
  speed?: number; // 0.1x to 5x
  intensity?: number; // 0 to 100%
  loop?: boolean;
  align?: 'left' | 'center' | 'right';
  style?: React.CSSProperties;
}

/**
 * LiquidFlowText
 * Ported from Framer: https://framer.com/m/LiquidFlowText-flxfg6.js@ztuEVobY3JU2gGCE2xmR
 * Provides a continuous, seamless chromatic wave flowing across text typography.
 */
export const LiquidFlowText: React.FC<LiquidFlowTextProps> = ({
  text,
  className = '',
  baseColor = '#FFFFFF',
  waveColor1 = '#38BDF8', // Telegram Cyan
  waveColor2 = '#A855F7', // Electric Violet
  waveColor3 = '#F43F5E', // FlashFile Rose
  speed = 1.2,
  intensity = 55,
  loop = true,
  align = 'center',
  style = {},
}) => {
  const uid = useId().replace(/[:]/g, '');
  const animName = `lw-move-${uid}`;

  const i = Math.max(0, Math.min(100, intensity)) / 100;
  const band = 0.18 + i * 0.52;
  const half = band / 2;
  const duration = 6 / Math.max(0.1, speed);

  const stops = buildStops(baseColor, [waveColor1, waveColor2, waveColor3], half);

  return (
    <div
      className={`inline-flex items-center overflow-hidden ${
        align === 'left'
          ? 'justify-start text-left'
          : align === 'right'
          ? 'justify-end text-right'
          : 'justify-center text-center'
      } ${className}`}
    >
      {loop && (
        <style>{`
          @keyframes ${animName} {
            0%   { background-position: 200% 0%; }
            100% { background-position: -100% 0%; }
          }
          @media (prefers-reduced-motion: reduce) {
            .lw-text-${uid} { animation: none !important; }
          }
        `}</style>
      )}
      <span
        className={`lw-text-${uid} inline-block`}
        style={{
          margin: 0,
          color: baseColor,
          backgroundImage: `linear-gradient(90deg, ${stops})`,
          backgroundSize: '300% 100%',
          backgroundPosition: '0% 0%',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          animation: loop ? `${animName} ${duration}s linear infinite` : 'none',
          whiteSpace: 'pre-wrap',
          textAlign: align,
          ...style,
        }}
      >
        {text}
      </span>
    </div>
  );
};

function buildStops(base: string, waves: [string, string, string], half: number): string {
  const [w1, w2, w3] = waves;
  const center = 0.5;
  const start = Math.max(0, center - half);
  const end = Math.min(1, center + half);
  const q = (t: number) => `${(t * 100).toFixed(1)}%`;
  const mid1 = start + (end - start) * 0.33;
  const mid2 = start + (end - start) * 0.66;

  return [
    `${base} 0%`,
    `${base} ${q(start)}`,
    `${w1} ${q(mid1)}`,
    `${w2} ${q(center)}`,
    `${w3} ${q(mid2)}`,
    `${base} ${q(end)}`,
    `${base} 100%`,
  ].join(', ');
}

export default LiquidFlowText;
