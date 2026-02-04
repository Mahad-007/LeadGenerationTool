# Shopify UI Audit MVP - React UI Implementation Plan

## Overview
Create a React-based web UI for the existing Shopify UI Audit MVP using TDD methodology.

**Tech Stack:**
- Frontend: React 18 + TypeScript + Tailwind CSS + shadcn/ui
- Backend: FastAPI (wrapping existing Python scripts)
- Real-time: WebSocket for progress tracking
- Testing: Vitest + React Testing Library + Playwright

## Project Structure

```
/media/mahad/NewVolume/LeadGen/
├── frontend/                    # New React app
│   ├── src/
│   │   ├── app/                 # Page routes
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── context/             # React context providers
│   │   ├── services/            # API clients
│   │   ├── types/               # TypeScript types
│   │   └── lib/                 # Utilities
│   ├── tests/                   # Test files
│   └── package.json
│
├── backend/                     # New FastAPI backend
│   ├── app/
│   │   ├── api/                 # REST endpoints
│   │   ├── websocket/           # WebSocket handlers
│   │   ├── services/            # Script runners
│   │   └── models/              # Pydantic models
│   └── requirements.txt
│
└── scripts/                     # Existing Python scripts (unchanged)
```

---

## TDD Implementation Phases

### Phase 1: Project Setup & Foundation

#### 1.1 Frontend Setup
```bash
cd /media/mahad/NewVolume/LeadGen
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install -D tailwindcss postcss autoprefixer
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
npx shadcn@latest init
```

#### 1.2 Backend Setup
```bash
cd /media/mahad/NewVolume/LeadGen
mkdir -p backend/app/{api,websocket,services,models}
# requirements.txt: fastapi, uvicorn, websockets, pydantic
```

---

### Phase 2: TypeScript Types (RED → GREEN → REFACTOR)

**Files to create:**
- `frontend/src/types/discovery.ts`
- `frontend/src/types/verification.ts`
- `frontend/src/types/audit.ts`
- `frontend/src/types/contacts.ts`
- `frontend/src/types/outreach.ts`
- `frontend/src/types/websocket.ts`
- `frontend/src/types/pipeline.ts`

**TDD Steps:**
1. Write type tests (compile-time validation)
2. Define interfaces matching existing JSON outputs
3. Validate against actual JSON files

---

### Phase 3: Shared Components (TDD)

#### 3.1 StatusBadge Component
```
RED:   Write test for StatusBadge rendering different statuses
GREEN: Implement minimal StatusBadge
REFACTOR: Add variants, improve styling
```

#### 3.2 ProgressBar Component
```
RED:   Write test for progress percentage display
GREEN: Implement ProgressBar with percentage
REFACTOR: Add animation, accessibility
```

#### 3.3 DataTable Component
```
RED:   Write test for table rendering with data
GREEN: Implement basic table with sorting
REFACTOR: Add pagination, filtering
```

---

### Phase 4: Core Hooks (TDD)

#### 4.1 useWebSocket Hook
```typescript
// Test file: frontend/tests/hooks/useWebSocket.test.ts
// Test cases:
// - Connects to WebSocket server
// - Receives and parses messages
// - Handles disconnection/reconnection
// - Dispatches pipeline events
```

#### 4.2 usePipelineState Hook
```typescript
// Test file: frontend/tests/hooks/usePipelineState.test.ts
// Test cases:
// - Initial state is 'idle'
// - Transitions through step states
// - Tracks progress for each step
// - Handles errors gracefully
```

---

### Phase 5: Page Components (TDD)

#### 5.1 Dashboard Page
```
RED:   Test pipeline status cards render correctly
GREEN: Implement Dashboard with PipelineStatus components
REFACTOR: Add RunPipelineButton, step indicators
```

#### 5.2 Discovery Page
```
RED:   Test niche input form submission
GREEN: Implement NicheInput and DiscoveredSitesTable
REFACTOR: Add search source badges, export functionality
```

#### 5.3 Audit Page with ScreenshotViewer
```
RED:   Test screenshot viewer renders desktop/mobile tabs
GREEN: Implement ScreenshotViewer with tab switching
REFACTOR: Add zoom modal, performance metrics display
```

