# LLM Data Analysis Platform with Amazon Bedrock

## Project Overview

This project implements a **secure, enterprise-ready data analysis platform** powered by Amazon Bedrock and Claude. It provides a modern web interface for users to submit analysis queries and receive structured, actionable insights.

### Primary Goals

1. **Security-First Design**: Protect against prompt injection attacks and ensure all LLM interactions are safe and auditable
2. **Configurable Access Levels**: Allow administrators to control how users interact with the LLM (templates only, guided input, or open access)
3. **Structured Output**: Ensure consistent, parseable responses using Bedrock's tool use capabilities
4. **Modern UX**: Deliver a responsive, real-time interface using HTMX and Alpine.js
5. **Complete Auditability**: Log all prompts and responses for security review and compliance

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Constrained  │  │   Guided     │  │    Open + Filter     │   │
│  │  Templates   │  │  Free-Text   │  │   (Admin Only)       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         └─────────────────┼─────────────────────┘               │
│                           ▼                                     │
│              ┌────────────────────────┐                         │
│              │   Feature Flag Router   │  ◄── Admin Toggle      │
│              └───────────┬────────────┘                         │
└──────────────────────────┼──────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FILTERING PIPELINE                           │
│  ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐   │
│  │ Input       │   │ Bedrock         │   │ Prompt Injection │   │
│  │ Validation  │──▶│ Guardrails      │──▶│ Detection        │   │
│  │ (Django)    │   │ (AWS Native)    │   │ (Custom Layer)   │   │
│  └─────────────┘   └─────────────────┘   └────────┬─────────┘   │
│                                                    │             │
│                    ┌──────────────────────────────┘             │
│                    ▼                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ AUDIT LOG: All prompts logged for security review       │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BEDROCK INVOCATION                            │
│  ┌──────────────────┐      ┌─────────────────────────────────┐  │
│  │ Converse API     │      │ Tool Use for Structured Output  │  │
│  │ (Claude Model)   │─────▶│ → Hypothesis Cards              │  │
│  │                  │      │ → Search Results                │  │
│  │ System Prompt:   │      │ → Explanations                  │  │
│  │ Data Analyst     │      └─────────────────────────────────┘  │
│  └──────────────────┘                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend** | Django 5.2+, Poetry | Mature, secure framework with excellent ORM and admin |
| **Frontend** | HTMX, Alpine.js, Tailwind (CDN) | Modern interactivity without SPA complexity |
| **Task Queue** | Celery + Redis | Ready for async processing if needed |
| **LLM** | Amazon Bedrock (Claude) | Enterprise-grade, managed LLM with built-in guardrails |
| **Filtering** | Bedrock Guardrails + Custom | Defense in depth approach |
| **Database** | PostgreSQL (Django ORM) | Production-ready, SQLite for development |

---

## Key Design Decisions

### 1. Three-Tier Input Modes

The platform supports three input modes, configurable by administrators:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Constrained** | Users can only select from pre-defined templates | High-security environments, standardized reporting |
| **Guided** | Free-text input with suggestions and validation | Standard users, balanced flexibility |
| **Open** | Full free-text with filtering (admin only) | Power users, development, testing |

**Rationale**: Different organizations have different risk tolerances. This flexibility allows the platform to adapt to various security requirements while maintaining a consistent architecture.

### 2. Defense in Depth Security

Security is implemented in multiple layers:

1. **Django Form Validation**: Length limits, required fields, basic sanitization
2. **Custom Prompt Injection Detection**: 40+ regex patterns detecting known attack vectors
3. **Off-Topic Filtering**: Blocks requests outside the data analysis domain
4. **Bedrock Guardrails**: AWS-native content filtering, PII detection, topic blocking
5. **Complete Audit Logging**: Every prompt logged with user, IP, timestamp, and outcome

**Rationale**: No single security measure is foolproof. By layering multiple detection mechanisms, we significantly reduce the attack surface while maintaining usability.

### 3. Structured Output via Tool Use

Rather than parsing free-form LLM text, we use Bedrock's tool use feature to enforce structured JSON output:

