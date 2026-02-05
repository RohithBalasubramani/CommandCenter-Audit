import os
import uuid as _uuid

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from dataclasses import asdict

_FEEDBACK_API_KEY = os.environ.get("FEEDBACK_API_KEY", "")


class FeedbackThrottle(AnonRateThrottle):
    rate = "20/minute"

from .models import RAGPipeline, RAGQuery, RAGResult
from .serializers import (
    RAGPipelineSerializer,
    RAGQuerySerializer,
    RAGResultSerializer,
)
from .orchestrator import get_orchestrator, Intent, RAGResult as OrchestratorRAGResult


class RAGPipelineViewSet(viewsets.ModelViewSet):
    """
    Layer 2 — RAG Pipeline registry.

    Endpoints:
      GET    /api/layer2/pipelines/           — List all pipelines
      POST   /api/layer2/pipelines/           — Register a new pipeline
      GET    /api/layer2/pipelines/{id}/       — Get pipeline details
      PATCH  /api/layer2/pipelines/{id}/       — Update pipeline (enable/disable)
      DELETE /api/layer2/pipelines/{id}/       — Remove pipeline
    """
    queryset = RAGPipeline.objects.all()
    serializer_class = RAGPipelineSerializer


class RAGQueryViewSet(viewsets.ModelViewSet):
    """
    Layer 2 — RAG query log.

    Endpoints:
      GET    /api/layer2/queries/             — List all queries
      POST   /api/layer2/queries/             — Log a new query
      GET    /api/layer2/queries/{id}/         — Get query with result
    """
    queryset = RAGQuery.objects.select_related("result").all()
    serializer_class = RAGQuerySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        domain = self.request.query_params.get("domain")
        if domain:
            qs = qs.filter(pipeline__domain=domain)
        return qs


@api_view(["POST"])
def industrial_rag_query(request):
    """
    Layer 2B — Industrial RAG endpoint.

    Receives a query from the frontend orchestrator and returns
    domain-specific data from the industrial data sources.

    POST /api/layer2/rag/industrial/
    Body: { "query": "...", "context": {} }
    """
    query_text = request.data.get("query", "")
    # context = request.data.get("context", {})

    # Stub: In production, this would query LoggerDeploy / PostgreSQL
    # for metrics, devices, device_status tables
    return Response(
        {
            "domain": "industrial",
            "raw_data": {
                "message": f"Industrial RAG stub for query: {query_text}",
                "metrics": [],
                "devices": [],
                "alerts": [],
            },
            "status": "stub",
        }
    )


@api_view(["GET"])
def industrial_rag_health(request):
    """
    Health check for Industrial RAG pipeline.

    Returns status and index statistics.
    """
    try:
        from .rag_pipeline import get_rag_pipeline

        pipeline = get_rag_pipeline()
        stats = pipeline.get_stats()

        return Response({
            "status": "ok",
            "domain": "industrial",
            "equipment_count": stats.get("equipment_count", 0),
            "alerts_count": stats.get("alerts_count", 0),
            "maintenance_count": stats.get("maintenance_count", 0),
            "llm_available": stats.get("llm_available", False),
            "llm_model": stats.get("llm_model", "unknown"),
        })
    except Exception as e:
        return Response({
            "status": "error",
            "domain": "industrial",
            "error": str(e),
            "equipment_count": 0,
            "alerts_count": 0,
            "maintenance_count": 0,
            "llm_available": False,
            "llm_model": "unknown",
        })


