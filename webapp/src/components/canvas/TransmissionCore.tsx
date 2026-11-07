import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface TransmissionCoreProps {
  className?: string;
  workerCount?: number;
}

/**
 * Three.js WebGL Transmission Core Component
 * Features:
 * - Central rotating icosahedron geodesic wireframe with inner glowing point lattice
 * - Orbiting worker node satellites with dynamic line tethers
 * - 500 subtle glowing micro-particles with spring mouse dampening
 * - Battery-friendly IntersectionObserver (pauses animation when out of view)
 * - Prefers-reduced-motion & WebGL support fallback
 */
export const TransmissionCore: React.FC<TransmissionCoreProps> = ({
  className = '',
  workerCount = 6,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fallbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    const fallback = fallbackRef.current;
    if (!container || !canvas) return;

    // 1. Accessibility & WebGL Check
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

    // 2. Scene & Renderer Setup
    const scene = new THREE.Scene();
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || 650;
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 11);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    const sceneGroup = new THREE.Group();
    scene.add(sceneGroup);

    // 3. Central Transmission Core (Geodesic Wireframe + Glowing Points)
    const coreGroup = new THREE.Group();
    sceneGroup.add(coreGroup);

    const outerGeo = new THREE.IcosahedronGeometry(2.1, 1);
    const outerMat = new THREE.MeshBasicMaterial({
      color: 0xff3b5c,
      wireframe: true,
      transparent: true,
      opacity: 0.32,
    });
    const outerMesh = new THREE.Mesh(outerGeo, outerMat);
    coreGroup.add(outerMesh);

    const innerGeo = new THREE.IcosahedronGeometry(1.35, 2);
    const innerMat = new THREE.PointsMaterial({
      color: 0xff526d,
      size: 2.2,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const innerPoints = new THREE.Points(innerGeo, innerMat);
    coreGroup.add(innerPoints);

    const centerSphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.35, 12, 12),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.75 })
    );
    coreGroup.add(centerSphere);

    // 4. Orbiting Worker Satellites (Multi-Client Bots)
    const satellites: Array<{ group: THREE.Group; angle: number; speed: number; orbitTilt: number }> = [];
    const satGroup = new THREE.Group();
    sceneGroup.add(satGroup);
    const satRadius = 3.8;

    const tetherPositions = new Float32Array(workerCount * 6);
    const tetherGeo = new THREE.BufferGeometry();
    tetherGeo.setAttribute('position', new THREE.BufferAttribute(tetherPositions, 3));
    const tetherLines = new THREE.LineSegments(
      tetherGeo,
      new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.18 })
    );
    satGroup.add(tetherLines);

    const colors = [0x38bdf8, 0x10b981, 0xff3b5c, 0x38bdf8, 0xf59e0b, 0x10b981];
    for (let i = 0; i < workerCount; i++) {
      const satNode = new THREE.Group();
      satNode.add(
        new THREE.Mesh(
          new THREE.SphereGeometry(0.12, 10, 10),
          new THREE.MeshBasicMaterial({ color: colors[i % colors.length] })
        )
      );

      const haloGeo = new THREE.BufferGeometry();
      haloGeo.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
      satNode.add(
        new THREE.Points(
          haloGeo,
          new THREE.PointsMaterial({
            color: colors[i % colors.length],
            size: 5.5,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending,
          })
        )
      );

      satGroup.add(satNode);
      satellites.push({
        group: satNode,
        angle: (i / workerCount) * Math.PI * 2,
        speed: 0.35 + (i % 2) * 0.1,
        orbitTilt: i % 3 === 0 ? 0.3 : -0.25,
      });
    }

    // 5. Interactive Particle Constellation (500 Particles)
    const particleCount = 500;
    const posArray = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      const r = 2.4 + Math.random() * 4.6;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      posArray[i] = r * Math.sin(phi) * Math.cos(theta);
      posArray[i + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.65;
      posArray[i + 2] = r * Math.cos(phi);
    }
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particlesMesh = new THREE.Points(
      particleGeo,
      new THREE.PointsMaterial({
        color: 0x94a3b8,
        size: 1.6,
        transparent: true,
        opacity: 0.42,
        blending: THREE.AdditiveBlending,
      })
    );
    sceneGroup.add(particlesMesh);

    // 6. Smooth Spring Mouse Tracking
    let targetX = 0, targetY = 0;
    let currentX = 0, currentY = 0;
    const handleMouseMove = (e: MouseEvent) => {
      targetX = (e.clientX / window.innerWidth) * 2 - 1;
      targetY = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    // 7. Battery Optimization (IntersectionObserver)
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

    // 8. Animation Loop
    const clock = new THREE.Clock();
    const animate = () => {
      if (!isVisible) return;
      animId = requestAnimationFrame(animate);

      const time = clock.getElapsedTime();

      // Core rotation & gentle pulse
      outerMesh.rotation.y = time * 0.22;
      outerMesh.rotation.x = time * 0.14;
      innerPoints.rotation.y = -time * 0.35;
      const pulse = 1 + Math.sin(time * 2.2) * 0.035;
      coreGroup.scale.set(pulse, pulse, pulse);

      // Satellites update & tethers
      const posAttr = tetherLines.geometry.attributes.position as THREE.BufferAttribute;
      satellites.forEach((sat, i) => {
        const currentAngle = sat.angle + time * sat.speed;
        const x = Math.cos(currentAngle) * satRadius;
        const z = Math.sin(currentAngle) * satRadius;
        const y = Math.sin(time * 1.6 + i) * 0.45 + x * sat.orbitTilt * 0.3;

        sat.group.position.set(x, y, z);
        posAttr.setXYZ(i * 2, 0, 0, 0);
        posAttr.setXYZ(i * 2 + 1, x, y, z);
      });
      posAttr.needsUpdate = true;

      // Particle slow drift
      particlesMesh.rotation.y = time * 0.04;

      // Spring mouse interpolation
      currentX += (targetX - currentX) * 0.045;
      currentY += (targetY - currentY) * 0.045;
      sceneGroup.rotation.y = currentX * 0.32;
      sceneGroup.rotation.x = currentY * 0.22;

      renderer.render(scene, camera);
    };
    animate();

    // 9. Resize Handling
    const handleResize = () => {
      const newWidth = container.clientWidth || window.innerWidth;
      const newHeight = container.clientHeight || 650;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    };
    window.addEventListener('resize', handleResize, { passive: true });

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      observer.disconnect();
      if (animId) cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, [workerCount]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[650px] overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="w-full h-full block opacity-90 transition-opacity duration-700" />
      <div
        ref={fallbackRef}
        className="hidden absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(255,59,92,0.22)_0%,rgba(56,189,248,0.08)_45%,transparent_70%)] blur-[80px]"
      />
    </div>
  );
};
