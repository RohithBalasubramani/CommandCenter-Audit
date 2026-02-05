"use client";

import React, { createContext, useContext, useRef, useEffect, useCallback } from "react";
import type { WidgetLifecycle } from "@/types";

/**
 * WidgetLifecycleContext — Provides lifecycle registration and container
 * resize observation to widget components.
 *
 * WidgetSlot wraps its children with this provider. Widget components can
 * use the `useWidgetLifecycle` hook to register lifecycle callbacks.
 *
 * Blueprint spec (README.md — Widget Lifecycle):
 *   Each widget must implement onMount, onResize, onDataUpdate, onUnmount.
 */

interface WidgetLifecycleContextValue {
  /** Register lifecycle hooks for this widget. Returns unregister function. */
  register: (lifecycle: WidgetLifecycle) => () => void;
  /** The container DOM element ref for resize observation. */
  containerRef: React.RefObject<HTMLDivElement | null>;
}

const LifecycleContext = createContext<WidgetLifecycleContextValue | null>(null);

interface WidgetLifecycleProviderProps {
  children: React.ReactNode;
  data?: Record<string, unknown>;
}

export function WidgetLifecycleProvider({ children, data }: WidgetLifecycleProviderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const lifecycleRef = useRef<WidgetLifecycle | null>(null);
  const dataRef = useRef(data);
  const mountedRef = useRef(false);

  const register = useCallback((lifecycle: WidgetLifecycle) => {
    lifecycleRef.current = lifecycle;
    return () => { lifecycleRef.current = null; };
  }, []);

  // onMount + onUnmount
  useEffect(() => {
    if (!mountedRef.current) {
      mountedRef.current = true;
      lifecycleRef.current?.onMount?.();
    }
    return () => {
      lifecycleRef.current?.onUnmount?.();
    };
  }, []);

  // onResize via ResizeObserver
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        lifecycleRef.current?.onResize?.(Math.round(width), Math.round(height));
      }
    });

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // onDataUpdate — detect data prop changes
  useEffect(() => {
    if (!mountedRef.current) return;
    const prev = dataRef.current;
    dataRef.current = data;
    if (prev !== data && data) {
      lifecycleRef.current?.onDataUpdate?.(data);
    }
  }, [data]);

  return (
    <LifecycleContext.Provider value={{ register, containerRef }}>
      <div ref={containerRef} className="h-full w-full" data-widget-lifecycle="active">
        {children}
      </div>
    </LifecycleContext.Provider>
  );
}

/**
 * useWidgetLifecycle — Hook for widget components to register lifecycle callbacks.
 *
 * Usage:
 *   function MyWidget({ data }: { data: Record<string, unknown> }) {
 *     useWidgetLifecycle({
 *       onMount: () => console.log("mounted"),
 *       onResize: (w, h) => console.log(`${w}x${h}`),
 *       onDataUpdate: (d) => console.log("data updated", d),
 *       onUnmount: () => console.log("cleanup"),
 *     });
 *     return <div>...</div>;
 *   }
 */
export function useWidgetLifecycle(lifecycle: WidgetLifecycle) {
  const ctx = useContext(LifecycleContext);
  useEffect(() => {
    if (!ctx) return;
    const unregister = ctx.register(lifecycle);
    return unregister;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx]);
}
