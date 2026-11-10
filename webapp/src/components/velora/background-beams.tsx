import React, { useSyncExternalStore } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

const noopSubscribe = () => () => {};

export interface BackgroundBeamsProps {
  className?: string;
  count?: number;
}

/**
 * Decorative light beams flowing along curved paths - a full-section
 * background with pitch-black theme and warm amber/orange accent beams.
 */
export function BackgroundBeams({ className, count = 7 }: BackgroundBeamsProps) {
  const hydrated = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const reducedMotion = useReducedMotion() === true && hydrated;

  const paths = Array.from({ length: count }, (_, i) => {
    const o = i * 90;
    return `M-${300 + o} -${100 + i * 40} C ${-100 + o} ${120 + i * 30}, ${
      200 + o
    } ${180 + i * 30}, ${640 + o} ${440 + i * 40}`;
  });

  return (
    <div
      aria-hidden
      data-slot="background-beams"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <svg
        className="size-full"
        viewBox="0 0 960 540"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
      >
        {paths.map((d, i) => (
          <path
            key={`base-${i}`}
            d={d}
            stroke="rgba(255, 255, 255, 0.06)"
            strokeOpacity={0.4}
            strokeWidth={1}
          />
        ))}
        {!reducedMotion &&
          paths.map((d, i) => (
            <path
              key={`beam-${i}`}
              d={d}
              stroke={`url(#beam-gradient-${i})`}
              strokeWidth={1.75}
              strokeLinecap="round"
            />
          ))}
        {!reducedMotion && (
          <defs>
            {paths.map((_, i) => (
              <motion.linearGradient
                key={`grad-${i}`}
                id={`beam-gradient-${i}`}
                gradientUnits="userSpaceOnUse"
                initial={{ x1: "0%", x2: "6%", y1: "0%", y2: "6%" }}
                animate={{
                  x1: ["0%", "100%"],
                  x2: ["6%", "106%"],
                  y1: ["0%", "100%"],
                  y2: ["6%", "106%"],
                }}
                transition={{
                  duration: 6 + (i % 4) * 2,
                  delay: i * 0.9,
                  repeat: Infinity,
                  ease: "linear",
                }}
              >
                <stop stopColor="#D97757" stopOpacity="0" />
                <stop offset="30%" stopColor="#D97757" stopOpacity="0.85" />
                <stop offset="60%" stopColor="#EA580C" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#EA580C" stopOpacity="0" />
              </motion.linearGradient>
            ))}
          </defs>
        )}
      </svg>
    </div>
  );
}