```python
ANALYSIS_OUTPUT_SCHEMA = {
    "hypotheses": [
        {
            "title": "string",
            "confidence": "high|medium|low",
            "summary": "string",
            "evidence": ["string"],
            "visualization_type": "chart|table|text|none"
        }
    ],
    "search_results": [...],
    "explanation": {
        "methodology": "string",
        "limitations": "string",
        "next_steps": ["string"]
    }
}
```

**Rationale**: Tool use guarantees the output matches our schema, enabling reliable UI rendering and downstream processing. Free-form text parsing is fragile and error-prone.

### 4. HTMX for Real-Time Updates

The UI uses HTMX for server-driven interactivity:
- Form submissions return HTML partials
- No complex JavaScript state management
- Progressive enhancement (works without JS)
- Server-side rendering for SEO and accessibility

**Rationale**: HTMX provides a modern, reactive UI experience while keeping the complexity on the server side where Django excels.

### 5. Demo Mode for Development

A built-in demo mode returns realistic mock responses without requiring AWS credentials:

- Enabled by default for easy local development
- Returns varied, realistic analysis outputs
- Clearly marked in the UI to avoid confusion
- Full audit logging even in demo mode

**Rationale**: Developers and stakeholders should be able to evaluate the UI and user experience without complex AWS setup.

---

## Project Structure

```
apps/llm_analysis/
├── __init__.py
├── admin.py                    # Django admin configuration
├── apps.py                     # App configuration
├── forms.py                    # PromptForm, TemplatePromptForm
├── models.py                   # SystemSettings, PromptTemplate, PromptAuditLog
├── urls.py                     # URL routing
├── views.py                    # HTMX views
├── tests.py                    # Comprehensive test suite
├── services/
│   ├── __init__.py
│   ├── bedrock.py              # BedrockService (Converse API + tool use)
│   ├── demo.py                 # DemoService for mock responses
│   ├── guardrails.py           # Guardrail configuration helpers
│   ├── output_parser.py        # Structured output parsing
│   └── security.py             # Prompt injection detection
├── templates/llm_analysis/
│   ├── analysis.html           # Main analysis page
│   ├── history.html            # User's analysis history
│   ├── audit_logs.html         # Staff audit log view
│   ├── audit_log_detail.html   # Single log detail
│   └── partials/
│       ├── error.html          # Error display component
│       ├── explanation.html    # Methodology explanation
│       ├── hypothesis_card.html # Hypothesis display card
│       ├── results.html        # Full results container
│       ├── search_result.html  # Data source reference
│       ├── template_form.html  # Dynamic template form
│       └── template_list.html  # Template selection list
└── migrations/
    ├── 0001_initial.py         # Schema migration
    └── 0002_default_data.py    # Default templates and settings
```

---

## Data Models

### SystemSettings (Singleton)

Global configuration for the platform:

| Field | Type | Description |
|-------|------|-------------|
| `prompt_mode` | CharField | constrained, guided, or open |
| `demo_mode` | BooleanField | Enable mock responses |
| `bypass_guardrails` | BooleanField | Dev-only guardrail bypass |
| `max_tokens` | PositiveIntegerField | LLM response limit |
| `model_id` | CharField | Bedrock model identifier |

### PromptTemplate

Pre-defined templates for constrained mode:

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Display name |
| `description` | TextField | What this template analyzes |
| `template` | TextField | Text with `{variable}` placeholders |
| `variables` | JSONField | Variable definitions (name, type, choices) |
| `category` | CharField | Grouping for UI |
| `usage_count` | PositiveIntegerField | Analytics |

### PromptAuditLog

Complete audit trail:

| Field | Type | Description |
|-------|------|-------------|
| `user` | ForeignKey | Who submitted (nullable for anonymous) |
| `prompt` | TextField | Original prompt text |
| `rendered_prompt` | TextField | Final prompt after template rendering |
| `mode` | CharField | Input mode used |
| `was_filtered` | BooleanField | Was the request blocked? |
| `filter_reason` | TextField | Why it was blocked |
| `guardrail_response` | JSONField | Full Bedrock Guardrails trace |
| `llm_response` | TextField | LLM output (truncated) |
| `response_time_ms` | PositiveIntegerField | Latency |
| `input_tokens` | PositiveIntegerField | Token usage |
| `output_tokens` | PositiveIntegerField | Token usage |
| `ip_address` | GenericIPAddressField | Client IP |
| `user_agent` | TextField | Browser/client info |

