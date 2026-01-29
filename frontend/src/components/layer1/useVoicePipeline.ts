"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSpeechRecognition } from "./useSpeechRecognition";
import { useSpeechSynthesis } from "./useSpeechSynthesis";
import {
  getLayer2Service,
  Layer2Response,
  Layer2LayoutJSON,
} from "@/lib/layer2";
import { commandCenterBus } from "@/lib/events";

export type VoicePipelineState =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "error";

interface UseVoicePipelineReturn {
  // State
  state: VoicePipelineState;
  isActive: boolean;
  error: string | null;

  // Controls
  start: () => void;
  stop: () => void;

  // Transcripts
  userTranscript: string;
  interimTranscript: string;
  aiResponse: string;

  // Conversation history
  messages: ConversationMessage[];

  // TTS control
  isTTSSpeaking: boolean;
  stopTTS: () => void;

  // Support flags
  isSpeechRecognitionSupported: boolean;
  isSpeechSynthesisSupported: boolean;
}

export interface ConversationMessage {
  id: string;
  speaker: "user" | "ai" | "system";
  text: string;
  timestamp: number;
  type?: "transcript" | "filler" | "response";
}

/**
 * useVoicePipeline — Main integration hook for voice-driven AI interaction.
 *
 * This hook orchestrates:
 * - Layer 1: Speech Recognition (STT) for user input
 * - Layer 2: AI Orchestrator for intelligent responses
 * - TTS: Speech Synthesis for AI voice output
 * - Layer 3: Layout commands for Blob (via event bus)
 *
 * Flow:
 * 1. User speaks → STT transcribes
 * 2. Transcript → Layer 2 orchestrator
 * 3. Filler spoken immediately while processing
 * 4. Response received → TTS speaks it
 * 5. Layout JSON → emitted to Blob via event bus
 */
export function useVoicePipeline(): UseVoicePipelineReturn {
  const [state, setState] = useState<VoicePipelineState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [aiResponse, setAiResponse] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  // Refs for tracking
  const isProcessingRef = useRef(false);
  const lastTranscriptRef = useRef("");
  const sessionIdRef = useRef<string | null>(null);
  const messageIdRef = useRef(0);

  // Speech Recognition (STT)
  const {
    transcript: userTranscript,
    interimTranscript,
    isListening,
    start: startSTT,
    stop: stopSTT,
    isSupported: isSpeechRecognitionSupported,
  } = useSpeechRecognition();

  // Speech Synthesis (TTS)
  const {
    speak,
    stop: stopTTS,
    isSpeaking: isTTSSpeaking,
    isSupported: isSpeechSynthesisSupported,
  } = useSpeechSynthesis();

  // Layer 2 Service
  const layer2Service = getLayer2Service();

  // Generate session ID on mount
  useEffect(() => {
    sessionIdRef.current = `session-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    layer2Service.setSessionId(sessionIdRef.current);
  }, [layer2Service]);

  // Add message to conversation
  const addMessage = useCallback(
    (
      speaker: ConversationMessage["speaker"],
      text: string,
      type: ConversationMessage["type"] = "transcript"
    ) => {
      const message: ConversationMessage = {
        id: `msg-${++messageIdRef.current}-${Date.now()}`,
        speaker,
        text,
        timestamp: Date.now(),
        type,
      };
      setMessages((prev) => [...prev, message]);
      return message;
    },
    []
  );

  // Handle filler from Layer 2
  const handleFiller = useCallback(
    (fillerText: string) => {
      if (!fillerText) return;

      console.info("[VoicePipeline] Speaking filler:", fillerText);
      addMessage("ai", fillerText, "filler");

      speak(fillerText, {
        rate: 1.1, // Slightly faster for fillers
        onEnd: () => {
          console.info("[VoicePipeline] Filler finished");
        },
      });
    },
    [speak, addMessage]
  );

  // Handle response from Layer 2
  const handleResponse = useCallback(
    (response: Layer2Response) => {
      console.info("[VoicePipeline] Received response:", response);

      const voiceResponse = response.voice_response;
      setAiResponse(voiceResponse);
      addMessage("ai", voiceResponse, "response");

      // Wait a moment if TTS is still speaking filler
      const speakResponse = () => {
        setState("speaking");
        speak(voiceResponse, {
          rate: 1.0,
          onEnd: () => {
            console.info("[VoicePipeline] Response finished");
            setState(isListening ? "listening" : "idle");
            isProcessingRef.current = false;
          },
          onError: () => {
            setState(isListening ? "listening" : "idle");
            isProcessingRef.current = false;
          },
        });
      };

      // Small delay to let filler finish
      setTimeout(speakResponse, 100);
    },
    [speak, addMessage, isListening]
  );

  // Handle layout updates from Layer 2
  const handleLayout = useCallback((layout: Layer2LayoutJSON) => {
    console.info("[VoicePipeline] Layout update:", layout);

    // Emit to event bus for Blob (Layer 3)
    commandCenterBus.emit({
      type: "LAYOUT_UPDATE",
      layout: layout as any,
    });
  }, []);

  // Set up Layer 2 callbacks
  useEffect(() => {
    layer2Service.onFiller(handleFiller);
    layer2Service.onResponse(handleResponse);
    layer2Service.onLayout(handleLayout);
  }, [layer2Service, handleFiller, handleResponse, handleLayout]);

  // Process transcript when user finishes speaking
  useEffect(() => {
    // Only process when we have new finalized transcript
    if (
      !userTranscript ||
      userTranscript === lastTranscriptRef.current ||
      isProcessingRef.current
    ) {
      return;
    }

    // Get the new part of the transcript
    const newText = userTranscript.slice(lastTranscriptRef.current.length).trim();
    if (!newText) {
      lastTranscriptRef.current = userTranscript;
      return;
    }

    console.info("[VoicePipeline] New transcript:", newText);
    lastTranscriptRef.current = userTranscript;

    // Add user message to conversation
    addMessage("user", newText, "transcript");

    // Process through Layer 2
    isProcessingRef.current = true;
    setState("processing");

    layer2Service
      .processTranscript(newText)
      .catch((err) => {
        console.error("[VoicePipeline] Layer 2 error:", err);
        setError(err.message || "Failed to process");

        // Speak error message
        speak("I'm sorry, I encountered an error processing your request.", {
          onEnd: () => {
            setState(isListening ? "listening" : "idle");
            isProcessingRef.current = false;
          },
        });
      });
  }, [userTranscript, layer2Service, addMessage, speak, isListening]);

  // Update state based on listening status
  useEffect(() => {
    if (isListening && !isProcessingRef.current && !isTTSSpeaking) {
      setState("listening");
    }
  }, [isListening, isTTSSpeaking]);

  // Start the voice pipeline
  const start = useCallback(() => {
    console.info("[VoicePipeline] Starting...");
    setError(null);
    lastTranscriptRef.current = "";

    if (isSpeechRecognitionSupported) {
      startSTT();
      setState("listening");

      // Emit event
      commandCenterBus.emit({ type: "VOICE_INPUT_START" });
    } else {
      setError("Speech recognition not supported");
      setState("error");
    }
  }, [isSpeechRecognitionSupported, startSTT]);

  // Stop the voice pipeline
  const stop = useCallback(() => {
    console.info("[VoicePipeline] Stopping...");

    stopSTT();
    stopTTS();
    isProcessingRef.current = false;
    setState("idle");

    // Emit event
    commandCenterBus.emit({ type: "VOICE_INPUT_STOP" });
  }, [stopSTT, stopTTS]);

  return {
    state,
    isActive: state !== "idle" && state !== "error",
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
  };
}