#### 5.4 Outreach Page with EmailDraftEditor
```
RED:   Test email editor allows editing and copying
GREEN: Implement EmailDraftEditor with save/copy
REFACTOR: Add preview mode, validation
```

---

### Phase 6: FastAPI Backend (TDD)

#### 6.1 API Endpoints
```python
# Test file: backend/tests/test_api.py
# Endpoints to implement:
GET  /api/pipeline/status
POST /api/pipeline/run
POST /api/pipeline/stop
GET  /api/discovery
POST /api/discovery/run
GET  /api/verification
GET  /api/audit
GET  /api/audit/screenshot/{filename}
GET  /api/contacts
GET  /api/outreach
PUT  /api/outreach/{url}
```

#### 6.2 WebSocket Handler
```python
# Test file: backend/tests/test_websocket.py
WS   /ws/pipeline
# Events: step_started, step_progress, step_completed, pipeline_completed
```

#### 6.3 Pipeline Runner Service
```python
# Test file: backend/tests/test_pipeline_runner.py
# Test cases:
# - Executes Python scripts via subprocess
# - Broadcasts progress via WebSocket
# - Handles script errors gracefully
# - Supports stopping mid-pipeline
```

---

### Phase 7: Integration & E2E Tests

#### 7.1 Integration Tests
- API client integration with FastAPI
- WebSocket message handling
- Context provider state management

#### 7.2 E2E Tests (Playwright)
```typescript
// Tests:
// - Full pipeline flow from discovery to outreach
// - Screenshot viewer with desktop/mobile switching
// - Email draft editing and copying
// - Real-time progress updates
```

---

## Component Architecture

### Layout Components
```
src/components/layout/
├── AppShell.tsx              # Main app shell with sidebar
├── Sidebar.tsx               # Navigation sidebar
├── Header.tsx                # Top header bar
└── StepIndicator.tsx         # Pipeline step progress indicator
```

### Pipeline Components
```
src/components/pipeline/
├── PipelineStatus.tsx        # Overall pipeline status card
├── StepCard.tsx              # Individual step status card
├── RunPipelineButton.tsx     # Start/stop pipeline controls
└── PipelineProgress.tsx      # Real-time progress display
```

### Discovery Components
```
src/components/discovery/
├── NicheInput.tsx            # Niche keyword input form
├── DiscoveredSitesTable.tsx  # Table of discovered URLs
└── SearchSourceBadge.tsx     # Badge showing source (Google/Bing/DB)
```

### Verification Components
```
src/components/verification/
├── VerificationTable.tsx     # Shopify verification results
├── ConfidenceBadge.tsx       # Confidence score indicator
└── SignalsList.tsx           # List of detected Shopify signals
```

### Audit Components
```
src/components/audit/
├── AuditTable.tsx            # Audit results table
├── ScreenshotViewer.tsx      # Desktop/mobile screenshot viewer
├── ScreenshotZoom.tsx        # Zoom modal for screenshots
├── PerformanceMetrics.tsx    # LCP, FCP, TTFB display
└── ConsoleErrorsList.tsx     # Console errors accordion
```

### Analysis Components
```
src/components/analysis/
├── AnalysisTable.tsx         # AI analysis results table
├── IssueCard.tsx             # Individual issue display card
├── SeverityBadge.tsx         # High/Medium/Low severity badge
└── IssuesSummary.tsx         # Summary of all issues
```

### Contacts Components
```
src/components/contacts/
├── ContactsTable.tsx         # Extracted contacts table
├── SocialLinksDisplay.tsx    # Social media links display
└── EmailsList.tsx            # List of extracted emails
```

### Outreach Components
```
src/components/outreach/
├── DraftsTable.tsx           # Email drafts table
├── EmailDraftEditor.tsx      # Edit email draft
├── EmailPreview.tsx          # Preview formatted email
└── CopyToClipboard.tsx       # Copy email button
```

### Shared Components
```
src/components/shared/
├── DataTable.tsx             # Reusable data table component
├── ProgressBar.tsx           # Progress bar with percentage
├── StatusBadge.tsx           # Generic status badge
├── LoadingSpinner.tsx        # Loading indicator
├── ErrorAlert.tsx            # Error display component
├── EmptyState.tsx            # Empty data state display
└── ConfirmDialog.tsx         # Confirmation dialog
```

