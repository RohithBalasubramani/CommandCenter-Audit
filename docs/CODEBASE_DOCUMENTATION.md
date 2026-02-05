# Command Center - Complete Codebase Documentation

**A Line-by-Line Guide to Understanding Every File**

This document explains every file in the Command Center codebase in simple, everyday language. Think of Command Center as a smart assistant for factory workers - they can talk to it, ask questions about their equipment, and see visual dashboards that answer their questions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [How the System Works](#how-the-system-works)
3. [Backend Files](#backend-files)
   - [Django Configuration](#django-configuration) — settings.py, urls.py, wsgi.py, asgi.py, manage.py
   - [Layer 1 - Voice Input/Output](#layer-1---voice-inputoutput) — models, views, admin, apps, serializers, urls, tests
   - [Layer 2 - The AI Brain](#layer-2---the-ai-brain) — models, orchestrator, intent_parser, widget_selector, widget_catalog, rag_pipeline
   - [Pipeline Optimization](#pipeline-optimization) — data_prefetcher, parallel_llm, pipeline_executor
   - [Data Quality & Validation](#data-quality--validation) — dimensions, widget_normalizer, widget_schemas, data_collector, user_memory
   - [Reconciliation System](#reconciliation-system) — types, reconciler, pipeline
   - [Reconciliation Sub-modules](#reconciliation-sub-modules) — errors, rewriter, resolver, prompts, normalizer, validator_integration, audit, tests
   - [Speech-to-Text Server](#speech-to-text-server) — stt/server.py
   - [Reinforcement Learning Details](#reinforcement-learning-details) — config, trainer
   - [Layer 2 Supporting Files](#backendlayer2adminpy) — admin, apps, serializers, urls, views, fixture_selector, llm_fixture_selector, reconciler, audit_tests, tests
   - [Management Commands](#management-commands) — populate_industrial_db, generate_rich_data, index_rag, train_dpo, export_model, evaluate_model
   - [Additional RL Files](#additional-reinforcement-learning-files) — background_trainer, dataset_builder, export, e2e_test, test_continuous, tests
   - [Benchmarks](#benchmarks) — benchmark_suite
   - [Django Core Files](#django-core-files) — manage.py, asgi.py
   - [Actions Module](#actions-module) — models, handlers, admin, apps, urls, views
   - [Feedback Module](#feedback-module) — models, views, signals, admin, apps, serializers, urls, tests
   - [Industrial Module](#industrial-module) — models, admin, apps
   - [Reinforcement Learning](#reinforcement-learning) — continuous, online_learner, data_formatter, experience_buffer, reward_signals
4. [Frontend Files](#frontend-files)
   - [Library Utilities](#library-utilities) — events.ts, config.ts, layer2/client.ts, layer2/index.ts, personaplex (protocol, decoder, persona)
   - [Layer 2 Frontend Components](#layer-2-frontend-components) — types.ts, orchestrator.ts, pipelines/industrial.ts
   - [Spot Component](#spot-component) — SpotWalk.ts, Spot.tsx
   - [Layer 1 Components](#layer-1-components) — useVoicePipeline, useSTT, useKokoroTTS, usePersonaPlex, useSpeechRecognition, useSpeechSynthesis, useVAD, MetricsCollector, VoiceInterface, VoiceInterfaceV2, VoiceControlBar, TranscriptPanel, AudioVisualizer, ConnectionStatus, DeviceSelector, MetricsDashboard, TextInputOverlay, ConversationTranscript
   - [Status Bar](#status-bar) — StatusBar.tsx
   - [Canvas](#canvas) — Canvas.tsx
   - [Layer 3 Components](#layer-3-components) — Blob.tsx, useLayoutState.ts, WidgetSlot.tsx, WidgetToolbar.tsx, BlobGrid.tsx, defaultLayout.ts
   - [Layer 4 Components](#layer-4-components) — widgetRegistry.ts, fixtureData.ts, 18+ widget .tsx files
   - [App Pages & Layout](#app-pages--layout) — layout.tsx, page.tsx, dashboard/page.tsx, widgets/page.tsx, widgets/test/page.tsx, widgets/rate/page.tsx, FeedbackForm.tsx, SampleDashboard.tsx, SimulationView.tsx, globals.css, widget-feedback route
   - [Frontend Types & Stores](#frontend-types--stores) — types/index.ts, metrics.ts, web-speech.d.ts, opus-recorder.d.ts, feedbackStore.ts
   - [Debug Tools](#debug-tools) — DebugPanel.tsx
   - [Frontend Configuration](#frontend-configuration) — package.json, next.config, tailwind.config, tsconfig, playwright.config, server.js, postcss.config
5. [Scripts and Automation](#scripts-and-automation) — dev.sh, deploy.sh, setup.sh, bmc-metrics-logger.sh, personaplex-daemon.sh
   - [Simulation Scripts](#simulation-scripts) — run_simulation.py, analyze_results.py, run_exhaustive.py, export_training_data.py
   - [Systemd Service Files](#systemd-service-files) — cc-backend, cc-frontend, cc-stt, cc-tts
6. [Tests](#tests)
   - [Backend Tests](#backend-tests) — layer2/tests, audit_tests, rl/tests, reconciliation tests
   - [Frontend Tests](#frontend-tests) — E2E test-utils, realistic-scenarios, mega-validation, stress/adversarial/performance specs
7. [Summary](#summary)

---

## Project Overview

Command Center is like having a smart assistant in a factory. Imagine you're a factory worker and you want to know "How is pump 3 doing?" Instead of walking to a computer, finding the right screen, and clicking through menus, you just ask out loud. The system:

1. **Hears you** (Speech-to-Text)
2. **Understands what you want** (AI Brain)
3. **Finds the information** (Database Search)
4. **Shows you visual charts and numbers** (Dashboard)
5. **Tells you the answer out loud** (Text-to-Speech)

The code is organized into **4 layers**:
- **Layer 1**: Handles hearing and speaking (voice input/output)
- **Layer 2**: The brain that understands questions and finds answers
- **Layer 3**: Arranges visual widgets on screen
- **Layer 4**: The actual charts, graphs, and numbers you see

---

## How the System Works

Here's what happens when you ask "What's the pump status?":

```
YOU SPEAK: "What's the pump status?"
     ↓
[LAYER 1: Voice] Your voice is converted to text
     ↓
[LAYER 2: Brain] The AI understands you want pump information
     ↓
[LAYER 2: Search] Searches the database for pump data
     ↓
[LAYER 2: Widgets] Decides to show a trend chart + status + alerts
     ↓
[LAYER 3: Layout] Arranges those widgets nicely on screen
     ↓
[LAYER 4: Display] Actually draws the charts and numbers
     ↓
[LAYER 1: Voice] Says "Pump 3 is running at 85% capacity"
     ↓
YOU SEE AND HEAR THE ANSWER
```

---

## Backend Files

The backend is written in Python using Django (a popular web framework). It runs on the server and handles all the "thinking" - understanding questions, searching databases, and deciding what to show.

---

### Django Configuration

These files set up how the Django web server works.

---

#### `backend/command_center/settings.py`

**What it does:** This is the main configuration file for the entire backend. Think of it as the "control panel" that tells Django how to behave.

**In simple terms:** Just like your phone has settings for Wi-Fi, notifications, and display, this file has settings for the web server.

**Key sections explained:**

```python
SECRET_KEY = 'django-insecure-x@47$...'
```
**What this means:** A password that Django uses internally to keep things secure. The "insecure" prefix warns that this shouldn't be used in a real production system - it's fine for testing.

```python
DEBUG = True
```
**What this means:** When something goes wrong, show detailed error messages. This is like "developer mode" - helpful for finding problems, but you'd turn it off before real users see the system.

```python
ALLOWED_HOSTS = ["*"]
```
**What this means:** Accept requests from any computer. The `*` means "anyone" - in a real system, you'd list specific allowed addresses.

```python
INSTALLED_APPS = [
    'django.contrib.admin',    # Built-in admin dashboard
    'rest_framework',          # Tools for building APIs
    'corsheaders',             # Allows frontend to talk to backend
    'layer1',                  # Our voice handling code
    'layer2',                  # Our AI brain code
    'industrial',              # Factory equipment data
    'actions',                 # Voice commands like "start pump"
    'feedback',                # User ratings and feedback
]
```
**What this means:** A list of all the "apps" (code modules) that are part of this system. Each app handles a specific job.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
**What this means:** Where to store data. SQLite is a simple database stored in a single file called `db.sqlite3`. It's like a spreadsheet file that holds all our data.

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3100',      # Development computer
    'http://192.168.1.20:3100',   # Office network
]
```
**What this means:** Which websites are allowed to talk to this backend. The frontend (user interface) runs on a different address, so we need to explicitly allow it.

---

#### `backend/command_center/urls.py`

**What it does:** This file is like a phone directory - it tells Django where to send different requests.

**In simple terms:** When someone visits a web address, this file decides which code should handle it.

```python
urlpatterns = [
    path("admin/", admin.site.urls),           # /admin/ goes to Django's admin panel
    path("api/layer1/", include("layer1.urls")),  # /api/layer1/... goes to voice code
    path("api/layer2/", include("layer2.urls")),  # /api/layer2/... goes to AI brain code
    path("api/actions/", include("actions.urls")), # /api/actions/... goes to action code
    path("api/", include("feedback.urls")),        # /api/... goes to feedback code
]
```
**What this means:**
- If someone visits `/admin/`, show the admin dashboard
- If someone visits `/api/layer1/something`, let the Layer 1 code handle it
- And so on...

---

#### `backend/command_center/wsgi.py`

**What it does:** This is the "entry point" for running the backend in production.

**In simple terms:** When you want to run the server for real users (not just testing), this file tells the computer how to start it.

```python
application = get_wsgi_application()
```
**What this means:** Creates an "application" object that web servers (like Gunicorn) can use to run Django.

---

### Layer 1 - Voice Input/Output

Layer 1 handles everything related to voice - hearing what users say and speaking responses back.

---

#### `backend/layer1/models.py`

**What it does:** Defines the database tables for storing voice-related information.

**In simple terms:** This creates "spreadsheet templates" for storing conversation data.

**The VoiceSession model:**
```python
class VoiceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("error", "Error")])
```
**What this means:** Each conversation gets its own "session" record. It tracks:
- `id`: A unique identifier (like a ticket number)
- `started_at`: When the conversation began
- `ended_at`: When it finished (blank if still going)
- `status`: Whether it's active, completed, or had an error

**The Transcript model:**
```python
class Transcript(models.Model):
    session = models.ForeignKey(VoiceSession, on_delete=models.CASCADE)
    role = models.CharField(choices=[("user", "User"), ("assistant", "Assistant")])
    text = models.TextField()
    is_final = models.BooleanField(default=True)
```
**What this means:** Each thing someone says (or the AI says) gets recorded:
- `session`: Which conversation this belongs to
- `role`: Who said it - the human user or the AI assistant
- `text`: The actual words
- `is_final`: Whether this is the final version (speech recognition sometimes updates as you speak)

**The PersonaPlexConfig model:**
```python
class PersonaPlexConfig(models.Model):
    server_url = models.URLField(default="http://localhost:8090")
    model = models.CharField(default="personaplex-7b-v1")
    voice = models.CharField(default="NATF0")
    always_on = models.BooleanField(default=False)
```
**What this means:** Settings for the voice AI system:
- `server_url`: Where the voice AI server is running
- `model`: Which AI model to use
- `voice`: Which voice style (NATF0 = Natural Female voice)
- `always_on`: Whether to keep the connection open all the time

---

#### `backend/layer1/views.py`

**What it does:** Handles web requests related to voice sessions and transcripts.

**In simple terms:** When the frontend wants to save a transcript or start a session, this code handles those requests.

```python
class VoiceSessionViewSet(viewsets.ModelViewSet):
    queryset = VoiceSession.objects.all()
    serializer_class = VoiceSessionSerializer
```
**What this means:** Automatically creates these API endpoints:
- `GET /api/layer1/sessions/` - List all voice sessions
- `POST /api/layer1/sessions/` - Start a new session
- `GET /api/layer1/sessions/123/` - Get details of session 123
- `DELETE /api/layer1/sessions/123/` - Delete session 123

```python
@action(detail=True, methods=["post"])
def end(self, request, pk=None):
    session = self.get_object()
    session.status = "completed"
    session.ended_at = timezone.now()
    session.save()
```
**What this means:** A custom action to mark a session as finished. When you call `POST /api/layer1/sessions/123/end/`, it sets the status to "completed" and records the end time.

---

#### `backend/layer1/admin.py`

**What it does:** Django admin registration for Layer 1 models.

**In simple terms:** This file is empty — no Layer 1 models are registered in the Django admin panel. Voice sessions and transcripts are managed through the API only.

---

#### `backend/layer1/apps.py`

**What it does:** Declares the Layer 1 Django application configuration.

```python
class Layer1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'layer1'
```
**What this means:** Tells Django that "layer1" exists as an app. This is the minimum boilerplate Django needs to load the module.

---

#### `backend/layer1/serializers.py`

**What it does:** Converts Layer 1 database models to/from JSON for the REST API.

**In simple terms:** When the frontend asks for voice session data, serializers turn database rows into JSON that JavaScript can understand.

**Three serializers defined:**
- `TranscriptSerializer` — Converts `Transcript` records (who said what, when)
- `VoiceSessionSerializer` — Converts `VoiceSession` records (conversation start/end times)
- `PersonaPlexConfigSerializer` — Converts `PersonaPlexConfig` records (server URL, voice settings)

---

#### `backend/layer1/urls.py`

**What it does:** Maps web addresses to Layer 1 views using Django REST Framework's router.

```python
router = DefaultRouter()
router.register(r"sessions", VoiceSessionViewSet)
router.register(r"transcripts", TranscriptViewSet)
router.register(r"config", PersonaPlexConfigViewSet)
```
**What this means:** Automatically creates CRUD endpoints:
- `GET/POST /api/layer1/sessions/` — List or create voice sessions
- `GET/POST /api/layer1/transcripts/` — List or save transcripts
- `GET/PATCH /api/layer1/config/` — Get or update PersonaPlex configuration

---

#### `backend/layer1/tests.py`

**What it does:** Placeholder test file for Layer 1. Currently empty — voice functionality is tested via the E2E test suite and integration tests.

---

### Layer 2 - The AI Brain

This is the most important part - it understands what users want and decides what to show them.

---

#### `backend/layer2/models.py`

**What it does:** Database tables for tracking AI queries and user memory.

**The RAGPipeline model:**
```python
class RAGPipeline(models.Model):
    DOMAIN_CHOICES = [
        ("industrial", "Industrial"),
        ("supply", "Supply Chain"),
        ("people", "People"),
        ("tasks", "Tasks"),
        ("alerts", "Alerts"),
    ]
    domain = models.CharField(choices=DOMAIN_CHOICES, unique=True)
    enabled = models.BooleanField(default=True)
    endpoint_url = models.URLField()
```
**What this means:** The system has different "knowledge areas" (domains):
- **Industrial**: Equipment, sensors, energy data
- **Supply**: Inventory, vendors, shipments
- **People**: Employees, shifts, schedules
- **Tasks**: Work orders, tickets
- **Alerts**: Alarms and warnings

Each domain can be enabled/disabled and has its own data source.

**The UserMemory model:**
```python
class UserMemory(models.Model):
    user_id = models.CharField(max_length=100)
    query = models.CharField(max_length=500)
    primary_characteristic = models.CharField(max_length=50)
    domains = models.JSONField(default=list)
    scenarios_used = models.JSONField(default=list)
```
**What this means:** The system remembers what each user has asked:
- `user_id`: Who asked
- `query`: What they asked
- `primary_characteristic`: What type of question (trend, comparison, etc.)
- `domains`: Which knowledge areas were used
- `scenarios_used`: Which widgets were shown

This helps the AI avoid showing the same things repeatedly and maintain conversation context.

---

#### `backend/layer2/orchestrator.py`

**What it does:** The central coordinator that processes user questions and generates responses.

**In simple terms:** This is the "brain" - it receives a question, figures out what it means, finds the answer, and decides how to display it.

**Key constants:**

```python
DOMAIN_KEYWORDS = {
    "industrial": ["pump", "motor", "temperature", "voltage", "power", ...],
    "supply": ["inventory", "stock", "vendor", "shipment", ...],
    "people": ["employee", "shift", "attendance", ...],
    "tasks": ["task", "work order", "ticket", ...],
    "alerts": ["alert", "alarm", "warning", ...],
}
```
**What this means:** Words that help identify which knowledge area a question belongs to. If someone says "pump", it's probably about industrial equipment.

```python
SCENARIO_HEIGHT_HINTS = {
    "kpi": "short",           # A single number - doesn't need much space
    "alerts": "medium",        # A list of alerts - moderate space
    "trend": "tall",          # A chart showing history - needs more space
    "flow-sankey": "x-tall",  # A complex flow diagram - needs lots of space
}
```
**What this means:** How much vertical space each widget type needs on screen.

```python
FILLER_TEMPLATES = {
    "checking": ["Let me check that for you.", "One moment while I look that up."],
    "processing": ["Processing your request.", "Analyzing the data."],
}
```
**What this means:** Things the AI says while it's working on your question, so you know it heard you.

```python
OUT_OF_SCOPE_MESSAGE = (
    "That's outside what I can help with. "
    "I'm your industrial operations assistant — I can help with "
    "equipment monitoring, alerts, maintenance, supply chain, "
    "workforce management, and task tracking."
)
```
**What this means:** What to say when someone asks about something the system can't help with (like "What's the weather?").

**The main processing function:**

```python
def process_transcript(self, transcript: str, session_context: dict = None,
                       user_id: str = "default_user") -> OrchestratorResponse:
```
**What this means:** This is THE main function. You give it what the user said (`transcript`), and it returns:
- `voice_response`: What to say back
- `layout_json`: What widgets to show
- `processing_time_ms`: How long it took
- `query_id`: A unique ID for tracking feedback

**The processing stages:**

1. **Intent Parsing** (understanding what the user wants):
```python
parsed = self._intent_parser.parse(transcript)
```
Figures out: Is this a question? A command? A greeting? What topics does it involve?

2. **Short-circuit for simple cases:**
```python
if parsed.type == "out_of_scope":
    return OrchestratorResponse(voice_response=OUT_OF_SCOPE_MESSAGE, ...)

if parsed.type == "greeting":
    return OrchestratorResponse(voice_response=self._generate_greeting(), ...)
```
Some questions don't need complex processing - greetings, out-of-scope questions, etc.

3. **Widget Selection** (choosing what to show):
```python
widget_plan = self._widget_selector.select(parsed, data_summary, user_context)
```
Based on the question, choose which charts/graphs/numbers to display.

4. **Data Collection** (getting the actual data):
```python
widget_data = self._data_collector.collect_all(widget_plan.widgets, transcript)
```
Fetch the actual numbers and information for each widget.

5. **Voice Response Generation:**
```python
voice_response = self._generate_voice_response_v2(parsed, layout_json, transcript)
```
Create a natural language answer to speak back.

6. **Save to Memory:**
```python
memory_mgr.record(user_id, transcript, parsed, scenarios_used)
```
Remember this interaction for context in future questions.

---

#### `backend/layer2/intent_parser.py`

**What it does:** Understands what type of question the user is asking.

**In simple terms:** Like a secretary who reads your message and figures out "this is a question about equipment" or "this is asking to send a message."

**Intent Types:**
```python
INTENT_TYPES = [
    "query",              # Asking for information
    "action_reminder",    # Set a reminder
    "action_message",     # Send a message to someone
    "action_control",     # Start/stop equipment
    "action_task",        # Create a work order
    "conversation",       # Small talk ("how are you")
    "out_of_scope",       # Not related to factory operations
]
```

**Characteristics** (what kind of visualization is needed):
```python
CHARACTERISTICS = [
    "comparison",    # Comparing two things
    "trend",         # How something changes over time
    "distribution",  # Breaking down into categories
    "maintenance",   # Repair/service information
    "energy",        # Power consumption
    "alerts",        # Warnings and alarms
    # ... and more
]
```

**How it works:**
```python
def parse(self, transcript: str) -> ParsedIntent:
    # Try the smart AI method first
    try:
        result = self._parse_with_llm(transcript)
        if result is not None:
            return result
    except Exception:
        pass

    # If AI fails, use simple pattern matching
    return self._parse_with_regex(transcript)
```
**What this means:**
1. First, try using a smart AI model to understand the question
2. If that doesn't work (server down, etc.), fall back to simpler pattern matching

**The AI parsing prompt:**
```python
PARSE_PROMPT_TEMPLATE = """Classify this user message for an industrial command center.

Intent types:
- "query": asking for information, status, data
- "action_reminder": set a reminder
- "action_control": start/stop equipment
...

User message: "{transcript}"

JSON:"""
```
**What this means:** We tell the AI exactly what categories exist and ask it to classify the user's message.

---

#### `backend/layer2/widget_selector.py`

**What it does:** Chooses which visual widgets to show based on the user's question.

**In simple terms:** Like a TV director who decides "for this story, we should show a graph, three numbers, and a list of alerts."

**Configuration:**
```python
MAX_HEIGHT_UNITS = 24   # Total "space budget" for the dashboard
MAX_WIDGETS = 10        # Maximum number of widgets
MAX_KPIS = 4            # Maximum simple number displays (avoid clutter)
BANNED_SCENARIOS = {"helpview", "pulseview"}  # Never show these
```

**The fast selection prompt:**
```python
FAST_SELECT_PROMPT = '''Select 8 widgets for this industrial operations query.

## WIDGET CATALOG
{catalog}

## QUERY
"{query}"

## SIZING RULES
Hero-capable widgets (use for first/main answer):
  trend, comparison, flow-sankey, matrix-heatmap...

Small widgets (NOT hero, use for supporting info):
  kpi: compact or normal only
  alerts: normal or expanded only

## RULES
1. First widget MUST be hero-capable with size="hero"
2. Use EXACT scenario names
3. Include diverse widget types
4. 8 widgets total

## OUTPUT (JSON only)
{{"heading": "<title>", "widgets": [...]}}'''
```
**What this means:** We give the AI:
- A catalog of all available widgets
- The user's question
- Rules about sizing and selection
- And ask it to pick 8 appropriate widgets

**Template descriptions:**
```python
WHY_TEMPLATES = {
    "kpi": "Shows the current value and status of the key metric at a glance.",
    "trend": "Displays how this metric has changed over time to identify patterns.",
    "alerts": "Lists active alerts and warnings that need attention.",
    "flow-sankey": "Visualizes how energy or resources flow through the system.",
    # ... more
}
```
**What this means:** Pre-written descriptions for each widget type. Instead of asking the AI to write these (slow), we use these templates.

**Validation:**
```python
def _validate_and_build_plan(self, data: dict, method: str = "llm") -> WidgetPlan:
    for w in raw_widgets:
        scenario = w.get("scenario", "").lower()

        # Is this a known widget type?
        if scenario not in VALID_SCENARIOS:
            continue  # Skip unknown types

        # Is it banned?
        if scenario in BANNED_SCENARIOS:
            continue  # Skip banned types

        # Would it exceed our budget?
        if budget - height < 0:
            continue  # Skip if no room

        # Is the size valid for this widget?
        if size not in allowed_sizes:
            size = next(s for s in ["hero", "expanded", "normal", "compact"] if s in allowed_sizes)
```
**What this means:** Even after the AI picks widgets, we double-check everything:
- Only allow known widget types
- Skip banned widgets
- Don't exceed space budget
- Fix invalid size selections

---

#### `backend/layer2/widget_catalog.py`

**What it does:** A registry of all available widget types with their properties.

**In simple terms:** Like a menu at a restaurant - it lists all the "dishes" (widgets) available and describes each one.

```python
WIDGET_CATALOG = [
    {
        "scenario": "kpi",
        "description": "Single metric display — shows one number with label, unit, and optional state (warning/critical).",
        "good_for": ["single metric", "status", "live reading", "count", "percentage"],
        "sizes": ["compact", "normal"],
        "height_units": 1,
    },
    {
        "scenario": "trend",
        "description": "Time series line/area chart for a single metric. Shows how a value changes over time.",
        "good_for": ["trend", "history", "over time", "monitoring", "last 24 hours"],
        "sizes": ["expanded", "hero"],
        "height_units": 3,
    },
    {
        "scenario": "flow-sankey",
        "description": "Sankey diagram showing flow from sources to destinations — energy flows, losses.",
        "good_for": ["flow", "energy balance", "losses", "where does it go"],
        "sizes": ["hero"],
        "height_units": 4,
    },
    # ... 20 more widget types
]
```
**What this means:** Each widget has:
- `scenario`: Its name/ID
- `description`: What it shows
- `good_for`: Keywords that suggest when to use it
- `sizes`: What sizes it can be displayed at
- `height_units`: How much vertical space it needs (1=small, 4=large)

---

#### `backend/layer2/rag_pipeline.py`

**What it does:** Searches through documents and data to find relevant information.

**In simple terms:** Like a librarian who can quickly find relevant books based on your question.

**RAG = Retrieval-Augmented Generation:**
1. **Retrieval**: Find relevant documents/data
2. **Augmented**: Add that context to the AI's knowledge
3. **Generation**: Generate an answer using that context

**Embedding Service:**
```python
class EmbeddingService:
    def embed(self, text: str) -> list[float]:
        # Convert text into numbers (a "vector")
        return self._model.encode(text).tolist()
```
**What this means:** Converts text into a list of numbers. Similar texts have similar numbers, which helps find related content.

**Vector Store:**
```python
class VectorStoreService:
    def search(self, collection: str, query: str, k: int = 5):
        # Find the k most similar documents to the query
        query_embedding = self.embedding_service.embed(query)
        results = collection.query(query_embeddings=[query_embedding], n_results=k)
        return results
```
**What this means:** Searches a collection of documents to find the ones most similar to your question.

**LLM Service:**
```python
class LLMService:
    def generate_json(self, prompt: str, system_prompt: str = None):
        # Ask the AI model and get JSON back
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[...],
            format="json"
        )
        return json.loads(response)
```
**What this means:** Sends a question to the AI model (like ChatGPT) and gets a structured answer back.

---

### Pipeline Optimization

These files make the AI brain faster by running tasks in parallel and managing resources intelligently.

---

#### `backend/layer2/data_prefetcher.py`

**What it does:** Searches the database for relevant data BEFORE the AI needs it.

**In simple terms:** Like a waiter who starts preparing common ingredients while you're still ordering - by the time you decide, half the work is already done.

**The Prefetcher Class:**
```python
class DataPrefetcher:
    def __init__(self, max_workers: int = 6):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.collections = [
            "industrial_equipment",
            "industrial_alerts",
            "maintenance_records",
        ]
```
**What this means:** Uses 6 parallel workers to search 3 different data collections simultaneously.

**Prefetch Function:**
```python
def prefetch(self, query: str, domains: list[str]) -> dict:
    """
    Kick off parallel searches for likely-needed data.
    Returns a dict mapping collection names to results.
    """
    futures = {}
    for collection in self._get_relevant_collections(domains):
        future = self.executor.submit(self._search_collection, collection, query)
        futures[collection] = future

    # Wait for all searches to complete
    results = {}
    for collection, future in futures.items():
        try:
            results[collection] = future.result(timeout=2.0)
        except TimeoutError:
            results[collection] = []  # Don't block on slow searches

    return results
```
**What this means:**
1. Start searches in ALL relevant collections at once
2. Wait up to 2 seconds for each
3. If one search is slow, don't hold up the others

**Domain-to-Collection Mapping:**
```python
DOMAIN_COLLECTIONS = {
    "industrial": ["industrial_equipment", "industrial_alerts"],
    "maintenance": ["maintenance_records", "work_orders"],
    "supply": ["inventory", "vendors"],
}
```
**What this means:** When someone asks about "industrial" topics, search equipment and alerts collections.

---

#### `backend/layer2/parallel_llm.py`

**What it does:** Manages multiple AI requests with priority queuing.

**In simple terms:** Like a hospital emergency room - critical cases go first, but everyone eventually gets treated. Also has a "fast doctor" for quick decisions and a "specialist" for complex cases.

**Priority Levels:**
```python
class Priority(IntEnum):
    LOW = 0       # Background tasks, can wait
    NORMAL = 1    # Standard requests
    HIGH = 2      # Important, user-facing
    CRITICAL = 3  # Must process immediately
```
**What this means:** Requests are sorted by importance. A critical request jumps ahead of normal ones.

**Dual-Model Support:**
```python
class ParallelLLMClient:
    def __init__(self):
        self.model_fast = os.environ.get("OLLAMA_MODEL_FAST", "qwen2.5:7b")
        self.model_quality = os.environ.get("OLLAMA_MODEL_QUALITY", "qwen2.5:70b")
        self.max_concurrent = int(os.environ.get("OLLAMA_MAX_CONCURRENT", 4))
```
**What this means:** Two AI models available:
- **Fast** (7B parameters): Quick responses, good enough for simple tasks
- **Quality** (70B parameters): Slower but more accurate for complex tasks

**Request Dataclass:**
```python
@dataclass
class LLMRequest:
    prompt: str
    priority: Priority = Priority.NORMAL
    model_preference: str = "fast"  # "fast" or "quality"
    timeout: float = 30.0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

**Convenience Functions:**
```python
def generate_fast(prompt: str, timeout: float = 10.0) -> str:
    """Quick generation using fast model."""
    return client.generate(LLMRequest(prompt=prompt, model_preference="fast", timeout=timeout))

def generate_quality(prompt: str, timeout: float = 60.0) -> str:
    """Higher quality generation using larger model."""
    return client.generate(LLMRequest(prompt=prompt, model_preference="quality", timeout=timeout))

def generate_json_fast(prompt: str) -> dict:
    """Generate and parse JSON using fast model."""
    text = generate_fast(prompt)
    return json.loads(text)
```
**What this means:** Easy-to-use functions for common cases:
- Need a quick answer? → `generate_fast()`
- Need accuracy? → `generate_quality()`
- Need structured data? → `generate_json_fast()`

**Priority Queue Processing:**
```python
def _process_queue(self):
    while True:
        # Get highest priority request
        priority, request = self.queue.get()

        # Process with appropriate model
        model = self.model_fast if request.model_preference == "fast" else self.model_quality
        result = self._call_ollama(model, request.prompt)

        # Store result for retrieval
        self.results[request.request_id] = result
```
**What this means:** A background worker processes requests in priority order.

---

#### `backend/layer2/pipeline_executor.py`

**What it does:** Runs multiple processing stages in parallel when possible.

**In simple terms:** Like a factory assembly line where some workers can work simultaneously. Instead of one person doing everything sequentially, multiple people work at once.

**Pipeline Stages:**
```python
@dataclass
class PipelineStage:
    name: str
    function: Callable
    dependencies: list[str] = field(default_factory=list)
    timeout: float = 5.0
```
**What this means:** Each stage has a name, function to execute, what it depends on, and a timeout.

**Stage Dependencies:**
```python
# These stages can run in parallel (no dependencies on each other):
STAGE_1_PARALLEL = [
    PipelineStage("intent_parsing", parse_intent, dependencies=[]),
    PipelineStage("data_prefetch", prefetch_data, dependencies=[]),
]

# This stage depends on intent parsing completing first:
STAGE_2 = [
    PipelineStage("widget_selection", select_widgets, dependencies=["intent_parsing"]),
]

# This stage depends on both widget selection and prefetch:
STAGE_3 = [
    PipelineStage("data_collection", collect_data, dependencies=["widget_selection", "data_prefetch"]),
]
```
**What this means:**
1. Intent parsing and data prefetch run **simultaneously**
2. Once intent parsing finishes, widget selection starts
3. Once both widget selection and prefetch finish, data collection starts

**Executor Class:**
```python
class PipelineExecutor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute(self, stages: list[PipelineStage], initial_context: dict) -> PipelineResult:
        completed = {}
        context = initial_context.copy()

        # Group stages by dependency level
        for stage_group in self._group_by_dependencies(stages):
            # Run all stages in this group in parallel
            futures = {
                stage.name: self.executor.submit(stage.function, context)
                for stage in stage_group
                if self._dependencies_met(stage, completed)
            }

            # Wait for all to complete
            for name, future in futures.items():
                completed[name] = future.result(timeout=stage.timeout)
                context.update(completed[name])

        return PipelineResult(context=context, completed_stages=list(completed.keys()))
```
**What this means:**
1. Group stages by what they depend on
2. Run independent stages in parallel
3. Once a group completes, start the next group

**Efficiency Tracking:**
```python
@dataclass
class PipelineResult:
    context: dict                    # All collected data
    completed_stages: list[str]      # Which stages ran
    total_time_ms: float             # How long it took
    sequential_time_ms: float        # How long it WOULD have taken sequentially
    parallel_efficiency: float       # Time saved / sequential time
```
**What this means:** Tracks how much time parallelization saved. If sequential would take 1000ms but parallel takes 400ms, efficiency is 60%.

---

### Data Quality & Validation

These files ensure data is correct, consistent, and safe before displaying it.

---

#### `backend/layer2/dimensions.py`

**What it does:** Defines physical units and converts between them.

**In simple terms:** Like a universal translator for measurements. Whether data comes in as "kW", "MW", or "HP", it all gets converted to a standard format.

**Dimension Enum:**
```python
class Dimension(Enum):
    POWER = "power"           # Energy flow rate (kW, MW, HP)
    ENERGY = "energy"         # Total energy (kWh, MWh, BTU)
    TEMPERATURE = "temp"      # Heat level (°C, °F, K)
    PRESSURE = "pressure"     # Force per area (bar, psi, kPa)
    FLOW_RATE = "flow"        # Volume over time (m³/h, gpm)
    PERCENTAGE = "percent"    # Ratios (%, unitless)
    TIME = "time"             # Duration (s, min, hr)
    COUNT = "count"           # Integer quantities
```
**What this means:** The system knows about 8 types of physical measurements.

**Unit Specifications:**
```python
@dataclass
class UnitSpec:
    symbol: str              # "kW"
    name: str                # "kilowatt"
    to_base: float           # Multiplier to convert to base unit
    aliases: list[str]       # ["kilowatts", "KW", "Kw"]

UNITS = {
    Dimension.POWER: DimensionSpec(
        base_unit="kW",
        units=[
            UnitSpec("W", "watt", 0.001, ["watts"]),
            UnitSpec("kW", "kilowatt", 1.0, ["kilowatts", "KW"]),
            UnitSpec("MW", "megawatt", 1000.0, ["megawatts"]),
            UnitSpec("HP", "horsepower", 0.7457, ["hp", "horsepower"]),
        ]
    ),
    Dimension.TEMPERATURE: DimensionSpec(
        base_unit="°C",
        units=[
            UnitSpec("°C", "celsius", 1.0, ["C", "celsius", "Celsius"]),
            UnitSpec("°F", "fahrenheit", None, ["F", "fahrenheit"]),  # Special conversion
            UnitSpec("K", "kelvin", None, ["kelvin"]),
        ]
    ),
}
```
**What this means:** Each dimension has a "base unit" (standard) and rules to convert from other units.

**Conversion Functions:**
```python
def convert_value(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a value from one unit to another."""
    dimension = infer_dimension(from_unit)

    # Special case for temperature (not linear)
    if dimension == Dimension.TEMPERATURE:
        return _convert_temperature(value, from_unit, to_unit)

    # Linear conversion: value * (from_to_base / to_to_base)
    from_spec = get_unit_spec(from_unit)
    to_spec = get_unit_spec(to_unit)
    base_value = value * from_spec.to_base
    return base_value / to_spec.to_base

def normalize_to_base(value: float, unit: str) -> tuple[float, str]:
    """Convert any value to the base unit for its dimension."""
    dimension = infer_dimension(unit)
    base_unit = UNITS[dimension].base_unit
    normalized = convert_value(value, unit, base_unit)
    return normalized, base_unit
```
**What this means:**
- `convert_value(100, "HP", "kW")` → 74.57
- `normalize_to_base(212, "°F")` → (100, "°C")

**Temperature Conversion (Special Case):**
```python
def _convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Temperature requires offset, not just multiplication."""
    # First convert to Celsius
    if from_unit in ["°F", "F"]:
        celsius = (value - 32) * 5 / 9
    elif from_unit in ["K", "kelvin"]:
        celsius = value - 273.15
    else:
        celsius = value

    # Then convert from Celsius to target
    if to_unit in ["°F", "F"]:
        return celsius * 9 / 5 + 32
    elif to_unit in ["K", "kelvin"]:
        return celsius + 273.15
    return celsius
```
**What this means:** Temperature can't use simple multiplication (0°C ≠ 0°F), so it has special handling.

---

#### `backend/layer2/widget_normalizer.py`

**What it does:** Transforms widget data to ensure consistency while preserving all information.

**In simple terms:** Like a translator who not only translates words but also keeps notes about the original phrasing so nothing is lost.

**Normalization Result:**
```python
@dataclass
class NormalizationResult:
    data: dict                           # The normalized data
    transformations: list[dict]          # Record of every change made
    original_data: dict                  # Backup of input data
    is_modified: bool                    # Whether any changes were made

    def add_transformation(self, field: str, original: Any, normalized: Any, reason: str):
        self.transformations.append({
            "field": field,
            "original_value": original,
            "normalized_value": normalized,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })
```
**What this means:** Every change is recorded with what changed, why, and when. You can always see the original.

**Main Normalization Function:**
```python
def normalize_widget_data(scenario: str, data: dict) -> NormalizationResult:
    """Normalize data for a specific widget scenario."""
    result = NormalizationResult(
        data=copy.deepcopy(data),
        transformations=[],
        original_data=data,
        is_modified=False,
    )

    # Get the normalizer for this scenario type
    normalizer = SCENARIO_NORMALIZERS.get(scenario)
    if normalizer:
        normalizer(result)

    return result
```

**Scenario-Specific Normalizers:**
```python
def _normalize_kpi(result: NormalizationResult):
    """Normalize KPI widget data."""
    data = result.data

    # Normalize unit to base form
    if "unit" in data and "value" in data:
        dimension = infer_dimension(data["unit"])
        if dimension:
            original_value = data["value"]
            original_unit = data["unit"]
            normalized, base_unit = normalize_to_base(data["value"], data["unit"])

            if base_unit != original_unit:
                data["value"] = normalized
                data["unit"] = base_unit
                result.add_transformation(
                    field="value",
                    original=f"{original_value} {original_unit}",
                    normalized=f"{normalized} {base_unit}",
                    reason=f"Converted to base unit for {dimension.value}",
                )
                result.is_modified = True

def _normalize_comparison(result: NormalizationResult):
    """Normalize comparison widget data - ensure both values use same unit."""
    data = result.data

    # If comparing two values, normalize both to same unit
    if all(k in data for k in ["valueA", "unitA", "valueB", "unitB"]):
        dim_a = infer_dimension(data["unitA"])
        dim_b = infer_dimension(data["unitB"])

        if dim_a == dim_b and data["unitA"] != data["unitB"]:
            # Convert B to A's unit for fair comparison
            converted = convert_value(data["valueB"], data["unitB"], data["unitA"])
            result.add_transformation(
                field="valueB",
                original=f"{data['valueB']} {data['unitB']}",
                normalized=f"{converted} {data['unitA']}",
                reason="Aligned units for comparison",
            )
            data["valueB"] = converted
            data["unitB"] = data["unitA"]
            result.is_modified = True
```
**What this means:**
- **KPI**: Converts "500 W" to "0.5 kW" (base unit)
- **Comparison**: If comparing "100 kW" vs "150000 W", converts to "100 kW" vs "150 kW"

---

#### `backend/layer2/widget_schemas.py`

**What it does:** Defines what data each widget type requires and validates it.

**In simple terms:** Like a form with required fields - if you're missing something or put in the wrong type, it tells you what's wrong.

**Schema Definition:**
```python
WIDGET_SCHEMAS = {
    "kpi": {
        "required": ["label", "value"],
        "optional": ["unit", "state", "max", "trend"],
        "types": {
            "label": str,
            "value": (int, float),
            "unit": str,
            "state": str,  # "normal", "warning", "critical"
            "max": (int, float),
        },
        "state_values": ["normal", "warning", "critical"],
    },
    "trend": {
        "required": ["label", "data"],
        "optional": ["unit", "threshold"],
        "types": {
            "label": str,
            "data": list,  # List of {time, value} points
            "unit": str,
            "threshold": (int, float),
        },
        "data_item_schema": {
            "required": ["time", "value"],
            "types": {"time": str, "value": (int, float)},
        },
    },
    "alerts": {
        "required": ["alerts"],
        "types": {
            "alerts": list,  # List of alert objects
        },
        "alert_item_schema": {
            "required": ["id", "message", "severity"],
            "types": {
                "id": str,
                "message": str,
                "severity": str,
            },
            "severity_values": ["low", "warning", "critical"],
        },
    },
}
```
**What this means:** Each widget type has:
- **Required fields**: Must be present
- **Optional fields**: Nice to have
- **Types**: What type each field should be
- **Allowed values**: For enum-like fields

**Validation Function:**
```python
def validate_widget_data(scenario: str, data: dict) -> tuple[bool, list[str]]:
    """
    Validate data against the schema for a widget type.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    schema = WIDGET_SCHEMAS.get(scenario)

    if not schema:
        return True, []  # Unknown schema, can't validate

    # Check required fields
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check types
    for field, expected_type in schema.get("types", {}).items():
        if field in data:
            if not isinstance(data[field], expected_type):
                errors.append(f"Field '{field}' should be {expected_type}, got {type(data[field])}")

    # Check enum values
    for field, allowed in schema.get("allowed_values", {}).items():
        if field in data and data[field] not in allowed:
            errors.append(f"Field '{field}' must be one of {allowed}, got '{data[field]}'")

    return len(errors) == 0, errors
```
**What this means:** Checks that:
1. All required fields are present
2. All fields have the right type
3. Enum fields have valid values

**Security Validation:**
```python
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
    r"(--|;|/\*|\*/)",
    r"(\bOR\b.*=.*\bOR\b)",
]

XSS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
]

def check_security(value: str) -> tuple[bool, str | None]:
    """Check a string value for security issues."""
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return False, "Potential SQL injection detected"

    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return False, "Potential XSS detected"

    return True, None
```
**What this means:** Scans text fields for dangerous patterns that could be hacking attempts.

---

### Reconciliation System

When the AI generates data that doesn't perfectly match what widgets expect, this system fixes it.

---

#### `backend/layer2/reconciliation/types.py`

**What it does:** Defines types and categories for data mismatches.

**In simple terms:** A classification system for "what went wrong" - is it a minor formatting issue or a serious problem?

**Mismatch Classes:**
```python
class MismatchClass(Enum):
    NONE = "none"                               # Perfect match
    STRUCTURAL_EQUIVALENCE = "structural_eq"    # Same data, different structure
    REPRESENTATIONAL_EQUIVALENCE = "repr_eq"    # Same meaning, different format
    UNKNOWN_AMBIGUOUS = "unknown"               # Can't determine
    SEMANTIC_DIFFERENCE = "semantic_diff"       # Actually different meaning
    SECURITY_VIOLATION = "security"             # Dangerous content detected
```
**What this means:**
- **NONE**: Perfect, nothing to fix
- **STRUCTURAL_EQUIVALENCE**: `{"value": 100}` vs `{"val": 100}` - same data, different key names
- **REPRESENTATIONAL_EQUIVALENCE**: `"100"` vs `100` - string vs number, same meaning
- **SEMANTIC_DIFFERENCE**: `100` vs `200` - actually different values (can't auto-fix)
- **SECURITY_VIOLATION**: Contains dangerous patterns (must reject)

**Provenance Tracking:**
```python
@dataclass
class Provenance:
    source: str              # "llm_output" or "reconciler"
    timestamp: datetime
    operation: str           # "original", "rewrite", "resolve"
    confidence: float        # 0.0 to 1.0
    reasoning: str           # Why this decision was made
```
**What this means:** Every piece of data knows where it came from and why it was changed.

**Mismatch Report:**
```python
@dataclass
class FieldMismatch:
    field_path: str               # "data.value" or "data.alerts[0].severity"
    expected_type: str            # "int"
    actual_type: str              # "str"
    expected_value: Any           # 100
    actual_value: Any             # "100"
    mismatch_class: MismatchClass # REPRESENTATIONAL_EQUIVALENCE
    is_rewritable: bool           # True (can be auto-fixed)
    suggested_rewrite: Any        # 100 (the int version)

@dataclass
class MismatchReport:
    scenario: str
    field_mismatches: list[FieldMismatch]
    overall_class: MismatchClass
    is_recoverable: bool          # Can we fix all mismatches?
    security_issues: list[str]    # Any security violations found
```
**What this means:** A complete report of everything wrong with the data and whether it can be fixed.

---

#### `backend/layer2/reconciliation/reconciler.py`

**What it does:** Analyzes data to find and classify mismatches.

**In simple terms:** Like a proofreader who doesn't just say "wrong" but explains exactly what's wrong and how to fix it.

**Classification Logic:**
```python
def classify_value_type(expected_type: type, actual_value: Any) -> tuple[MismatchClass, str, bool]:
    """
    Classify the type of mismatch between expected and actual.

    Returns:
        (mismatch_class, reason, is_rewritable)
    """
    actual_type = type(actual_value)

    # Exact match
    if isinstance(actual_value, expected_type):
        return MismatchClass.NONE, "Types match", True

    # String that could be a number
    if expected_type in (int, float) and isinstance(actual_value, str):
        try:
            float(actual_value)  # Can it be parsed?
            return MismatchClass.REPRESENTATIONAL_EQUIVALENCE, "String is parseable as number", True
        except ValueError:
            return MismatchClass.SEMANTIC_DIFFERENCE, "String is not a valid number", False

    # Number that could be a string
    if expected_type == str and isinstance(actual_value, (int, float)):
        return MismatchClass.REPRESENTATIONAL_EQUIVALENCE, "Number can be stringified", True

    # List vs single item
    if expected_type == list and not isinstance(actual_value, list):
        return MismatchClass.STRUCTURAL_EQUIVALENCE, "Single item should be wrapped in list", True

    # Incompatible types
    return MismatchClass.SEMANTIC_DIFFERENCE, f"Cannot convert {actual_type} to {expected_type}", False
```
**What this means:** Determines if a mismatch is fixable:
- `"100"` when expecting `int` → Fixable (just parse it)
- `"hello"` when expecting `int` → Not fixable (can't convert)

**Security Checking:**
```python
def check_security(data: dict) -> list[str]:
    """Recursively check all string values for security issues."""
    issues = []

    def _check_recursive(obj, path=""):
        if isinstance(obj, str):
            is_safe, reason = _check_string_security(obj)
            if not is_safe:
                issues.append(f"{path}: {reason}")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                _check_recursive(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_recursive(item, f"{path}[{i}]")

    _check_recursive(data)
    return issues
```
**What this means:** Walks through EVERY string in the data looking for dangerous patterns.

---

#### `backend/layer2/data_collector.py`

**What it does:** Collects real data for each widget using targeted database searches.

**In simple terms:** Once the widget selector decides "show a trend chart for pump 3," this file actually goes and fetches pump 3's data from the database.

**The Schema Data Collector:**
```python
class SchemaDataCollector:
    def collect_all(self, widgets: list[WidgetPlanItem], query: str) -> list[dict]:
        """Collect data for all widgets in parallel."""
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._collect_one, w, query): i
                for i, w in enumerate(widgets)
            }
            results = [None] * len(widgets)
            for future in as_completed(futures):
                data_override = future.result()
                # PIPELINE: normalize → validate → pass
                normalized_data = _normalize_and_validate(widget.scenario, data_override)
                results[idx] = {
                    "scenario": widget.scenario,
                    "size": widget.size,
                    "data_override": normalized_data,
                }
        return [r for r in results if r is not None]
```
**What this means:**
1. Start 5 parallel workers
2. Each worker fetches data for one widget
3. Normalize and validate the data
4. Return all results (skip any that failed validation)

**RAG Strategy Routing:**
```python
def _collect_one(self, widget: WidgetPlanItem, query: str) -> dict:
    strategy = schema["rag_strategy"]

    if strategy == "single_metric":
        return self._collect_single_metric(...)  # For KPI widget
    elif strategy == "alert_query":
        return self._collect_alerts(...)          # For alerts widget
    elif strategy == "time_series":
        return self._collect_time_series(...)     # For trend widget
    elif strategy == "multi_entity_metric":
        return self._collect_comparison(...)      # For comparison widget
    elif strategy == "flow_analysis":
        return self._collect_flow(...)            # For sankey diagram
    # ... more strategies
```
**What this means:** Each widget type has a specific data collection strategy:
- **KPI**: Search for one entity, extract one value
- **Alerts**: Search alerts collection, format as list
- **Trend**: Get time series data with timestamps
- **Comparison**: Get data for two entities, calculate delta

---

#### `backend/layer2/user_memory.py`

**What it does:** Remembers what each user has asked to provide context for future questions.

**In simple terms:** Like a personal assistant who remembers "Last time you asked about pumps, then chillers, then energy." This helps give more relevant answers.

**Memory Manager:**
```python
class UserMemoryManager:
    def record(self, user_id: str, transcript: str, parsed_intent, widget_scenarios: list):
        """Save one interaction and trim to MAX_HISTORY rows."""
        UserMemory.objects.create(
            user_id=user_id,
            query=transcript[:500],
            primary_characteristic=parsed_intent.primary_characteristic,
            domains=parsed_intent.domains,
            entities_mentioned=parsed_intent.entities.get("devices", []),
            scenarios_used=widget_scenarios,
        )
        # Keep only last 20 rows per user
        ids_to_delete = UserMemory.objects.filter(user_id=user_id)
            .order_by("-created_at").values_list("id", flat=True)[MAX_HISTORY:]
        UserMemory.objects.filter(id__in=ids_to_delete).delete()
```
**What this means:** After each question:
1. Save what they asked, what topics it covered, which equipment
2. If they have more than 20 saved questions, delete the oldest ones

**Building Context:**
```python
def get_context(self, user_id: str) -> dict:
    recent = UserMemory.objects.filter(user_id=user_id).order_by("-created_at")[:20]

    # Frequency analysis - what do they ask about most?
    char_freq = {}  # {"trend": 5, "alerts": 3}
    entity_freq = {}  # {"pump-3": 7, "chiller-1": 4}
    for r in recent:
        char_freq[r.primary_characteristic] += 1
        for e in r.entities_mentioned:
            entity_freq[e] += 1

    return {
        "history_count": len(recent),
        "recent_queries": [r.query for r in recent[:3]],
        "focus_areas": ["trend", "alerts"],  # Most common query types
        "frequent_entities": ["pump-3", "chiller-1"],  # Most mentioned equipment
        "summary": "User has asked 15 questions. Focus: trends. Frequently mentioned: pump-3."
    }
```
**What this means:** Analyzes past questions to understand:
- What topics they care about most
- Which equipment they ask about frequently
- Their recent questions for context

---

### Speech-to-Text Server

---

#### `backend/stt/server.py`

**What it does:** Converts spoken audio into text using AI models.

**In simple terms:** When you speak to the system, this server turns your voice into words the computer can understand.

**Available Models:**
```python
class ModelName(str, Enum):
    PARAKEET = "parakeet"  # NVIDIA's model - best for industrial terms
    WHISPER = "whisper"     # OpenAI's model - lightweight fallback
```
**What this means:** Two speech recognition engines:
- **Parakeet**: More accurate for technical terms like "kVA" or "chiller"
- **Whisper**: Lighter, works when Parakeet isn't available

**API Endpoints:**
```python
# POST /v1/stt — Convert audio to text
@app.post("/v1/stt")
async def transcribe(audio: UploadFile = File(...)):
    audio_data = await audio.read()
    text = active_model.transcribe(audio_data)
    return {"text": text, "model": active_model_name, "duration_ms": elapsed}

# GET /v1/stt/health — Check status
@app.get("/v1/stt/health")
async def health():
    return {"status": "ok", "active_model": "parakeet", "models": [...]}

# POST /v1/stt/switch — Change models
@app.post("/v1/stt/switch")
async def switch_model(request: SwitchRequest):
    # Unload current model, load requested model
    load_model(request.model)
    return {"success": True, "active_model": request.model}
```
**What this means:**
- Send audio → get text back
- Check which model is running
- Switch between models without restarting

---

### Reinforcement Learning Details

---

#### `backend/rl/config.py`

**What it does:** All the settings for how the AI learns from feedback.

**In simple terms:** Like the "settings menu" for the learning system - how fast to learn, how much data to collect, when to update.

**DPO Training Configuration:**
```python
DPO_CONFIG = {
    "lora_r": 16,              # How much the model can change (higher = more)
    "lora_alpha": 32,          # Scaling factor
    "learning_rate": 5e-5,     # How fast to learn (too fast = unstable)
    "beta": 0.1,               # Preference strength (lower = trust feedback more)
    "batch_size": 4,           # Examples processed at once
    "num_epochs": 3,           # Times through all training data
}
```
**What this means:** Settings for fine-tuning the AI:
- **LoRA**: Technology that makes training cheaper (only changes small parts of model)
- **Learning rate**: How big each update step is
- **Beta**: How strongly to prefer "good" over "bad" examples

**Continuous Learning Configuration:**
```python
CONTINUOUS_RL_CONFIG = {
    "buffer_size": 10000,       # Max experiences to remember
    "min_batch_size": 16,       # Min data before training
    "train_interval": 60,       # Seconds between training

    "reward_weights": {
        "explicit_rating": 1.0,     # Thumbs up/down (most important)
        "follow_up_type": 0.5,      # Did they need to rephrase?
        "widget_engagement": 0.3,   # Did they interact with widgets?
        "response_latency": 0.1,    # Was it fast?
    },
}
```
**What this means:** How to weight different feedback signals:
- User clicking thumbs up is the strongest signal
- User having to rephrase their question is negative
- Faster responses are slightly better

---

#### `backend/rl/trainer.py`

**What it does:** Runs the actual AI training using DPO (Direct Preference Optimization).

**In simple terms:** This is the "teacher" that shows the AI examples of good vs bad choices and helps it learn which is better.

**Training Result:**
```python
@dataclass
class TrainingResult:
    success: bool                    # Did training complete?
    checkpoint_path: Optional[str]   # Where the new model was saved
    final_loss: Optional[float]      # How well training went (lower = better)
    train_samples: int               # How many examples used
    error_message: Optional[str]     # What went wrong (if anything)
```

**The DPO Trainer:**
```python
class CommandCenterDPOTrainer:
    def __init__(self, config_name: str = "default"):
        # Three config presets:
        # "default" - balanced for most GPUs
        # "small_gpu" - for 8GB VRAM cards
        # "high_quality" - more training, better results

    def load_base_model(self):
        """Load model with QLoRA for memory efficiency."""
        # QLoRA = Quantized LoRA
        # Loads the 8B model using only 4GB VRAM instead of 16GB
        config = BitsAndBytesConfig(
            load_in_4bit=True,           # Use 4-bit weights
            bnb_4bit_compute_dtype="bfloat16",
            bnb_4bit_quant_type="nf4",   # Normalized float 4-bit
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model, quantization_config=config
        )

    def train(self, train_dataset, eval_dataset=None) -> TrainingResult:
        """Run DPO training."""
        # DPO shows the model pairs of (prompt, chosen, rejected)
        # Model learns to prefer "chosen" responses over "rejected" ones
        trainer = DPOTrainer(
            model=self.model,
            train_dataset=train_dataset,
            beta=0.1,  # How strongly to prefer chosen over rejected
        )
        trainer.train()
        trainer.save_model(checkpoint_path)
        return TrainingResult(success=True, checkpoint_path=checkpoint_path)
```
**What this means:**
1. Load the base AI model in a memory-efficient way (QLoRA)
2. Show it examples of good vs bad widget selections
3. Train it to prefer the good ones
4. Save the improved model

**Main Classification Function:**
```python
def classify_mismatch(scenario: str, data: dict, schema: dict) -> MismatchReport:
    """
    Analyze data against schema and produce a detailed mismatch report.
    """
    field_mismatches = []

    # Check each field against schema
    for field, expected_type in schema.get("types", {}).items():
        if field in data:
            mismatch_class, reason, is_rewritable = classify_value_type(
                expected_type, data[field]
            )
            if mismatch_class != MismatchClass.NONE:
                field_mismatches.append(FieldMismatch(
                    field_path=field,
                    expected_type=str(expected_type),
                    actual_type=str(type(data[field])),
                    actual_value=data[field],
                    mismatch_class=mismatch_class,
                    is_rewritable=is_rewritable,
                ))

    # Security check
    security_issues = check_security(data)
    if security_issues:
        for issue in security_issues:
            field_mismatches.append(FieldMismatch(
                field_path=issue.split(":")[0],
                mismatch_class=MismatchClass.SECURITY_VIOLATION,
                is_rewritable=False,
            ))

    # Determine overall class (worst case wins)
    overall_class = MismatchClass.NONE
    for fm in field_mismatches:
        if fm.mismatch_class.value > overall_class.value:  # Higher = worse
            overall_class = fm.mismatch_class

    return MismatchReport(
        scenario=scenario,
        field_mismatches=field_mismatches,
        overall_class=overall_class,
        is_recoverable=all(fm.is_rewritable for fm in field_mismatches),
        security_issues=security_issues,
    )
```
**What this means:**
1. Check every field against what's expected
2. Scan for security issues
3. Report everything found
4. Determine if all issues are fixable

---

#### `backend/layer2/reconciliation/pipeline.py`

**What it does:** The complete 5-stage pipeline for fixing data problems.

**In simple terms:** Like an assembly line for data repair:
1. Identify problems → 2. Simple fixes → 3. Smart fixes → 4. Unit conversion → 5. Final check

**The 5 Stages:**
```python
class ReconciliationPipeline:
    STAGES = [
        "CLASSIFY",    # Find all problems
        "REWRITE",     # Fix simple type mismatches
        "RESOLVE",     # Use AI for ambiguous cases
        "NORMALIZE",   # Convert units to standard form
        "VALIDATE",    # Final schema validation
    ]
```

**Pipeline Execution:**
```python
def process(self, scenario: str, data: dict) -> PipelineResult:
    """
    Run the full reconciliation pipeline.

    Returns either validated data or a structured refusal.
    """
    context = {"scenario": scenario, "data": copy.deepcopy(data)}

    # Stage 1: CLASSIFY
    report = classify_mismatch(scenario, data, self.schemas[scenario])
    context["mismatch_report"] = report

    # Short-circuit: Security violation = immediate rejection
    if report.overall_class == MismatchClass.SECURITY_VIOLATION:
        return PipelineResult(
            success=False,
            refusal=RefusalDetail(
                reason="Security violation detected",
                violations=report.security_issues,
                stage="CLASSIFY",
            ),
        )

    # Short-circuit: Perfect match = skip to end
    if report.overall_class == MismatchClass.NONE:
        return PipelineResult(success=True, data=data)

    # Stage 2: REWRITE (simple fixes)
    if report.is_recoverable:
        rewritten = self.rewriter.rewrite(data, report)
        context["data"] = rewritten.data

    # Stage 3: RESOLVE (AI-assisted for remaining issues)
    remaining_issues = [fm for fm in report.field_mismatches if not fm.is_rewritable]
    if remaining_issues:
        resolved = self.resolver.resolve(context["data"], remaining_issues)
        if resolved.success:
            context["data"] = resolved.data
        else:
            return PipelineResult(
                success=False,
                refusal=RefusalDetail(
                    reason="Could not resolve semantic differences",
                    stage="RESOLVE",
                ),
            )

    # Stage 4: NORMALIZE (unit conversion)
    normalized = normalize_widget_data(scenario, context["data"])
    context["data"] = normalized.data
    context["transformations"] = normalized.transformations

    # Stage 5: VALIDATE (final check)
    is_valid, errors = validate_widget_data(scenario, context["data"])
    if not is_valid:
        return PipelineResult(
            success=False,
            refusal=RefusalDetail(
                reason="Validation failed after reconciliation",
                errors=errors,
                stage="VALIDATE",
            ),
        )

    return PipelineResult(
        success=True,
        data=context["data"],
        transformations=context.get("transformations", []),
        stages_completed=self.STAGES,
    )
```
**What this means:**
1. **CLASSIFY**: Find all problems and their severity
2. **REWRITE**: Fix easy problems (string→number, wrap in list)
3. **RESOLVE**: Use AI to fix harder problems or reject if impossible
4. **NORMALIZE**: Convert units (HP→kW, °F→°C)
5. **VALIDATE**: Final check that everything is correct

**Refusal Detail:**
```python
@dataclass
class RefusalDetail:
    reason: str                # Human-readable explanation
    stage: str                 # Which stage failed
    errors: list[str] = None   # Specific validation errors
    violations: list[str] = None  # Security violations found

@dataclass
class PipelineResult:
    success: bool
    data: dict = None          # The fixed data (if success)
    refusal: RefusalDetail = None  # Why it failed (if not success)
    transformations: list[dict] = None  # Audit trail of changes
    stages_completed: list[str] = None  # Which stages ran
```
**What this means:** Every result either has fixed data OR a clear explanation of why it couldn't be fixed.

---

#### `backend/layer2/admin.py`

**What it does:** Django admin registration for Layer 2 models. Currently empty — RAG pipelines and queries are managed through the API.

---

#### `backend/layer2/apps.py`

**What it does:** Declares the Layer 2 Django application and starts the RL system on boot.

```python
class Layer2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'layer2'
    verbose_name = 'Layer 2 — AI Brain'

    def ready(self):
        from rl.continuous import get_rl_system
        rl = get_rl_system()
        rl.start()
```
**What this means:** When Django starts, this automatically launches the Continuous RL system in a background thread. The RL system begins collecting experiences and updating widget/fixture selection strategies from user feedback.

---

#### `backend/layer2/serializers.py`

**What it does:** Converts Layer 2 database models to/from JSON.

**Three serializers defined:**
- `RAGResultSerializer` — Converts search results (domain, raw data, confidence, timing)
- `RAGQuerySerializer` — Converts query records (nested result using `RAGResultSerializer`)
- `RAGPipelineSerializer` — Converts pipeline registrations (domain, enabled status, description)

---

#### `backend/layer2/urls.py`

**What it does:** Maps all Layer 2 API endpoints — both auto-generated CRUD and custom endpoints.

```python
router = DefaultRouter()
router.register(r"pipelines", RAGPipelineViewSet)
router.register(r"queries", RAGQueryViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("orchestrate/", orchestrate),          # Main AI brain endpoint
    path("filler/", get_filler),                # Quick filler text while processing
    path("proactive/", proactive_trigger),      # System-initiated conversations
    path("feedback/", submit_feedback),          # User thumbs up/down
    path("rl-status/", rl_status),              # RL system health
    path("rag/industrial/", industrial_rag_query),      # Industrial RAG queries
    path("rag/industrial/health/", industrial_rag_health), # RAG health check
]
```

---

#### `backend/layer2/views.py`

**What it does:** The HTTP request handlers for all Layer 2 endpoints. This is where web requests get processed and responses get sent back.

**In simple terms:** Each function here is like a receptionist — it receives a request, figures out what to do with it, and sends back a response.

**Key endpoints:**

1. **`orchestrate(request)`** — The main brain endpoint. Receives a transcript like "What's the status of the pumps?", passes it through the orchestrator (intent parsing → RAG queries → response generation), and returns voice response text, layout JSON for widgets, and context updates. Every response includes a `query_id` used for RL feedback tracking.

2. **`get_filler(request)`** — Returns quick filler text (e.g., "Let me check that for you") so Layer 1 can speak something immediately while the full answer is being computed.

3. **`proactive_trigger(request)`** — Called when system conditions change (new alerts, shift start). Returns a trigger phrase the system can proactively speak to the user.

4. **`submit_feedback(request)`** — Receives user feedback (thumbs up/down, corrections, widget interactions) tied to a `query_id`. Updates the RL system's experience buffer and persists to the `WidgetRating` database model.

5. **`rl_status(request)`** — Returns the current state of the RL system (running, buffer size, training stats).

6. **`RAGPipelineViewSet` / `RAGQueryViewSet`** — Standard CRUD endpoints for managing RAG pipelines and viewing query logs.

---

#### `backend/layer2/fixture_selector.py`

**What it does:** Selects which visual variant (fixture) to use for each widget based on its data content.

**In simple terms:** Imagine you have a "temperature" widget. Should it be a gauge, a progress bar, or a status badge? This file makes that decision by analyzing what data the widget contains.

**How it works (436 lines):**

The `FixtureSelector` class uses a multi-step strategy:
1. **Data-driven matching** — Looks at the actual data values. If the data has `state: "critical"`, it picks the red alert KPI variant. If it has `unit: "kW"`, it picks the high-contrast electrical reading variant.
2. **Context string matching** — Searches the query context for keywords. "energy consumption" → area chart, "3-phase" → RGB phase lines, "OEE" → OEE-by-machine bars.
3. **Diversity scoring** — Tracks which fixtures have already been used in the current dashboard and penalizes duplicates. Adjacent widgets should look different.
4. **Default fallback** — If nothing matches, picks the default fixture for that scenario.

Each widget type (KPI, trend, alerts, distribution, etc.) has its own selection logic with scenario-specific rules.

---

#### `backend/layer2/llm_fixture_selector.py`

**What it does:** An upgraded version of fixture selection that uses a small LLM (8B model) instead of keyword rules.

**In simple terms:** Instead of using if/else rules to pick visual styles, this asks an AI to look at all the widgets at once and pick the best visual for each one. The AI can reason about cross-widget diversity — making sure the dashboard looks varied and interesting.

**How it works (305 lines):**

1. **Single batched call** — All widgets are sent in one prompt, so the LLM can see the full dashboard context and ensure visual variety.
2. **Structured prompt** — Lists each widget's scenario, data context (label, state, unit), and available fixture variants with descriptions.
3. **JSON output** — LLM responds with `{"fixtures": [{"index": 0, "fixture": "kpi_alert-critical-state", "reason": "critical alarm state"}]}`.
4. **Validation** — Each LLM-suggested fixture is checked against the valid set for that scenario. Invalid suggestions are silently rejected.
5. **Graceful fallback** — Any widget the LLM doesn't handle (or gets wrong) falls back to the rule-based `FixtureSelector`.
6. **Skip optimization** — Single-variant widgets (chatstream, edgedevicepanel, etc.) bypass the LLM entirely.

Controlled by `FIXTURE_SELECT_LLM` environment variable (default: enabled).

---

#### `backend/layer2/reconciler.py`

**What it does:** A general-purpose reconciliation engine that checks widget data for mismatches against expected schemas.

**In simple terms:** Before any widget data gets displayed, this engine inspects it to make sure values are the right type, within valid ranges, and properly formatted. Think of it as a quality control inspector at a factory — every widget passes through this checkpoint.

**Key capabilities:**
- **Type classification** — Detects when a string should be a number ("42" → 42), a boolean ("true" → True), or contains units ("500 kW" → needs parsing).
- **Security scanning** — Checks for SQL injection patterns (`DROP TABLE`, `UNION SELECT`) and XSS attacks (`<script>`, `onerror=`).
- **Nesting depth protection** — Prevents denial-of-service via deeply nested data structures (max depth limit).
- **Mismatch classification** — Categorizes issues as STRUCTURAL_EQUIVALENCE (fixable automatically), REPRESENTATIONAL_EQUIVALENCE (type coercion needed), UNKNOWN_AMBIGUOUS (needs AI help), or SEMANTIC_CONFLICT (irreconcilable).

---

#### `backend/layer2/audit_tests.py`

**What it does:** An engineering test harness that benchmarks the entire orchestrator pipeline for accuracy and latency.

**In simple terms:** This runs a battery of real questions through the system and checks whether the AI understood them correctly, picked the right widgets, and responded fast enough.

**What it tests:**
- **Intent parsing accuracy** — Given "What's the status of the pumps?", does the parser correctly identify it as a "query" intent about the "industrial" domain?
- **Widget selection quality** — Are the right widget types (KPI, trend, alerts) chosen for each query type?
- **Domain matching** — Do industrial questions produce industrial widgets?
- **Latency benchmarks** — Is the orchestrator responding within acceptable time limits?
- **Edge cases** — Greetings, out-of-scope questions, ambiguous queries.

---

#### `backend/layer2/tests.py`

**What it does:** Comprehensive unit test suite for all Layer 2 components (421 lines).

**Test classes:**
- `WidgetRegistryTests` — Verifies that all 18+ widget scenarios are registered with correct schemas and fixture variants.
- `IntentParserTests` — Tests intent classification (query, greeting, action, out-of-scope) across industrial, supply chain, people, alerts, and tasks domains.
- `WidgetSelectorTests` — Tests that the selector picks appropriate widgets, enforces hero sizing for the first widget, and respects the widget catalog.
- `DataCollectorTests` — Tests that RAG data collection produces valid data for each widget type.
- `OrchestratorTests` — Integration tests running full queries through the pipeline.
- `WidgetSchemaTests` — Tests schema validation catches invalid data and passes valid data.
- `IntegrationTests` — End-to-end tests combining multiple components.

---

### Reconciliation Sub-modules

The reconciliation system is split into specialized modules, each handling one stage of the data quality pipeline.

---

#### `backend/layer2/reconciliation/errors.py`

**What it does:** Defines the complete error hierarchy for reconciliation — every type of problem that can occur during data validation.

**Error types (223 lines):**
- `ReconcileError` — Base error with scenario, field path, original value, and attempted fixes
- `ClassificationError` — Failed to classify the type of mismatch
- `RewriteError` — A deterministic rewrite rule failed (includes `rule_id`)
- `ResolutionError` — LLM-based resolution failed (includes `attempts` and `last_llm_response`)
- `NormalizationError` — Unit conversion failed (includes `dimension`, `from_unit`, `to_unit`)
- `EscalationRequired` — Issue too complex for automation, needs human review. Includes `reason`, `missing_fields`, `conflicting_values`, and `recommendations`. Can generate a human-readable escalation ticket via `to_escalation_ticket()`.
- `SecurityViolation` — SQL injection, XSS, or DoS patterns detected. Blocks all further processing immediately.
- `ValidationGateError` — Final validation check failed (includes list of specific validation errors)

---

#### `backend/layer2/reconciliation/rewriter.py`

**What it does:** Applies deterministic, lossless, reversible transformations to fix data mismatches that have clear mechanical solutions.

**In simple terms:** If a number arrives as the string "42" but should be the integer 42, the rewriter can fix that automatically. Every fix it makes can be undone (reversed), so nothing is permanently altered.

**Eight rewrite rules (525 lines):**
1. `UnwrapDemoDataRule` — Unwraps `{demoData: {value: 42}}` → `{value: 42}`
2. `UnwrapSingletonArrayRule` — Unwraps `[{value: 42}]` → `{value: 42}`
3. `StringToIntRule` — Converts `"42"` → `42` (reversible)
4. `StringToFloatRule` — Converts `"3.14"` → `3.14` (reversible)
5. `StringToBoolRule` — Converts `"true"` → `True` (reversible)
6. `StringToNullRule` — Converts `"null"` → `None` (reversible)
7. `WhitespaceNormalizeRule` — Trims and normalizes whitespace
8. `ISODateNormalizeRule` — Normalizes date strings to ISO 8601 format

Every rule has an `inverse()` method — the transformation can always be reversed. Structural rules run first, then representational rules.

---

#### `backend/layer2/reconciliation/resolver.py`

**What it does:** Uses an LLM to resolve ambiguous data mismatches that can't be fixed mechanically.

**In simple terms:** When the rewriter encounters something like "500 kW" (a value with a unit embedded), it can't just do a simple conversion. It hands the problem to an AI that can understand the context and separate the number from the unit.

**How it works (479 lines):**
1. **Escalating prompts** — Tries three levels of increasingly strict prompts (basic → detailed → canonical)
2. **JSON schema validation** — LLM output must match a strict JSON schema (value, unit, metric_id, frame, assumptions, confidence, reasoning)
3. **Confidence threshold** — For sensitive fields like `metric_id` and `frame`, the LLM must express ≥90% confidence or the issue escalates to human review
4. **Assumption tracking** — Every LLM assumption is explicitly recorded in the provenance chain
5. **Safety validation** — Resolved values are re-checked for security patterns before being accepted
6. **Escalation** — If all 3 attempts fail or confidence is too low, raises `EscalationRequired` for human review

---

#### `backend/layer2/reconciliation/prompts.py`

**What it does:** Contains all LLM prompt templates used by the resolver (262 lines).

**Three escalating prompt levels:**
1. `BASIC_RESOLUTION_PROMPT` — Initial attempt with examples and clear rules
2. `DETAILED_RESOLUTION_PROMPT` — Adds confidence calibration guidance and shows examples of incorrect responses to avoid
3. `CANONICAL_RESOLUTION_PROMPT` — Final attempt restricted to purely syntactic (mechanical) transformations only

Also includes `RESOLVE_CANDIDATE_SCHEMA` (the JSON Schema that LLM output must match) and `ESCALATION_SUMMARY_TEMPLATE` (formats human-readable escalation reports).

---

#### `backend/layer2/reconciliation/normalizer.py`

**What it does:** Converts physical units within the same dimension — for example, watts to kilowatts, or Fahrenheit to Celsius.

**In simple terms:** If one data source reports power in watts (W) and another in kilowatts (kW), the normalizer converts everything to a consistent unit so the dashboard can display it correctly.

**How it works (335 lines):**
- `DimensionConfig` — Defines unit conversion factors within a dimension (e.g., POWER: W=1, kW=1000, MW=1000000)
- `DomainConfig` — Collections of dimensions with default units
- `DefaultDomainNormalizer` — Integrates with the `layer2/dimensions.py` registry for comprehensive unit conversion
- Handles value/unit pairs, comparison values (valueA/valueB), and time-series items
- Plugin architecture: `get_normalizer()` / `set_normalizer()` allow swapping the implementation

---

#### `backend/layer2/reconciliation/validator_integration.py`

**What it does:** The final validation gate — the last checkpoint before any data reaches the dashboard (192 lines).

**In simple terms:** Like airport security, this is the non-negotiable final check. Every piece of widget data must pass through here. There is no bypass.

**Key functions:**
- `validate_final(scenario, data, provenance)` — The ONLY exit point. Calls `validate_widget_data()` from the schema system. Raises `ValidationGateError` on failure.
- `validate_or_refuse()` — Graceful alternative that returns success/failure instead of raising
- `pre_validate_structure()` — Quick structural check before full validation
- CI enforcement: Module-level `_validation_invoked` flag ensures tests can verify that validation was actually called — `assert_validation_invoked()` fails the test if any code path skipped validation

---

#### `backend/layer2/reconciliation/audit.py`

**What it does:** Append-only audit logging for every reconciliation decision (320 lines).

**In simple terms:** Every time the system transforms, refuses, or escalates widget data, it writes a permanent record of what happened, why, and how. These records can't be edited or deleted — only appended.

**Three sink types:**
- `FileAuditSink` — Writes JSON Lines to a file, thread-safe via `threading.Lock`
- `MemoryAuditSink` — In-memory storage for testing
- `LoggingAuditSink` — Writes to Python's logging system at appropriate levels (INFO for transforms, WARNING for refusals)

**Convenience functions:**
- `audit_event()` — Log a general reconciliation event
- `audit_transform()` — Log a successful data transformation
- `audit_refuse()` — Log a data rejection
- `audit_escalate()` — Log an escalation to human review

---

#### `backend/layer2/reconciliation/tests/conftest.py`

**What it does:** Shared pytest fixtures for reconciliation tests (185 lines).

**Key fixtures provided:**
- `kpi_schema`, `comparison_schema` — Pre-built widget schemas for testing
- `mock_llm` — A deterministic mock LLM caller with pre-programmed responses
- `memory_audit` — An in-memory audit sink for verifying audit trail creation
- `reset_validation` — Auto-use fixture that resets the validation gate flag before each test
- Test data: `valid_kpi_data`, `invalid_kpi_data_string_value`, `ambiguous_kpi_data`, `semantic_conflict_data`, `xss_injection_data`, `sql_injection_data`

---

#### `backend/layer2/reconciliation/tests/test_reconciler.py`

**What it does:** Unit tests for the mismatch classification layer (210 lines).

**Test categories:**
- Value classification — string-to-number (representational), string-with-unit (ambiguous), invalid string (semantic)
- Security checks — SQL injection patterns, XSS script tags, XSS event handlers
- Nesting depth — Shallow OK, deep nesting blocked (DoS protection)
- Full mismatch classification — Valid data, string numbers, demoData wrappers, missing required fields, security violations

---

#### `backend/layer2/reconciliation/tests/test_pipeline.py`

**What it does:** Integration tests for the complete reconciliation pipeline (366 lines).

**Tests all 6 outcome types:**
1. PASSTHROUGH — Valid data passes through unchanged
2. TRANSFORM — String-to-number and demoData unwrapping
3. RESOLVE — LLM-based value-with-unit resolution
4. NORMALIZE — Unit conversions (W→kW, MW→kW)
5. REFUSE — Missing required fields or max retries exhausted
6. ESCALATE — Low-confidence semantic claims trigger human review

Plus security tests (XSS/SQL injection immediate rejection), validation gate enforcement, and provenance tracking verification (every transformation has `rule_id`, `timestamp`, `reversible` flag, and `proof_token`).

---

### Management Commands

These are scripts you run from the terminal to set up data, train models, and manage the system. They're invoked with `python manage.py <command_name>`.

---

#### `backend/industrial/management/commands/populate_industrial_db.py`

**What it does:** Seeds the database with realistic factory equipment (983 lines).

**In simple terms:** Creates a virtual factory full of equipment you can ask questions about. Without this, the system would have nothing to show.

**What it creates:**
- 20+ transformers (convert high voltage to usable voltage)
- 15+ diesel generators (backup power)
- 50+ electrical panels (distribute power to areas)
- 25+ UPS systems (battery backup for critical equipment)
- 10+ chillers (cooling systems)
- 40+ AHUs (air handling units for HVAC)
- 8+ cooling towers (industrial cooling)
- 60+ pumps (fluid movement)
- 15+ compressors (compressed air)
- 80+ motors (run machinery)
- 100+ energy meters (measure consumption)
- Plus initial alerts and maintenance records for each

Each piece of equipment gets realistic attributes: manufacturer, building, floor, zone, installation date, health percentage, current status, and specifications.

**Usage:** `python manage.py populate_industrial_db`

---

#### `backend/industrial/management/commands/generate_rich_data.py`

**What it does:** Generates massive volumes of realistic operational data on top of the base equipment records (1326 lines).

**In simple terms:** After `populate_industrial_db` creates the equipment, this command fills in the history — all the alerts, maintenance logs, and readings that a real factory would accumulate over months.

**What it generates:**
- 500+ alerts across 11 equipment categories with realistic descriptions and severities
- 2000+ maintenance records with work descriptions and completion dates
- 1500+ operational documents (SOPs, inspection reports, incident reports, calibration certificates, energy audits)
- 5000+ energy time-series readings (hourly kWh values with realistic patterns)
- 1000+ shift logs with operator notes
- 800+ work orders with priority levels and status tracking

Creates additional SQL tables directly: `operational_documents`, `energy_readings`, `shift_logs`, `work_orders`.

**Usage:** `python manage.py generate_rich_data`

---

#### `backend/layer2/management/commands/index_rag.py`

**What it does:** Indexes all industrial data into the RAG search engine for semantic search (66 lines).

**In simple terms:** Takes all the equipment data, alerts, and maintenance records from the database and loads them into ChromaDB (a vector search engine) so the AI can search by meaning rather than exact keywords. "How are the cooling systems?" would find chillers, cooling towers, and AHUs.

**Usage:** `python manage.py index_rag`

---

#### `backend/rl/management/commands/train_dpo.py`

**What it does:** Runs DPO (Direct Preference Optimization) training on collected user feedback (239 lines).

**In simple terms:** Takes the thumbs-up/thumbs-down feedback from users and uses it to teach the AI which widget selections are better. It's like training a dog — rewarding good choices and discouraging bad ones.

**Key options:**
- `--source db|file` — Get training data from database feedback or simulation files
- `--preset default|small_gpu|high_quality` — Pre-configured training profiles
- `--epochs`, `--batch-size`, `--learning-rate` — Fine-tune training parameters
- `--resume` — Continue from a previous checkpoint
- `--export` — Automatically convert the trained model for Ollama after training
- `--dry-run` — Preview what would happen without actually training

**Usage:** `python manage.py train_dpo --source db --preset small_gpu --export`

---

#### `backend/rl/management/commands/export_model.py`

**What it does:** Converts a trained model checkpoint to GGUF format and registers it with Ollama (128 lines).

**In simple terms:** After training, the model exists as a large set of weight files. This command compresses it into a format that Ollama (local LLM server) can use, then registers it so the orchestrator can start using the improved model.

**Key options:**
- `--checkpoint` — Path to the trained LoRA checkpoint (required)
- `--quantization` — Compression level (q4_k_m is a good balance of size vs quality; f16 keeps full precision)
- `--register` — Also register the exported model with Ollama
- `--list-models` — Show models currently registered with Ollama

**Usage:** `python manage.py export_model --checkpoint ./outputs/best --quantization q4_k_m --register`

---

#### `backend/rl/management/commands/evaluate_model.py`

**What it does:** Tests a trained model against held-out test data and optionally compares it to the base model (235 lines).

**In simple terms:** Before deploying a newly trained model, this checks how accurate it is. Does the fine-tuned version actually make better widget selections than the original? It compares loss values on chosen vs. rejected responses.

**Usage:** `python manage.py evaluate_model --checkpoint ./outputs/best --compare-base --num-samples 100`

---

### Additional Reinforcement Learning Files

---

#### `backend/rl/background_trainer.py`

**What it does:** Runs continuous RL training in a background daemon thread (278 lines).

**In simple terms:** While the system is running and serving users, a background process is constantly learning from their feedback. It samples recent experiences, computes which widget selections worked well, and nudges the selectors to make better choices over time.

**How it works:**
1. Runs in a daemon thread (dies when main process exits)
2. Periodically samples from the `ExperienceBuffer`
3. Creates preference pairs: good experiences (high reward) vs bad experiences (low reward)
4. Updates widget selector preferences using DPO-style learning
5. Updates fixture selector preferences similarly
6. Tracks training statistics (iterations, updates, best reward)

---

#### `backend/rl/dataset_builder.py`

**What it does:** Builds HuggingFace-compatible DPO training datasets from user feedback (281 lines).

**In simple terms:** Collects all the thumbs-up and thumbs-down feedback, pairs them up (good choice vs bad choice for the same question), and formats them into the structure that the DPO trainer expects.

**Two data sources:**
- `build_dataset_from_db()` — Pulls feedback from the Django database (`WidgetRating` model)
- `build_dataset_from_files()` — Reads from simulation result JSON files

**Output:** HuggingFace `DatasetDict` with train/test splits containing prompt/chosen/rejected triplets.

---

#### `backend/rl/export.py`

**What it does:** Full pipeline for deploying fine-tuned models to Ollama (407 lines).

**Pipeline stages:**
1. **Merge LoRA weights** — Combines the small fine-tuned adapter (LoRA) with the base model into a single model
2. **Convert to GGUF** — Transforms the model from HuggingFace format to GGUF (a compact format Ollama uses) via llama.cpp
3. **Create Modelfile** — Generates an Ollama Modelfile with system prompt and parameters
4. **Register with Ollama** — Runs `ollama create` to make the model available for inference

Also provides `list_ollama_models()` and `delete_ollama_model()` utilities.

---

#### `backend/rl/e2e_test.py`

**What it does:** End-to-end HTTP-based test suite for the Continuous RL system (569 lines).

**In simple terms:** Fires real HTTP requests at the running server and tests 20+ scenarios to make sure the full RL feedback loop works — from submitting a query, through getting a response, to submitting feedback and verifying it was recorded.

**Test categories:**
1. Basic flow — Health check, RL status, basic query, query_id verification
2. Feedback scenarios — Positive/negative feedback, corrections, widget interactions
3. Follow-up classification — New topic detection, refinement detection, correction detection
4. Multi-user — Session independence, concurrent queries
5. Edge cases — Empty/long/special-character transcripts, repeated feedback
6. RL system state — Experience accumulation, feedback stats, trainer stats

**Usage:** `python -m rl.e2e_test` (requires a running server on port 8100)

---

#### `backend/rl/test_continuous.py`

**What it does:** Unit tests for the continuous RL components without needing a running server (236 lines).

**Tests:**
- `ExperienceBuffer` — CRUD operations, sampling, buffer capacity
- `RewardSignalAggregator` and `ImplicitSignalDetector` — Follow-up classification, correction detection, reward computation
- `ContinuousRL` coordinator — Experience recording, feedback updates, status reporting
- `BackgroundTrainer` — Initialization and statistics

---

#### `backend/rl/tests.py`

**What it does:** Django TestCase-based tests for the offline RL training pipeline (347 lines).

**Test classes:**
- `TestConfig` — Verifies training configuration presets (default, small_gpu, high_quality)
- `TestDataFormatter` — Tests prompt/response formatting and DPO pair construction
- `TestDatasetBuilder` — Tests scenario listing, feedback merging, and dataset statistics
- `TestOnlineLearner` — Tests feedback buffering, retrain thresholds, and buffer clearing
- `TestTrainerMocked` — Tests the trainer and `TrainingResult` dataclass with mocked models
- `TestExportMocked` — Tests Ollama Modelfile generation and GGUF export utilities

---

### Benchmarks

---

#### `backend/benchmarks/benchmark_suite.py`

**What it does:** Comprehensive performance benchmarking suite that measures latency and accuracy across all system layers (676 lines).

**In simple terms:** Runs timing tests on every part of the system to find bottlenecks. How fast is speech-to-text? How fast is the RAG search? How fast is the whole pipeline end-to-end?

**What it benchmarks:**
- **STT Server** — Tests with 1s, 3s, and 5s audio clips at multiple iterations
- **RAG Accuracy** — 10 predefined queries checking domain and term matching
- **RAG Latency** — Repeated timing measurements of search operations
- **TTS Server** — Tests with varying sentence lengths
- **E2E Orchestrator** — Direct pipeline performance (bypassing HTTP)
- **E2E API** — Full HTTP round-trip performance

**Output:** JSON report with min/max/mean/median/p95/p99 statistics saved to `benchmarks/results/`.

**Usage:** `python -m benchmarks.benchmark_suite`

---

### Django Core Files

---

#### `backend/manage.py`

**What it does:** The standard Django management entry point (23 lines). Every `python manage.py <command>` goes through this file. It sets `DJANGO_SETTINGS_MODULE` to `command_center.settings` and delegates to Django's command dispatcher.

---

#### `backend/command_center/asgi.py`

**What it does:** The ASGI (Asynchronous Server Gateway Interface) entry point for the Django backend (17 lines). Used when deploying with async-capable servers like Daphne or Uvicorn. Sets up the same application as `wsgi.py` but with async support.

---

### Actions Module

Handles voice commands that DO something (not just ask questions).

---

#### `backend/actions/models.py`

**What it does:** Database tables for storing voice-triggered actions.

**Reminder Model:**
```python
class Reminder(models.Model):
    message = models.TextField()              # "Check pump 3 pressure"
    trigger_time = models.DateTimeField()     # When to remind
    recurring = models.CharField()             # "daily", "weekly", or blank
    status = models.CharField(choices=[
        ("pending", "Pending"),
        ("triggered", "Triggered"),
        ("dismissed", "Dismissed"),
    ])
    entity = models.CharField()               # Related equipment name
```
**What this means:** Stores reminders that users set via voice, like "Remind me to check pump 3 in 30 minutes."

**Message Model:**
```python
class Message(models.Model):
    recipient = models.CharField()   # "maintenance team"
    content = models.TextField()     # "The chiller needs inspection"
    channel = models.CharField(choices=[
        ("internal", "Internal"),
        ("sms", "SMS"),
        ("email", "Email"),
    ])
    status = models.CharField()      # "queued", "sent", "failed"
```
**What this means:** Stores messages to be sent, like "Send a message to maintenance about the chiller issue."

**DeviceCommand Model:**
```python
class DeviceCommand(models.Model):
    device_type = models.CharField()        # "pump"
    device_name = models.CharField()        # "pump_3"
    command = models.CharField()            # "start", "stop", "set_parameter"
    parameters = models.JSONField()         # {"speed": 75}
    requires_confirmation = models.BooleanField(default=True)
    confirmed = models.BooleanField(default=False)
    status = models.CharField(choices=[
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("executed", "Executed"),
        ("failed", "Failed"),
        ("rejected", "Rejected"),
    ])
```
**What this means:** Stores equipment control commands like "Start pump 3." These require confirmation for safety - you don't want accidental "stop everything" commands!

---

#### `backend/actions/handlers.py`

**What it does:** Executes voice commands and saves them to the database.

```python
class ActionHandler:
    def execute(self, intent: ParsedIntent) -> ActionResult:
        handlers = {
            "action_reminder": self._create_reminder,
            "action_message": self._send_message,
            "action_control": self._device_command,
            "action_task": self._create_task,
        }
        handler = handlers.get(intent.type)
        return handler(intent)
```
**What this means:** Routes each action type to its handler function.

**Creating a reminder:**
```python
def _create_reminder(self, intent: ParsedIntent) -> ActionResult:
    trigger_time = self._parse_trigger_time(params)

    reminder = Reminder.objects.create(
        message=message,
        trigger_time=trigger_time,
        recurring=params.get("recurring", ""),
    )

    return ActionResult(
        success=True,
        voice_response=f"Reminder set for {time_str}: {message[:60]}",
    )
```
**What this means:** Creates a reminder in the database and confirms it to the user.

**Device command (with safety):**
```python
def _device_command(self, intent: ParsedIntent) -> ActionResult:
    cmd = DeviceCommand.objects.create(
        device_name=device_name,
        command=command,
        requires_confirmation=True,  # Safety first!
    )

    return ActionResult(
        success=True,
        voice_response=(
            f"Command '{command}' for {device_name} is pending confirmation. "
            f"Please confirm to proceed."
        ),
    )
```
**What this means:** Equipment commands don't run immediately - they wait for confirmation. This prevents accidents.

---

#### `backend/actions/admin.py`

**What it does:** Registers all action-related models with the Django admin panel.

**Models registered:**
- `Reminder` — Scheduled reminders ("Check pump pressure at 3 PM")
- `Message` — Messages sent between operators
- `DeviceCommand` — Commands sent to equipment ("Start pump 3")
- `ActionLog` — Audit log of all executed actions

Each registration includes `list_display` (columns shown), `list_filter` (sidebar filters), and `search_fields` (searchable columns) for easy browsing in the admin interface.

---

#### `backend/actions/apps.py`

**What it does:** Declares the Actions Django application.

```python
class ActionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actions'
    verbose_name = 'Command Center Actions'
```

---

#### `backend/actions/urls.py`

**What it does:** Maps the Actions API endpoints.

**Routes:**
- `GET/POST /api/actions/reminders/` — List or create reminders
- `GET/POST /api/actions/messages/` — List or create messages
- `GET/POST /api/actions/commands/` — List or create device commands
- `POST /api/actions/commands/{id}/confirm/` — Confirm a pending device command
- `GET /api/actions/log/` — View the action audit log

---

#### `backend/actions/views.py`

**What it does:** API request handlers for the actions system (160 lines).

**Key views:**
- `ReminderViewSet` — CRUD for voice-triggered reminders. When a user says "Remind me to check the boiler in 30 minutes," the frontend creates a reminder here.
- `MessageViewSet` — CRUD for inter-operator messages
- `DeviceCommandViewSet` — CRUD for equipment commands with a `confirm` action that marks commands as approved and logs them
- `ActionLogViewSet` — Read-only access to the audit trail of all executed actions

---

### Feedback Module

Collects user feedback to improve the system over time.

---

#### `backend/feedback/models.py`

**What it does:** Stores user ratings and feedback on widgets.

```python
class WidgetRating(models.Model):
    entry_id = models.CharField()      # Which widget was rated
    rating = models.CharField(choices=[("up", "Up"), ("down", "Down")])
    tags = models.JSONField()          # ["wrong data", "confusing"]
    notes = models.TextField()         # Free-text feedback
    device_id = models.CharField()     # Browser fingerprint
```
**What this means:** When users click thumbs up/down on a widget, it's stored here. This helps the system learn what works and what doesn't.

```python
class WidgetFeedback(models.Model):
    scenario = models.CharField()      # "trend"
    variant = models.CharField()       # "trend_line-standard"
    feedback_type = models.CharField(choices=[
        ("size", "Size Adjustment"),
        ("issue", "Issue Report"),
    ])
    data = models.JSONField()          # Full feedback details
```
**What this means:** More detailed feedback about specific widgets - whether they're the wrong size, showing wrong data, etc.

---

#### `backend/feedback/views.py`

**What it does:** API endpoints for submitting and retrieving ratings.

**In simple terms:** The "doors" that the frontend uses to send thumbs up/down and get feedback data.

**Single Rating Endpoint:**
```python
@api_view(["GET", "POST"])
def ratings_list(request):
    if request.method == "GET":
        qs = WidgetRating.objects.all()
        return Response(WidgetRatingSerializer(qs, many=True).data)

    # POST — upsert (update or create)
    obj, created = WidgetRating.objects.update_or_create(
        entry_id=entry_id,
        device_id=device_id,
        defaults={
            "rating": serializer.validated_data["rating"],
            "tags": serializer.validated_data.get("tags", []),
            "notes": serializer.validated_data.get("notes", ""),
        },
    )
```
**What this means:**
- GET: Returns all ratings
- POST: Creates or updates a rating (if you rate the same widget twice, it updates instead of creating duplicate)

**Bulk Rating Sync:**
```python
@api_view(["POST"])
def ratings_bulk(request):
    ratings_map = request.data.get("ratings", {})
    device_id = request.data.get("device_id", "")

    for entry_id, payload in ratings_map.items():
        WidgetRating.objects.update_or_create(
            entry_id=entry_id,
            device_id=device_id,
            defaults={...}
        )

    return Response({"created": created_count, "updated": updated_count})
```
**What this means:** The frontend stores ratings in the browser first (localStorage), then syncs them all at once when coming online. This handles offline usage.

---

#### `backend/feedback/signals.py`

**What it does:** Connects feedback to the learning system automatically.

**In simple terms:** Whenever someone rates a widget, this code automatically tells the AI learning system about it.

```python
@receiver(post_save, sender=WidgetRating)
def on_rating_saved(sender, instance, created, **kwargs):
    """Notify online learner of new feedback."""
    if not created:
        return  # Only process new ratings

    # Add to online learner buffer
    feedback = {
        "entry_id": instance.entry_id,
        "rating": instance.rating,
        "tags": instance.tags or [],
        "notes": instance.notes or "",
    }

    should_retrain = online_learner.add_feedback(feedback)

    if should_retrain:
        # Queue async retraining task
        async_task("rl.online_learner.trigger_retrain")
```
**What this means:**
1. Django "signals" automatically call this function when a rating is saved
2. The rating is added to the learning buffer
3. If enough ratings have accumulated, trigger a retraining job

This is how the system automatically improves over time without manual intervention.

---

#### `backend/feedback/admin.py`

**What it does:** Django admin registration for feedback models. Currently empty — no feedback models are exposed in the admin panel. Feedback is managed through the API.

---

#### `backend/feedback/apps.py`

**What it does:** Declares the Feedback Django application and initializes key systems on startup.

```python
class FeedbackConfig(AppConfig):
    name = 'feedback'
    verbose_name = 'Widget Feedback & Ratings'

    def ready(self):
        import feedback.signals       # Activate signal handlers
        from rl.online_learner import get_online_learner
        get_online_learner()           # Start online learning system
```
**What this means:** When Django starts, this automatically:
1. Activates the signal handlers that process new feedback entries
2. Initializes the online learner that can retrain from accumulated feedback

---

#### `backend/feedback/serializers.py`

**What it does:** Converts feedback models to/from JSON for the API.

**Two serializers:**
- `WidgetRatingSerializer` — Handles individual widget ratings (entry_id, rating, tags, notes, timestamp)
- `WidgetFeedbackSerializer` — Handles the full feedback export format with optional notes

---

#### `backend/feedback/urls.py`

**What it does:** Maps the Feedback API endpoints.

**Routes:**
- `POST /api/ratings/` — Submit a single widget rating
- `POST /api/ratings/bulk/` — Submit multiple ratings at once (batch operation)
- `POST /api/feedback/` — Submit general feedback with notes and tags

---

#### `backend/feedback/tests.py`

**What it does:** Placeholder test file for the feedback module. Currently empty — feedback testing is covered by the RL test suite and E2E tests.

---

### Industrial Module

Defines all the factory equipment the system can monitor.

---

#### `backend/industrial/models.py`

**What it does:** Database models for every type of industrial equipment.

**In simple terms:** Templates for storing information about pumps, motors, generators, chillers, and all other factory equipment.

**Base Equipment (common fields for all equipment):**
```python
class BaseEquipment(models.Model):
    equipment_id = models.CharField(unique=True)     # "PUMP-001"
    name = models.CharField()                        # "Main Coolant Pump"
    location = models.CharField()                    # "Building A, Floor 2"
    status = models.CharField(choices=[
        ("running", "Running"),
        ("stopped", "Stopped"),
        ("maintenance", "Under Maintenance"),
        ("fault", "Fault"),
    ])
    health_score = models.IntegerField()             # 0-100
    last_maintenance = models.DateTimeField()
    running_hours = models.FloatField()
```
**What this means:** Every piece of equipment has these basic properties.

**Transformer (electrical power):**
```python
class Transformer(BaseEquipment):
    capacity_kva = models.FloatField()       # Power rating
    primary_voltage = models.FloatField()    # Input voltage
    secondary_voltage = models.FloatField()  # Output voltage
    load_percent = models.FloatField()       # Current load (0-100%)
    oil_temperature = models.FloatField()    # For cooling
    winding_temperature = models.FloatField()
```

**Diesel Generator (backup power):**
```python
class DieselGenerator(BaseEquipment):
    capacity_kw = models.FloatField()        # Power output
    fuel_level_percent = models.FloatField() # How much fuel left
    coolant_temperature = models.FloatField()
    oil_pressure = models.FloatField()
    total_run_hours = models.FloatField()
```

**Chiller (cooling equipment):**
```python
class Chiller(BaseEquipment):
    capacity_tr = models.FloatField()              # Cooling capacity (tons)
    refrigerant_type = models.CharField()          # "R134a", "R410A"
    chilled_water_supply_temp = models.FloatField()
    chilled_water_return_temp = models.FloatField()
    power_consumption_kw = models.FloatField()
```

**Pump:**
```python
class Pump(BaseEquipment):
    flow_rate = models.FloatField()          # m³/hr
    motor_kw = models.FloatField()           # Motor power
    discharge_pressure = models.FloatField() # Output pressure
    vibration = models.FloatField()          # Vibration level (high = problem)
    bearing_temperature = models.FloatField()
```

**Alert (alarms and warnings):**
```python
class Alert(models.Model):
    equipment_id = models.CharField()
    severity = models.CharField(choices=[
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ])
    alert_type = models.CharField(choices=[
        ("threshold", "Threshold Breach"),
        ("fault", "Equipment Fault"),
        ("maintenance", "Maintenance Due"),
    ])
    message = models.TextField()             # "Temperature exceeded 80°C"
    acknowledged = models.BooleanField()     # Has someone seen this?
    resolved = models.BooleanField()         # Is it fixed?
```
**What this means:** Alerts are created when something goes wrong - temperature too high, equipment failure, maintenance needed, etc.

---

#### `backend/industrial/admin.py`

**What it does:** Registers all 12 equipment model types with the Django admin panel (108 lines).

**In simple terms:** Makes all factory equipment browsable and searchable in Django's built-in admin dashboard at `/admin/`.

**Models registered with custom admin configurations:**
| Model | List Display Columns | Filters | Search |
|-------|---------------------|---------|--------|
| Transformer | name, capacity_kva, voltage, status | status, building | name, location |
| DieselGenerator | name, capacity_kw, fuel_type, status | status, fuel_type | name |
| ElectricalPanel | name, panel_type, voltage, status | panel_type, building | name |
| UPSSystem | name, capacity_kva, battery_type, status | status, battery_type | name |
| Chiller | name, capacity_tr, refrigerant, status | status, building | name |
| AHU | name, capacity_cfm, zone, status | status, zone | name |
| CoolingTower | name, capacity_tr, tower_type, status | status, tower_type | name |
| Pump | name, pump_type, flow_rate, status | status, pump_type | name |
| Compressor | name, capacity_cfm, compressor_type, status | status, compressor_type | name |
| Motor | name, power_kw, voltage, status | status, building | name |
| EnergyMeter | name, meter_type, location, status | meter_type, building | name |
| Alert | title, severity, equipment, status | severity, status, created_at | title, equipment |
| MaintenanceRecord | title, equipment, maintenance_type, status | maintenance_type, status | title |

---

#### `backend/industrial/apps.py`

**What it does:** Declares the Industrial Django application.

```python
class IndustrialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'industrial'
    verbose_name = 'Industrial Energy Database'
```

---

### Reinforcement Learning

The system learns and improves based on user feedback.

---

#### `backend/rl/continuous.py`

**What it does:** Coordinates the continuous learning system.

**In simple terms:** Like a student who keeps learning - every time a user says "good" or "bad," the system remembers and tries to do better next time.

```python
class ContinuousRL:
    def record_experience(self, query_id, transcript, parsed_intent, widget_plan, ...):
        """Called after every question - stores what happened."""
        experience = Experience(
            query_id=query_id,
            transcript=transcript,
            parsed_intent=parsed_intent,
            widget_plan=widget_plan,
            ...
        )
        self.buffer.add(experience)
```
**What this means:** Every time someone asks a question, we record:
- What they asked
- What we understood
- What we showed them
- How long it took

```python
    def update_feedback(self, query_id, rating=None, interactions=None):
        """Called when user gives feedback (thumbs up/down)."""
        self.buffer.update_feedback(query_id, {"rating": rating})

        # Compute reward and learn
        exp = self.buffer.get_by_query_id(query_id)
        exp.computed_reward = self.reward_aggregator.compute_reward(exp)
```
**What this means:** When a user clicks thumbs up/down:
1. Find the experience we recorded earlier
2. Add the feedback to it
3. Calculate a "reward score" (positive for thumbs up, negative for down)
4. Use this to improve future selections

---

#### `backend/rl/online_learner.py`

**What it does:** Manages continuous learning from production feedback.

**In simple terms:** A system that accumulates user feedback and automatically retrains the AI when enough data has been collected.

**The FeedbackSample dataclass:**
```python
@dataclass
class FeedbackSample:
    entry_id: str           # Which widget was rated
    rating: str             # "up" or "down"
    tags: list[str]         # ["wrong data", "too small"]
    notes: str              # Free text feedback
    timestamp: datetime     # When the rating happened
    scenario: str           # "trend", "kpi", etc.
    fixture: str            # "trend_line-standard"
    query: str              # Original user question
```
**What this means:** Each piece of feedback contains everything needed to learn from it.

**The OnlineLearner class:**
```python
class OnlineLearner:
    def __init__(self, min_samples=50, max_buffer_size=1000, retrain_interval_hours=24):
        self.min_samples = min_samples           # Need at least 50 ratings before training
        self.max_buffer_size = max_buffer_size   # Keep at most 1000 samples
        self.retrain_interval_hours = retrain_interval_hours  # Train at most daily

        self.feedback_buffer = deque(maxlen=max_buffer_size)  # Ring buffer
        self.last_train_time = None
        self.is_training = False
```
**What this means:** Configuration for when to trigger training:
- Wait until 50 ratings accumulate
- Don't keep more than 1000 ratings (old ones fall off)
- Don't train more than once per day

**Adding feedback:**
```python
def add_feedback(self, feedback: dict) -> bool:
    sample = FeedbackSample(
        entry_id=feedback["entry_id"],
        rating=feedback["rating"],
        ...
    )

    with self.lock:  # Thread-safe
        self.feedback_buffer.append(sample)
        self._save_buffer()  # Persist to disk

    return self.should_retrain()  # Returns True if training should start
```
**What this means:** Thread-safe because Django handles multiple requests at once.

**Triggering training:**
```python
def _run_training(self) -> bool:
    # Snapshot and clear buffer
    with self.lock:
        samples = list(self.feedback_buffer)
        self.feedback_buffer.clear()

    # Build training dataset from samples
    widget_pairs = build_widget_dpo_pairs(entries, all_scenarios)
    fixture_pairs = build_fixture_dpo_pairs(entries, fixture_descriptions)
    dataset = pairs_to_hf_dataset(all_pairs)

    # Run DPO training
    trainer = CommandCenterDPOTrainer()
    trainer.load_base_model()
    result = trainer.train(train_dataset=train_data)

    # Export and deploy new model
    if self.auto_export:
        export_to_ollama(checkpoint_path=result.checkpoint_path)

    self.last_train_time = datetime.now()
```
**What this means:** The full training pipeline:
1. Take all accumulated feedback
2. Convert to training pairs (good vs bad choices)
3. Fine-tune the AI model using DPO (Direct Preference Optimization)
4. Export the improved model for use

---

#### `backend/rl/data_formatter.py`

**What it does:** Converts user ratings into training data for the AI.

**In simple terms:** Turns "thumbs up on widget A, thumbs down on widget B" into "when asked X, prefer A over B."

**DPO Training Pairs:**
```python
@dataclass
class DPOPair:
    prompt: str      # The user's question + context
    chosen: str      # The response that got thumbs up
    rejected: str    # The response that got thumbs down
    question_id: str # Links back to original interaction
```
**What this means:** DPO (Direct Preference Optimization) trains the AI by showing it pairs of choices and which one humans preferred.

**Building widget selection pairs:**
```python
def build_widget_dpo_pairs(entries: list[dict], all_scenarios: list[str]) -> list[DPOPair]:
    # Group ratings by question
    by_question = defaultdict(lambda: {
        "liked_scenarios": set(),
        "disliked_scenarios": set(),
    })

    for entry in entries:
        qid = entry.get("question_id")
        if entry["rating"] == "up":
            by_question[qid]["liked_scenarios"].add(entry["scenario"])
        else:
            by_question[qid]["disliked_scenarios"].add(entry["scenario"])

    # Create DPO pairs
    pairs = []
    for qid, data in by_question.items():
        prompt = format_widget_selection_prompt(query, all_scenarios)
        chosen = format_widget_selection_response(data["liked_scenarios"])
        rejected = format_widget_selection_response(data["disliked_scenarios"])

        pairs.append(DPOPair(prompt=prompt, chosen=chosen, rejected=rejected))

    return pairs
```
**What this means:** For each question where users rated some widgets good and others bad:
1. Group all the "liked" widgets together
2. Group all the "disliked" widgets together
3. Create a training example: "For this question, choose these (liked) not those (disliked)"

**Example training pair:**
```
Prompt: "User query: What's the pump status?
         Available scenarios: [kpi, trend, alerts, comparison, ...]
         Select the most appropriate widgets."

Chosen: "kpi (compact), trend (hero), alerts (normal)"
Rejected: "distribution (expanded), matrix-heatmap (hero)"
```

---

#### `backend/rl/experience_buffer.py`

**What it does:** Stores recent interactions in memory for learning.

```python
@dataclass
class Experience:
    query_id: str                    # Unique identifier
    timestamp: datetime              # When it happened
    transcript: str                  # What user asked
    parsed_intent: dict              # How we understood it
    widget_plan: dict                # What widgets we chose
    fixtures: dict                   # Which visual variants
    explicit_feedback: dict = None   # Thumbs up/down
    implicit_signals: dict = None    # Other behavior signals
    computed_reward: float = 0.0     # Final reward value
```
**What this means:** Each experience captures everything about one interaction.

```python
class ExperienceBuffer:
    def add(self, experience: Experience):
        """Add new experience to buffer."""
        self._buffer.append(experience)
        # Keep buffer from growing too large
        if len(self._buffer) > self._max_size:
            self._buffer.pop(0)  # Remove oldest
```
**What this means:** A "ring buffer" that keeps the most recent interactions. Old ones get removed when new ones come in.

---

#### `backend/rl/reward_signals.py`

**What it does:** Calculates how "good" each interaction was.

```python
class RewardSignalAggregator:
    def compute_reward(self, experience: Experience) -> float:
        reward = 0.0

        # Explicit feedback (thumbs up/down)
        if experience.explicit_feedback:
            rating = experience.explicit_feedback.get("rating")
            if rating == "up":
                reward += 1.0
            elif rating == "down":
                reward -= 1.0

        # Implicit signals (user behavior)
        if experience.follow_up_type == "drill_down":
            reward += 0.5  # User wanted more detail = good
        elif experience.follow_up_type == "refinement":
            reward -= 0.3  # User had to rephrase = not great

        return reward
```
**What this means:**
- Thumbs up = +1.0 (good)
- Thumbs down = -1.0 (bad)
- User drilled down for more = +0.5 (interested = good)
- User had to rephrase = -0.3 (we didn't understand well)

---

## Frontend Files

The frontend is built with React/Next.js and runs in the user's browser. It handles the user interface - what users see and interact with.

---

### Library Utilities

Helper code used throughout the frontend.

---

#### `frontend/src/lib/events.ts`

**What it does:** A messaging system that lets different parts of the app talk to each other.

**In simple terms:** Like a radio station - some parts "broadcast" messages, others "tune in" to hear them.

```typescript
class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();
```
**What this means:** A dictionary that maps event names to lists of functions that want to hear about them.

```typescript
  on(eventType: string, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(eventType)?.delete(handler);
    };
  }
```
**What this means:** "I want to listen for events of type X, and here's what to do when one happens." Returns a function to stop listening.

```typescript
  emit(event: CommandCenterEvent): void {
    const typeHandlers = this.handlers.get(event.type);
    typeHandlers?.forEach((handler) => {
      try {
        handler(event);
      } catch (e) {
        console.error("Handler error:", e);
      }
    });
  }
```
**What this means:** "Here's an event - tell everyone who's listening."

**Usage example:**
```typescript
// Component A: "I want to know when layouts update"
commandCenterBus.on("LAYOUT_UPDATE", (event) => {
  setWidgets(event.layout.widgets);
});

// Component B: "New layout ready!"
commandCenterBus.emit({ type: "LAYOUT_UPDATE", layout: {...} });
```

---

#### `frontend/src/lib/config.ts`

**What it does:** Stores configuration settings for the frontend.

```typescript
export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100',
  },
  stt: {
    serverUrl: process.env.NEXT_PUBLIC_STT_SERVER_URL || 'http://localhost:8890',
  },
  tts: {
    serverUrl: process.env.NEXT_PUBLIC_TTS_SERVER_URL || 'http://localhost:8880',
  },
};
```
**What this means:** URLs for different services. Can be overridden with environment variables.

---

#### `frontend/src/lib/layer2/client.ts`

**What it does:** Talks to the Layer 2 backend API.

```typescript
class Layer2Service {
  async processTranscript(text: string): Promise<Layer2Response> {
    const response = await fetch(`${this.baseUrl}/api/layer2/orchestrate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: text,
        session_id: this.sessionId,
        context: {},
      }),
    });
    return response.json();
  }
}
```
**What this means:** Sends the user's words to the backend and gets back what to show and say.

---

#### `frontend/src/lib/layer2/index.ts`

**What it does:** Barrel export file that re-exports everything from `client.ts` — the Layer 2 AI + RAG module.

**Exports:** `orchestrate`, `getFiller`, `checkProactiveTrigger`, `getLayer2Service`, `Layer2Service`, and all related types (`Layer2Intent`, `Layer2RAGResult`, `Layer2WidgetCommand`, `Layer2LayoutJSON`, `Layer2Response`, `ProactiveTrigger`).

---

#### `frontend/src/lib/personaplex/protocol.ts`

**What it does:** Implements the PersonaPlex/Moshi binary WebSocket protocol (107 lines).

**In simple terms:** The voice AI server speaks a custom binary language over WebSockets. This file defines that language — how to encode and decode messages with single-byte type prefixes.

**Message types (single-byte prefix):**
| Prefix | Type | Content |
|--------|------|---------|
| 0x00 | Handshake | Session setup with model, voice, system prompt |
| 0x01 | Audio | Raw Opus audio bytes |
| 0x02 | Text | UTF-8 text (transcripts, responses) |
| 0x03 | Control | start, endTurn, pause, restart |
| 0x04 | Metadata | JSON metadata blobs |
| 0x05 | Error | Error messages |
| 0x06 | Ping | Keep-alive |

**Key exports:** `encodeMessage()`, `decodeMessage()`, `WSMessage` type, `ControlAction` type, `SocketStatus` type.

---

#### `frontend/src/lib/personaplex/decoder.ts`

**What it does:** Manages a Web Worker for decoding Opus/Ogg audio from the PersonaPlex server (79 lines).

**In simple terms:** When the AI server sends back audio, it's compressed in Opus format. This file creates a Web Worker that decodes that audio into raw PCM samples the browser can play through speakers.

**Key exports:** `createDecoderWorker()`, `initDecoder(worker, sampleRate)` — includes a "warmup" step that sends a synthetic audio header to prime the decoder.

---

#### `frontend/src/lib/personaplex/persona.ts`

**What it does:** Defines the system prompt for the PersonaPlex AI voice assistant (12 lines).

**The prompt:** Restricts the assistant to industrial operations topics only — production lines, equipment status, quality metrics, supply chain, safety protocols. This keeps the AI focused on factory work rather than general conversation.

---

### Layer 2 Frontend Components

---

#### `frontend/src/components/layer2/types.ts`

**What it does:** TypeScript interfaces for the frontend RAG pipeline system (28 lines).

**Key types:**
- `RAGPipeline` — Interface all pipelines must implement: `domain`, `enabled`, `execute(query)`, `healthCheck()`
- `PipelineRegistryEntry` — Wraps a pipeline with a priority number for ordering

---

#### `frontend/src/components/layer2/orchestrator.ts`

**What it does:** The frontend-side Layer 2A orchestrator (241 lines).

**In simple terms:** This is a frontend copy of the intent parsing logic. It receives transcripts from Layer 1, classifies them by domain using keyword matching across 5 domains (industrial, supply, people, alerts, tasks), and spawns parallel RAG queries.

**Key methods:**
- `registerPipeline()` / `unregisterPipeline()` — Add or remove RAG data sources
- `parseIntent(transcript)` — Keyword-based domain classification
- `executeParallel(queries)` — Runs RAG queries in parallel via `Promise.allSettled`
- `processTranscript(transcript)` — Full pipeline: parse → query → emit results

---

#### `frontend/src/components/layer2/pipelines/industrial.ts`

**What it does:** The frontend Industrial RAG pipeline (77 lines). Sends queries to the Django backend endpoint (`/api/layer2/rag/industrial/`) to retrieve device metrics, status, and alert history.

---

### Spot Component

---

#### `frontend/src/components/spot/SpotWalk.ts`

**What it does:** State machine controller for "Spot," the visual AI indicator (163 lines).

**In simple terms:** Spot is a small animated dot in the status bar that shows what the AI is doing — glowing when idle, pulsing when listening, rapid when speaking. SpotWalk maps internal states to visual configurations.

**State → Visual mapping:**
| State | Particle Speed | Density | Color | Chaos |
|-------|---------------|---------|-------|-------|
| idle | 0.3 | 20 | cyan | 0.1 |
| listening | 0.8 | 40 | green | 0.3 |
| speaking | 1.2 | 60 | blue | 0.5 |
| processing | 0.6 | 30 | amber | 0.8 |
| success | 0.4 | 50 | green | 0.2 |
| error | 1.5 | 15 | red | 1.0 |

---

#### `frontend/src/components/spot/Spot.tsx`

**What it does:** The visual renderer for Spot — an animated particle canvas (157 lines).

**In simple terms:** Draws a cluster of particles on an HTML canvas. The particles float, drift, and pulse according to the state set by SpotWalk. There's also a soft glow effect behind the particles.

**How it works:** Subscribes to SpotWalk state changes → initializes particles at random positions within a circular boundary → animates them with velocity, chaos, and center-attraction → draws them on a canvas with the configured color and opacity.

---

### Layer 1 Components

Voice input/output components.

---

#### `frontend/src/components/layer1/useVoicePipeline.ts`

**What it does:** The main voice processing hook - coordinates speech-to-text, backend calls, and text-to-speech.

**In simple terms:** The "conductor" that makes sure everything happens in the right order when you speak.

**State management:**
```typescript
const [state, setState] = useState<VoicePipelineState>("idle");
// Possible states: "idle" | "listening" | "speaking" | "error"

const [messages, setMessages] = useState<ConversationMessage[]>([]);
// Conversation history
```

**The main flow:**
```typescript
// When transcript changes (user is speaking)
useEffect(() => {
  if (!userTranscript) return;

  // Check if speech has stabilized (user stopped talking)
  if (userTranscript === lastTranscriptRef.current) {
    stableCountRef.current++;

    if (stableCountRef.current >= requiredStableCount) {
      // User stopped - send to backend
      const delta = userTranscript.slice(lastSentLenRef.current).trim();
      processOneTranscript(delta);
    }
  }
}, [userTranscript]);
```
**What this means:**
1. Track what the user is saying
2. When the transcript stops changing (user stopped talking)
3. Send the new part to the backend

**Processing a transcript:**
```typescript
const processOneTranscript = useCallback((text: string) => {
  console.info(`[VoicePipeline] Processing: "${text}"`);
  setState("processing");

  layer2Service.processTranscript(text)
    .then(() => {
      setState("ready");
    })
    .catch((err) => {
      setError(err.message);
      setState("ready");
    });
}, [layer2Service]);
```

**Handling the response:**
```typescript
const handleResponse = (response: Layer2Response) => {
  const voiceResponse = response.voice_response;

  // Add to conversation
  addMessage("ai", voiceResponse, "response");

  // Update the dashboard
  commandCenterBus.emit({
    type: "LAYOUT_UPDATE",
    layout: response.layout_json,
  });

  // Speak the response
  setState("speaking");
  speak(voiceResponse, {
    onEnd: () => {
      setState("listening");  // Ready for next question
    },
  });
};
```
**What this means:**
1. Get the voice response text
2. Add it to the conversation display
3. Tell the dashboard to update (broadcast LAYOUT_UPDATE)
4. Speak the response out loud
5. When done speaking, go back to listening

**VAD (Voice Activity Detection):**
```typescript
const { start: startVAD, isSpeaking: vadIsSpeaking } = useVAD({
  onSpeechEnd: () => {
    // User stopped talking - process immediately
    vadSpeechEndRef.current = true;
  },
});
```
**What this means:** VAD detects when someone stops speaking, so we can send the transcript immediately instead of waiting for a timeout.

---

#### `frontend/src/components/layer1/useSTT.ts`

**What it does:** Converts speech to text using a server or browser API.

```typescript
export function useSTT(deviceId?: string) {
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [isListening, setIsListening] = useState(false);
```

**Server-based STT:**
```typescript
// Send audio to server for transcription
const transcribeAudio = async (audioData: Blob) => {
  const formData = new FormData();
  formData.append("audio", audioData);

  const response = await fetch(`${sttServerUrl}/transcribe`, {
    method: "POST",
    body: formData,
  });

  const result = await response.json();
  setTranscript(result.text);
};
```

**Browser fallback (Web Speech API):**
```typescript
// If server isn't available, use browser's built-in speech recognition
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;

recognition.onresult = (event) => {
  let interim = "";
  let final = "";

  for (let i = event.resultIndex; i < event.results.length; i++) {
    if (event.results[i].isFinal) {
      final += event.results[i][0].transcript;
    } else {
      interim += event.results[i][0].transcript;
    }
  }

  setTranscript(prev => prev + final);
  setInterimTranscript(interim);
};
```
**What this means:** While you're speaking, we show "interim" results (might change). When you pause, we finalize them.

---

#### `frontend/src/components/layer1/useKokoroTTS.ts`

**What it does:** Converts text to speech using the Kokoro engine.

```typescript
export function useKokoroTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback(async (text: string, options?: TTSOptions) => {
    setIsSpeaking(true);

    try {
      // Request audio from TTS server
      const response = await fetch(`${ttsServerUrl}/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: "NATF2" }),
      });

      // Play the audio
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setIsSpeaking(false);
        options?.onEnd?.();
      };

      audio.play();
    } catch (error) {
      setIsSpeaking(false);
      options?.onError?.(error);
    }
  }, [ttsServerUrl]);

  return { speak, isSpeaking, stop };
}
```
**What this means:**
1. Send text to the TTS server
2. Get audio back
3. Play it through the browser
4. Call callbacks when done or on error

---

#### `frontend/src/components/layer1/usePersonaPlex.ts`

**What it does:** The core React hook for Layer 1 Voice I/O — the largest and most complex frontend file (1005 lines).

**In simple terms:** This hook establishes a full-duplex audio connection with the PersonaPlex-7B AI server. It captures your microphone audio, compresses it to Opus format, streams it over a WebSocket, receives the AI's audio response, decodes it, and plays it through your speakers — all simultaneously and in real-time.

**Audio pipeline:**
```
Microphone → opus-recorder (Opus 24kHz) → WebSocket → PersonaPlex Server
                                                          ↓
Speakers ← AudioWorklet ← Opus Decoder Worker ← WebSocket
```

**Key features:**
- Ctrl+Space hotkey to toggle listening
- 30-second inactivity auto-disconnect
- 5-second ping keepalive to prevent WebSocket timeout
- Text injection for V2 TTS fallback
- Audio analyzer nodes for waveform visualization
- Full metrics collection (latency, audio quality, connection state)
- Conversation message history tracking

**Returns:** `{ state, transcripts, isListening, isSpeaking, startListening, stopListening, error, audioDevices, metricsSnapshot, latencyStats, conversationMessages, sendText, sendControl }`

---

#### `frontend/src/components/layer1/useSpeechRecognition.ts`

**What it does:** React hook wrapping the browser's built-in Web Speech API for speech-to-text (176 lines).

**In simple terms:** Uses the browser's native speech recognition (available in Chrome) as a fallback when the PersonaPlex server isn't available. Includes auto-restart logic because browsers stop listening after a silence period.

**Returns:** `{ transcript, interimTranscript, isListening, start, stop, isSupported, error }`

---

#### `frontend/src/components/layer1/useSpeechSynthesis.ts`

**What it does:** React hook wrapping the browser's built-in Web Speech API for text-to-speech (159 lines).

**In simple terms:** Uses the browser's native voice synthesis as a fallback TTS. Auto-selects natural/neural English voices when available.

**Returns:** `{ speak, stop, isSpeaking, isSupported, voices, selectedVoice, setVoice }`

---

#### `frontend/src/components/layer1/useVAD.ts`

**What it does:** React hook for Voice Activity Detection using Silero VAD (176 lines).

**In simple terms:** Detects when you start and stop speaking. More accurate than just checking microphone volume — it uses a neural network (Silero) to distinguish actual speech from background noise.

**Key settings:**
- `minSpeechMs: 250` — Must speak for at least 250ms to count
- `positiveSpeechThreshold: 0.5` — Confidence needed to detect speech start
- `negativeSpeechThreshold: 0.35` — Confidence needed to detect speech end
- `redemptionMs: 320` — Grace period before declaring speech ended
- `preSpeechPadMs: 480` — Captures audio slightly before speech started

---

#### `frontend/src/components/layer1/MetricsCollector.ts`

**What it does:** Comprehensive metrics collection for monitoring the voice pipeline (306 lines).

**In simple terms:** Like a flight data recorder for the voice system. Tracks everything that happens — how fast audio travels, connection quality, errors — with circular buffers capped at 1000 samples.

**What it tracks:**
- Latency (audio sent → audio received round-trip time)
- Audio quality (RMS levels, peak values)
- Connection state changes (connected, disconnected, reconnecting)
- Errors (with categorization)
- GPU usage
- Session statistics (total audio sent/received, message counts)

**Key methods:** `recordAudioSent()`, `recordAudioReceived()`, `getSnapshot()`, `getLatencyStats()`, `exportJSON()`

---

#### `frontend/src/components/layer1/VoiceInterface.tsx`

**What it does:** The V1 voice pipeline UI (782 lines).

**In simple terms:** The full-page voice interface for the PersonaPlex (V1) pipeline. Orchestrates the WebSocket connection to PersonaPlex, browser-based speech recognition, and Layer 2 RAG processing. When you ask a question, it immediately speaks filler text ("Let me check that...") while the RAG system finds the real answer, then injects the final response into the voice output.

**Features:** Conversation transcript, audio visualizers (mic + speaker), pipeline status chips, device selector, metrics dashboard overlay.

---

#### `frontend/src/components/layer1/VoiceInterfaceV2.tsx`

**What it does:** The V2 voice pipeline UI (741 lines).

**In simple terms:** The cleaner, server-based voice interface. Uses `useVoicePipeline` hook with server STT (Parakeet/Whisper) and TTS (Kokoro). No filler speech — messages queue naturally. Includes a settings panel for switching STT/TTS models at runtime.

**Features:** Chat-bubble transcript, per-stage performance stats (STT, TTS, RAG, end-to-end latency), pipeline settings panel.

---

#### `frontend/src/components/layer1/VoiceControlBar.tsx`

**What it does:** Compact floating voice control bar for dashboard view (257 lines).

**In simple terms:** A minimal bar that floats over the dashboard with a microphone button. Supports push-to-talk (hold Shift+Space) and continuous listening mode. Emits transcript events on the event bus so Layer 2 can process them.

**Features:** Mic button with waveform animation, status text, PTT/continuous toggle, server health indicator dots.

---

#### `frontend/src/components/layer1/TranscriptPanel.tsx`

**What it does:** Floating transcript overlay (63 lines). Subscribes to `TRANSCRIPT_UPDATE` events from the event bus and shows the rolling conversation (user + assistant messages). Displays the last 10 entries.

---

#### `frontend/src/components/layer1/AudioVisualizer.tsx`

**What it does:** Real-time audio waveform visualization (143 lines).

**In simple terms:** A canvas that draws a live waveform from an `AnalyserNode`. Shows the audio wave shape, an RMS level meter, a peak meter, and a clipping indicator. Blue color for microphone input, purple for speaker output.

---

#### `frontend/src/components/layer1/ConnectionStatus.tsx`

**What it does:** WebSocket connection status display (138 lines). Shows connection state, latency, GPU VRAM usage, uptime, and reconnect attempts for the PersonaPlex server. Color-coded indicators (green=connected, amber=connecting, red=error).

---

#### `frontend/src/components/layer1/DeviceSelector.tsx`

**What it does:** Audio device selector (138 lines). Enumerates microphone and speaker devices via `navigator.mediaDevices` API. Listens for hot-plug events (connecting/disconnecting headsets). Two dropdown selectors — one for microphone, one for speakers. Disabled during active listening.

---

#### `frontend/src/components/layer1/MetricsDashboard.tsx`

**What it does:** Full-screen metrics overlay (393 lines).

**In simple terms:** A detailed performance dashboard showing everything about the voice pipeline's health — session statistics, latency percentiles (p95, p99), sparkline graphs for recent latency samples, audio quality metrics, error log, and GPU utilization.

**Features:** Canvas-based sparkline charts, JSON export button, auto-refresh.

---

#### `frontend/src/components/layer1/TextInputOverlay.tsx`

**What it does:** Full-screen text input modal (120 lines). Toggled via Ctrl+Shift+K. Lets the user type a query that bypasses speech recognition and goes directly to Layer 2. Renders as a centered input field with a blurred backdrop.

---

#### `frontend/src/components/layer1/ConversationTranscript.tsx`

**What it does:** Chat-style conversation transcript (238 lines).

**In simple terms:** A scrolling chat log that shows the conversation between the user and the AI. Each message has a timestamp, speech duration, and role indicator. AI messages have thumbs-up/thumbs-down buttons that submit feedback to the RL backend. Shows interim (live) transcription as the user speaks.

---

### Status Bar

---

#### `frontend/src/components/status-bar/StatusBar.tsx`

**What it does:** The fixed bottom dock bar showing system status (66 lines).

**Renders:**
- Left: Spot particle indicator + state text (Ready/Listening/Speaking/Connecting/Error)
- Center: Capability chips showing active layers (Layer 1: Voice I/O, Layer 2: RAG)
- Right: Ledger status placeholder

---

### Layer 3 Components

The layout system that arranges widgets on screen.

---

#### `frontend/src/components/layer3/Blob.tsx`

**What it does:** The main layout component that renders all widgets.

**In simple terms:** Like a grid where you can place different sized tiles (widgets).

```typescript
export default function Blob() {
  const { layout, pinnedKeys, dismissWidget, ... } = useLayoutState();
```
**What this means:** Get the current layout and functions to modify it.

**Sorting widgets:**
```typescript
const sortedWidgets = useMemo(() => {
  return layout.widgets.filter((w) => w.size !== "hidden");
}, [layout.widgets]);
```
**What this means:** Take all widgets from the layout, but hide any marked as "hidden."

**Rendering widgets:**
```typescript
return (
  <BlobGrid heading={layout.heading}>
    <AnimatePresence mode="popLayout">
      {sortedWidgets.map((instruction, index) => {
        const WidgetComponent = getWidgetComponent(instruction.scenario);

        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: 60 }}    // Start invisible, to the right
            animate={{ opacity: 1, x: 0 }}      // Fade in, slide to position
            exit={{ opacity: 0, x: -60 }}       // Fade out, slide left
            className={sizeClasses(instruction.size, instruction.heightHint)}
          >
            <WidgetSlot scenario={instruction.scenario} size={instruction.size}>
              <WidgetComponent data={resolveWidgetData(instruction)} />
            </WidgetSlot>
          </motion.div>
        );
      })}
    </AnimatePresence>
  </BlobGrid>
);
```
**What this means:**
1. Create a grid container
2. For each widget instruction:
   - Get the React component for that widget type
   - Wrap it in an animation container
   - Apply size classes (hero, expanded, normal, compact)
   - Pass it the data to display

**Size classes:**
```typescript
function sizeClasses(size: string, heightHint?: WidgetHeightHint): string {
  switch (size) {
    case "hero":    return "col-span-12 row-span-4";  // Full width, 4 rows tall
    case "expanded": return "col-span-6";              // Half width
    case "normal":   return "col-span-4";              // Third width
    case "compact":  return "col-span-3";              // Quarter width
    default:         return "col-span-4";
  }
}
```
**What this means:** Maps size names to CSS grid classes. The grid has 12 columns.

---

#### `frontend/src/components/layer3/useLayoutState.ts`

**What it does:** Manages the state of the dashboard layout.

```typescript
export function useLayoutState() {
  const [layout, setLayout] = useState<LayoutJSON>(defaultLayout);
  const [pinnedKeys, setPinnedKeys] = useState<Set<string>>(new Set());
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
```

**Listening for layout updates:**
```typescript
useEffect(() => {
  const unsubscribe = commandCenterBus.on("LAYOUT_UPDATE", (event) => {
    if (event.type === "LAYOUT_UPDATE") {
      // Merge new layout with pinned widgets
      const newWidgets = [...event.layout.widgets];

      // Keep pinned widgets from previous layout
      pinnedKeys.forEach((key) => {
        const pinned = layout.widgets.find((w) => widgetKey(w) === key);
        if (pinned && !newWidgets.some((w) => widgetKey(w) === key)) {
          newWidgets.push(pinned);
        }
      });

      setLayout({ ...event.layout, widgets: newWidgets });
    }
  });

  return unsubscribe;
}, [layout, pinnedKeys]);
```
**What this means:** When a new layout arrives:
1. Start with the new widgets
2. Add back any widgets the user "pinned" (wanted to keep)
3. Update the state

**Widget actions:**
```typescript
const pinWidget = (key: string) => {
  setPinnedKeys((prev) => {
    const next = new Set(prev);
    if (next.has(key)) next.delete(key);  // Toggle off
    else next.add(key);                    // Toggle on
    return next;
  });
};

const dismissWidget = (key: string) => {
  setLayout((prev) => ({
    ...prev,
    widgets: prev.widgets.map((w) =>
      widgetKey(w) === key ? { ...w, size: "hidden" } : w
    ),
  }));
  setPinnedKeys((prev) => {
    const next = new Set(prev);
    next.delete(key);
    return next;
  });
};
```
**What this means:**
- **Pin**: Keep this widget even when the layout changes
- **Dismiss**: Hide this widget

---

#### `frontend/src/components/layer3/WidgetSlot.tsx`

**What it does:** A wrapper component that provides consistent styling and behavior for all widgets.

**In simple terms:** Think of it as a "picture frame" that every widget sits inside - it provides the border, title, toolbar, and error handling.

**Error Boundary:**
```typescript
class WidgetErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex items-center justify-center bg-red-950/30 border border-red-900/50 rounded-xl p-4">
          <p className="text-xs text-red-400/70 font-mono">
            {this.props.scenario}: {this.state.error?.message}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
```
**What this means:** If a widget crashes (bad data, coding error), instead of crashing the whole dashboard, it shows a red error box just for that widget. The rest of the dashboard keeps working.

**Size Classes:**
```typescript
const SIZE_CLASSES: Record<WidgetSize, string> = {
  hero: "col-span-12 row-span-2",    // Full width (12/12 columns), tall
  expanded: "col-span-6",             // Half width (6/12 columns)
  normal: "col-span-4",               // Third width (4/12 columns)
  compact: "col-span-3",              // Quarter width (3/12 columns)
  hidden: "hidden",                   // Not shown
};
```
**What this means:** The dashboard uses a 12-column grid (like a newspaper). Each size takes different number of columns.

**The Slot Component:**
```typescript
export default function WidgetSlot({
  scenario,      // Widget type ("kpi", "trend", etc.)
  size,          // How big to display it
  children,      // The actual widget content
  title,         // Label shown on hover
  description,   // Text at the bottom
  onPin,         // Callback when user pins widget
  onDismiss,     // Callback when user dismisses widget
  onDrillDown,   // Callback when user clicks for more detail
  ...
}: WidgetSlotProps) {
  return (
    <div className="relative h-full w-full group rounded-xl border border-neutral-700/50 bg-neutral-900/80">
      {/* Title - appears on hover */}
      {title && (
        <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100">
          <span className="text-[11px]">{title}</span>
        </div>
      )}

      {/* Toolbar - pin, resize, dismiss buttons */}
      {hasToolbar && <WidgetToolbar ... />}

      {/* Widget content with error handling */}
      <div className="flex-1" onClick={handleBodyClick}>
        <WidgetErrorBoundary scenario={scenario}>
          <Suspense fallback={<WidgetSkeleton />}>
            {children}
          </Suspense>
        </WidgetErrorBoundary>
      </div>

      {/* Description footer */}
      {description && (
        <div className="px-3 py-1.5 border-t">
          <p className="text-[11px] text-neutral-400">{description}</p>
        </div>
      )}
    </div>
  );
}
```
**What this means:** Every widget gets:
- A semi-transparent dark background with rounded corners
- Title on hover (top-left)
- Toolbar with pin/resize/dismiss buttons (top-right)
- Error handling (shows error message if widget crashes)
- Loading skeleton while content loads
- Description footer (optional)

---

#### `frontend/src/components/layer3/WidgetToolbar.tsx`

**What it does:** Hover-reveal floating toolbar for widget interactions (157 lines).

**In simple terms:** When you hover over a widget, a small toolbar appears with 5 action buttons:
- **Pin** — Keep this widget on screen even when new queries come in
- **Resize** — Cycle through sizes (compact → normal → expanded)
- **Focus** — Expand this widget to fill the screen
- **Snapshot** — Take a screenshot of the widget
- **Dismiss** — Remove the widget from the dashboard

---

#### `frontend/src/components/layer3/BlobGrid.tsx`

**What it does:** 12-column CSS Grid container for the widget layout (39 lines). Fills available viewport height with dense auto-flow. Inner grid area scrolls vertically for dashboards with many widgets. Supports an optional heading.

---

#### `frontend/src/components/layer3/defaultLayout.ts`

**What it does:** Defines the default dashboard shown on initial load before any voice commands (70 lines).

**In simple terms:** When you first open the app, you see a pre-built dashboard. This file defines what that dashboard looks like — configured for the "project engineer" persona.

**Default layout (6 widgets):**
1. Grid Voltage KPI (compact) — Shows current grid voltage
2. Total Power KPI (compact) — Shows total power consumption
3. Equipment Online KPI (compact) — Shows count of online equipment
4. Active Alerts KPI (compact) — Shows count of active alerts
5. Energy Trend chart (expanded) — Shows energy consumption over time
6. Active Alerts panel (expanded) — Shows alert details

---

### Layer 4 Components

The actual widget components that display data. There are 21+ different widget types, each designed for specific data visualization needs.

---

#### `frontend/src/components/layer4/widgetRegistry.ts`

**What it does:** Maps widget scenario names to their React components.

```typescript
const registry: Record<string, React.FC<WidgetProps>> = {
  "kpi": KPIWidget,
  "trend": TrendWidget,
  "alerts": AlertsWidget,
  "comparison": ComparisonWidget,
  "flow-sankey": FlowSankeyWidget,
  // ... more widgets
};

export function getWidgetComponent(scenario: string): React.FC<WidgetProps> | null {
  return registry[scenario] || null;
}
```
**What this means:** A lookup table to find the right component for each widget type.

---

#### `frontend/src/components/layer4/widgets/kpi.tsx`

**What it does:** Displays a single metric (Key Performance Indicator).

**In simple terms:** A box showing one number with a label - like "Temperature: 72°F" or "Pump Status: Running."

**Design Tokens:**
```typescript
const COLORS = {
  success: '#16a34a',    // Green for good values
  warning: '#d97706',    // Orange for caution
  critical: '#ef4444',   // Red for problems
  accent: '#2563eb',     // Blue for neutral highlights
};
```

**The KPI Renderer:**
```typescript
const KpiRenderer: React.FC<KpiRendererProps> = ({ spec }) => {
  const { layout, visual, demoData, variant } = spec;

  // Helper to determine text colors based on state
  const valueColor = demoData.state === 'critical' ? 'text-red-600' :
                     demoData.state === 'warning' ? 'text-amber-600' :
                     'text-neutral-900';

  return (
    <div className="p-4 rounded-lg border flex flex-col justify-between h-full">
      {/* Label - what this metric is */}
      <div className="flex justify-between items-start">
        <span className="text-[10px] uppercase tracking-widest text-neutral-400">
          {demoData.label}
        </span>
        {/* Show warning icon if state is warning or critical */}
        {demoData.state === 'critical' && <AlertTriangle className="text-red-500" />}
      </div>

      {/* Value - the actual number */}
      <div className="flex items-baseline gap-1.5">
        <span className={`text-xl font-bold ${valueColor}`}>
          {demoData.value}
        </span>
        <span className="text-xs text-neutral-400">{demoData.unit}</span>
      </div>

      {/* Progress bar for lifecycle KPIs */}
      {variant === 'KPI_LIFECYCLE' && demoData.max && (
        <div className="mt-1.5 w-full bg-neutral-100 rounded-full h-1">
          <div
            className="h-full rounded-full bg-blue-600"
            style={{ width: `${(demoData.value / demoData.max) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
};
```
**What this means:** Shows a compact card with:
- Label at top (e.g., "Temperature")
- Large value in the middle (e.g., "72")
- Unit next to value (e.g., "°F")
- Color changes based on state (red for critical, orange for warning)
- Optional progress bar for showing percentage values

---

#### `frontend/src/components/layer4/widgets/trend.tsx`

**What it does:** Displays a time-series chart showing how values change over time.

**In simple terms:** A line graph like "Power consumption over the last 24 hours."

**Using Recharts library:**
```typescript
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
```
**What this means:** We use the Recharts library to draw professional-looking charts.

**Chart Rendering:**
```typescript
const TrendRenderer: React.FC<TrendRendererProps> = ({ spec }) => {
  const { demoData, variant, representation } = spec;
  const mainColor = visual.colors?.[0] || '#2563eb';

  // Different chart types based on representation
  if (representation === 'Area') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={demoData.timeSeries}>
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={mainColor} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={mainColor} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke={mainColor} fill="url(#grad)" />
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  // Default: Line chart
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={demoData.timeSeries}>
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke={mainColor} dot={false} />
        {/* Critical threshold line for alerts */}
        {variant === 'TREND_ALERT_CONTEXT' && (
          <ReferenceLine y={85} stroke="#ef4444" strokeDasharray="3 3" label="Crit" />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
};
```
**What this means:** The chart:
- Automatically sizes to fit its container
- Shows time on X-axis, values on Y-axis
- Can be a line chart or filled area chart
- Shows a tooltip when you hover over data points
- Can show a critical threshold line (red dashed) if configured

**Live Indicator:**
```typescript
{variant === 'TREND_LIVE' && (
  <div className="absolute top-0 right-0 flex items-center gap-1.5 bg-red-500/10 px-2 py-0.5 rounded-full">
    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
    <span className="text-[9px] font-bold text-red-500">LIVE</span>
  </div>
)}
```
**What this means:** For live-updating charts, shows a pulsing red "LIVE" badge.

---

#### `frontend/src/components/layer4/widgets/alerts.tsx`

**What it does:** Displays alert notifications with severity levels and actions.

**In simple terms:** A list of problems or warnings like "Pump 3 temperature high - needs attention."

**Severity Configuration:**
```typescript
const SEVERITY_CONFIG = {
  critical: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-500',
    icon: XCircle
  },
  warning: {
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-500',
    icon: AlertTriangle
  },
  low: {
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-500',
    icon: Info
  },
  success: {
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-500',
    icon: CheckCircle2
  },
};
```
**What this means:** Different severity levels get different colors and icons:
- Critical = Red with X icon
- Warning = Orange with triangle icon
- Low = Blue with info icon
- Success = Green with checkmark

**State Configuration:**
```typescript
const STATE_CONFIG = {
  new: { icon: ZapIcon, label: 'New', style: 'text-blue-600 bg-blue-50' },
  acknowledged: { icon: Check, label: 'Ack', style: 'text-neutral-600 bg-neutral-100' },
  in_progress: { icon: PlayCircle, label: 'Active', style: 'text-purple-600 bg-purple-50' },
  resolved: { icon: CheckCircle2, label: 'Resolved', style: 'text-green-600 bg-green-50' },
  escalated: { icon: ArrowUpCircle, label: 'Escalated', style: 'text-orange-600 bg-orange-50' },
};
```
**What this means:** Alerts have workflow states showing where they are in the resolution process.

**Multiple Display Variants:**
The alert component can display in several ways:
- **Badge**: Compact pill showing severity and count
- **Toast**: Popup notification that slides in
- **Banner**: Full-width inline message
- **Modal**: Blocking popup for critical alerts
- **Card**: Full details with actions (default)

**The Card Variant (default):**
```typescript
return (
  <div className="bg-white rounded-xl border p-4 hover:shadow-md transition-all">
    {/* Severity Strip on left edge */}
    <div className={`absolute left-0 top-0 bottom-0 w-1 ${severityCfg.accent}`} />

    {/* Header: Category, Source, State Badge, Time */}
    <div className="flex items-center justify-between">
      <span className="text-[10px] uppercase">{data.category} • {data.source}</span>
      <span className="text-xs text-neutral-400">{formatTime(data.timestamp)}</span>
    </div>

    {/* Content: Title, Message, Evidence */}
    <h4 className="text-sm font-bold">{data.title}</h4>
    <p className="text-xs text-neutral-500">{data.message}</p>

    {/* Primary Evidence (sensor reading that triggered alert) */}
    {data.evidence && (
      <div className="bg-neutral-50 rounded px-2 py-1.5">
        <span className="text-[9px]">{data.evidence.label}</span>
        <span className="text-sm font-mono">{data.evidence.value}{data.evidence.unit}</span>
      </div>
    )}

    {/* Action Buttons (shown on hover) */}
    <div className="opacity-0 group-hover:opacity-100 transition-all">
      {data.actions.map((action) => (
        <button onClick={() => onAction?.(data.id, action.intent)}>
          {action.label}
        </button>
      ))}
    </div>
  </div>
);
```
**What this means:** Each alert card shows:
- Color-coded severity strip on the left edge
- Category and source (e.g., "HVAC • Chiller-1")
- State badge (New, Acknowledged, etc.)
- Time since alert (e.g., "5m ago")
- Title and detailed message
- Evidence that triggered the alert (e.g., "Temperature: 92°C")
- Action buttons on hover (Acknowledge, View Details, etc.)

---

#### `frontend/src/components/layer4/fixtureData.ts`

**What it does:** Demo data and metadata for each widget type.

```typescript
export const FIXTURES: Record<string, FixtureMeta> = {
  "kpi": {
    name: "KPI",
    icon: "gauge",
    description: "Single metric display",
    defaultFixture: "kpi_live-standard",
    variants: {
      "kpi_live-standard": {
        demoData: { label: "Temperature", value: 72, unit: "°F", state: "normal" }
      },
      "kpi_live-alert-critical": {
        demoData: { label: "Pressure", value: 150, unit: "psi", state: "critical" }
      },
      // more variants
    }
  },
  "trend": {
    name: "Trend Chart",
    variants: {
      "trend_line-standard": {
        demoData: {
          label: "Power Consumption",
          unit: "kW",
          data: [
            { time: "08:00", value: 120 },
            { time: "09:00", value: 135 },
            // more data points
          ]
        }
      }
    }
  },
  // more widget types
};
```
**What this means:** Each widget type has:
- Display name and icon
- Multiple visual variants (styles)
- Demo data for each variant (used when real data isn't available)

---

#### `frontend/src/components/layer4/widgets/distribution.tsx`

**What it does:** Renders distribution charts showing how values are spread across categories (294 lines).

**Chart types available:**
- Pie chart — Simple percentage breakdown
- Donut chart — Pie with a hole in the center (default)
- Horizontal bar — Values as horizontal bars, good for rankings
- Pareto bar — Sorted bars with cumulative line, shows "top contributors"
- Grouped bar — Side-by-side bars for comparison
- 100% stacked bar — Proportional breakdown adding to 100%

Uses Recharts library. Variant determined by `spec.representation` field.

---

#### `frontend/src/components/layer4/widgets/comparison.tsx`

**What it does:** Renders comparison visualizations between two values or datasets (624 lines).

**Six visual variants:**
- **Side-by-side** — Two big numbers next to each other with a delta arrow
- **Delta bar** — Bars showing positive/negative deviations from a baseline
- **Grouped bar** — Multiple bars per category for multi-parameter comparison
- **Waterfall** — Shows how values build up or break down (gain/loss analysis)
- **Small multiples** — Grid of small charts for comparing across zones/areas
- **Composition split** — Split view showing composition breakdown on each side

---

#### `frontend/src/components/layer4/widgets/flow-sankey.tsx`

**What it does:** Renders interactive Sankey/flow diagrams showing how energy or materials flow through a system (797 lines).

**Five variants:**
- **Standard** — Classic left-to-right flow diagram
- **Energy balance** — Flow with explicit loss branches dropping off (showing waste)
- **Multi-source** — Many-to-one flow (multiple sources feeding one destination)
- **Layered** — Multi-stage hierarchical flow (plant → subsystem → asset)
- **Time-sliced** — Sankey with a time scrubber to see flow changes over periods

Uses custom SVG rendering (not Recharts).

---

#### `frontend/src/components/layer4/widgets/matrix-heatmap.tsx`

**What it does:** Renders heatmap/matrix visualizations with interactive cell selection (612 lines).

**Five variants:**
- **Value heatmap** — Equipment × parameter color-coded grid (default)
- **Correlation matrix** — Shows relationships between parameters
- **Calendar heatmap** — Daily/weekly/monthly patterns on a calendar grid
- **Status matrix** — Equipment health grid (online/offline/warning)
- **Density matrix** — Frequency/distribution visualization

---

#### `frontend/src/components/layer4/widgets/timeline.tsx`

**What it does:** Renders interactive timelines with zoom and pan controls (717 lines).

**Five variants:**
- **Linear** — Simple left-to-right event markers (default)
- **Status** — Machine state blocks (running/stopped/idle) over time
- **Multilane** — Multi-row shift schedule or crew roster
- **Forensic** — Annotated incident analysis with markers and notes
- **Dense** — Event density/burst analysis showing frequency patterns

Includes custom SVG rendering with `TimeAxis`, `LinearEventMarker`, `StatusBlock`, `AnnotationPin`, and `ClusterBubble` sub-components.

---

#### `frontend/src/components/layer4/widgets/composition.tsx`

**What it does:** Renders composition/part-of-whole charts (546 lines).

**Five variants:**
- **Donut** — Ring chart showing proportional shares (default)
- **Stacked area** — Composition over time as stacked areas
- **Stacked bar** — Category composition as stacked bars
- **Treemap** — Hierarchical/nested breakdown as rectangles
- **Waterfall** — Gain/loss/bridge breakdown

Uses Recharts (PieChart, AreaChart, BarChart, Treemap).

---

#### `frontend/src/components/layer4/widgets/eventlogstream.tsx`

**What it does:** Renders a full event log stream with search, filtering, and drill-down (1249 lines).

**Five display modes:**
- **Chronological timeline** — Events listed in time order (default)
- **Compact card feed** — Brief summary cards
- **Tabular log view** — Spreadsheet-style table
- **Correlation stack** — Related events grouped together
- **Grouped by asset** — Events organized by equipment

Includes a `FilterBar` for searching/filtering by severity, a `DrillDownDrawer` that slides in to show event details, and mini sparkline charts using Recharts.

---

#### `frontend/src/components/layer4/widgets/edgedevicepanel.tsx`

**What it does:** Renders an edge device network topology viewer — the largest widget file (2021 lines).

**In simple terms:** Shows a visual map of all the IoT devices and edge computers connected to the system, with interactive graph visualization, detail panels, and multi-tab inspection.

**Features:**
- Interactive SVG graph with radial layout computation
- 9 detail tabs (overview, health, network, connectors, ingestion, workloads, logs, config, dependencies)
- List mode and graph mode toggle
- Sparkline SVG rendering for metrics
- Filtering by device type and status

Uses MUI components exclusively. Self-contained with hardcoded topology and metrics data.

---

#### `frontend/src/components/layer4/widgets/supplychainglobe.tsx`

**What it does:** Renders an interactive 3D globe showing supply chain shipping lanes (323 lines).

**In simple terms:** A spinning Earth with animated arcs showing shipping routes between locations. You can rotate and zoom the globe to explore supply chain connections.

Uses Three.js with `@react-three/fiber` and `@react-three/drei`. Earth texture loaded from remote URL. Arcs animate with color-coded status.

---

#### `frontend/src/components/layer4/widgets/trends-cumulative.tsx`

**What it does:** Renders cumulative trend charts with time controls (472 lines).

**Features:**
- Time range selector (1H, 6H, 24H, 7D, 30D)
- Date picker for historical data
- Threshold bands (colored horizontal regions)
- Target line overlay
- Multiple chart variants (Line, Area, Step)

Uses Recharts `ComposedChart` with `Area` and `Line` components.

---

#### `frontend/src/components/layer4/widgets/trend-multi-line.tsx`

**What it does:** Renders multi-line trend charts with dual Y-axes (278 lines).

**In simple terms:** Shows multiple metrics on the same chart — for example, temperature on the left Y-axis and pressure on the right. Includes threshold reference lines showing limits.

Uses Recharts `LineChart` with configurable series (each with its own color, unit, Y-axis, and line style).

---

#### `frontend/src/components/layer4/widgets/category-bar.tsx`

**What it does:** Renders category bar charts in multiple orientations and styles (256 lines).

**Seven variants:**
- Vertical bars, Horizontal bars, Stacked bars, 100% stacked bars, Grouped bars, Diverging bars (positive/negative), Dense bars (with scrollable brush)

Uses Recharts `BarChart` with optional `Brush` component for scrolling through large datasets.

---

#### `frontend/src/components/layer4/widgets/chatstream.tsx`

**What it does:** Renders a full-featured AI chat interface (1574 lines).

**In simple terms:** A complete chat window where users can type questions and get AI responses, with rich formatting, provenance tracking, and inline widget previews.

**Features:**
- Virtualized message list (react-window) for performance with thousands of messages
- Message bubbles with role-based styling (user, assistant, system)
- Provenance chips showing where information came from
- Trace panel showing AI reasoning steps
- Inline widget stubs that preview dashboard elements
- Composer with draft persistence (saved to sessionStorage)
- Error banners for failed messages

Uses MUI styled components.

---

#### `frontend/src/components/layer4/widgets/peoplehexgrid.tsx`

**What it does:** Renders a 3D hexagonal grid showing team/shift staffing coverage (295 lines).

**In simple terms:** Each hexagon represents a team. The color shows coverage status: green = fully staffed, amber = gap, red = critical shortage. Built with Three.js for a modern 3D look.

---

#### `frontend/src/components/layer4/widgets/peoplenetwork.tsx`

**What it does:** Renders a 3D particle network showing department interconnections (315 lines).

**In simple terms:** Floating particles represent people/departments. Lines between them show connections. The overall coverage percentage is displayed. Built with Three.js.

---

#### `frontend/src/components/layer4/widgets/peopleview.tsx`

**What it does:** Renders a People & Permissions admin page (184 lines). Shows a role matrix table, team directory cards with avatars, and an email invite form. Self-contained with hardcoded demo data. Uses MUI components.

---

#### `frontend/src/components/layer4/widgets/vaultview.tsx`

**What it does:** Renders a Vault & Ingestion management page (201 lines). Shows document ingestion queue status cards with progress bars and a document registry table. Self-contained with hardcoded demo data. Uses MUI components.

---

#### `frontend/src/components/layer4/widgets/agentsview.tsx`

**What it does:** Renders an AI Agents & Routing admin page (306 lines). Shows agent registry cards (each agent with name, model, and status), a routing overview table mapping intent patterns to agents, and a dialog for per-agent chat. Self-contained with hardcoded demo data. Uses MUI components.

---

### Canvas

---

#### `frontend/src/components/canvas/Canvas.tsx`

**What it does:** Root layout container for the entire application (40 lines). A 100vh × 100vw zero-scroll container that splits into a flex-1 main area (for widgets/voice UI) and a fixed-height status bar footer. No global scrollbar — individual widgets manage their own scrolling.

**Props:** `children` (main content) and `statusBar` (footer content).

---

### App Pages & Layout

---

#### `frontend/src/app/layout.tsx`

**What it does:** Next.js root layout — the HTML shell for the entire application (39 lines).

**Key configuration:**
- Loads Geist Sans and Geist Mono fonts as CSS variables
- Applies `className="dark"` to `<html>` for dark mode
- Injects `<DevConsoleInterceptor>` for development logging
- Sets metadata: title "Command Center" and description

---

#### `frontend/src/app/page.tsx`

**What it does:** The main page of the Command Center application (253 lines).

**In simple terms:** This is the home screen. It orchestrates two views you can toggle with Ctrl+B:

**Dashboard view:** Shows the full Blob widget grid with a floating voice control bar. This is the normal operating mode where you see all your equipment dashboards.

**Voice view:** Shows the V2 voice interface and transcript panel. This is a focused voice interaction mode.

**Always visible:** Status bar at the bottom, control buttons in the top-right (view toggle, text input toggle, transcript viewer), text input overlay (Ctrl+Shift+K), and debug panel (Ctrl+D).

---

#### `frontend/src/app/widgets/page.tsx`

**What it does:** Widget Gallery page — a development/QA tool for browsing all widget types (842 lines).

**In simple terms:** A catalog page where developers can preview every widget scenario at different sizes (compact, normal, expanded, hero) side by side. Includes feedback forms for rating widget quality, sample dashboard presets, and pagination for browsing all variants.

**Features:**
- Sidebar listing all scenarios (multi-variant and single-variant)
- Size adjustment controls per widget
- Widget error boundaries to prevent one broken widget from crashing the page
- Lazy loading for performance
- Sample dashboards with pre-configured widget combinations

---

#### `frontend/src/app/globals.css`

**What it does:** Global stylesheet defining the visual design system (131 lines).

**Key definitions:**
- CSS custom properties (design tokens): `--cc-bg`, `--cc-surface`, `--cc-accent`, `--cc-text`, etc. for a dark industrial UI theme
- Tailwind CSS directives
- Keyframe animations for Spot states (pulse, listening, processing, success, error)
- Voice waveform bar animations
- Custom scrollbar styling for the dark theme

---

#### `frontend/src/app/dashboard/page.tsx`

**What it does:** Test route at `/dashboard` (16 lines). Renders the default dashboard layout (Blob + Widgets) without any voice UI. Used for testing Layer 3 and Layer 4 in isolation.

---

#### `frontend/src/app/widgets/FeedbackForm.tsx`

**What it does:** Issue tracker / feedback form system (439 lines).

**In simple terms:** Provides feedback forms that appear on widgets, dashboards, and pages. Users can rate with stars, select issue tags, and write notes. A `FeedbackChecklist` component aggregates all submitted issues with open/closed toggle.

**Four exported components:**
- `WidgetFeedbackForm` — Rating + tags + notes for individual widgets
- `DashboardFeedbackForm` — Rating + tags + notes for complete dashboard layouts
- `PageFeedbackForm` — Rating + tags + notes for entire page experiences
- `FeedbackChecklist` — Aggregated issue list with open/closed filtering

---

#### `frontend/src/app/widgets/SampleDashboard.tsx`

**What it does:** Pre-configured dashboard renderer (233 lines). Renders a set of widgets using `BlobGrid` + `WidgetSlot`, resolves fixture data, and supports fullscreen overlay (portaled to body, Esc to close).

**Exports 5 pre-built dashboards:**
1. Monitor Equipment — KPIs + trend + alerts
2. Energy Consumption — Trends + distribution + cumulative
3. Maintenance Status — Timeline + event log + KPIs
4. Compare Devices — Comparison + multi-line + category bar
5. Power Quality — Heatmap + Sankey + distribution

---

#### `frontend/src/app/widgets/SimulationView.tsx`

**What it does:** Simulation result viewer (346 lines). Loads simulation run results from a JSON log file and displays each question's generated dashboard. Features category filtering, pagination, metadata badges, error states, and a feedback checklist.

---

#### `frontend/src/app/widgets/test/page.tsx`

**What it does:** Comprehensive widget test suite page at `/widgets/test` (652 lines). Defines test cases for 13 multi-variant scenarios and 6 single-variant scenarios. Shows per-fixture test cards with both generated and static (fixture) data side-by-side. Includes sidebar navigation and coverage statistics.

---

#### `frontend/src/app/widgets/rate/page.tsx`

**What it does:** Widget rating page at `/widgets/rate` (798 lines).

**In simple terms:** A dedicated page for rating widget quality. Loads exhaustive simulation data and presents one widget at a time for thumbs-up/thumbs-down rating with tags and notes. Designed to efficiently collect training data for DPO fine-tuning.

**Features:**
- Keyboard shortcuts for rapid rating
- Filters by category, scenario, natural/forced, and rating status
- localStorage + backend sync for ratings
- DPO-ready JSON export
- Error boundary to prevent broken widgets from blocking the workflow

---

#### `frontend/src/app/api/widget-feedback/route.ts`

**What it does:** Next.js API route for persisting widget feedback to disk (31 lines).

**Endpoints:**
- `POST` — Saves widget feedback JSON to `../ref/widget-feedback.json`
- `GET` — Reads and returns saved feedback, or empty defaults

---

### Frontend Types & Stores

---

#### `frontend/src/types/index.ts`

**What it does:** Central shared type definitions for the entire 4-layer architecture (170 lines).

**Layer 1 types:** `PersonaPlexState`, `Transcript`, `PersonaPlexConfig`
**Spot types:** `SpotState`, `SpotSize`, `SpotParticleConfig`, `SpotWalkState`
**Layer 2 types:** `RAGDomain`, `RAGQuery`, `RAGResult`, `OrchestratorOutput`
**Layer 3 types:** `WidgetSize`, `WidgetHeightHint`, `WidgetPosition`, `TransitionType`, `WidgetInstruction`, `LayoutJSON`
**Layer 4 types:** `WidgetDomain`, `WidgetContract`
**Events:** `CommandCenterEvent` — discriminated union of 14 event types, plus `LayoutSnapshot`

---

#### `frontend/src/types/metrics.ts`

**What it does:** TypeScript interfaces for the metrics system (71 lines).

**Types defined:** `LatencyMetric`, `AudioQualityMetric`, `ConnectionMetric`, `ErrorMetric`, `GPUMetric`, `SessionStats`, `MetricsSnapshot`, `MetricsStats`

---

#### `frontend/src/types/web-speech.d.ts`

**What it does:** TypeScript ambient declarations for the Web Speech API (52 lines). Provides type definitions for `SpeechRecognition`, `SpeechRecognitionEvent`, `SpeechRecognitionErrorEvent`, etc., which aren't included in TypeScript's default library.

---

#### `frontend/src/types/opus-recorder.d.ts`

**What it does:** TypeScript ambient declarations for the `opus-recorder` npm package (33 lines). Defines `RecorderOptions` interface and `Recorder` class types.

---

#### `frontend/src/app/widgets/feedbackStore.ts`

**What it does:** Client-side feedback persistence using localStorage (297 lines).

**In simple terms:** When users rate widgets (thumbs up/down, tag issues, adjust sizes), this file saves that feedback locally in the browser and also syncs it to the server via the API route.

**Three feedback collections:**
- Widget feedback — Ratings and tags for individual widgets
- Dashboard feedback — Ratings for complete dashboard layouts
- Page feedback — Ratings for entire page experiences

**Size adjustments:** Tracks when users resize widgets and persists those preferences.

**Key functions:** `saveWidgetFeedback()`, `getAllWidgetFeedback()`, `saveSizeAdjustment()`, `exportAllFeedback()`, `clearAllFeedback()`

**11 predefined feedback tags:** Too large, Too small, Wrong data, Missing data, Hard to read, Confusing layout, Love it, Needs color fix, Wrong chart type, Slow to load, Perfect size.

---

### Debug Tools

---

#### `frontend/src/components/debug/DebugPanel.tsx`

**What it does:** Full-screen debug overlay for inspecting the system pipeline (522 lines).

**In simple terms:** A developer tool toggled with Ctrl+D. Shows the health and status of every system layer so you can quickly identify what's working and what's broken.

**What it shows:**
- **Layer 1 status** — Voice I/O connection state, PersonaPlex server reachability
- **Layer 2 status** — Backend API health, Ollama LLM availability, RAG index statistics (equipment, alerts, and maintenance document counts from ChromaDB)
- **Test query input** — Type a question and see exactly what the orchestrator returns
- **Query log** — Last 10 queries with full response details
- **Pipeline diagram** — ASCII art showing the data flow through all layers

---

#### `frontend/src/components/debug/index.ts`

**What it does:** Barrel export for the debug module (2 lines). Re-exports `DebugPanel` from `./DebugPanel`.

---

### Frontend Configuration

---

#### `frontend/package.json`

**What it does:** NPM project manifest for the frontend (49 lines).

**Key scripts:**
- `dev` — Start Next.js development server
- `build` — Production build
- `start` — Start production server
- `lint` — Run ESLint
- `test:e2e` — Run Playwright E2E tests

**Key dependencies:**
- Next.js 14.2.35, React 18
- Three.js + @react-three/fiber (3D visualizations)
- MUI 7 (Material UI components)
- Recharts (2D charting)
- framer-motion (animations)
- opus-recorder (audio compression)
- @ricky0123/vad-web (voice activity detection)
- react-window (virtualized lists)

---

#### `frontend/next.config.mjs`

**What it does:** Next.js configuration (11 lines). Key setting: `eslint.ignoreDuringBuilds: true` — skips ESLint during production builds to speed up deployments.

---

#### `frontend/tailwind.config.ts`

**What it does:** Tailwind CSS configuration (20 lines). Scans `src/pages/`, `src/components/`, `src/app/` for class usage. Extends theme with CSS variable-based colors.

---

#### `frontend/tsconfig.json`

**What it does:** TypeScript compiler configuration (27 lines). Strict mode, ESNext target, `@/*` path alias pointing to `./src/*`, incremental compilation, JSX preserve mode.

---

#### `frontend/postcss.config.mjs`

**What it does:** PostCSS configuration (9 lines). Single plugin: `tailwindcss`.

---

#### `frontend/playwright.config.ts`

**What it does:** Playwright E2E test configuration (98 lines).

**Key settings:**
- Tests located in `./e2e`
- Single worker, sequential execution
- 1920×1080 viewport
- Video recording on all tests, screenshots on failure
- Two browser projects: Chromium (with fake media streams) and Firefox
- Base URL: `http://localhost:3100`
- Auto-starts `npm run dev` as web server
- 2-minute global timeout

---

#### `frontend/server.js`

**What it does:** Custom HTTPS production server for Next.js (27 lines). Reads TLS certificates from `../certs/` (lan.key, lan.crt) and serves the app over HTTPS on `0.0.0.0:3100`. Used by the `cc-frontend` systemd service in production.

---

## Scripts and Automation

Scripts for development, deployment, simulation, and system monitoring.

---

#### `scripts/dev.sh`

**What it does:** Unified development server launcher (501 lines).

**In simple terms:** Starts everything you need for development with one command. Manages all services with colored log output, handles port conflicts, and shuts everything down cleanly when you press Ctrl+C.

**Two voice pipeline modes:**
- `./scripts/dev.sh` — V2 pipeline (STT Parakeet/Whisper + TTS Kokoro + Django + Next.js)
- `./scripts/dev.sh --v1` — V1 pipeline (PersonaPlex full-duplex)

**Key flags:**
- `--setup` — Run setup first, then start
- `--full` — Full reset + setup + start

**Ports used:**
| Service | Port |
|---------|------|
| Django Backend | 8100 |
| Next.js Frontend | 3100 |
| PersonaPlex (V1) | 8998 |
| STT Server | 8890 |
| TTS Server | 8880 |

**Features:**
- Auto-starts Ollama LLM if not running
- Stops conflicting systemd production services before starting dev servers
- Color-coded log output per service (green=backend, blue=frontend, etc.)
- Session-based logging to `logs/` directory
- Log rotation to prevent disk fill
- Graceful shutdown via signal traps (kills all child processes)

---

#### `scripts/deploy.sh`

**What it does:** LAN production deployment script (178 lines).

**In simple terms:** Takes the development version and turns it into a proper production deployment that starts automatically, stays running, and survives reboots.

**What it does:**
1. Installs gunicorn (production Python server)
2. Builds the Next.js frontend (`npm run build`)
3. Copies systemd service files to `~/.config/systemd/user/`
4. Enables all services with auto-start
5. Starts services in order: STT → TTS → Backend → Frontend
6. Enables linger for persistence across logouts

**Subcommands:**
- `./scripts/deploy.sh --stop` — Stop all services
- `./scripts/deploy.sh --status` — Show service status
- `./scripts/deploy.sh --logs` — Tail service logs

**Target LAN IP:** 192.168.1.20

---

#### `scripts/setup.sh`

**What it does:** Full environment initialization script (401 lines).

**In simple terms:** Sets up everything from scratch — creates the Python virtual environment, installs packages, runs database migrations, populates equipment data, and indexes the RAG search engine.

**Key flags:**
- `--backend` — Set up backend only
- `--frontend` — Set up frontend only
- `--rag` — Index RAG data only
- `--reset` — Delete everything and start fresh

**What it sets up:**
1. Python virtual environment with all backend dependencies
2. Django database migrations
3. Industrial equipment data (500+ records via `populate_industrial_db`)
4. Rich operational data (alerts, maintenance, documents via `generate_rich_data`)
5. RAG index (ChromaDB + sentence-transformers via `index_rag`)
6. Frontend npm packages
7. Ollama LLM model (pulls Qwen3-7B or phi4)

---

#### `scripts/bmc-metrics-logger.sh`

**What it does:** Continuous system metrics logger (97 lines).

**In simple terms:** Runs in the background and records how hard your computer is working — CPU usage, RAM usage, GPU temperature, disk space — so you can spot problems.

**What it logs (every 30 seconds by default):**
- CPU usage percentage
- RAM usage
- Hardware sensor readings (via `lm-sensors`)
- GPU stats (via `nvidia-smi`)
- Disk usage
- Load average
- Process count

**Log rotation:** 100MB max file size, keeps last 5 rotated logs. Writes to `/var/log/bmc-metrics/` or `~/.local/share/bmc-metrics/` as fallback.

---

#### `scripts/personaplex-daemon.sh`

**What it does:** Manages PersonaPlex-7B as a persistent background daemon (186 lines).

**Subcommands:**
- `start` — Start PersonaPlex in the background with PID tracking
- `stop` — Stop the daemon gracefully
- `restart` — Stop then start
- `status` — Check if running
- `logs` — Tail the log output

**Key settings:**
- Port 8998
- Optional SSL (via `PERSONAPLEX_SSL` env var with auto-generated self-signed certificates)
- 120-second readiness timeout
- Uses `nohup` for backgrounding

---

### Simulation Scripts

---

#### `scripts/simulation/run_simulation.py`

**What it does:** Dashboard simulation runner that sends questions through the pipeline and captures results (395 lines).

**In simple terms:** Runs a battery of real questions through the system and records everything — what the AI understood, which widgets it picked, how fast it responded, and whether the domain matching was correct.

**Key features:**
- Question bank organized by category
- Captures full response data (voice response, layout JSON, intent, RAG results)
- Domain and scenario match analysis
- Timing measurements per query
- Aggregate statistics with percentile breakdowns (p50, p95, p99)
- Parallel execution mode for throughput testing

**Output:** `simulation_log.json` + `summary.json` per run, copied to `frontend/public/simulation/` for the widget gallery to display.

**Usage:** `python scripts/simulation/run_simulation.py --category industrial --parallel 4`

---

#### `scripts/simulation/analyze_results.py`

**What it does:** Post-simulation analysis tool (442 lines).

**In simple terms:** Takes simulation results and user feedback, joins them together, and produces a report telling you exactly what to fix in the orchestrator.

**Key features:**
- Identifies low-rated categories
- Flags fixture issues (average rating below 3.0)
- Detects characteristic detection gaps (below 70% detection rate)
- Compares two tagged runs side-by-side to measure improvements
- Terminal-formatted report output

**Usage:** `python scripts/simulation/analyze_results.py --tag v1.2 --compare v1.1 v1.2`

---

#### `scripts/simulation/run_exhaustive.py`

**What it does:** Exhaustive widget test data generator (801 lines).

**In simple terms:** For every question in the test bank, this script: (1) runs it through the real backend pipeline to get natural widget selections, (2) expands each widget across ALL fixture variants of that scenario, and (3) creates synthetic widgets for any missing scenarios and expands those too. The result is a massive dataset covering every possible question × scenario × fixture combination.

**Key features:**
- Parallel execution for speed
- Resume capability (saves progress incrementally)
- Dry-run mode
- Copies output to `frontend/public/simulation/` for the rating page

**Usage:** `python scripts/simulation/run_exhaustive.py --parallel 4 --tag v1.3`

---

#### `scripts/simulation/export_training_data.py`

**What it does:** Exports rated widget entries into JSONL training data for LLM fine-tuning (321 lines).

**In simple terms:** Takes the ratings from the `/widgets/rate` page and converts them into training data that can teach the LLM to make better widget and fixture selections.

**Two training targets:**
1. **Fixture selection** — Which visual variant is best for a given scenario + query
2. **Widget selection** — Which widget scenarios should appear for a given query

**Two export modes:**
- `positive-only` — SFT (Supervised Fine-Tuning) with only good examples
- `pair` — DPO (Direct Preference Optimization) with chosen/rejected pairs

**Usage:** `python scripts/simulation/export_training_data.py --mode pair --output rl_training_data/`

---

### Systemd Service Files

These files define how each service runs in production. They ensure services start automatically, restart on failure, and log output properly.

---

#### `scripts/systemd/cc-backend.service`

**What it does:** Runs the Django backend via gunicorn with 3 workers on `0.0.0.0:8100` (19 lines).
- 120-second timeout per request
- Restarts automatically after 5 seconds on failure
- Logs to `~/desktop/CommandCenter/logs/backend.log`

---

#### `scripts/systemd/cc-frontend.service`

**What it does:** Runs the Next.js production frontend via `node server.js` (custom HTTPS server) (19 lines).
- Depends on `cc-backend.service` (starts after backend)
- `NODE_ENV=production`
- Restarts automatically after 5 seconds on failure
- Logs to `~/desktop/CommandCenter/logs/frontend.log`

---

#### `scripts/systemd/cc-stt.service`

**What it does:** Runs the Speech-to-Text server (Parakeet/Whisper) (18 lines).
- Runs `python server.py` from `backend/stt/`
- Restarts automatically after 10 seconds on failure
- Logs to `~/desktop/CommandCenter/logs/stt.log`

---

#### `scripts/systemd/cc-tts.service`

**What it does:** Runs the TTS server (Kokoro-FastAPI with native GPU) (22 lines).
- Runs uvicorn on `0.0.0.0:8880`
- `USE_GPU=true`, `USE_ONNX=false`
- Restarts automatically after 10 seconds on failure
- Logs to `~/desktop/CommandCenter/logs/tts.log`

---

## Tests

Automated tests to make sure everything works correctly.

---

### Backend Tests

---

#### `backend/layer2/tests.py`

**What it does:** Comprehensive unit test suite for all Layer 2 components (421 lines). Tests widget registry, intent parsing, widget selection, data collection, orchestrator integration, schema validation, and multi-component integration.

---

#### `backend/layer2/audit_tests.py`

**What it does:** Engineering audit test harness that benchmarks intent parsing accuracy, widget selection quality, domain matching, and latency against real-world queries.

---

#### `backend/rl/tests.py`

**What it does:** Django TestCase-based tests for the offline RL training pipeline (347 lines). Tests configuration presets, data formatting, dataset building, online learning, trainer, and export utilities.

---

#### `backend/rl/test_continuous.py`

**What it does:** Unit tests for the continuous RL components (236 lines). Tests experience buffer, reward signals, follow-up classification, and the RL coordinator.

---

#### `backend/rl/e2e_test.py`

**What it does:** End-to-end HTTP test suite with 20+ scenarios (569 lines). Tests the full stack from API to RL feedback loop against a live server.

---

#### `backend/layer2/reconciliation/tests/test_reconciler.py`

**What it does:** Unit tests for mismatch classification (210 lines). Tests value classification, security checks, nesting depth protection, and schema building.

---

#### `backend/layer2/reconciliation/tests/test_pipeline.py`

**What it does:** Integration tests for the full reconciliation pipeline (366 lines). Tests all 6 outcome types plus security enforcement and provenance tracking.

---

### Frontend Tests

---

#### `frontend/e2e/helpers/test-utils.ts`

**What it does:** Shared E2E test utilities (483 lines). Exports the `CommandCenterPage` page-object class and predefined test datasets.

**Key exports:**
- `CommandCenterPage` — Page object with methods for navigation, text input, voice simulation, widget querying, performance metrics, and layout validation
- `REALISTIC_SCENARIOS` — 30 real-world query test cases across all 5 domains
- `CONTEXT_STRESS_SCENARIOS` — 3 multi-turn conversations (10 turns each)
- `ADVERSARIAL_SCENARIOS` — 18 edge-case inputs (SQL injection, XSS, empty, gibberish, very long)
- `ALL_WIDGETS` — List of all 18 widget scenario types
- `WIDGET_TRIGGER_QUERIES` — Mapping of queries known to trigger each widget type

---

#### `frontend/e2e/tests/realistic-scenarios.spec.ts`

**What it does:** 30+ real-world user scenario tests (290 lines). Tests industrial queries, alerts, people, tasks, supply chain, and complex multi-domain queries. Validates that each query produces the expected domains and minimum widget count.

---

#### `frontend/e2e/tests/mega-validation-phase2.spec.ts`

**What it does:** Comprehensive release-gate E2E suite (663 lines). Five test phases:
1. Realistic scenario validation
2. Multi-turn conversation stress (10-turn + rapid-fire)
3. Adversarial input handling (SQL injection, XSS, empty, very long)
4. Widget rendering validation (all scenarios render without errors)
5. Performance validation (10s render budget, 50K DOM node cap, 30 FPS minimum)

Generates a JSON report and blocks release on critical failures.

---

#### Additional E2E test files:
- `context-stress.spec.ts` — Multi-turn conversation stress tests
- `adversarial.spec.ts` — Adversarial input handling tests
- `performance-load.spec.ts` — Performance and load tests
- `failure-injection.spec.ts` — Failure injection / resilience tests
- `widget-exhaustion.spec.ts` — Widget coverage / exhaustion tests

---

## Summary

Command Center is a voice-controlled industrial dashboard with these key parts:

1. **Voice Pipeline (Layer 1)**: Two modes — V1 (PersonaPlex full-duplex speech-to-speech) and V2 (separate STT Parakeet/Whisper + TTS Kokoro). Handles all voice input/output with VAD, metrics collection, and visual feedback via Spot.

2. **AI Brain (Layer 2)**: Understands what users want through intent parsing (5 domains), finds information through RAG search (ChromaDB + Ollama LLM), selects appropriate widgets, applies fixture variants (rule-based + LLM-based), and generates voice responses. Includes full data quality pipeline (schema validation, reconciliation with 5 stages, physical unit normalization).

3. **Blob Layout (Layer 3)**: Arranges widgets on screen with physics-based animations, responsive sizing (compact/normal/expanded/hero), and smooth transitions.

4. **Widget Components (Layer 4)**: 18+ visualization types including KPIs, trend charts, distribution charts, comparisons, Sankey flows, heatmaps, timelines, event logs, 3D globe, hex grids, particle networks, chat streams, and admin panels.

5. **Reinforcement Learning**: Continuous online learning from user feedback (thumbs up/down), plus offline DPO training with model export to Ollama. Background trainer runs continuously while users interact.

6. **Actions & Feedback**: Voice-triggered actions (reminders, messages, device commands), explicit feedback collection with 11 tag types, and signal-based processing.

7. **Industrial Data**: 12 equipment model types, management commands for data population and RAG indexing, with 500+ equipment records and thousands of operational documents.

8. **DevOps**: Development launcher (`dev.sh`), production deployment (`deploy.sh`), setup automation (`setup.sh`), systemd services, benchmarking suite, simulation runner, and comprehensive E2E testing via Playwright.

All the pieces communicate through:
- **Backend API**: REST endpoints (Django + DRF) for the frontend to call
- **WebSocket**: Full-duplex binary protocol for PersonaPlex voice streaming
- **Event Bus**: Frontend components broadcasting typed events to each other
- **Database**: SQLite for equipment data, sessions, feedback; ChromaDB for vector search
- **Ollama**: Local LLM inference for intent parsing, widget selection, and fixture selection

---

*This documentation covers every file in the Command Center codebase. Generated by analyzing all source files, configurations, scripts, tests, and deployment artifacts.*
