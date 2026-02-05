from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RAGPipelineViewSet,
    RAGQueryViewSet,
    industrial_rag_query,
    industrial_rag_health,
    orchestrate,
    get_filler,
    proactive_trigger,
    submit_feedback,
    approve_lora_training,
    rl_status,
    system_triggers,
    webhook_trigger,
)

router = DefaultRouter()
router.register(r"pipelines", RAGPipelineViewSet, basename="rag-pipeline")
router.register(r"queries", RAGQueryViewSet, basename="rag-query")

urlpatterns = [
    path("", include(router.urls)),
    # Main orchestration endpoint (Layer 2 brain)
    path("orchestrate/", orchestrate, name="layer2-orchestrate"),
    path("filler/", get_filler, name="layer2-filler"),
    path("proactive/", proactive_trigger, name="layer2-proactive"),
    # Continuous RL endpoints
    path("feedback/", submit_feedback, name="layer2-feedback"),
    path("approve-training/", approve_lora_training, name="layer2-approve-training"),
    path("rl-status/", rl_status, name="layer2-rl-status"),
    # RAG pipeline endpoints
    path("rag/industrial/", industrial_rag_query, name="industrial-rag-query"),
    path("rag/industrial/health/", industrial_rag_health, name="industrial-rag-health"),
    # System triggers (alert_fired, threshold_breach, scheduled_event, time_of_day, etc.)
    path("triggers/", system_triggers, name="layer2-triggers"),
    # External webhook/role_change trigger intake
    path("triggers/webhook/", webhook_trigger, name="layer2-webhook-trigger"),
]