---

## Page Layouts

### Dashboard Page (Home)
```
+------------------------------------------------------------------+
| Header: Shopify UI Audit Tool                    [Settings] [Help] |
+------------------------------------------------------------------+
|         |                                                         |
|         |  +------------------+  +------------------+              |
| Sidebar |  | Pipeline Status  |  | Quick Actions    |              |
|         |  | Step: 3/6 Active |  | [Run Pipeline]   |              |
| [Home]  |  | Progress: 45%    |  | [Add URLs]       |              |
|         |  +------------------+  +------------------+              |
| Steps:  |                                                         |
| 1.Disc  |  +------------------------------------------------+     |
| 2.Veri  |  |                 Step Progress                  |     |
| 3.Audit |  | [1.Done] [2.Done] [3.Running] [4] [5] [6]      |     |
| 4.Anal  |  +------------------------------------------------+     |
| 5.Cont  |                                                         |
| 6.Out   |  +----------------------+  +----------------------+     |
|         |  | Sites Discovered: 15 |  | Shopify Verified: 12 |     |
|         |  +----------------------+  +----------------------+     |
|         |  +----------------------+  +----------------------+     |
|         |  | Audits Complete: 8   |  | Issues Found: 24     |     |
|         |  +----------------------+  +----------------------+     |
|         |  +----------------------+  +----------------------+     |
|         |  | Contacts Found: 10   |  | Drafts Ready: 8      |     |
|         |  +----------------------+  +----------------------+     |
+------------------------------------------------------------------+
```

### Audit Page with Screenshot Viewer
```
+------------------------------------------------------------------+
| Header: Homepage Audit                           [Run Step] [Back] |
+------------------------------------------------------------------+
|         |                                                         |
| Sidebar |  +------------------------------------------------+     |
|         |  | Audit Results (8 sites)                [Export]|     |
|         |  +------------------------------------------------+     |
|         |  | URL           | Status | Issues | Screenshots  |     |
|         |  |---------------|--------|--------|--------------|     |
|         |  | gymshark.com  | Done   | 3      | [View]       |     |
|         |  | allbirds.com  | Done   | 1      | [View]       |     |
|         |  +------------------------------------------------+     |
|         |                                                         |
|         |  +------------------------------------------------+     |
|         |  | Screenshot Viewer: gymshark.com                |     |
|         |  +------------------------------------------------+     |
|         |  | [Desktop] [Mobile]                    [Zoom +] |     |
|         |  | +------------------------------------------+   |     |
|         |  | |                                          |   |     |
|         |  | |         Screenshot Preview               |   |     |
|         |  | |         (1440x900 viewport)              |   |     |
|         |  | |                                          |   |     |
|         |  | +------------------------------------------+   |     |
|         |  | Performance: LCP: 3624ms  FCP: 1936ms          |     |
|         |  +------------------------------------------------+     |
+------------------------------------------------------------------+
```

### Outreach Page with Email Editor
```
+------------------------------------------------------------------+
| Header: Email Outreach                           [Generate] [Back] |
+------------------------------------------------------------------+
|         |                                                         |
| Sidebar |  +------------------------------------------------+     |
|         |  | Email Drafts (8 ready)                  [Export]|     |
|         |  +------------------------------------------------+     |
|         |  | Store         | Subject        | To     | Act  |     |
|         |  |---------------|----------------|--------|------|     |
|         |  | Gymshark      | Mobile issue..| social | Edit |     |
|         |  | Allbirds      | Design feedba.| email  | Edit |     |
|         |  +------------------------------------------------+     |
|         |                                                         |
|         |  +------------------------------------------------+     |
|         |  | Email Editor: Gymshark                         |     |
|         |  +------------------------------------------------+     |
|         |  | To: (social media - no email found)            |     |
|         |  | Subject: [Mobile experience feedback for Gy..] |     |
|         |  | +------------------------------------------+   |     |
|         |  | | Hi there,                                |   |     |
|         |  | |                                          |   |     |
|         |  | | I viewed Gymshark on mobile and noticed  |   |     |
|         |  | | something that might be impacting your   |   |     |
|         |  | | mobile shoppers...                       |   |     |
|         |  | |                                          |   |     |
|         |  | +------------------------------------------+   |     |
|         |  | [Copy to Clipboard] [Save Changes] [Reset]     |     |
|         |  +------------------------------------------------+     |
+------------------------------------------------------------------+
```

