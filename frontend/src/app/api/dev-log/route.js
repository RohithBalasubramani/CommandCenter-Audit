/**
 * dev-log API Route - Browser Console Log Receiver
 *
 * Receives browser console.log calls from DevConsoleInterceptor
 * and prints them to the Node.js terminal with [BROWSER] prefix.
 *
 * INSTALLATION:
 *   Copy this file to: frontend/app/api/dev-log/route.js
 *
 * Only works in development mode.
 */

export async function POST(request) {
  if (process.env.NODE_ENV === "production") {
    return Response.json({ error: "Not available" }, { status: 404 });
  }

  try {
    const { level = "log", args = [], source = "" } = await request.json();

    const timestamp = new Date().toLocaleTimeString("en-US", { hour12: false });
    const prefix = `[${timestamp}] [BROWSER]`;
    const sourceTag = source ? ` (${source})` : "";

    const message = args
      .map(arg => {
        if (typeof arg === "object") {
          try { return JSON.stringify(arg, null, 2); }
          catch { return String(arg); }
        }
        return String(arg);
      })
      .join(" ");

    const colors = {
      log: "\x1b[36m",
      info: "\x1b[34m",
      warn: "\x1b[33m",
      error: "\x1b[31m",
      debug: "\x1b[90m",
    };
    const reset = "\x1b[0m";
    const color = colors[level] || colors.log;

    const levelTag = level !== "log" ? ` [${level.toUpperCase()}]` : "";
    console.log(`${color}${prefix}${levelTag}${sourceTag} ${message}${reset}`);

    return Response.json({ ok: true });
  } catch (error) {
    console.error("[BROWSER] Failed to parse log:", error.message);
    return Response.json({ error: "Invalid request" }, { status: 400 });
  }
}
