"use client";

import { useEffect, useState } from "react";
import Spot from "@/components/spot/Spot";
import { PersonaPlexState } from "@/types";
import { commandCenterBus } from "@/lib/events";

/**
 * StatusBar — Fixed bottom dock.
 *
 * Layout:
 * ┌────────┐                                              ┌────────┐
 * │  SPOT  │  [Capability Chips]        [Voice Status]    │ Ledger │
 * │ (dock) │                                              │ Panel  │
 * └────────┘                                              └────────┘
 */
export default function StatusBar() {
  const [ppState, setPpState] = useState<PersonaPlexState>("idle");

  useEffect(() => {
    const unsub = commandCenterBus.on("PERSONAPLEX_STATE_CHANGE", (event) => {
      if (event.type === "PERSONAPLEX_STATE_CHANGE") {
        setPpState(event.state);
      }
    });
    return unsub;
  }, []);

  return (
    <div className="h-full flex items-center justify-between px-4">
      {/* Left: Spot dock */}
      <div className="flex items-center gap-3">
        <Spot />
        <span className="text-xs text-[var(--cc-text-muted)] font-mono">
          {ppState === "listening"
            ? "Listening..."
            : ppState === "speaking"
            ? "Speaking..."
            : ppState === "connecting"
            ? "Connecting..."
            : ppState === "error"
            ? "Error"
            : "Ready"}
        </span>
      </div>

      {/* Center: Capability Chips (placeholder) */}
      <div className="flex items-center gap-2">
        <div className="px-2 py-0.5 rounded-full bg-[var(--cc-surface-hover)] text-[10px] text-[var(--cc-text-muted)] border border-[var(--cc-border)]">
          Layer 1: Voice I/O
        </div>
        <div className="px-2 py-0.5 rounded-full bg-[var(--cc-surface-hover)] text-[10px] text-[var(--cc-text-muted)] border border-[var(--cc-border)]">
          Layer 2: RAG ×1
        </div>
      </div>

      {/* Right: Ledger Panel stub */}
      <div className="flex items-center gap-2">
        <div className="text-xs text-[var(--cc-text-muted)]">
          Ledger: 0 pending
        </div>
      </div>
    </div>
  );
}
