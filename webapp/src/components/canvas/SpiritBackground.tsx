import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface SpiritBackgroundProps {
  className?: string;
  particleCount?: number;
}

/**
 * The Spirit (particle-love.com by Edan Kwan) - Exact Three.js 3D Particle WebGL Engine
 *
 * Algorithm details:
 * - 4D Simplex Noise Derivatives matrix by Stefan Gustavson / Ian McEwan
 * - 3-Octave 4D Curl Noise Potential Derivatives
 * - Dual-color fluid gradient with life attenuation and ethereal core bloom
 * - 60 FPS requestAnimationFrame with scroll-progress coupling and mouse spring dampening
 * - Fixed background placement synced across full-page scrolling
 */
export const SpiritBackground: React.FC<SpiritBackgroundProps> = ({
  className = '',
  particleCount = 2800,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
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
    const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 8.5);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    // Particle Attributes & Fibonacci Sphere Distribution
    const count = Math.max(1200, Math.min(particleCount, 5000));
    const positions = new Float32Array(count * 3);
    const origins = new Float32Array(count * 3);
    const offsets = new Float32Array(count);
    const speeds = new Float32Array(count);
    const scales = new Float32Array(count);
    const lifes = new Float32Array(count);

    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    for (let i = 0; i < count; i++) {
      const theta = 2 * Math.PI * i / goldenRatio;
      const phi = Math.acos(1 - 2 * (i + 0.5) / count);
      const r = 1.2 * Math.cbrt(Math.random());

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      origins[i * 3 + 0] = x;
      origins[i * 3 + 1] = y;
      origins[i * 3 + 2] = z;

      positions[i * 3 + 0] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      offsets[i] = Math.random();
      speeds[i] = 0.7 + Math.random() * 0.6;
      scales[i] = 0.6 + Math.random() * 0.9;
      lifes[i] = Math.random();
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('aOrigin', new THREE.BufferAttribute(origins, 3));
    geometry.setAttribute('aOffset', new THREE.BufferAttribute(offsets, 1));
    geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1));
    geometry.setAttribute('aScale', new THREE.BufferAttribute(scales, 1));

    // Exact GLSL Shaders from Edan Kwan's "The Spirit" (simplexNoiseDerivatives4 + curl4)
    const vertexShader = `
      uniform float uTime;
      uniform float uSpeed;
      uniform float uDieSpeed;
      uniform float uRadius;
      uniform float uCurlSize;
      uniform float uAttraction;
      uniform vec3  uMouse3D;
      uniform float uScrollProgress;
      uniform float uScrollVelocity;

      attribute vec3  aOrigin;
      attribute float aOffset;
      attribute float aSpeed;
      attribute float aScale;

      varying float vLife;
      varying vec3  vWorldPos;

      // --- Stefan Gustavson / Ian McEwan 4D Simplex Noise Derivatives ---
      vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
      float mod289(float x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
      vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
      float permute(float x) { return mod289(((x*34.0)+1.0)*x); }
      vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
      float taylorInvSqrt(float r) { return 1.79284291400159 - 0.85373472095314 * r; }

      vec4 grad4(float j, vec4 ip) {
        const vec4 ones = vec4(1.0, 1.0, 1.0, -1.0);
        vec4 p, s;
        p.xyz = floor(fract(vec3(j) * ip.xyz) * 7.0) * ip.z - 1.0;
        p.w = 1.5 - dot(abs(p.xyz), ones.xyz);
        s = vec4(lessThan(p, vec4(0.0)));
        p.xyz = p.xyz + (s.xyz*2.0 - 1.0) * s.www;
        return p;
      }

      #define F4 0.309016994374947451

      vec4 simplexNoiseDerivatives(vec4 v) {
        const vec4 C = vec4(0.138196601125011, 0.276393202250021, 0.414589803375032, -0.447213595499958);
        vec4 i = floor(v + dot(v, vec4(F4)));
        vec4 x0 = v - i + dot(i, C.xxxx);

        vec4 i0;
        vec3 isX = step(x0.yzw, x0.xxx);
        vec3 isYZ = step(x0.zww, x0.yyz);
        i0.x = isX.x + isX.y + isX.z;
        i0.yzw = 1.0 - isX;
        i0.y += isYZ.x + isYZ.y;
        i0.zw += 1.0 - isYZ.xy;
        i0.z += isYZ.z;
        i0.w += 1.0 - isYZ.z;

        vec4 i3 = clamp(i0, 0.0, 1.0);
        vec4 i2 = clamp(i0 - 1.0, 0.0, 1.0);
        vec4 i1 = clamp(i0 - 2.0, 0.0, 1.0);

        vec4 x1 = x0 - i1 + C.xxxx;
        vec4 x2 = x0 - i2 + C.yyyy;
        vec4 x3 = x0 - i3 + C.zzzz;
        vec4 x4 = x0 + C.wwww;

        i = mod289(i);
        float j0 = permute(permute(permute(permute(i.w) + i.z) + i.y) + i.x);
        vec4 j1 = permute(permute(permute(permute(
                  i.w + vec4(i1.w, i2.w, i3.w, 1.0))
                + i.z + vec4(i1.z, i2.z, i3.z, 1.0))
                + i.y + vec4(i1.y, i2.y, i3.y, 1.0))
                + i.x + vec4(i1.x, i2.x, i3.x, 1.0));

        vec4 ip = vec4(1.0/294.0, 1.0/49.0, 1.0/7.0, 0.0);
        vec4 p0 = grad4(j0, ip);
        vec4 p1 = grad4(j1.x, ip);
        vec4 p2 = grad4(j1.y, ip);
        vec4 p3 = grad4(j1.z, ip);
        vec4 p4 = grad4(j1.w, ip);

        vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
        p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
        p4 *= taylorInvSqrt(dot(p4,p4));

        vec3 values0 = vec3(dot(p0, x0), dot(p1, x1), dot(p2, x2));
        vec2 values1 = vec2(dot(p3, x3), dot(p4, x4));

        vec3 m0 = max(0.5 - vec3(dot(x0,x0), dot(x1,x1), dot(x2,x2)), 0.0);
        vec2 m1 = max(0.5 - vec2(dot(x3,x3), dot(x4,x4)), 0.0);

        vec3 temp0 = -6.0 * m0 * m0 * values0;
        vec2 temp1 = -6.0 * m1 * m1 * values1;

        vec3 mmm0 = m0 * m0 * m0;
        vec2 mmm1 = m1 * m1 * m1;

        float dx = temp0[0]*x0.x + temp0[1]*x1.x + temp0[2]*x2.x + temp1[0]*x3.x + temp1[1]*x4.x + mmm0[0]*p0.x + mmm0[1]*p1.x + mmm0[2]*p2.x + mmm1[0]*p3.x + mmm1[1]*p4.x;
        float dy = temp0[0]*x0.y + temp0[1]*x1.y + temp0[2]*x2.y + temp1[0]*x3.y + temp1[1]*x4.y + mmm0[0]*p0.y + mmm0[1]*p1.y + mmm0[2]*p2.y + mmm1[0]*p3.y + mmm1[1]*p4.y;
        float dz = temp0[0]*x0.z + temp0[1]*x1.z + temp0[2]*x2.z + temp1[0]*x3.z + temp1[1]*x4.z + mmm0[0]*p0.z + mmm0[1]*p1.z + mmm0[2]*p2.z + mmm1[0]*p3.z + mmm1[1]*p4.z;
        float dw = temp0[0]*x0.w + temp0[1]*x1.w + temp0[2]*x2.w + temp1[0]*x3.w + temp1[1]*x4.w + mmm0[0]*p0.w + mmm0[1]*p1.w + mmm0[2]*p2.w + mmm1[0]*p3.w + mmm1[1]*p4.w;

        return vec4(dx, dy, dz, dw) * 49.0;
      }

      // --- Edan Kwan's Exact 4D Curl Function ---
      vec3 curl(in vec3 p, in float noiseTime, in float persistence) {
        vec4 xNoise = vec4(0.0);
        vec4 yNoise = vec4(0.0);
        vec4 zNoise = vec4(0.0);

        for (int i = 0; i < 3; ++i) {
          float twoPowI = pow(2.0, float(i));
          float scale = 0.5 * twoPowI * pow(persistence, float(i));
          xNoise += simplexNoiseDerivatives(vec4(p * twoPowI, noiseTime)) * scale;
          yNoise += simplexNoiseDerivatives(vec4((p + vec3(123.4, 129845.6, -1239.1)) * twoPowI, noiseTime)) * scale;
          zNoise += simplexNoiseDerivatives(vec4((p + vec3(-9519.0, 9051.0, -123.0)) * twoPowI, noiseTime)) * scale;
        }

        return vec3(
          zNoise[1] - yNoise[2],
          xNoise[2] - zNoise[0],
          yNoise[0] - xNoise[1]
        );
      }

      void main() {
        // Individual cycle progression (life: 0.0 -> 1.0 -> 0.0)
        float cycle = fract(uTime * 0.10 * aSpeed + aOffset);
        vLife = sin(cycle * 3.14159265);

        // Core base position with rhythmic pulsing
        vec3 pos = aOrigin * (1.0 + sin(uTime * 1.5) * 0.15) * (uRadius + uScrollProgress * 0.6);

        // Curl turbulence displacement
        float noiseTime = uTime * 0.25;
        vec3 curlForce = curl(pos * uCurlSize, noiseTime, 0.15 + (1.0 - vLife) * 0.12);
        pos += curlForce * (1.8 + uScrollVelocity * 3.0) * cycle;

        // Ethereal cursor tracking & gravitational attraction
        vec3 mouseDiff = uMouse3D - pos;
        float mouseDist = length(mouseDiff);
        if (mouseDist < 4.5) {
          pos += normalize(mouseDiff) * (1.0 - smoothstep(0.0, 4.5, mouseDist)) * uAttraction * 0.95;
        }

        vWorldPos = pos;
        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;

        // Perspective size attenuation with smooth edge fade
        gl_PointSize = (aScale * 38.0 * vLife) / (-mvPosition.z);
      }
    `;

    const fragmentShader = `
      precision highp float;
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      uniform vec3 uColorCore;

      varying float vLife;
      varying vec3  vWorldPos;

      void main() {
        // Crisp circular soft particle mask
        vec2 uv = gl_PointCoord - vec2(0.5);
        float dist = length(uv);
        if (dist > 0.5) discard;

        // Smooth quadratic radial falloff
        float alpha = smoothstep(0.5, 0.0, dist) * vLife * 0.88;

        // Ethereal dual-tone fluid color gradient
        vec3 col = mix(uColor2, uColor1, smoothstep(0.0, 0.75, vLife));

        // Intense core energy highlight
        if (vLife > 0.82) {
          col = mix(col, uColorCore, (vLife - 0.82) * 5.5);
        }

        gl_FragColor = vec4(col, alpha);
      }
    `;

    // Uniforms matching The Spirit settings & FlashFile Brand
    const uniforms = {
      uTime: { value: 0.0 },
      uSpeed: { value: 1.0 },
      uDieSpeed: { value: 0.015 },
      uRadius: { value: 1.85 },
      uCurlSize: { value: 0.22 },
      uAttraction: { value: 1.2 },
      uMouse3D: { value: new THREE.Vector3(0, 0, 0) },
      uScrollProgress: { value: 0.0 },
      uScrollVelocity: { value: 0.0 },
      uColor1: { value: new THREE.Color('#FF3B5C') },    // Crimson flame
      uColor2: { value: new THREE.Color('#8B5CF6') },    // Ethereal purple/violet
      uColorCore: { value: new THREE.Color('#FFFFFF') },  // Pure white energetic core
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

    // Mouse Tracking with Spring Dampening
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

    // Smooth Scroll Coupling
    let scrollProgress = 0;
    let targetScrollProgress = 0;
    let lastScrollY = window.scrollY;
    let scrollVelocity = 0;

    const onScroll = () => {
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      targetScrollProgress = Math.min(1, Math.max(0, window.scrollY / maxScroll));
      const currentScrollY = window.scrollY;
      scrollVelocity = Math.abs(currentScrollY - lastScrollY) * 0.005;
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
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    };
    window.addEventListener('resize', onResize);

    // Animation Loop with Visibility Optimization
    let animationFrameId: number;
    let clock = new THREE.Clock();
    let isVisible = true;

    const onVisibilityChange = () => {
      isVisible = !document.hidden;
      if (isVisible) clock.start();
    };
    document.addEventListener('visibilitychange', onVisibilityChange);

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (!isVisible) return;

      const delta = Math.min(clock.getDelta(), 0.1);
      const elapsedTime = clock.getElapsedTime();

      // Mouse spring interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.06;
      mouse.y += (mouse.targetY - mouse.y) * 0.06;

      // Project mouse into 3D world space
      uniforms.uMouse3D.value.set(mouse.x * 3.5, mouse.y * 2.5, 0);

      // Scroll interpolation
      scrollProgress += (targetScrollProgress - scrollProgress) * 0.07;
      scrollVelocity *= 0.92;

      uniforms.uTime.value = elapsedTime;
      uniforms.uScrollProgress.value = scrollProgress;
      uniforms.uScrollVelocity.value = scrollVelocity;

      // Dynamic 3D rotation and drift synced with scroll position
      particles.rotation.y = scrollProgress * Math.PI * 2.4 + elapsedTime * 0.12;
      particles.rotation.x = Math.sin(scrollProgress * Math.PI) * 0.4 + mouse.y * 0.25;
      particles.rotation.z = Math.cos(scrollProgress * Math.PI) * 0.25;

      // Fluid positional sway through sections
      particles.position.x = Math.sin(scrollProgress * Math.PI * 2.0) * 1.4 + mouse.x * 0.8;
      particles.position.y = -(scrollProgress - 0.5) * 2.2 + mouse.y * 0.4;
      camera.position.z = 8.5 - Math.sin(scrollProgress * Math.PI) * 1.8;

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
      ref={containerRef}
      className={`fixed inset-0 pointer-events-none -z-10 overflow-hidden ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
      {/* Graceful fallback for prefers-reduced-motion and non-WebGL environments */}
      <div
        ref={fallbackRef}
        className="hidden absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_35%,rgba(255,59,92,0.15),transparent_70%)]"
      />
    </div>
  );
};
