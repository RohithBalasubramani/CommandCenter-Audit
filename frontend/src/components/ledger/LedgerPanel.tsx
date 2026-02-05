"use client";

import { useState, useEffect, useRef } from "react";
import { commandCenterBus } from "@/lib/events";

/**
 * LedgerPanel — Persistent audit trail and governance dock.
 *
 * Blueprint spec (README.md — Ledger Panel):
 *   Persistent dock for proposals awaiting approval, action audit trail,
 *   co-signature requests, and governance visibility.
 *
 * Gated by ENABLE_LEDGER flag (config.flags.enableLedger).
 * When enabled, shows a collapsible panel at the bottom of the screen
 * with recent pipeline events: layout updates, system triggers, voice
 * input events, widget interactions.
 */

interface LedgerEntry {
  id: string;
  timestamp: number;
  type: string;
  summary: string;
}

const MAX_ENTRIES = 50;

export default function LedgerPanel() {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [collapsed, setCollapsed] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const entryIdRef = useRef(0);

  // Subscribe to all auditable events
  useEffect(() => {
    const addEntry = (type: string, summary: string) => {
      setEntries((prev) => {
        const entry: LedgerEntry = {
          id: `ledger-${++entryIdRef.current}`,
          timestamp: Date.now(),
          type,
          summary,
        };
        const next = [...prev, entry];
        if (next.length > MAX_ENTRIES) {
          return next.slice(next.length - MAX_ENTRIES);
        }
        return next;
      });
    };

    const unsubs = [
      commandCenterBus.on("LAYOUT_UPDATE", (e) => {
        if (e.type === "LAYOUT_UPDATE") {
          const count = e.layout?.widgets?.length ?? 0;
          addEntry("LAYOUT", `Dashboard updated: ${count} widgets`);
        }
      }),
      commandCenterBus.on("SYSTEM_TRIGGER", (e) => {
        if (e.type === "SYSTEM_TRIGGER") {
          addEntry("TRIGGER", `${e.trigger.kind}: ${e.trigger.message}`);
        }
      }),
      commandCenterBus.on("VOICE_INPUT_START", () => {
        addEntry("VOICE", "Voice input started");
      }),
      commandCenterBus.on("VOICE_INPUT_STOP", () => {
        addEntry("VOICE", "Voice input stopped");
      }),
      commandCenterBus.on("TEXT_INPUT_SUBMIT", (e) => {
        if (e.type === "TEXT_INPUT_SUBMIT") {
          addEntry("INPUT", `Text query: "${e.text.slice(0, 60)}"`);
        }
      }),
      commandCenterBus.on("WIDGET_FOCUS", (e) => {
        if (e.type === "WIDGET_FOCUS") {
          addEntry("WIDGET", `Focus: ${e.label}`);
        }
      }),
      commandCenterBus.on("WIDGET_DRILL_DOWN", (e) => {
        if (e.type === "WIDGET_DRILL_DOWN") {
          addEntry("WIDGET", `Drill-down: ${e.label} → ${e.context}`);
        }
      }),
    ];

    return () => unsubs.forEach((u) => u());
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (!collapsed) {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [entries, collapsed]);

  const typeColors: Record<string, string> = {
    LAYOUT: "text-blue-400",
    TRIGGER: "text-yellow-400",
    VOICE: "text-green-400",
    INPUT: "text-cyan-400",
    WIDGET: "text-purple-400",
  };

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-neutral-700 bg-neutral-900/95 backdrop-blur-md"
      data-testid="ledger-panel"
    >
      {/* Header / Toggle */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-1.5 hover:bg-neutral-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-neutral-400"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          <span className="text-xs font-medium text-neutral-300">
            Ledger Panel
          </span>
          <span className="text-[10px] text-neutral-500">
            {entries.length} event{entries.length !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {entries.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setEntries([]);
              }}
              className="text-[10px] text-neutral-500 hover:text-neutral-300 px-1"
            >
              Clear
            </button>
          )}
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`text-neutral-400 transition-transform ${collapsed ? "" : "rotate-180"}`}
          >
            <polyline points="18 15 12 9 6 15" />
          </svg>
        </div>
      </button>

      {/* Entries */}
      {!collapsed && (
        <div
          ref={scrollRef}
          className="max-h-48 overflow-y-auto px-4 pb-2 space-y-0.5"
        >
          {entries.length === 0 ? (
            <div className="text-center text-neutral-500 text-xs py-4">
              No events recorded yet. Interact with the dashboard to see audit entries.
            </div>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="flex items-start gap-2 text-xs leading-relaxed">
                <span className="text-neutral-600 shrink-0 font-mono w-16">
                  {new Date(entry.timestamp).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false,
                  })}
                </span>
                <span
                  className={`shrink-0 font-mono w-14 ${typeColors[entry.type] || "text-neutral-400"}`}
                >
                  {entry.type}
                </span>
                <span className="text-neutral-300 truncate">{entry.summary}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
