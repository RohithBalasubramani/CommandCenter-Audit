"use client";

import { ReactNode } from "react";

interface CanvasProps {
  children: ReactNode;
  statusBar: ReactNode;
}

/**
 * Canvas — The 100vh x 100vw zero-scroll container.
 * Everything in Command Center lives inside this canvas.
 * No global scroll — widgets manage their own scroll context.
 *
 * Layout:
 * ┌────────────────────────────────────┐
 * │           WIDGET GRID              │ flex-1
 * │   (Layer 3: Blob places widgets)   │
 * │                                    │
 * ├────────────────────────────────────┤
 * │ STATUS BAR (Spot + Chips + Ledger) │ fixed 48px
 * └────────────────────────────────────┘
 */
export default function Canvas({ children, statusBar }: CanvasProps) {
  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-[var(--cc-bg)]">
      {/* Widget Grid Area — Blob will control this */}
      <main className="flex-1 relative overflow-hidden">{children}</main>

      {/* Status Bar — Fixed bottom dock */}
      <footer
        className="shrink-0 border-t border-[var(--cc-border)] bg-[var(--cc-surface)]"
        style={{ height: "var(--cc-status-bar-height)" }}
      >
        {statusBar}
      </footer>
    </div>
  );
}
