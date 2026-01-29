import {
  SpotState,
  SpotSize,
  SpotParticleConfig,
  SpotWalkState,
  PersonaPlexState,
} from "@/types";
import { commandCenterBus } from "@/lib/events";

const LOG_PREFIX = "[SpotWalk]";

function dbg(...args: unknown[]) {
  console.debug(LOG_PREFIX, ...args);
}
function info(...args: unknown[]) {
  console.info(LOG_PREFIX, ...args);
}

// Default particle configs per state
const PARTICLE_CONFIGS: Record<SpotState, SpotParticleConfig> = {
  idle: { speed: 0.3, density: 20, color: "#6366f1", chaos: 0.1 },
  listening: { speed: 1.0, density: 40, color: "#818cf8", chaos: 0.4 },
  speaking: { speed: 0.8, density: 35, color: "#6366f1", chaos: 0.3 },
  processing: { speed: 1.5, density: 50, color: "#a78bfa", chaos: 0.7 },
  success: { speed: 0.5, density: 30, color: "#22c55e", chaos: 0.2 },
  error: { speed: 1.2, density: 25, color: "#ef4444", chaos: 0.8 },
};

const SIZE_FROM_STATE: Record<SpotState, SpotSize> = {
  idle: "small",
  listening: "medium",
  speaking: "medium",
  processing: "large",
  success: "medium",
  error: "medium",
};

/**
 * SpotWalk — Behavior controller for Spot.
 *
 * Controls Spot's visual state based on PersonaPlex and system events.
 * Spot does NOT move — it stays docked in the status bar.
 * SpotWalk only controls: state, size, and particle config.
 */
export class SpotWalk {
  private _state: SpotWalkState;
  private listeners: Set<(state: SpotWalkState) => void> = new Set();
  private pulseTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    info("SpotWalk initialized — state=idle, size=small");
    this._state = {
      state: "idle",
      size: "small",
      particleConfig: PARTICLE_CONFIGS.idle,
    };

    // Listen to PersonaPlex state changes
    commandCenterBus.on("PERSONAPLEX_STATE_CHANGE", (event) => {
      if (event.type === "PERSONAPLEX_STATE_CHANGE") {
        dbg(`Received PERSONAPLEX_STATE_CHANGE: ${event.state}`);
        this.handlePersonaPlexState(event.state);
      }
    });

    // Listen to voice input events
    commandCenterBus.on("VOICE_INPUT_START", () => {
      dbg("Received VOICE_INPUT_START");
      this.setState("listening");
    });

    commandCenterBus.on("VOICE_INPUT_STOP", () => {
      dbg("Received VOICE_INPUT_STOP");
      if (this._state.state === "listening") {
        this.setState("idle");
      }
    });
  }

  get state(): SpotWalkState {
    return this._state;
  }

  /** Transition Spot to a new state */
  setState(spotState: SpotState): void {
    const prev = this._state.state;
    this._state = {
      state: spotState,
      size: SIZE_FROM_STATE[spotState],
      particleConfig: PARTICLE_CONFIGS[spotState],
    };

    info(`State: ${prev} → ${spotState} (size=${this._state.size}, color=${this._state.particleConfig.color})`);
    this.notify();

    commandCenterBus.emit({
      type: "SPOT_STATE_CHANGE",
      state: this._state,
    });
  }

  /** Temporarily pulse to a state, then return to idle */
  pulse(spotState: "success" | "error", durationMs = 2000): void {
    info(`Pulse: ${spotState} for ${durationMs}ms`);
    if (this.pulseTimeout) clearTimeout(this.pulseTimeout);

    this.setState(spotState);
    this.pulseTimeout = setTimeout(() => {
      dbg(`Pulse timeout — returning to idle`);
      this.setState("idle");
      this.pulseTimeout = null;
    }, durationMs);
  }

  /** Set size independently */
  setSize(size: SpotSize): void {
    dbg(`Size override: ${this._state.size} → ${size}`);
    this._state = { ...this._state, size };
    this.notify();
  }

  /** Subscribe to state changes */
  subscribe(listener: (state: SpotWalkState) => void): () => void {
    this.listeners.add(listener);
    dbg(`Subscriber added (${this.listeners.size} total)`);
    return () => {
      this.listeners.delete(listener);
      dbg(`Subscriber removed (${this.listeners.size} total)`);
    };
  }

  private notify(): void {
    dbg(`Notifying ${this.listeners.size} subscriber(s)`);
    this.listeners.forEach((l) => l(this._state));
  }

  private handlePersonaPlexState(ppState: PersonaPlexState): void {
    dbg(`Mapping PersonaPlex state "${ppState}" → Spot state`);
    switch (ppState) {
      case "listening":
        this.setState("listening");
        break;
      case "speaking":
        this.setState("speaking");
        break;
      case "connecting":
      case "processing":
        this.setState("processing");
        break;
      case "error":
        this.pulse("error");
        break;
      case "idle":
      case "disconnected":
        this.setState("idle");
        break;
    }
  }
}

// Singleton
export const spotWalk = new SpotWalk();
