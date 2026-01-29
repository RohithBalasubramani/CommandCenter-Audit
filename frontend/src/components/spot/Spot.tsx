"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { SpotWalkState, SpotState } from "@/types";
import { spotWalk } from "./SpotWalk";

// Spot sizes in px
const SIZE_PX: Record<string, number> = {
  small: 28,
  medium: 36,
  large: 44,
};

// CSS animation class per state
const ANIMATION_CLASS: Record<SpotState, string> = {
  idle: "animate-[spot-pulse_3s_ease-in-out_infinite]",
  listening: "animate-[spot-listening_1s_ease-in-out_infinite]",
  speaking: "animate-[spot-pulse_0.8s_ease-in-out_infinite]",
  processing: "animate-[spot-processing_1.5s_linear_infinite]",
  success: "animate-[spot-success_0.6s_ease-out]",
  error: "animate-[spot-error_0.4s_ease-in-out]",
};

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
}

/**
 * Spot — Visual AI presence in the status bar.
 * A particle visualization that reflects the AI state.
 * Controlled by SpotWalk — Spot never makes decisions.
 */
export default function Spot() {
  const [walkState, setWalkState] = useState<SpotWalkState>(spotWalk.state);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    const unsub = spotWalk.subscribe(setWalkState);
    return unsub;
  }, []);

  // Initialize particles
  const initParticles = useCallback(
    (count: number, size: number) => {
      const center = size / 2;
      const radius = size / 3;
      return Array.from({ length: count }, () => {
        const angle = Math.random() * Math.PI * 2;
        const r = Math.random() * radius;
        return {
          x: center + Math.cos(angle) * r,
          y: center + Math.sin(angle) * r,
          vx: (Math.random() - 0.5) * walkState.particleConfig.speed,
          vy: (Math.random() - 0.5) * walkState.particleConfig.speed,
          size: 1 + Math.random() * 2,
          opacity: 0.3 + Math.random() * 0.7,
        };
      });
    },
    [walkState.particleConfig.speed]
  );

  // Particle animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const px = SIZE_PX[walkState.size];
    const dpr = window.devicePixelRatio || 1;
    canvas.width = px * dpr;
    canvas.height = px * dpr;
    ctx.scale(dpr, dpr);

    particlesRef.current = initParticles(
      walkState.particleConfig.density,
      px
    );

    const { speed, chaos, color } = walkState.particleConfig;
    const center = px / 2;
    const maxRadius = px / 2.5;

    const animate = () => {
      ctx.clearRect(0, 0, px, px);

      particlesRef.current.forEach((p) => {
        // Add chaos
        p.vx += (Math.random() - 0.5) * chaos * 0.1;
        p.vy += (Math.random() - 0.5) * chaos * 0.1;

        // Attract to center
        const dx = center - p.x;
        const dy = center - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > maxRadius) {
          p.vx += (dx / dist) * 0.3;
          p.vy += (dy / dist) * 0.3;
        }

        // Dampen
        p.vx *= 0.95;
        p.vy *= 0.95;

        // Move
        p.x += p.vx * speed;
        p.y += p.vy * speed;

        // Draw
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = p.opacity;
        ctx.fill();
      });

      ctx.globalAlpha = 1;
      animFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animFrameRef.current);
  }, [walkState, initParticles]);

  const px = SIZE_PX[walkState.size];

  return (
    <div
      className={`relative flex items-center justify-center transition-all duration-300 ${ANIMATION_CLASS[walkState.state]}`}
      style={{ width: px, height: px }}
    >
      {/* Glow background */}
      <div
        className="absolute inset-0 rounded-full blur-md opacity-30 transition-colors duration-300"
        style={{ backgroundColor: walkState.particleConfig.color }}
      />

      {/* Particle canvas */}
      <canvas
        ref={canvasRef}
        className="relative rounded-full"
        style={{ width: px, height: px }}
      />
    </div>
  );
}
