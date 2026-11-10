import React from "react";
import { cn } from "@/lib/utils";

export interface BackgroundBeamsProps {
  className?: string;
  count?: number;
}

/**
 * Ultra-optimized, GPU-accelerated decorative light beams.
 * Uses static SVG gradients with CSS hardware-accelerated stroke-dash animations
 * to ensure 60 FPS performance without CPU/DOM layout recalculation lag.
 */
export function BackgroundBeams({ className, count = 5 }: BackgroundBeamsProps) {
  const paths = [
    "M-200 -60 C -40 140, 260 200, 720 460",
    "M-110 -20 C 50 170, 350 230, 810 490",
    "M-20 20 C 140 200, 440 260, 900 520",
    "M70 60 C 230 230, 530 290, 990 550",
    "M160 100 C 320 260, 620 320, 1080 580",
  ].slice(0, count);

  return (
    <div
      aria-hidden
      data-slot="background-beams"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <style>{`
        @keyframes flowBeam {
          0% {
            stroke-dashoffset: 1400;
            opacity: 0.2;
          }
          15% {
            opacity: 0.9;
          }
          85% {
            opacity: 0.9;
          }
          100% {
            stroke-dashoffset: -1400;
            opacity: 0.2;
          }
        }
        .gpu-beam {
          will-change: stroke-dashoffset;
          animation: flowBeam 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
      `}</style>

      <svg
        className="size-full"
        viewBox="0 0 960 540"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          {/* Static gradient definitions - zero JS layout thrashing */}
          <linearGradient id="beam-grad-primary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#D97757" stopOpacity="0" />
            <stop offset="35%" stopColor="#D97757" stopOpacity="0.95" />
            <stop offset="70%" stopColor="#EA580C" stopOpacity="1" />
            <stop offset="100%" stopColor="#F59E0B" stopOpacity="0" />
          </linearGradient>

          <linearGradient id="beam-grad-secondary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EA580C" stopOpacity="0" />
            <stop offset="40%" stopColor="#D97757" stopOpacity="0.85" />
            <stop offset="75%" stopColor="#FB923C" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#D97757" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Static subtle guide tracks */}
        {paths.map((d, i) => (
          <path
            key={`base-${i}`}
            d={d}
            stroke="rgba(255, 255, 255, 0.04)"
            strokeWidth={1}
          />
        ))}

        {/* High-speed GPU hardware accelerated beams */}
        {paths.map((d, i) => (
          <path
            key={`active-beam-${i}`}
            d={d}
            stroke={i % 2 === 0 ? "url(#beam-grad-primary)" : "url(#beam-grad-secondary)"}
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeDasharray="220 1100"
            className="gpu-beam"
            style={{
              animationDelay: `${i * 1.5}s`,
              animationDuration: `${7 + i * 1.2}s`,
            }}
          />
        ))}
      </svg>
    </div>
  );
}
