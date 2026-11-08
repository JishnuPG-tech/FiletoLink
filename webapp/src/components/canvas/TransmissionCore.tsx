import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface TransmissionCoreProps {
  className?: string;
  particleCount?: number;
}

/**
 * Three.js "The Spirit" (particle-love.com by Edan Kwan) Curl-Noise WebGL Engine
 * Themed to FlashFile Obsidian & Crimson-Coral Palette.
 *
 * Architecture:
 * - Analytical 3D Simplex & Curl Noise evaluated on GPU in GLSL vertex shader
 * - Organic fluid turbulence & life-cycle fade
 * - Smooth spring mouse dampening & cursor attraction
 * - Scroll-coupled rotational velocity without React re-renders
 * - IntersectionObserver loop optimization for 60-120 FPS battery-friendly performance
 * - Graceful fallback for prefers-reduced-motion and non-WebGL environments
 */
export const TransmissionCore: React.FC<TransmissionCoreProps> = ({
  className = '',
  particleCount = 700,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fallbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    const fallback = fallbackRef.current;
    if (!container || !canvas) return;

    // 1. Accessibility & WebGL check
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const hasWebGL = (() => {
      try {
        const testCanvas = document.createElement('canvas');
        return !!(
          window.WebGLRenderingContext &&
          (testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl'))
        );
      } catch {
        return false;
      }
    })();

    if (prefersReducedMotion || !hasWebGL) {
      if (fallback) fallback.style.display = 'block';
      canvas.style.display = 'none';
      return;
    }

    // 2. Scene & Camera setup
    const scene = new THREE.Scene();
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || 750;
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.8);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    // 3. GLSL Shaders for Curl Noise Spirit
    const vertexShader = `
      uniform float uTime;
      uniform vec3 uMouse;
      uniform float uScrollProgress;
      
      attribute vec3 aOrigin;
      attribute float aOffset;
      attribute float aSpeed;
      attribute float aScale;
      
      varying float vLife;
      varying vec3 vPos;

      vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
      vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

      float snoise(vec3 v){
        const vec2  C = vec2(1.0/6.0, 1.0/3.0);
        const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);

        vec3 i  = floor(v + dot(v, C.yyy));
        vec3 x0 = v - i + dot(i, C.xxx);

        vec3 g = step(x0.yzx, x0.xyz);
        vec3 l = 1.0 - g;
        vec3 i1 = min( g.xyz, l.zxy );
        vec3 i2 = max( g.xyz, l.zxy );

        vec3 x1 = x0 - i1 + 1.0 * C.xxx;
        vec3 x2 = x0 - i2 + 2.0 * C.xxx;
        vec3 x3 = x0 - 1.0 + 3.0 * C.xxx;

        i = mod(i, 289.0 );
        vec4 p = permute( permute( permute( 
                   i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
                 + i.y + vec4(0.0, i1.y, i2.y, 1.0 )) 
                 + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));

        float n_ = 0.142857142857;
        vec3  ns = n_ * D.wyz - D.xzx;

        vec4 j = p - 49.0 * floor(p * ns.z *ns.z);

        vec4 x_ = floor(j * ns.z);
        vec4 y_ = floor(j - 7.0 * x_ );

        vec4 x = x_ *ns.x + ns.yyyy;
        vec4 y = y_ *ns.x + ns.yyyy;
        vec4 h = 1.0 - abs(x) - abs(y);

        vec4 b0 = vec4( x.xy, y.xy );
        vec4 b1 = vec4( x.zw, y.zw );

        vec4 s0 = floor(b0)*2.0 + 1.0;
        vec4 s1 = floor(b1)*2.0 + 1.0;
        vec4 sh = -step(h, vec4(0.0));

        vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
        vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

        vec3 p0 = vec3(a0.xy,h.x);
        vec3 p1 = vec3(a0.zw,h.y);
        vec3 p2 = vec3(a1.xy,h.z);
        vec3 p3 = vec3(a1.zw,h.w);

        vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
        p0 *= norm.x;
        p1 *= norm.y;
        p2 *= norm.z;
        p3 *= norm.w;

        vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
        m = m * m;
        return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
      }

      vec3 curlNoise(vec3 p) {
        const float e = 0.1;
        float dx = snoise(p + vec3(e, 0.0, 0.0)) - snoise(p - vec3(e, 0.0, 0.0));
        float dy = snoise(p + vec3(0.0, e, 0.0)) - snoise(p - vec3(0.0, e, 0.0));
        float dz = snoise(p + vec3(0.0, 0.0, e)) - snoise(p - vec3(0.0, 0.0, e));
        return normalize(vec3(dy - dz, dz - dx, dx - dy));
      }

      void main() {
        float progress = fract(uTime * 0.11 * aSpeed + aOffset);
        vLife = sin(progress * 3.14159265);

        vec3 pos = aOrigin;
        vec3 noisePos = pos * 0.45 + vec3(uTime * 0.08, uTime * 0.05, 0.0);
        vec3 curl = curlNoise(noisePos);

        pos += curl * progress * (2.2 + uScrollProgress * 1.5);

        // Subtle mouse pull
        vec3 mouseDiff = uMouse - pos;
        float mouseDist = length(mouseDiff);
        if (mouseDist < 4.0) {
            pos += normalize(mouseDiff) * (1.0 - mouseDist / 4.0) * 0.45;
        }

        vPos = pos;
        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;

        // Size attenuation with life fade
        gl_PointSize = (aScale * 38.0 * vLife) / -mvPosition.z;
      }
    `;

    const fragmentShader = `
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      uniform vec3 uColor3;

      varying float vLife;
      varying vec3 vPos;

      void main() {
          vec2 coord = gl_PointCoord - vec2(0.5);
          float dist = length(coord);
          if (dist > 0.5) discard;

          float alpha = smoothstep(0.5, 0.0, dist) * vLife * 0.85;

          vec3 col = mix(uColor1, uColor2, vLife);
          if (vLife > 0.80) {
              col = mix(col, uColor3, (vLife - 0.80) * 5.0);
          }

          gl_FragColor = vec4(col, alpha);
      }
    `;

    // 4. Geometry & Attributes
    const geometry = new THREE.BufferGeometry();
    const origins = new Float32Array(particleCount * 3);
    const offsets = new Float32Array(particleCount);
    const speeds = new Float32Array(particleCount);
    const scales = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      const radius = 1.2 + Math.random() * 2.8;
      const theta = Math.random() * Math.PI * 2;
      const ySpread = (Math.random() - 0.5) * 2.4;

      origins[i * 3] = Math.cos(theta) * radius;
      origins[i * 3 + 1] = ySpread + Math.sin(theta * 2.0) * 0.5;
      origins[i * 3 + 2] = Math.sin(theta) * radius;

      offsets[i] = Math.random();
      speeds[i] = 0.7 + Math.random() * 0.8;
      scales[i] = 0.8 + Math.random() * 1.5;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(origins, 3));
    geometry.setAttribute('aOrigin', new THREE.BufferAttribute(origins, 3));
    geometry.setAttribute('aOffset', new THREE.BufferAttribute(offsets, 1));
    geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1));
    geometry.setAttribute('aScale', new THREE.BufferAttribute(scales, 1));

    // 5. Shader Material with FlashFile Theme Colors
    const uniforms = {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector3(0, 0, 0) },
      uScrollProgress: { value: 0 },
      uColor1: { value: new THREE.Color(0xff3b5c) }, // Crimson
      uColor2: { value: new THREE.Color(0xe11d48) }, // Deep Coral
      uColor3: { value: new THREE.Color(0x38bdf8) }, // Electric Cyan
    };

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    const spiritMesh = new THREE.Points(geometry, material);
    scene.add(spiritMesh);

    // 6. Smooth Spring Cursor Dampening
    let targetMouseX = 0, targetMouseY = 0;
    let currentMouseX = 0, currentMouseY = 0;

    const onMouseMove = (e: MouseEvent) => {
      targetMouseX = ((e.clientX / window.innerWidth) * 2 - 1) * 3.8;
      targetMouseY = (-(e.clientY / window.innerHeight) * 2 + 1) * 2.2;
    };
    window.addEventListener('mousemove', onMouseMove, { passive: true });

    // 7. Scroll synchronization without React re-render
    const onScroll = () => {
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const progress = Math.min(1, Math.max(0, window.scrollY / maxScroll));
      uniforms.uScrollProgress.value = progress;
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    // 8. Battery & GPU Optimization with IntersectionObserver
    let isVisible = true;
    let animId: number | null = null;
    const observer = new IntersectionObserver(
      (entries) => {
        isVisible = entries[0].isIntersecting;
        if (isVisible && !animId) {
          animate();
        } else if (!isVisible && animId) {
          cancelAnimationFrame(animId);
          animId = null;
        }
      },
      { threshold: 0.05 }
    );
    observer.observe(container);

    // 9. Animation Loop
    const clock = new THREE.Clock();
    const animate = () => {
      if (!isVisible) return;
      animId = requestAnimationFrame(animate);

      const time = clock.getElapsedTime();
      uniforms.uTime.value = time;

      currentMouseX += (targetMouseX - currentMouseX) * 0.05;
      currentMouseY += (targetMouseY - currentMouseY) * 0.05;
      uniforms.uMouse.value.set(currentMouseX, currentMouseY, 0);

      spiritMesh.rotation.y = time * 0.06 + uniforms.uScrollProgress.value * 0.8;
      spiritMesh.rotation.z = Math.sin(time * 0.04) * 0.08;

      renderer.render(scene, camera);
    };
    animate();

    // 10. Resize Handling
    const onResize = () => {
      const newWidth = container.clientWidth || window.innerWidth;
      const newHeight = container.clientHeight || 750;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    };
    window.addEventListener('resize', onResize, { passive: true });

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      observer.disconnect();
      if (animId) cancelAnimationFrame(animId);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
    };
  }, [particleCount]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[650px] md:h-[750px] overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="w-full h-full block opacity-85 transition-opacity duration-700" />
      <div
        ref={fallbackRef}
        className="hidden absolute inset-0 bg-[radial-gradient(ellipse_at_50%_45%,rgba(255,59,92,0.22)_0%,rgba(56,189,248,0.08)_45%,transparent_70%)] blur-[90px]"
      />
    </div>
  );
};
