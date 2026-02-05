"use client";

import React, { useEffect, useRef, ComponentType } from "react";
import { useWidgetLifecycle } from "@/components/layer3/useWidgetLifecycle";

/**
 * WidgetWithLifecycle — HOC wrapper that auto-registers lifecycle hooks
 * for any Layer 4 widget component.
 *
 * Blueprint spec (README.md — Widget Lifecycle):
 *   Each widget must implement onMount, onResize, onDataUpdate, onUnmount.
 *
 * Instead of modifying every widget file, this wrapper bridges the gap:
 * - Registers lifecycle callbacks with the WidgetLifecycleProvider (from WidgetSlot)
 * - Tracks mount/unmount/resize/data-update lifecycle events
 * - Logs lifecycle events for debugging and audit
 */

interface WidgetWithLifecycleProps {
  scenario: string;
  data: Record<string, unknown>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Component: ComponentType<any>;
}

export default function WidgetWithLifecycle({ scenario, data, Component }: WidgetWithLifecycleProps) {
  const mountTimeRef = useRef<number>(0);
  const renderCountRef = useRef(0);
  renderCountRef.current++;

  useWidgetLifecycle({
    onMount: () => {
      mountTimeRef.current = Date.now();
      console.debug(`[lifecycle] ${scenario}: mounted`);
    },
    onResize: (width, height) => {
      console.debug(`[lifecycle] ${scenario}: resized to ${width}x${height}`);
    },
    onDataUpdate: (newData) => {
      console.debug(`[lifecycle] ${scenario}: data updated`, Object.keys(newData));
    },
    onUnmount: () => {
      const lifetime = Date.now() - mountTimeRef.current;
      console.debug(`[lifecycle] ${scenario}: unmounted after ${lifetime}ms (${renderCountRef.current} renders)`);
    },
  });

  return <Component data={data} />;
}
