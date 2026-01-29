"use client";

import { useEffect } from "react";
import { useVoicePipeline, ConversationMessage } from "./useVoicePipeline";

const stateLabels: Record<string, string> = {
  idle: "Press Ctrl+Space or click Speak to start",
  listening: "Listening — speak now",
  processing: "Processing your request...",
  speaking: "AI is responding...",
  error: "Error — click Speak to retry",
};

const stateColors: Record<string, string> = {
  idle: "text-white/60",
  listening: "text-blue-400",
  processing: "text-yellow-400",
  speaking: "text-purple-400",
  error: "text-red-400",
};

/**
 * VoiceInterfaceV2 — Layer 1 + Layer 2 integrated voice interface.
 *
 * This version uses:
 * - Web Speech API for STT (user input)
 * - Layer 2 orchestrator for intelligent responses
 * - Web Speech API for TTS (AI output)
 *
 * Flow:
 * 1. User speaks → STT transcribes
 * 2. Transcript → Layer 2 (filler spoken immediately)
 * 3. Layer 2 responds → TTS speaks response
 * 4. Layout JSON → Blob (Layer 3)
 */
export default function VoiceInterfaceV2() {
  const {
    state,
    isActive,
    error,
    start,
    stop,
    userTranscript,
    interimTranscript,
    aiResponse,
    messages,
    isTTSSpeaking,
    stopTTS,
    isSpeechRecognitionSupported,
    isSpeechSynthesisSupported,
  } = useVoicePipeline();

  // Keyboard shortcut (Ctrl+Space)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        if (isActive) {
          stop();
        } else {
          start();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isActive, start, stop]);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  const getMessageStyle = (msg: ConversationMessage) => {
    if (msg.speaker === "user") {
      return "bg-blue-600/30 border-blue-500/40";
    }
    if (msg.type === "filler") {
      return "bg-yellow-600/20 border-yellow-500/30";
    }
    return "bg-purple-600/30 border-purple-500/40";
  };

  return (
    <div className="flex flex-col h-full bg-[var(--cc-background)]">
      {/* Header */}
      <div className="p-3 border-b border-white/10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-white">
            Command Center Voice
          </h2>
          <div className="flex items-center gap-2">
            {/* State indicator */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  state === "listening"
                    ? "bg-blue-400 animate-pulse"
                    : state === "processing"
                      ? "bg-yellow-400 animate-pulse"
                      : state === "speaking"
                        ? "bg-purple-400 animate-pulse"
                        : state === "error"
                          ? "bg-red-400"
                          : "bg-white/30"
                }`}
              />
              <span className={`text-sm ${stateColors[state]}`}>
                {stateLabels[state]}
              </span>
            </div>
          </div>
        </div>

        {/* Support warnings */}
        {!isSpeechRecognitionSupported && (
          <p className="text-yellow-400 text-xs mt-2">
            Speech recognition not supported in this browser
          </p>
        )}
        {!isSpeechSynthesisSupported && (
          <p className="text-yellow-400 text-xs mt-2">
            Text-to-speech not supported in this browser
          </p>
        )}
      </div>

      {/* Conversation */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && !interimTranscript && (
          <div className="flex items-center justify-center h-full text-white/40 text-sm">
            Start speaking to begin the conversation
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${
              msg.speaker === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[75%] ${getMessageStyle(msg)} border rounded-lg px-3 py-2`}
            >
              {/* Speaker label and timestamp */}
              <div className="flex items-center justify-between gap-3 mb-1">
                <span
                  className={`text-xs font-medium ${
                    msg.speaker === "user"
                      ? "text-blue-300"
                      : msg.type === "filler"
                        ? "text-yellow-300"
                        : "text-purple-300"
                  }`}
                >
                  {msg.speaker === "user"
                    ? "You"
                    : msg.type === "filler"
                      ? "AI (processing...)"
                      : "AI Assistant"}
                </span>
                <span className="text-xs text-white/40">
                  {formatTime(msg.timestamp)}
                </span>
              </div>

              {/* Message text */}
              <div
                className={`text-sm text-white/90 leading-relaxed ${
                  msg.type === "filler" ? "italic" : ""
                }`}
              >
                {msg.text}
              </div>
            </div>
          </div>
        ))}

        {/* Interim transcription */}
        {interimTranscript && (
          <div className="flex justify-end">
            <div className="max-w-[75%] bg-blue-600/20 border-blue-500/30 border border-dashed rounded-lg px-3 py-2">
              <div className="flex items-center justify-between gap-3 mb-1">
                <span className="text-xs font-medium text-blue-300/70">
                  You (speaking...)
                </span>
              </div>
              <div className="text-sm text-white/60 leading-relaxed italic">
                {interimTranscript}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Controls */}
      <div className="px-3 pb-3 space-y-3">
        {/* Voice Control Bar */}
        <div className="bg-black/20 backdrop-blur-sm rounded-lg border border-white/10 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Waveform visualization */}
            {state === "listening" && (
              <div className="flex items-center gap-[2px] h-5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-[3px] bg-blue-400 rounded-full animate-pulse"
                    style={{
                      animationDelay: `${i * 0.1}s`,
                      height: `${8 + i * 4}px`,
                    }}
                  />
                ))}
              </div>
            )}

            {/* Status text */}
            <span className="text-sm text-white/60">{stateLabels[state]}</span>

            {/* Interim transcript preview */}
            {interimTranscript && (
              <span className="text-sm text-blue-400/70 italic ml-2 max-w-xs truncate">
                "{interimTranscript}"
              </span>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/40">Ctrl+Space</span>

            {/* Stop TTS button */}
            {isTTSSpeaking && (
              <button
                onClick={stopTTS}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors"
              >
                Stop Speaking
              </button>
            )}

            {/* Main button */}
            <button
              onClick={isActive ? stop : start}
              disabled={state === "processing"}
              className={`
                px-6 py-2 rounded-lg text-sm font-medium transition-all
                ${
                  isActive
                    ? "bg-red-500 text-white hover:bg-red-600"
                    : state === "processing"
                      ? "bg-white/10 text-white/40 cursor-wait"
                      : state === "error"
                        ? "bg-yellow-500 text-black hover:bg-yellow-400"
                        : "bg-blue-500 text-white hover:bg-blue-600"
                }
              `}
            >
              {isActive
                ? "Stop"
                : state === "processing"
                  ? "Processing..."
                  : state === "error"
                    ? "Retry"
                    : "Speak"}
            </button>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs font-mono">
            {error}
          </div>
        )}

        {/* Info banner */}
        <div className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-400 text-xs">
          <strong>Layer 1 + Layer 2 Pipeline:</strong> Speech Recognition → AI
          Orchestrator → Text-to-Speech
        </div>
      </div>
    </div>
  );
}