---

## Critical Components with TDD Order

### Priority 1: Foundation
| Component | Test File | Implementation File |
|-----------|-----------|---------------------|
| Types | `tests/types/*.test.ts` | `src/types/*.ts` |
| API Client | `tests/services/api.test.ts` | `src/services/api.ts` |
| WebSocket Hook | `tests/hooks/useWebSocket.test.ts` | `src/hooks/useWebSocket.ts` |

### Priority 2: Core UI
| Component | Test File | Implementation File |
|-----------|-----------|---------------------|
| AppShell | `tests/components/layout/AppShell.test.tsx` | `src/components/layout/AppShell.tsx` |
| Sidebar | `tests/components/layout/Sidebar.test.tsx` | `src/components/layout/Sidebar.tsx` |
| DataTable | `tests/components/shared/DataTable.test.tsx` | `src/components/shared/DataTable.tsx` |
| ProgressBar | `tests/components/shared/ProgressBar.test.tsx` | `src/components/shared/ProgressBar.tsx` |

### Priority 3: Feature Components
| Component | Test File | Implementation File |
|-----------|-----------|---------------------|
| PipelineStatus | `tests/components/pipeline/PipelineStatus.test.tsx` | `src/components/pipeline/PipelineStatus.tsx` |
| ScreenshotViewer | `tests/components/audit/ScreenshotViewer.test.tsx` | `src/components/audit/ScreenshotViewer.tsx` |
| EmailDraftEditor | `tests/components/outreach/EmailDraftEditor.test.tsx` | `src/components/outreach/EmailDraftEditor.tsx` |

### Priority 4: Backend
| Component | Test File | Implementation File |
|-----------|-----------|---------------------|
| Pipeline Router | `backend/tests/test_pipeline.py` | `backend/app/api/pipeline.py` |
| WebSocket Manager | `backend/tests/test_websocket.py` | `backend/app/websocket/manager.py` |
| Pipeline Runner | `backend/tests/test_runner.py` | `backend/app/services/pipeline_runner.py` |

---

## API Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/pipeline/status` | Get current pipeline status |
| POST | `/api/pipeline/run` | Start full pipeline |
| POST | `/api/pipeline/stop` | Stop running pipeline |
| GET | `/api/discovery` | Get discovered sites |
| POST | `/api/discovery/run` | Run discovery step |
| GET | `/api/verification` | Get verification results |
| POST | `/api/verification/run` | Run verification step |
| GET | `/api/audit` | Get audit results |
| GET | `/api/audit/screenshot/:file` | Get screenshot image |
| POST | `/api/audit/run` | Run audit step |
| GET | `/api/analysis` | Get analysis results |
| POST | `/api/analysis/run` | Run Gemini analysis |
| GET | `/api/contacts` | Get extracted contacts |
| POST | `/api/contacts/run` | Run contact extraction |
| GET | `/api/outreach` | Get email drafts |
| PUT | `/api/outreach/:url` | Update email draft |
| POST | `/api/outreach/run` | Generate email drafts |
| WS | `/ws/pipeline` | Real-time progress updates |

---

## WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `connected` | Server→Client | `{ clientId }` |
| `pipeline_started` | Server→Client | `{ runId, steps }` |
| `step_started` | Server→Client | `{ step }` |
| `step_progress` | Server→Client | `{ step, current, total, percentage, message }` |
| `step_completed` | Server→Client | `{ step, duration, itemsProcessed }` |
| `step_failed` | Server→Client | `{ step, error }` |
| `pipeline_completed` | Server→Client | `{ summary }` |
| `pipeline_failed` | Server→Client | `{ error }` |

---

## TypeScript Type Definitions

### Discovery Types
```typescript
interface DiscoveryMetadata {
  generated_at: string;
  total_niches: number;
  total_urls: number;
}

interface Discovery {
  niche: string;
  discovered_at: string;
  total_urls: number;
  urls: string[];
  search_metadata: SearchMetadata[];
  source: 'database' | 'search_engines';
}

interface SearchMetadata {
  engine: 'google' | 'bing' | 'duckduckgo' | 'built_in_database';
  query: string;
  results_count: number;
}

interface DiscoveryResponse {
  metadata: DiscoveryMetadata;
  discoveries: Discovery[];
}
```

