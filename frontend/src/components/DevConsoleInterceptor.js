"use client";

import { useEffect } from "react";

/**
 * DevConsoleInterceptor - Browser Console Log Bridge
 *
 * Intercepts all browser console.log/warn/error calls and sends them
 * to the terminal via /api/dev-log endpoint.
 *
 * INSTALLATION:
 *   1. Copy this file to: frontend/components/DevConsoleInterceptor.js
 *   2. Copy dev-log-route.js to: frontend/app/api/dev-log/route.js
 *   3. Import in your root provider/layout:
 *
 *      import DevConsoleInterceptor from "@/components/DevConsoleInterceptor";
 *      <DevConsoleInterceptor />
 *
 * Only active in development mode.
 */
export default function DevConsoleInterceptor() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "development") return;
    if (typeof window === "undefined") return;

    const original = {
      log: console.log,
      info: console.info,
      warn: console.warn,
      error: console.error,
      debug: console.debug,
    };

    function getSource() {
      try {
        const stack = new Error().stack?.split("\n")[4] || "";
        const match = stack.match(/\((.+):(\d+):(\d+)\)/) ||
                      stack.match(/at\s+(.+):(\d+):(\d+)/);
        if (match) {
          const file = match[1].split("/").pop()?.split("?")[0] || "";
          return `${file}:${match[2]}`;
        }
      } catch {}
      return "";
    }

    async function sendLog(level, args) {
      try {
        await fetch("/api/dev-log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            level,
            args: args.map(arg => {
              if (arg instanceof Error) return `Error: ${arg.message}`;
              if (arg instanceof Element) return `<${arg.tagName?.toLowerCase() || "element"}>`;
              if (typeof arg === "object") {
                try { return JSON.parse(JSON.stringify(arg)); }
                catch { return String(arg); }
              }
              return arg;
            }),
            source: getSource(),
          }),
        });
      } catch {}
    }

    ["log", "info", "warn", "error", "debug"].forEach(level => {
      console[level] = (...args) => {
        original[level].apply(console, args);
        sendLog(level, args);
      };
    });

    return () => Object.assign(console, original);
  }, []);

  return null;
}
