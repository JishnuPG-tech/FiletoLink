import React, { useEffect, useRef } from 'react';

interface SpiritBackgroundProps {
  className?: string;
}

/**
 * SpiritBackground
 *
 * Exact 3D Particle Animation reverse-engineered from particle-love.com ("The Spirit", Medium preset).
 *
 * Visual Architecture:
 * - Ping-pong GPGPU 256x256 FBO Particle Simulation (65,536 particles)
 * - 4D Simplex Curl Turbulence with fluid wandering emitters
 * - Billboard quads aligned dynamically with screen-space particle velocity
 * - Motion-blur normal-mapped sprite atlas texture sampling (images/motion_blur.png)
 * - Exact Spirit Quad-Tone Palette:
 *     Color 1: #559498 (Celestial Cyan / Teal)
 *     Color 2: #28394d (Deep Indigo / Twilight Slate)
 *     Color 3: #727546 (Golden Olive / Champagne Radiance)
 *     Color 4: #643f15 (Warm Amber Bronze)
 * - Full-page scroll coupling:
 *     - 360° orbital camera rotation around the central spirit cloud synced to scroll progress
 *     - Dynamic vortex swirl & curl surge on scroll velocity, easing back smoothly to baseline
 *     - Smooth spring-dampened mouse tilt & parallax
 * - 60 FPS rock-solid performance with zero CPU lag
 */
export const SpiritBackground: React.FC<SpiritBackgroundProps> = ({
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Only load once
    if ((window as any).__spiritEngineLoaded) return;

    // Check WebGL support
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        console.warn('WebGL not supported for SpiritBackground');
        return;
      }
    } catch {
      return;
    }

    const script = document.createElement('script');
    script.src = '/js/spirit.js';
    script.async = true;
    script.onload = () => {
      (window as any).__spiritEngineLoaded = true;
    };
    script.onerror = (err) => {
      console.error('Failed to load /js/spirit.js', err);
    };

    document.body.appendChild(script);

    return () => {
      // In production Vite SPA, the fixed background stays persistent
    };
  }, []);

  return (
    <div className={`fixed inset-0 pointer-events-none z-0 overflow-hidden ${className}`}>
      {/* Exact 3D Spirit Canvas */}
      <canvas
        id="spirit-canvas"
        ref={canvasRef}
        className="absolute inset-0 w-full h-full block"
        style={{
          background: '#04070e',
        }}
      />

      {/* Subtle radial ambient vignette to accentuate text readability without hiding particles */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at 50% 30%, rgba(4,7,14,0.15) 0%, rgba(4,7,14,0.45) 60%, rgba(4,7,14,0.85) 100%)',
        }}
      />
    </div>
  );
};

export default SpiritBackground;