@api_view(["POST"])
def orchestrate(request):
    """
    Layer 2 Main Orchestration Endpoint.

    Receives transcript from Layer 1, processes through:
    - 2A: Intent parsing
    - 2B: Parallel RAG queries
    - 2C: Response generation + Layout decisions

    POST /api/layer2/orchestrate/
    Body: {
        "transcript": "What's the status of the pumps?",
        "session_id": "uuid",
        "context": {}
    }

    Returns: {
        "voice_response": "3 of 4 pumps running...",
        "filler_text": "Let me check that for you.",
        "layout_json": { "widgets": [...] },
        "context_update": {...},
        "intent": {...},
        "processing_time_ms": 150
    }
    """
    transcript = request.data.get("transcript", "")
    session_id = request.data.get("session_id")
    context = request.data.get("context", {})
    user_id = request.data.get("user_id", "default_user")

    if not transcript:
        return Response(
            {"error": "transcript is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get orchestrator and process
    orchestrator = get_orchestrator()
    result = orchestrator.process_transcript(transcript, context, user_id)

    # Convert dataclasses to dicts for JSON serialization
    response_data = {
        "query_id": result.query_id,  # For RL feedback tracking
        "voice_response": result.voice_response,
        "filler_text": result.filler_text,
        "layout_json": result.layout_json,
        "context_update": result.context_update,
        "intent": {
            "type": result.intent.type,
            "domains": result.intent.domains,
            "entities": result.intent.entities,
            "confidence": result.intent.confidence,
        } if result.intent else None,
        "rag_results": [
            {
                "domain": r.domain,
                "success": r.success,
                "data": r.data,
                "error": r.error,
                "execution_time_ms": r.execution_time_ms,
            }
            for r in result.rag_results
        ],
        "processing_time_ms": result.processing_time_ms,
    }

    return Response(response_data)


@api_view(["POST"])
def get_filler(request):
    """
    Get filler text for Layer 1 to speak while waiting.

    POST /api/layer2/filler/
    Body: { "intent_type": "query", "domains": ["industrial"] }
    """
    intent_type = request.data.get("intent_type", "query")
    domains = request.data.get("domains", ["industrial"])

    orchestrator = get_orchestrator()

    # Create a minimal intent for filler generation
    intent = Intent(
        type=intent_type,
        domains=domains,
        entities={},
        confidence=0.5,
        raw_text="",
    )

    filler = orchestrator._generate_filler(intent)

    return Response({"filler_text": filler})


@api_view(["POST"])
def proactive_trigger(request):
    """
    Get proactive question/trigger for Layer 1.

    Called when system context changes (alerts, shift start, etc.)
    Layer 1 can use this to initiate conversation proactively.

    POST /api/layer2/proactive/
    Body: {
        "system_context": {
            "active_alerts": 2,
            "shift_start": true,
            "anomalies": [...]
        }
    }
    """
    system_context = request.data.get("system_context", {})

    orchestrator = get_orchestrator()
    trigger = orchestrator.get_proactive_trigger(system_context)

    return Response({
        "has_trigger": trigger is not None,
        "trigger_text": trigger,
    })


@api_view(["POST"])
@throttle_classes([FeedbackThrottle])
def submit_feedback(request):
    """
    Submit feedback for continuous RL.

    Called by frontend when user provides explicit feedback.

    POST /api/layer2/feedback/
    Body: {
        "query_id": "uuid-from-response",
        "rating": "up" | "down",
        "interactions": [
            {"widget_index": 0, "action": "expand", "duration_ms": 5000},
            ...
        ],
        "correction": "I meant pump-002"  # Optional correction text
    }
    """
    # Lightweight API key check (skip if FEEDBACK_API_KEY not configured)
    if _FEEDBACK_API_KEY:
        provided_key = request.headers.get("X-Feedback-Key", "")
        if provided_key != _FEEDBACK_API_KEY:
            return Response(
                {"error": "Invalid or missing X-Feedback-Key header"},
                status=status.HTTP_403_FORBIDDEN,
            )

    query_id = request.data.get("query_id")
    rating = request.data.get("rating")
    interactions = request.data.get("interactions", [])
    correction = request.data.get("correction")

    if not query_id:
        return Response(
            {"error": "query_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate query_id is a UUID
    try:
        _uuid.UUID(query_id)
    except (ValueError, TypeError):
        return Response(
            {"error": "query_id must be a valid UUID"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate rating
    if rating is not None and rating not in ("up", "down"):
        return Response(
            {"error": "rating must be 'up' or 'down'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate correction length
    if correction and (not isinstance(correction, str) or len(correction) > 500):
        return Response(
            {"error": "correction must be a string with max 500 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate interactions
    if not isinstance(interactions, list) or len(interactions) > 50:
        return Response(
            {"error": "interactions must be a list with max 50 items"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from rl.continuous import get_rl_system

        rl = get_rl_system()
        success = rl.update_feedback(
            query_id=query_id,
            rating=rating,
            interactions=interactions,
            correction=correction,
        )

        if success:
            # Also persist to WidgetRating for durability
            try:
                from django.utils import timezone
                from feedback.models import WidgetRating

                WidgetRating.objects.create(
                    entry_id=query_id,
                    rating=rating or "up",
                    tags=[],
                    notes=correction or "",
                    rated_at=timezone.now(),
                )
            except Exception as e:
                # Non-critical - RL buffer already updated
                pass

            return Response({"status": "ok", "updated": True})
        else:
            return Response(
                {"status": "not_found", "updated": False},
                status=status.HTTP_404_NOT_FOUND,
            )

    except ImportError:
        return Response(
            {"error": "RL module not available"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def approve_lora_training(request):
    """
    Admin endpoint to approve pending Tier 2 LoRA training.

    POST /api/layer2/approve-training/
    """
    from rl.config import TRAINING_DATA_DIR

    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    approval_file = TRAINING_DATA_DIR / "approve_lora_training"
    approval_file.touch()

    return Response({"status": "approved", "file": str(approval_file)})


@api_view(["GET"])
def rl_status(request):
    """
    Get status of the continuous RL system.

    GET /api/layer2/rl-status/
    """
    try:
        from rl.continuous import get_rl_system

        rl = get_rl_system()
        return Response(rl.get_status())

    except ImportError:
        return Response({
            "running": False,
            "error": "RL module not available",
        })


# ── In-memory trigger queue for webhook & role_change triggers ──────────────
import threading

class _TriggerStore:
    """Thread-safe store for external triggers (webhook, role_change).

    Triggers are pushed via POST /api/layer2/triggers/webhook/ and drained
    on each GET /api/layer2/triggers/ poll.  Max 100 per kind to prevent
    unbounded growth.
    """
    _MAX_PER_KIND = 100

    def __init__(self):
        self._lock = threading.Lock()
        self._queues: dict[str, list[dict]] = {}

    def push(self, kind: str, trigger: dict):
        with self._lock:
            q = self._queues.setdefault(kind, [])
            q.append(trigger)
            if len(q) > self._MAX_PER_KIND:
                q[:] = q[-self._MAX_PER_KIND:]

    def drain(self, kind: str) -> list[dict]:
        with self._lock:
            items = self._queues.pop(kind, [])
        return items

_webhook_trigger_store = _TriggerStore()


@api_view(["GET"])
def system_triggers(request):
    """
    Poll for system triggers (per README blueprint):
      alert_fired, threshold_breach, scheduled_event, role_change, time_of_day, webhook

    GET /api/layer2/triggers/
    Query params:
      since — ISO timestamp (only triggers after this time)

    Returns:
      { "triggers": [...], "timestamp": "..." }
    """
    import time as _time
    from django.utils import timezone

    since_str = request.query_params.get("since")
    now = timezone.now()
    triggers = []

    # --- alert_fired: check for recent unacknowledged alerts ---
    try:
        from industrial.models import Alert
        alert_qs = Alert.objects.filter(acknowledged=False).order_by("-timestamp")
        if since_str:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since_str)
            if since_dt:
                alert_qs = alert_qs.filter(timestamp__gt=since_dt)

        for alert in alert_qs[:5]:
            triggers.append({
                "kind": "alert_fired",
                "source": str(alert.source) if hasattr(alert, "source") else alert.device_name if hasattr(alert, "device_name") else "unknown",
                "message": alert.message if hasattr(alert, "message") else str(alert),
                "timestamp": alert.timestamp.isoformat() if hasattr(alert, "timestamp") else now.isoformat(),
                "payload": {
                    "severity": alert.severity if hasattr(alert, "severity") else "unknown",
                    "alert_id": str(alert.pk),
                },
            })
    except Exception:
        pass  # industrial app may not be migrated

    # --- threshold_breach: check for readings above thresholds ---
    try:
        from industrial.models import SensorReading
        breach_qs = SensorReading.objects.filter(
            is_anomaly=True
        ).order_by("-timestamp")[:3]
        for reading in breach_qs:
            triggers.append({
                "kind": "threshold_breach",
                "source": reading.device_name if hasattr(reading, "device_name") else "sensor",
                "message": f"Threshold breach: {reading.value} {reading.unit}" if hasattr(reading, "value") else "Threshold breach detected",
                "timestamp": reading.timestamp.isoformat() if hasattr(reading, "timestamp") else now.isoformat(),
                "payload": {"reading_id": str(reading.pk)},
            })
    except Exception:
        pass

    # --- scheduled_event: upcoming maintenance within next 24h ---
    try:
        from industrial.models import MaintenanceRecord
        upcoming_qs = MaintenanceRecord.objects.filter(
            scheduled_date__gte=now,
            scheduled_date__lte=now + timezone.timedelta(hours=24),
            completed_at__isnull=True,
        ).order_by("scheduled_date")[:3]
        for maint in upcoming_qs:
            triggers.append({
                "kind": "scheduled_event",
                "source": maint.equipment_name if hasattr(maint, "equipment_name") else "maintenance",
                "message": f"Upcoming: {maint.maintenance_type} maintenance for {maint.equipment_name}",
                "timestamp": maint.scheduled_date.isoformat() if maint.scheduled_date else now.isoformat(),
                "payload": {
                    "record_id": str(maint.pk),
                    "maintenance_type": maint.maintenance_type,
                    "equipment": maint.equipment_name,
                },
            })
    except Exception:
        pass  # industrial app may not have MaintenanceRecord table

    # --- role_change: drain queued role-change triggers ---
    for rc in _webhook_trigger_store.drain("role_change"):
        triggers.append(rc)

    # --- time_of_day: shift-based triggers ---
    hour = now.hour
    if hour == 6:
        triggers.append({
            "kind": "time_of_day",
            "source": "system",
            "message": "Morning shift starting — loading shift overview",
            "timestamp": now.isoformat(),
            "payload": {"shift": "morning"},
        })
    elif hour == 14:
        triggers.append({
            "kind": "time_of_day",
            "source": "system",
            "message": "Afternoon shift starting — loading shift handover",
            "timestamp": now.isoformat(),
            "payload": {"shift": "afternoon"},
        })
    elif hour == 22:
        triggers.append({
            "kind": "time_of_day",
            "source": "system",
            "message": "Night shift starting — loading night monitoring",
            "timestamp": now.isoformat(),
            "payload": {"shift": "night"},
        })

    # --- webhook: drain queued external webhook triggers ---
    for wh in _webhook_trigger_store.drain("webhook"):
        triggers.append(wh)

    return Response({
        "triggers": triggers,
        "timestamp": now.isoformat(),
    })


@api_view(["POST"])
def webhook_trigger(request):
    """
    Accept external webhook triggers (per README blueprint).

    POST /api/layer2/triggers/webhook/
    Body: {
        "kind": "webhook" | "role_change",
        "source": "external-system-name",
        "message": "Human-readable description",
        "payload": { ... optional extra data ... }
    }

    Triggers are queued and returned on the next GET /api/layer2/triggers/ poll.
    """
    from django.utils import timezone

    kind = request.data.get("kind", "webhook")
    if kind not in ("webhook", "role_change"):
        return Response({"error": f"Invalid trigger kind: {kind}. Must be 'webhook' or 'role_change'."}, status=400)

    source = request.data.get("source", "external")
    message = request.data.get("message", "External trigger received")
    payload = request.data.get("payload", {})

    now = timezone.now()
    trigger = {
        "kind": kind,
        "source": source,
        "message": message,
        "timestamp": now.isoformat(),
        "payload": payload,
    }
    _webhook_trigger_store.push(kind, trigger)

    return Response({"status": "queued", "trigger": trigger}, status=201)
