import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface SpiritBackgroundProps {
  className?: string;
  particleCount?: number;
}

/**
 * The Spirit (particle-love.com) - Highly Optimized 60 FPS 3D Particle WebGL Engine
 *
 * Visual & Motion Characteristics:
 * - Fluid, ethereal smoky particle nebula ("The Spirit")
 * - Divergence-free 3D Curl Noise flow fields with rhythmic breathing and organic drift
 * - Additive blending with vibrant Crimson-Rose (#FF3B5C) and Ethereal Violet (#8B5CF6) glow
 * - Core energy highlights on youth particles
 * - Full-page scroll coupling: rotates, drifts sideways, and zooms parallax depth across sections
 * - Spring-damped cursor and touch interaction (spirit follows and swirls around pointer)
 * - Rock-solid 60 FPS on mobile and desktop (0 lag, lightweight GPU execution, visibility pausing)
 */
export const SpiritBackground: React.FC<SpiritBackgroundProps> = ({
  className = '',
  particleCount = 1100,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fallbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const fallback = fallbackRef.current;
    if (!canvas) return;

    // Check prefers-reduced-motion and WebGL support
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const hasWebGL = (() => {
      try {
        const test = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && (test.getContext('webgl') || test.getContext('experimental-webgl')));
      } catch {
        return false;
      }
    })();

    if (prefersReducedMotion || !hasWebGL) {
      if (fallback) fallback.style.display = 'block';
      canvas.style.display = 'none';
      return;
    }

    // Three.js Scene Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 7.5);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));

    // Particle Distribution: Golden Ratio Fibonacci Sphere
    const count = Math.max(800, Math.min(particleCount, 1600));
    const positions = new Float32Array(count * 3);
    const origins = new Float32Array(count * 3);
    const offsets = new Float32Array(count);
    const speeds = new Float32Array(count);
    const scales = new Float32Array(count);

    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    for (let i = 0; i < count; i++) {
      const theta = 2 * Math.PI * i / goldenRatio;
      const phi = Math.acos(1 - 2 * (i + 0.5) / count);
      const radius = 1.35 * Math.cbrt(Math.random());

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      origins[i * 3 + 0] = x;
      origins[i * 3 + 1] = y;
      origins[i * 3 + 2] = z;

      positions[i * 3 + 0] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      offsets[i] = Math.random();
      speeds[i] = 0.8 + Math.random() * 0.5;
      scales[i] = 0.7 + Math.random() * 0.8;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('aOrigin', new THREE.BufferAttribute(origins, 3));
    geometry.setAttribute('aOffset', new THREE.BufferAttribute(offsets, 1));
    geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1));
    geometry.setAttribute('aScale', new THREE.BufferAttribute(scales, 1));

    // Optimized High-Performance GPU Curl Noise Vertex Shader
    const vertexShader = `
      uniform float uTime;
      uniform float uRadius;
      uniform vec3  uMouse3D;
      uniform float uScrollProgress;
      uniform float uScrollVelocity;

      attribute vec3  aOrigin;
      attribute float aOffset;
      attribute float aSpeed;
      attribute float aScale;

      varying float vLife;
      varying vec3  vPos;

      // Fast, smooth divergence-free 3D curl field based on trigonometric potential fields
      vec3 computeCurl(vec3 p, float t) {
        float x = sin(p.y * 1.8 + t * 0.4) + cos(p.z * 1.4 - t * 0.3);
        float y = sin(p.z * 1.6 + t * 0.35) + cos(p.x * 1.7 + t * 0.45);
        float z = sin(p.x * 1.5 - t * 0.3) + cos(p.y * 1.5 + t * 0.4);
        
        // Second harmonic for fine smoky tendrils
        x += 0.5 * sin(p.y * 3.4 - t * 0.7);
        y += 0.5 * cos(p.z * 3.2 + t * 0.6);
        z += 0.5 * sin(p.x * 3.1 + t * 0.65);
        
        return vec3(x, y, z) * 0.7;
      }

      void main() {
        // Individual cycle progression (life: 0.0 -> 1.0 -> 0.0)
        float cycle = fract(uTime * 0.09 * aSpeed + aOffset);
        vLife = sin(cycle * 3.14159265);

        // Core base position with rhythmic breathing
        float pulse = 1.0 + sin(uTime * 1.4 + aOffset * 6.28) * 0.18;
        vec3 pos = aOrigin * pulse * (uRadius + uScrollProgress * 0.7);

        // Curl turbulence displacement
        vec3 curl = computeCurl(pos * 0.85, uTime * 0.6);
        pos += curl * (1.9 + uScrollVelocity * 3.5) * cycle;

        // Spring-damped cursor attraction and swirl
        vec3 mouseDiff = uMouse3D - pos;
        float mouseDist = length(mouseDiff);
        if (mouseDist < 4.2) {
          float pull = (1.0 - smoothstep(0.0, 4.2, mouseDist));
          pos += normalize(mouseDiff) * pull * 1.1;
          // Subtle swirl around cursor
          pos += cross(normalize(mouseDiff), vec3(0.0, 0.0, 1.0)) * pull * 0.8;
        }

        vPos = pos;
        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;

        // Perspective particle size with soft fade on birth/death
        gl_PointSize = (aScale * 44.0 * vLife) / (-mvPosition.z);
      }
    `;

    // Fragment Shader: Soft Circular Particle Mask with Dual-Tone Ethereal Glow
    const fragmentShader = `
      precision mediump float;
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      uniform vec3 uColorCore;

      varying float vLife;
      varying vec3  vPos;

      void main() {
        // Crisp circular soft particle mask
        vec2 uv = gl_PointCoord - vec2(0.5);
        float dist = length(uv);
        if (dist > 0.5) discard;

        // Quadratic radial falloff for smoky glow
        float alpha = smoothstep(0.5, 0.0, dist) * vLife * 0.90;

        // Dual-tone spirit gradient: Crimson Rose -> Vibrant Purple/Violet
        vec3 col = mix(uColor2, uColor1, smoothstep(0.05, 0.75, vLife));

        // Brilliant pure white energetic highlight in core
        if (vLife > 0.80) {
          col = mix(col, uColorCore, (vLife - 0.80) * 5.0);
        }

        gl_FragColor = vec4(col, alpha);
      }
    `;

    // Uniforms matching The Spirit color palette & FlashFile identity
    const uniforms = {
      uTime: { value: 0.0 },
      uRadius: { value: 1.85 },
      uMouse3D: { value: new THREE.Vector3(0, 0, 0) },
      uScrollProgress: { value: 0.0 },
      uScrollVelocity: { value: 0.0 },
      uColor1: { value: new THREE.Color('#FF3B5C') },    // Vibrant Crimson Rose
      uColor2: { value: new THREE.Color('#8B5CF6') },    // Ethereal Purple
      uColorCore: { value: new THREE.Color('#FFFFFF') },  // Pure White Core
    };

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Mouse Tracking with Smooth Spring Dampening
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const onPointerMove = (e: MouseEvent | TouchEvent) => {
      let clientX = 0;
      let clientY = 0;
      if ('touches' in e && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
      } else if ('clientX' in e) {
        clientX = e.clientX;
        clientY = e.clientY;
      }
      mouse.targetX = (clientX / window.innerWidth) * 2 - 1;
      mouse.targetY = -(clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener('mousemove', onPointerMove, { passive: true });
    window.addEventListener('touchmove', onPointerMove, { passive: true });

    // Scroll Tracking
    let scrollProgress = 0;
    let targetScrollProgress = 0;
    let lastScrollY = window.scrollY;
    let scrollVelocity = 0;

    const onScroll = () => {
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      targetScrollProgress = Math.min(1, Math.max(0, window.scrollY / maxScroll));
      const currentScrollY = window.scrollY;
      scrollVelocity = Math.abs(currentScrollY - lastScrollY) * 0.006;
      lastScrollY = currentScrollY;
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    // Resize Handler
    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    };
    window.addEventListener('resize', onResize);

    // Visibility Listener to prevent background GPU drain
    let isVisible = true;
    const onVisibilityChange = () => {
      isVisible = !document.hidden;
    };
    document.addEventListener('visibilitychange', onVisibilityChange);

    // 60 FPS Render Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (!isVisible) return;

      const elapsedTime = clock.getElapsedTime();

      // Mouse spring interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.06;
      mouse.y += (mouse.targetY - mouse.y) * 0.06;
      uniforms.uMouse3D.value.set(mouse.x * 3.4, mouse.y * 2.4, 0);

      // Scroll spring interpolation
      scrollProgress += (targetScrollProgress - scrollProgress) * 0.08;
      scrollVelocity *= 0.90;

      uniforms.uTime.value = elapsedTime;
      uniforms.uScrollProgress.value = scrollProgress;
      uniforms.uScrollVelocity.value = scrollVelocity;

      // Synchronize 3D Spirit rotation & positional drift with page scroll
      particles.rotation.y = scrollProgress * Math.PI * 2.2 + elapsedTime * 0.12;
      particles.rotation.x = Math.sin(scrollProgress * Math.PI) * 0.45 + mouse.y * 0.25;
      particles.rotation.z = Math.cos(scrollProgress * Math.PI) * 0.25;

      // Spatial drift across sections
      particles.position.x = Math.sin(scrollProgress * Math.PI * 2.0) * 1.3 + mouse.x * 0.7;
      particles.position.y = -(scrollProgress - 0.5) * 2.0 + mouse.y * 0.35;
      camera.position.z = 7.5 - Math.sin(scrollProgress * Math.PI) * 1.6;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('touchmove', onPointerMove);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      document.removeEventListener('visibilitychange', onVisibilityChange);

      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, [particleCount]);

  return (
    <div
      className={`fixed inset-0 pointer-events-none z-0 overflow-hidden ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
      <div
        ref={fallbackRef}
        className="hidden absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_35%,rgba(255,59,92,0.18),transparent_70%)]"
      />
    </div>
  );
};
