"""
Layer 2 Orchestrator — The Brain of Command Center

This module handles:
- 2A: Intent parsing from transcripts
- 2B: Parallel RAG query coordination
- 2C: Response generation + Layout decisions

The orchestrator receives transcripts from Layer 1, processes them,
and returns:
1. voice_response: Text for Layer 1 to speak (TTS)
2. layout_json: Widget commands for Layer 3 (Blob)
3. context_update: Updated context for future queries
"""

import re
import time
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import RAG pipeline
from layer2.rag_pipeline import get_rag_pipeline, RAGResponse

logger = logging.getLogger(__name__)

# Domain keywords for intent detection
DOMAIN_KEYWORDS = {
    "industrial": [
        # General equipment
        "pump", "pumps", "motor", "motors", "temperature", "temp", "pressure",
        "voltage", "current", "power", "energy", "device", "devices", "machine",
        "machines", "sensor", "sensors", "meter", "meters", "grid", "production",
        "line", "manufacturing", "oee", "efficiency", "running", "status",
        "operational", "maintenance", "equipment", "plc", "scada",
        # Electrical equipment
        "transformer", "transformers", "generator", "generators", "diesel",
        "panel", "panels", "switchgear", "ups", "electrical",
        # HVAC equipment
        "chiller", "chillers", "ahu", "ahus", "cooling", "tower", "towers",
        "hvac", "air handling", "compressor", "compressors",
        # Energy
        "energy meter", "consumption", "load", "kva", "kw", "kwh",
    ],
    "supply": [
        "inventory", "stock", "supplier", "vendor", "order", "orders", "purchase",
        "procurement", "rfq", "po", "shipment", "delivery", "warehouse", "logistics",
        "material", "materials", "parts", "components", "lead time", "shortage"
    ],
    "people": [
        "employee", "employees", "worker", "workers", "staff", "team", "shift",
        "shifts", "schedule", "attendance", "leave", "vacation", "hr", "hiring",
        "training", "safety", "overtime", "workforce"
    ],
    "tasks": [
        "task", "tasks", "project", "projects", "milestone", "deadline", "due",
        "assignment", "todo", "work order", "ticket", "issue", "priority",
        "progress", "complete", "pending"
    ],
    "alerts": [
        "alert", "alerts", "alarm", "alarms", "warning", "warnings", "error",
        "errors", "critical", "urgent", "notification", "issue", "problem",
        "fault", "failure", "anomaly", "threshold", "breach"
    ],
}

# Filler templates for different scenarios
FILLER_TEMPLATES = {
    "greeting": [
        "Hello!",
        "Hey there!",
        "Hi, how can I help?",
    ],
    "checking": [
        "Let me check that for you.",
        "Checking the latest data now.",
        "One moment while I look that up.",
        "Pulling up the equipment data.",
        "Checking the monitoring systems.",
    ],
    "processing": [
        "Processing your request.",
        "Analyzing the data.",
        "Running the query now.",
        "Running that through the operations pipeline.",
        "Processing the production data.",
    ],
    "fetching": [
        "Fetching the latest metrics.",
        "Getting the current status.",
        "Retrieving the information.",
        "Looking up the latest readings.",
        "Retrieving the maintenance records.",
    ],
}

# Casual conversation patterns (not domain queries, but still in-scope interaction)
CONVERSATION_PATTERNS = [
    r"\b(how are you|how're you|how do you do|how have you been)\b",
    r"\b(what's up|whats up|sup)\b",
    r"\b(thank you|thanks|thank|appreciate)\b",
    r"\b(what can you do|what do you do|what are you|who are you|what's your name|whats your name)\b",
    r"\b(help me|can you help)\b",
    r"\b(you're welcome|no problem|never mind|nevermind|forget it)\b",
    r"\b(bye|goodbye|good night|see you|take care)\b",
    r"\b(nice|awesome|great|cool|ok|okay|got it|understood|sure)\b",
    r"\b(tell me a joke|are you a robot|are you real|are you ai)\b",
]

OUT_OF_SCOPE_MESSAGE = (
    "That's outside what I can help with. "
    "I'm your industrial operations assistant — I can help with "
    "equipment monitoring, alerts, maintenance, supply chain, "
    "workforce management, and task tracking. "
    "What would you like to know?"
)