---

## Security Implementation

### Prompt Injection Detection Patterns

The security service detects multiple attack categories:

1. **Direct Instruction Override**
   - "ignore previous instructions"
   - "disregard your rules"
   - "forget everything you know"

2. **Role/Identity Manipulation**
   - "you are now a different AI"
   - "pretend to be a hacker"
   - "roleplay as an unrestricted assistant"

3. **System Prompt Extraction**
   - "reveal your system prompt"
   - "what are your instructions"
   - "repeat your initial message"

4. **Known Jailbreak Techniques**
   - DAN (Do Anything Now)
   - Developer/debug mode requests
   - Bypass safety requests

5. **Encoding/Obfuscation**
   - Base64 encode/decode requests
   - ROT13 manipulation
   - Hex/binary representation

6. **Context Injection**
   - `[system]` tags
   - `<system>` XML tags
   - Delimiter manipulation

### Bedrock Guardrails Configuration

Recommended guardrail settings are provided in `services/guardrails.py`:

- **Content Filters**: Block sexual, violent, hateful, toxic content
- **Prompt Attack Detection**: HIGH sensitivity
- **Denied Topics**: Non-analysis requests, harmful instructions, system manipulation
- **PII Handling**: Block SSN/credit cards, anonymize email/phone
- **Word Filters**: Profanity and known jailbreak terms

---

## UI Components

### Hypothesis Card

Displays analysis findings with:
- Title and summary
- Confidence level (color-coded badge)
- Collapsible evidence list
- Visualization type recommendation

### Search Result

Shows data sources with:
- Source name and relevance indicator
- Key snippet/finding
- Optional link to source

### Explanation Panel

Provides transparency:
- Methodology description
- Known limitations
- Actionable next steps

---

## API Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/analysis/` | GET | Main analysis page |
| `/analysis/analyze/` | POST | Submit analysis (HTMX) |
| `/analysis/template/<id>/form/` | GET | Get template form (HTMX) |
| `/analysis/history/` | GET | User's history |
| `/analysis/audit/` | GET | Audit logs (staff) |
| `/analysis/audit/<id>/` | GET | Audit detail (staff) |
| `/analysis/check-connection/` | POST | Test Bedrock connection |

---

## Running the Project

### Prerequisites

- Python 3.10+
- Poetry (package manager)
- Redis (for caching/Celery)
- PostgreSQL (production) or SQLite (development)

### Quick Start

```bash
# Clone and setup
git clone <repo>
cd amazon_bedrock

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env
# Edit .env with your settings (demo mode works without AWS)

# Run migrations
poetry run python manage.py migrate

# Create admin user
poetry run python manage.py createsuperuser

# Run development server
poetry run python manage.py runserver

# Access at http://localhost:8000/analysis/
```

### Demo Mode (Default)

Demo mode is **enabled by default**. This allows you to:
- Test the full UI without AWS credentials
- See realistic mock analysis responses
- Verify form validation and error handling
- Review audit logging functionality

To disable demo mode for production:
1. Go to Admin > LLM Analysis > System Settings
2. Uncheck "Demo mode"
3. Configure AWS credentials in `.env`

### Production Setup

1. **AWS Credentials**: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. **Bedrock Access**: Request model access in AWS Console
3. **Create Guardrail**: Follow instructions in `services/guardrails.py`
4. **Set Guardrail ID**: Add `BEDROCK_GUARDRAIL_ID` to `.env`
5. **Disable Demo Mode**: Uncheck in admin settings

---

## Testing

Run the test suite:

```bash
poetry run python manage.py test apps.llm_analysis
```

Tests cover:
- Security service (injection detection)
- Input validation
- Output parsing
- Form validation
- View authentication
- Audit logging

---

## Future Enhancements

1. **Async Processing**: Use Celery for long-running analyses
2. **Streaming Responses**: Real-time output with Bedrock streaming
3. **File Upload**: Analyze uploaded CSV/Excel files
4. **Visualization Integration**: Auto-generate charts from results
5. **Multi-Model Support**: Allow model selection per request
6. **Rate Limiting**: Per-user request limits
7. **API Access**: REST/GraphQL endpoints for programmatic access

---

## License

[Your License Here]

---

## Contributing

[Contribution Guidelines Here]