### Verification Types
```typescript
interface VerificationMetadata {
  generated_at: string;
  total_verified: number;
  shopify_count: number;
  non_shopify_count: number;
  min_confidence_threshold: number;
}

interface ShopifySite {
  url: string;
  is_shopify: boolean;
  confidence: number;
  signals_found: string[];
  verified_at: string;
  error: string | null;
}

interface VerificationResponse {
  metadata: VerificationMetadata;
  shopify_sites: ShopifySite[];
  verification_log: ShopifySite[];
}
```

### Audit Types
```typescript
interface Viewport {
  width: number;
  height: number;
}

interface PerformanceMetrics {
  lcp: number | null;
  fcp: number | null;
  dom_content_loaded: number | null;
  load_complete: number | null;
  ttfb: number | null;
}

interface ViewportAudit {
  viewport_type: 'desktop' | 'mobile';
  viewport: Viewport;
  screenshot_path: string;
  console_errors: ConsoleError[];
  performance_metrics: PerformanceMetrics;
  dom_info: DomInfo;
  error: string | null;
}

interface Issue {
  id: string;
  category: 'typography' | 'layout' | 'images' | 'mobile' | 'contrast' | 'hierarchy';
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  location: string;
  evidence: string;
  recommendation: string;
}

interface Audit {
  url: string;
  audited_at: string;
  desktop: ViewportAudit | null;
  mobile: ViewportAudit | null;
  error: string | null;
  analysis?: {
    issues: Issue[];
    summary: AnalysisSummary;
  };
}
```

### Contacts Types
```typescript
interface SocialLinks {
  instagram?: string;
  facebook?: string;
  twitter?: string;
  linkedin?: string;
  tiktok?: string;
}

interface Contact {
  url: string;
  extracted_at: string;
  emails: string[];
  phones: string[];
  social: SocialLinks;
  contact_page_found: boolean;
  sources: string[];
  error: string | null;
}
```

### Outreach Types
```typescript
interface DraftInfo {
  url: string;
  file: string;
  subject: string;
  to_emails: string[];
  issue_category: string;
}

interface EmailDraft {
  store_url: string;
  subject: string;
  body: string;
  to_emails: string[];
  social: SocialLinks;
  issue_referenced: {
    title: string;
    category: string;
    severity: string;
  };
}
```

---

## Files to Create

### New Files (Frontend)
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tailwind.config.js`
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/types/*.ts` (7 files)
- `frontend/src/hooks/*.ts` (8 files)
- `frontend/src/context/*.tsx` (3 files)
- `frontend/src/services/*.ts` (7 files)
- `frontend/src/components/**/*.tsx` (~30 files)
- `frontend/tests/**/*.test.ts(x)` (~25 files)

### New Files (Backend)
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/api/*.py` (8 files)
- `backend/app/websocket/*.py` (3 files)
- `backend/app/services/*.py` (3 files)
- `backend/app/models/*.py` (6 files)
- `backend/tests/*.py` (5 files)

### Existing Files (No Changes)
- `/media/mahad/NewVolume/LeadGen/scripts/*.py` (unchanged)
- `/media/mahad/NewVolume/LeadGen/config/settings.py` (unchanged)

---

## Test Coverage Targets

| Category | Target |
|----------|--------|
| Components | 80% |
| Hooks | 90% |
| Services | 85% |
| Utils | 95% |
| Backend API | 85% |
| E2E Critical Paths | 100% |

---

## Execution Checklist

- [ ] Phase 1: Project setup (Vite, Tailwind, shadcn, FastAPI)
- [ ] Phase 2: TypeScript types with tests
- [ ] Phase 3: Shared components (TDD)
- [ ] Phase 4: Core hooks (TDD)
- [ ] Phase 5: Page components (TDD)
- [ ] Phase 6: FastAPI backend (TDD)
- [ ] Phase 7: Integration & E2E tests
- [ ] Phase 8: Final polish and documentation