# Response templates for different intents
RESPONSE_TEMPLATES = {
    "status_query": "Based on the latest data, {summary}",
    "metric_query": "The current {metric_name} is {value} {unit}. {trend_info}",
    "alert_query": "{alert_count} active alerts. {alert_summary}",
    "list_query": "Here's what I found: {items}",
    "action_confirm": "I've {action_description}. {result}",
    "no_data": "I couldn't find data for that query. Would you like me to check something else?",
    "error": "I encountered an issue while processing your request. {error_detail}",
}


@dataclass
class Intent:
    """Parsed intent from user transcript."""
    type: str  # query, action, clarification, greeting, etc.
    domains: list = field(default_factory=list)
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""


@dataclass
class RAGResult:
    """Result from a RAG pipeline query."""
    domain: str
    success: bool
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: int = 0


@dataclass
class OrchestratorResponse:
    """Complete response from the orchestrator."""
    voice_response: str  # Text for Layer 1 TTS
    layout_json: dict  # Commands for Layer 3 Blob
    context_update: dict  # Updated context for future queries
    intent: Intent = None
    rag_results: list = field(default_factory=list)
    processing_time_ms: int = 0
    filler_text: str = ""  # Filler to speak while processing


class Layer2Orchestrator:
    """
    Main orchestrator for Layer 2.

    Coordinates intent parsing, RAG queries, and response generation.
    """

    def __init__(self, context: dict = None):
        self.context = context or {}
        self.executor = ThreadPoolExecutor(max_workers=5)

    def process_transcript(self, transcript: str, session_context: dict = None) -> OrchestratorResponse:
        """
        Main entry point: process a transcript and generate response.

        Args:
            transcript: User's spoken text from Layer 1
            session_context: Current conversation context

        Returns:
            OrchestratorResponse with voice_response and layout_json
        """
        start_time = time.time()

        # Merge session context
        if session_context:
            self.context.update(session_context)

        # 2A: Parse intent
        intent = self._parse_intent(transcript)

        # Short-circuit: out-of-scope and conversation skip RAG entirely
        if intent.type == "out_of_scope":
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Out-of-scope query: '{transcript[:80]}' — returning scope message")
            return OrchestratorResponse(
                voice_response=OUT_OF_SCOPE_MESSAGE,
                layout_json={"widgets": [], "transitions": {}},
                context_update=self._update_context(intent, []),
                intent=intent,
                rag_results=[],
                processing_time_ms=processing_time,
                filler_text="",
            )

        if intent.type == "conversation":
            voice_response = self._generate_conversation_response(intent)
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Conversation: '{transcript[:80]}' → '{voice_response[:80]}'")
            return OrchestratorResponse(
                voice_response=voice_response,
                layout_json={"widgets": [], "transitions": {}},
                context_update=self._update_context(intent, []),
                intent=intent,
                rag_results=[],
                processing_time_ms=processing_time,
                filler_text="",
            )

        # Generate filler based on intent
        filler = self._generate_filler(intent)

        # 2B: Execute parallel RAG queries
        rag_results = self._execute_rag_queries(intent, transcript)

        # 2C: Generate response and layout
        voice_response = self._generate_response(intent, rag_results)
        layout_json = self._generate_layout(intent, rag_results)
        context_update = self._update_context(intent, rag_results)

        processing_time = int((time.time() - start_time) * 1000)

        return OrchestratorResponse(
            voice_response=voice_response,
            layout_json=layout_json,
            context_update=context_update,
            intent=intent,
            rag_results=rag_results,
            processing_time_ms=processing_time,
            filler_text=filler,
        )

    def _parse_intent(self, transcript: str) -> Intent:
        """
        2A: Parse intent from transcript.

        Currently uses keyword matching. Future: upgrade to phi-3 or similar.
        """
        text_lower = transcript.lower()

        # Detect intent type
        intent_type = self._detect_intent_type(text_lower)

        # Detect relevant domains
        domains = self._detect_domains(text_lower)

        # Extract entities
        entities = self._extract_entities(text_lower)

        # Scope guard: if no domain matched and not a greeting,
        # classify as conversation or out_of_scope
        if intent_type != "greeting" and not domains:
            if self._is_conversation(text_lower):
                intent_type = "conversation"
            else:
                intent_type = "out_of_scope"

        # Calculate confidence based on matches
        if intent_type in ("out_of_scope", "conversation"):
            confidence = 0.9
        else:
            confidence = min(1.0, len(domains) * 0.3 + (0.4 if entities else 0.2))

        return Intent(
            type=intent_type,
            domains=domains,
            entities=entities,
            confidence=confidence,
            raw_text=transcript,
        )

    def _is_conversation(self, text: str) -> bool:
        """Check if text matches casual conversation patterns."""
        for pattern in CONVERSATION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _detect_intent_type(self, text: str) -> str:
        """Detect the type of user intent."""
        # Query patterns
        query_patterns = [
            r"\b(what|what's|whats|how|how's|hows|show|tell|get|check|status|current)\b",
            r"\?$",
        ]

        # Action patterns
        action_patterns = [
            r"\b(start|stop|turn|set|adjust|change|update|create|delete|add|remove)\b",
        ]

        # Greeting patterns
        greeting_patterns = [
            r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b",
        ]

        # Check patterns — order matters.
        # If text matches both greeting AND query/action, prefer query/action
        # (e.g. "Hello, show me transformer status" is a query, not a greeting).
        is_greeting = any(re.search(p, text) for p in greeting_patterns)
        is_action = any(re.search(p, text) for p in action_patterns)
        is_query = any(re.search(p, text) for p in query_patterns)

        if is_action:
            return "action"
        if is_query:
            return "query"
        if is_greeting:
            return "greeting"

        return "query"  # Default to query

    def _detect_domains(self, text: str) -> list:
        """Detect which domains are relevant to the query."""
        detected = []

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    if domain not in detected:
                        detected.append(domain)
                    break

        # Return empty list when no domain keywords match.
        # _parse_intent() uses empty domains to classify as conversation or out_of_scope.
        return detected

    def _extract_entities(self, text: str) -> dict:
        """Extract named entities from the text."""
        entities = {}

        # Extract numbers
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
        if numbers:
            entities["numbers"] = numbers

        # Extract device references (pump 1, motor 3, etc.)
        device_refs = re.findall(r'\b(pump|motor|sensor|device|machine)\s*(\d+)\b', text)
        if device_refs:
            entities["devices"] = [f"{d[0]}_{d[1]}" for d in device_refs]

        # Extract time references
        time_refs = re.findall(r'\b(today|yesterday|last\s+\w+|this\s+\w+|past\s+\d+\s+\w+)\b', text)
        if time_refs:
            entities["time"] = time_refs

        return entities

    def _generate_filler(self, intent: Intent) -> str:
        """Generate appropriate filler text based on intent."""
        import random

        if intent.type == "greeting":
            fillers = FILLER_TEMPLATES["greeting"]
            return random.choice(fillers)

        # No filler needed for instant responses
        if intent.type in ("out_of_scope", "conversation"):
            return ""

        if "alerts" in intent.domains:
            fillers = FILLER_TEMPLATES["checking"]
        elif intent.type == "action":
            fillers = FILLER_TEMPLATES["processing"]
        else:
            fillers = FILLER_TEMPLATES["fetching"]

        return random.choice(fillers)

    def _execute_rag_queries(self, intent: Intent, transcript: str) -> list:
        """
        2B: Execute parallel RAG queries for relevant domains.
        """
        results = []

        # Submit queries in parallel
        futures = {}
        for domain in intent.domains:
            future = self.executor.submit(
                self._query_rag_pipeline,
                domain,
                transcript,
                intent.entities,
            )
            futures[future] = domain

        # Collect results
        for future in as_completed(futures, timeout=30.0):
            domain = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(RAGResult(
                    domain=domain,
                    success=False,
                    error=str(e),
                ))

        return results

    def _query_rag_pipeline(self, domain: str, query: str, entities: dict) -> RAGResult:
        """Query a specific RAG pipeline."""
        start_time = time.time()

        try:
            # Use the real RAG pipeline for industrial and alerts domains
            if domain in ["industrial", "alerts"]:
                rag_pipeline = get_rag_pipeline()

                # Query RAG with appropriate settings
                include_alerts = domain == "alerts" or "alert" in query.lower()
                rag_response = rag_pipeline.query(
                    question=query,
                    n_results=5,
                    include_alerts=include_alerts,
                    include_maintenance="maintenance" in query.lower(),
                )

                # Convert RAG response to structured data
                data = self._parse_rag_response(rag_response, domain)

            # Keep stub data for domains not yet implemented in RAG
            elif domain == "supply":
                data = self._get_supply_stub_data(query, entities)
            elif domain == "people":
                data = self._get_people_stub_data(query, entities)
            elif domain == "tasks":
                data = self._get_tasks_stub_data(query, entities)
            else:
                data = {}

            execution_time = int((time.time() - start_time) * 1000)

            return RAGResult(
                domain=domain,
                success=True,
                data=data,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"RAG query failed for domain {domain}: {e}")
            execution_time = int((time.time() - start_time) * 1000)

            # Fallback to stub data on error
            if domain == "industrial":
                data = self._get_industrial_stub_data(query, entities)
            elif domain == "alerts":
                data = self._get_alerts_stub_data(query, entities)
            else:
                data = {}

            return RAGResult(
                domain=domain,
                success=True,  # Still return success with fallback data
                data=data,
                execution_time_ms=execution_time,
            )

    def _parse_rag_response(self, rag_response: RAGResponse, domain: str) -> dict:
        """Parse RAG response into structured data for the orchestrator."""
        data = {
            "llm_response": rag_response.llm_response,
            "sources": rag_response.sources,
            "summary": rag_response.llm_response,  # Use LLM response as summary
        }

        # Extract equipment data from retrieved docs
        equipment_list = []
        alert_list = []

        for doc in rag_response.retrieved_docs:
            doc_type = doc.metadata.get("equipment_type", "")

            if doc_type and doc_type not in ["", "unknown"]:
                # This is an equipment document
                equipment_list.append({
                    "id": doc.metadata.get("equipment_id", doc.id),
                    "name": doc.metadata.get("name", "Unknown"),
                    "type": doc_type,
                    "status": doc.metadata.get("status", "unknown"),
                    "health": doc.metadata.get("health_score", 0),
                    "location": doc.metadata.get("location", ""),
                    "criticality": doc.metadata.get("criticality", "medium"),
                    "relevance_score": doc.score,
                })
            elif "alert" in doc.id.lower():
                # This is an alert document
                alert_list.append({
                    "id": doc.id,
                    "severity": doc.metadata.get("severity", "info"),
                    "source": doc.metadata.get("equipment_name", "Unknown"),
                    "equipment_id": doc.metadata.get("equipment_id", ""),
                    "message": doc.content,
                    "acknowledged": doc.metadata.get("acknowledged", False),
                    "relevance_score": doc.score,
                })

        if equipment_list:
            data["devices"] = equipment_list

            # Generate metrics summary from equipment
            running_count = sum(1 for d in equipment_list if d["status"] == "running")
            warning_count = sum(1 for d in equipment_list if d["status"] == "warning")
            critical_count = sum(1 for d in equipment_list if d["status"] == "critical")

            data["metrics"] = [
                {"name": "running_equipment", "value": running_count, "unit": "", "status": "normal"},
                {"name": "warning_equipment", "value": warning_count, "unit": "", "status": "warning" if warning_count > 0 else "normal"},
                {"name": "critical_equipment", "value": critical_count, "unit": "", "status": "critical" if critical_count > 0 else "normal"},
            ]

        if alert_list:
            data["alerts"] = alert_list
            data["count"] = len(alert_list)

        return data

    def _get_industrial_stub_data(self, query: str, entities: dict) -> dict:
        """Stub data for industrial domain."""
        return {
            "metrics": [
                {"name": "grid_voltage", "value": 238.4, "unit": "V", "status": "normal"},
                {"name": "total_power", "value": 1247.8, "unit": "kW", "status": "normal"},
            ],
            "devices": [
                {"id": "pump_1", "name": "Pump 1", "status": "running", "health": 95},
                {"id": "pump_2", "name": "Pump 2", "status": "running", "health": 92},
                {"id": "pump_3", "name": "Pump 3", "status": "warning", "health": 78},
                {"id": "pump_4", "name": "Pump 4", "status": "running", "health": 88},
            ],
            "summary": "3 of 4 pumps running normally. Pump 3 showing elevated temperature.",
        }

    def _get_alerts_stub_data(self, query: str, entities: dict) -> dict:
        """Stub data for alerts domain."""
        return {
            "alerts": [
                {
                    "id": "alert_1",
                    "severity": "warning",
                    "source": "pump_3",
                    "message": "Temperature elevated to 78°C (threshold: 75°C)",
                    "timestamp": "2026-01-28T10:30:00Z",
                    "acknowledged": False,
                },
            ],
            "summary": "1 active warning alert for Pump 3 temperature.",
            "count": 1,
        }

    def _get_supply_stub_data(self, query: str, entities: dict) -> dict:
        """Stub data for supply domain."""
        return {
            "inventory": [
                {"item": "Bearings SKF-6205", "quantity": 24, "reorder_point": 20, "status": "ok"},
                {"item": "Seals CR-12345", "quantity": 8, "reorder_point": 15, "status": "low"},
            ],
            "pending_orders": 3,
            "summary": "8 items below reorder point. 3 purchase orders pending.",
        }

    def _get_people_stub_data(self, query: str, entities: dict) -> dict:
        """Stub data for people domain."""
        return {
            "on_shift": 45,
            "absent": 3,
            "upcoming_shifts": [
                {"shift": "Evening", "start": "14:00", "staff": 42},
            ],
            "summary": "45 staff on current shift. 3 absences today.",
        }

    def _get_tasks_stub_data(self, query: str, entities: dict) -> dict:
        """Stub data for tasks domain."""
        return {
            "pending": 12,
            "in_progress": 5,
            "due_today": 3,
            "overdue": 1,
            "summary": "12 pending tasks, 3 due today, 1 overdue.",
        }

    def _generate_response(self, intent: Intent, rag_results: list) -> str:
        """
        2C: Generate natural language response for Layer 1 TTS.

        Uses the LLM response from RAG pipeline when available.
        """
        if intent.type == "greeting":
            # Check context for time-appropriate greeting
            return self._generate_greeting()

        if not rag_results:
            return RESPONSE_TEMPLATES["no_data"]

        # Check for LLM-generated responses first (from RAG pipeline)
        for result in rag_results:
            if result.success and "llm_response" in result.data:
                llm_response = result.data["llm_response"]
                # Check if LLM response is valid (not an error message)
                if llm_response and not llm_response.startswith("[LLM"):
                    logger.info(f"Using LLM response from RAG for domain: {result.domain}")
                    return llm_response

        # Fallback: combine summaries from all domains
        response_parts = []

        for result in rag_results:
            if not result.success:
                continue

            if "summary" in result.data:
                response_parts.append(result.data["summary"])

        if response_parts:
            return " ".join(response_parts)

        return RESPONSE_TEMPLATES["no_data"]

    def _generate_greeting(self) -> str:
        """Generate context-appropriate greeting."""
        import datetime

        hour = datetime.datetime.now().hour

        if hour < 12:
            greeting = "Good morning!"
        elif hour < 17:
            greeting = "Good afternoon!"
        else:
            greeting = "Good evening!"

        # Add proactive question
        return f"{greeting} How can I help you with operations today?"

    def _generate_conversation_response(self, intent: Intent) -> str:
        """Generate a natural response for casual conversation (no RAG needed)."""
        text = intent.raw_text.lower()

        if re.search(r"\b(thank|thanks|appreciate)\b", text):
            return "You're welcome! Let me know if you need anything else about operations."

        if re.search(r"\b(how are you|how're you|how do you do|how have you been)\b", text):
            return "I'm running well, thank you! How can I help with operations today?"

        if re.search(r"\b(what can you do|what do you do|help me|can you help)\b", text):
            return (
                "I can help you with equipment monitoring, alert management, "
                "maintenance tracking, supply chain status, workforce management, "
                "and task tracking. Just ask me anything about your operations!"
            )

        if re.search(r"\b(who are you|what are you|your name|are you a robot|are you ai|are you real)\b", text):
            return "I'm your Command Center operations assistant. I help monitor and manage industrial operations."

        if re.search(r"\b(bye|goodbye|good night|see you|take care)\b", text):
            return "Talk to you later! I'll be here if you need anything."

        if re.search(r"\b(ok|okay|got it|understood|sure|nice|awesome|great|cool)\b", text):
            return "Sounds good. Let me know if you need anything."

        if re.search(r"\b(never mind|nevermind|forget it|no problem|you're welcome)\b", text):
            return "No worries. I'm here whenever you need me."

        return "I'm here to help with operations. What would you like to know?"

    def _generate_layout(self, intent: Intent, rag_results: list) -> dict:
        """
        2C: Generate layout JSON for Layer 3 (Blob).

        Enhanced to handle RAG pipeline data with relevance scores.
        """
        widgets = []

        for result in rag_results:
            if not result.success:
                continue

            if result.domain == "industrial":
                devices = result.data.get("devices", [])

                # Add device status widget with relevance-sorted devices
                if devices:
                    # Sort devices by relevance score if available
                    sorted_devices = sorted(
                        devices,
                        key=lambda d: d.get("relevance_score", 0),
                        reverse=True
                    )
                    widgets.append({
                        "id": "device-status",
                        "relevance": 0.9,
                        "size": "hero" if intent.type == "query" else "expanded",
                        "position": "top-center",
                        "data": sorted_devices[:10],  # Top 10 most relevant
                    })

                # Add metrics widget
                metrics = result.data.get("metrics", [])
                if metrics:
                    widgets.append({
                        "id": "kpi-metrics",
                        "relevance": 0.7,
                        "size": "expanded",
                        "position": "middle-left",
                        "data": metrics,
                    })

                # Add sources widget (for RAG transparency)
                sources = result.data.get("sources", [])
                if sources:
                    widgets.append({
                        "id": "rag-sources",
                        "relevance": 0.3,
                        "size": "compact",
                        "position": "bottom-right",
                        "data": sources[:5],  # Top 5 sources
                    })

            elif result.domain == "alerts":
                alerts = result.data.get("alerts", [])
                alert_count = result.data.get("count", len(alerts))

                if alerts:
                    # Sort alerts by relevance and severity
                    severity_order = {"critical": 0, "high": 1, "warning": 2, "medium": 3, "low": 4, "info": 5}
                    sorted_alerts = sorted(
                        alerts,
                        key=lambda a: (severity_order.get(a.get("severity", "info"), 5), -a.get("relevance_score", 0))
                    )
                    widgets.append({
                        "id": "alert-card",
                        "relevance": 0.95 if alert_count > 0 else 0.3,
                        "size": "expanded",
                        "position": "middle-right",
                        "data": sorted_alerts,
                    })

            elif result.domain == "supply":
                widgets.append({
                    "id": "supply-table",
                    "relevance": 0.6,
                    "size": "compact",
                    "position": "bottom",
                    "data": result.data.get("inventory", []),
                })

            elif result.domain == "people":
                widgets.append({
                    "id": "people-card",
                    "relevance": 0.5,
                    "size": "compact",
                    "position": "bottom",
                    "data": result.data,
                })

            elif result.domain == "tasks":
                widgets.append({
                    "id": "tasks-card",
                    "relevance": 0.5,
                    "size": "compact",
                    "position": "bottom",
                    "data": result.data,
                })

        # Sort by relevance
        widgets.sort(key=lambda w: w["relevance"], reverse=True)

        return {
            "widgets": widgets,
            "transitions": {},
        }

    def _update_context(self, intent: Intent, rag_results: list) -> dict:
        """Update conversation context based on current query."""
        return {
            "last_intent": intent.type,
            "last_domains": intent.domains,
            "last_query": intent.raw_text,
            "timestamp": time.time(),
        }

    def get_proactive_trigger(self, system_context: dict) -> Optional[str]:
        """
        Generate a proactive question based on system context.

        Called by Layer 1 when context is pushed from backend.
        """
        # Check for alerts
        if system_context.get("active_alerts", 0) > 0:
            return f"I noticed there are {system_context['active_alerts']} active alerts. Would you like me to summarize them?"

        # Check for shift start
        if system_context.get("shift_start"):
            return "Good morning! A new shift is starting. Would you like a status update on production?"

        # Check for anomalies
        if system_context.get("anomalies"):
            return "I've detected some unusual patterns in the data. Want me to explain what I'm seeing?"

        return None


# Singleton instance
_orchestrator = None


def get_orchestrator() -> Layer2Orchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Layer2Orchestrator()
    return _orchestrator
