"use client";

import { useEffect, useRef } from "react";
import { config } from "./config";
import { commandCenterBus } from "./events";
import type { SystemTrigger } from "@/types";

/**
 * useSystemTriggers — Polls the backend for system triggers and emits events.
 *
 * Blueprint spec (README.md):
 *   6 trigger types: alert_fired, threshold_breach, scheduled_event,
 *   role_change, time_of_day, webhook.
 *
 * When a trigger is received, emits SYSTEM_TRIGGER events on the bus.
 * The orchestrator (or useLayoutState) can listen for these to auto-update
 * the dashboard layout.
 *
 * Poll interval: 30 seconds (configurable via NEXT_PUBLIC_TRIGGER_POLL_MS).
 */
const POLL_INTERVAL_MS = Number(
  process.env.NEXT_PUBLIC_TRIGGER_POLL_MS || "30000"
);

export function useSystemTriggers() {
  const lastTimestampRef = useRef<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    async function poll() {
      if (!mountedRef.current) return;

      try {
        const params = new URLSearchParams();
        if (lastTimestampRef.current) {
          params.set("since", lastTimestampRef.current);
        }

        const url = `${config.api.baseUrl}/api/layer2/triggers/?${params}`;
        const res = await fetch(url, { signal: AbortSignal.timeout(10000) });

        if (!res.ok) return;

        const data = await res.json();
        const triggers: SystemTrigger[] = data.triggers || [];

        if (data.timestamp) {
          lastTimestampRef.current = data.timestamp;
        }

        for (const trigger of triggers) {
          commandCenterBus.emit({ type: "SYSTEM_TRIGGER", trigger });
        }

        // If alert triggers came in, auto-submit a query to the orchestrator
        const alertTriggers = triggers.filter(
          (t) => t.kind === "alert_fired" || t.kind === "threshold_breach"
        );
        if (alertTriggers.length > 0) {
          const alertMsg = alertTriggers[0].message;
          commandCenterBus.emit({
            type: "TEXT_INPUT_SUBMIT",
            text: `System alert: ${alertMsg}. Show me the current status.`,
          });
        }
      } catch {
        // Network error — silently retry next poll
      }
    }

    // Initial poll after short delay
    const initialTimer = setTimeout(poll, 3000);
    // Recurring poll
    const interval = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      mountedRef.current = false;
      clearTimeout(initialTimer);
      clearInterval(interval);
    };
  }, []);
}
