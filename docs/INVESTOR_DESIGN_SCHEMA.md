# LibraryOfBabel - Multi-Modal AI Search Platform
## Frontend Design Schema | January 2026

---

## Executive Summary

LibraryOfBabel is a **multi-modal AI semantic search platform** with intelligent content routing across 5 specialized embedding models. Built on PostgreSQL-First architecture handling 8,673 books and 247,911 searchable chunks with <200ms response times.

### Unique Technical Differentiator
**5-Model AI Architecture with Intelligent Routing**
- Technical/academic content → `granite-embedding` (768d)
- Creative/narrative content → `bge-m3` (1024d)
- Multilingual content → `mxbai-embed-large` (1024d)
- General content → `nomic-embed-text` (768d)
- Specialized domains → `snowflake-arctic-embed` (1024d)

### Platform Statistics
| Metric | Value | Technical Significance |
|--------|-------|------------------------|
| Total Books | 8,673 | 3x recent growth via Calibre integration |
| Searchable Chunks | 247,911 | Passage-level granularity |
| AI Models Deployed | 5 models | Multi-modal intelligence |
| Vector Dimensions | 768d + 1024d | Hybrid architecture |
| Avg Response Time | <200ms | Production-ready performance |
| Search Accuracy | 94%+ | Semantic relevance scores |

---

## Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-MODAL AI SEARCH PLATFORM                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  SEARCH UI   │  │  BROWSE UI   │  │  ADMIN/API   │          │
│  │ (Multi-Modal)│  │ (8,673 books)│  │    DOCS      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
├─────────┴──────────────────┴──────────────────┴──────────────────┤
│                 REST API (Port 5562 Production)                  │
│   /search  │  /books/{id}/search  │  /books?action=*            │
├─────────────────────────────────────────────────────────────────┤
│  5-Model AI Routing Layer (Intelligent Content Classification)   │
├─────────────────────────────────────────────────────────────────┤
│    PostgreSQL + pgvector + 5 Embedding Columns (HNSW/IVFFlat)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 1: MULTI-MODAL SEARCH INTERFACE (Primary Product Demo)

### Purpose
Showcase intelligent AI model routing and semantic search quality across 247,911 chunks. This is the core differentiator - competitors use single embeddings, we use 5 specialized models with automatic content-aware routing.

### API Endpoints Used
```
GET /search?q={query}&limit={n}&model={type}           → Multi-modal semantic search
GET /books/{id}/search?q={query}                       → Book-specific search
GET /health                                            → System health/metrics
```

### Design Parameters

#### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: LibraryOfBabel Logo + [Browse] + [API Docs]            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  SEARCH BAR (Prominent, full-width)                    │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ 🔍  Search 247,911 passages across 5 AI models...│  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  │                                                         │     │
│  │  Recent: "quantum consciousness" "fraud detection"     │     │
│  │                                                         │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ 🧠 AI MODEL ROUTING (Auto-select or manual)     │  │     │
│  │  │ ○ Auto-Route  ● Technical  ○ Creative           │  │     │
│  │  │ ○ Multilingual  ○ General  ○ Specialized        │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────┐  ┌────────────────────────────────────────┐      │
│  │ FILTERS  │  │  RESULTS (Showing AI routing metadata) │      │
│  │          │  │                                         │      │
│  │ Author   │  │  ┌────────────────────────────────┐    │      │
│  │ [All ▼]  │  │  │ 📄 Discipline and Punish       │    │      │
│  │          │  │  │ Michel Foucault • 1975         │    │      │
│  │ Genre    │  │  │                                │    │      │
│  │ [All ▼]  │  │  │ 🧠 AI Model: granite-embedding │    │      │
│  │          │  │  │ 📊 Relevance: 94.2%           │    │      │
│  │ Content  │  │  │ 🎯 Routing: Technical/Academic │    │      │
│  │ Type     │  │  │ ⚡ Response: 89ms              │    │      │
│  │ [All ▼]  │  │  │                                │    │      │
│  │          │  │  │ "Visibility is a trap. The     │    │      │
│  │ Sort By  │  │  │ inmate must never know whether │    │      │
│  │ • Relev. │  │  │ he is being looked at..."      │    │      │
│  │ ○ Date   │  │  │                                │    │      │
│  │ ○ Author │  │  │ [📋 Copy] [🔗 Cite] [📖 Context]│    │      │
│  │          │  │  └────────────────────────────────┘    │      │
│  │ Results  │  │                                         │      │
│  │ 47 found │  │  ┌────────────────────────────────┐    │      │
│  │ 89ms     │  │  │ 📄 The Society of the Spectacle│    │      │
│  └──────────┘  │  │ Guy Debord • 1967              │    │      │
│                │  │                                 │    │      │
│                │  │ 🧠 AI Model: bge-m3            │    │      │
│                │  │ 📊 Relevance: 89.1%            │    │      │
│                │  │ 🎯 Routing: Creative/Cultural  │    │      │
│                │  │                                 │    │      │
│                │  │ "In societies dominated by...  │    │      │
│                │  │                                 │    │      │
│                │  │ [📋 Copy] [🔗 Cite] [📖 Context]│    │      │
│                │  └────────────────────────────────┘    │      │
│                │                                         │      │
│                │  [Load More Results]                    │      │
│                └────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### AI Model Selector (Key Differentiator)

```
┌──────────────────────────────────────────────────────────┐
│  Select AI Model (or let system auto-route)             │
├──────────────────────────────────────────────────────────┤
│  ○ Auto-Route (Recommended)                             │
│     System analyzes query and selects optimal model     │
│                                                          │
│  ○ 🔬 Technical (granite-embedding 768d)                │
│     Best for: Science, Philosophy, Tech, Business       │
│                                                          │
│  ○ 📖 Creative (bge-m3 1024d)                           │
│     Best for: Fiction, Literature, Narrative           │
│                                                          │
│  ○ 🌍 Multilingual (mxbai-embed-large 1024d)           │
│     Best for: History, Biography, Cultural studies      │
│                                                          │
│  ○ ⚡ General (nomic-embed-text 768d)                   │
│     Best for: Reference, Self-help, General topics      │
│                                                          │
│  ○ ❄️ Specialized (snowflake-arctic-embed 1024d)       │
│     Best for: Domain-specific technical content         │
└──────────────────────────────────────────────────────────┘
```

#### Result Card Component (Shows AI Routing)

```
┌──────────────────────────────────────────────────────┐
│ 📄 Discipline and Punish                             │
│ Michel Foucault • Philosophy • 1975                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 🧠 AI MODEL USED: granite-embedding (768d)          │
│ 🎯 ROUTING REASON: Technical/Academic Content       │
│ 📊 SEMANTIC SIMILARITY: 94.2%                       │
│ ⚡ RESPONSE TIME: 89ms                              │
│                                                      │
├──────────────────────────────────────────────────────┤
│ MATCHED PASSAGE:                                     │
│                                                      │
│ "Visibility is a trap. The inmate must never know   │
│ whether he is being looked at any one moment; but   │
│ he must be sure that he may always be so. The       │
│ Panopticon is a machine for dissociating the        │
│ see/being seen dyad..."                             │
│                                                      │
│ Chunk ID: 15847 | Type: fullbook | Index: 234      │
│                                                      │
├──────────────────────────────────────────────────────┤
│ [📋 Copy Passage] [🔗 Copy Citation]                 │
│ [📖 View Full Context] [🔍 More from this book]      │
└──────────────────────────────────────────────────────┘
```

#### Component Specifications

| Component | Tech Stack | Features |
|-----------|------------|----------|
| Search Input | React + Debounce (300ms) | Auto-suggest, keyboard shortcuts |
| AI Model Selector | Radix UI Radio Group | Tooltips explaining each model |
| Result Cards | React + Skeleton Loading | Expand for full passage |
| Relevance Bar | CSS + SVG | Animated fill, color-coded |
| Routing Badge | Tailwind Badge | Shows which AI model was used |
| Copy Buttons | Clipboard API | Toast notifications |

#### Color Palette (Search UI)

```css
/* Dark Mode Primary */
--bg-primary: #0f0f1a;        /* Deep background */
--bg-card: #1e1e2e;           /* Card background */
--text-primary: #e5e5e5;      /* Main text */
--text-secondary: #a0a0a0;    /* Metadata */

/* AI Model Colors */
--model-technical: #7c3aed;   /* Purple - Technical */
--model-creative: #e94560;    /* Coral - Creative */
--model-multilingual: #22c55e; /* Green - Multilingual */
--model-general: #3b82f6;     /* Blue - General */
--model-specialized: #f59e0b; /* Amber - Specialized */

/* Relevance Indicators */
--relevance-high: #22c55e;    /* >90% */
--relevance-med: #eab308;     /* 70-90% */
--relevance-low: #ef4444;     /* <70% */
```

---

## Section 2: LIBRARY BROWSE (8,673 Books)

### Purpose
Traditional library browsing with filtering by genre, author, and content classification. Shows the scale of the corpus.

### API Endpoints Used
```
GET /books?action=list&limit={n}&page={p}    → Paginated book list
GET /books?action=summary&id={id}            → Book metadata
```

### Design Parameters

#### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│  LIBRARY BROWSE: 8,673 Books                                │
├─────────────────────────────────────────────────────────────┤
│  TOOLBAR                                                     │
│  [Grid View] [List View] │ Sort: [Title ▼] │ Per Page: [20] │
│                                                              │
│  GENRE/CONTENT FILTERS (Horizontal Scroll)                  │
│  [All] [Philosophy] [Sci-Fi] [Tech] [Fiction] [History]... │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 📚      │ │ 📚      │ │ 📚      │ │ 📚      │           │
│  │ Book    │ │ Book    │ │ Book    │ │ Book    │           │
│  │ Cover   │ │ Cover   │ │ Cover   │ │ Cover   │           │
│  │ (Gen)   │ │ (Gen)   │ │ (Gen)   │ │ (Gen)   │           │
│  │         │ │         │ │         │ │         │           │
│  │ Title   │ │ Title   │ │ Title   │ │ Title   │           │
│  │ Author  │ │ Author  │ │ Author  │ │ Author  │           │
│  │ Genre   │ │ Genre   │ │ Genre   │ │ Genre   │           │
│  │ 🧠 Model│ │ 🧠 Model│ │ 🧠 Model│ │ 🧠 Model│           │
│  │ 425chk  │ │ 892chk  │ │ 234chk  │ │ 567chk  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                              │
│  [Load More] or Pagination: [1][2][3]...[434]               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Book Card (Grid View)

```
┌────────────────────────────┐
│  ┌──────────────────────┐  │
│  │                      │  │
│  │   GENERATED COVER    │  │  ← Procedural from genre+title
│  │   Based on genre     │  │
│  │   color palette      │  │
│  │                      │  │
│  └──────────────────────┘  │
│                            │
│  Discipline and Punish     │  ← Truncate long titles
│  Michel Foucault           │
│  Philosophy • 1975         │
│                            │
│  🧠 Technical Model        │  ← Shows routing
│  📊 425 chunks             │
│                            │
│  [🔍 Search Book]          │
│  [📖 View Details]         │
└────────────────────────────┘
```

#### Book Detail Modal

```
┌──────────────────────────────────────────────────────────┐
│  Discipline and Punish                              [✕]  │
│  Michel Foucault                                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📚 METADATA                                            │
│  Genre: Philosophy                                       │
│  Published: 1975                                         │
│  Chunks: 425 searchable passages                        │
│  AI Model: granite-embedding (Technical/Academic)       │
│  Content Type: Analytical, Theoretical                  │
│                                                          │
│  📝 SUMMARY                                             │
│  A seminal work on surveillance, power structures, and  │
│  the disciplinary society. Examines how institutions    │
│  exercise control through observation and normalization.│
│                                                          │
│  🔍 SEARCH THIS BOOK                                    │
│  ┌────────────────────────────────────────────────┐     │
│  │ Search within Discipline and Punish...        │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  [📖 Close]                                             │
└──────────────────────────────────────────────────────────┘
```

---

## Section 3: ADMIN/METRICS PANEL

### Purpose
System health monitoring and API usage metrics for demo/operations.

### API Endpoints Used
```
GET /health                                    → System status
```

### Design (Minimal MVP)

```
┌─────────────────────────────────────────────────────────┐
│  SYSTEM STATUS                                          │
├─────────────────────────────────────────────────────────┤
│  ✅ API Status: Operational                            │
│  ✅ Database: Connected                                │
│  ✅ All 5 AI Models: Available                         │
│                                                          │
│  📊 PLATFORM METRICS                                    │
│  • Total Books: 8,673                                   │
│  • Searchable Chunks: 247,911                           │
│  • Avg Response Time: <200ms                            │
│  • Search Accuracy: 94%+                                │
│                                                          │
│  🧠 AI MODEL STATUS                                     │
│  ✅ granite-embedding (768d)                            │
│  ✅ bge-m3 (1024d)                                      │
│  ✅ mxbai-embed-large (1024d)                           │
│  ✅ nomic-embed-text (768d)                             │
│  ✅ snowflake-arctic-embed (1024d)                      │
└─────────────────────────────────────────────────────────┘
```

---

## Global Design System

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| H1 (Page Title) | Inter | 36px | 700 |
| H2 (Section) | Inter | 24px | 600 |
| H3 (Card Title) | Inter | 18px | 600 |
| Body | Inter | 16px | 400 |
| Code/Metadata | JetBrains Mono | 14px | 400 |
| Search Input | Inter | 18px | 400 |

### Spacing System

```
4px  - xs (tight elements)
8px  - sm (compact spacing)
12px - md (default spacing)
16px - lg (comfortable spacing)
24px - xl (section gaps)
32px - 2xl (major sections)
```

### Animation Principles

1. **Performance First**: GPU-accelerated transforms only
2. **Duration**: 150ms for interactions, 300ms for transitions
3. **Easing**: `cubic-bezier(0.4, 0, 0.2, 1)`
4. **Loading**: Skeleton screens with shimmer effect
5. **Search**: Debounce 300ms, show "Searching..." state

### Responsive Breakpoints

| Breakpoint | Width | Search Layout |
|------------|-------|---------------|
| Mobile | < 640px | Stacked, bottom filters |
| Tablet | 640-1024px | 2-col results |
| Desktop | 1024-1440px | Sidebar + results |
| Wide | > 1440px | Max 1440px container |

---

## Tech Stack

### Frontend
```
React 18 + TypeScript
├── Next.js 14 (App Router for SSR)
├── Tailwind CSS + Headless UI
├── Radix UI (Accessible components)
├── React Query (API state management)
├── Framer Motion (Animations)
└── Recharts (Simple metrics viz)
```

### Key Libraries
```
- @tanstack/react-query - Server state
- @radix-ui/react-* - Accessible primitives
- tailwindcss - Utility-first CSS
- framer-motion - Animation
- zustand - Lightweight global state
- react-syntax-highlighter - Code display
```

### API Integration
```typescript
// Example API call structure
const searchResults = useQuery({
  queryKey: ['search', query, model],
  queryFn: () =>
    fetch(`${API_BASE}/search?q=${query}&limit=20&model=${model}`, {
      headers: { 'Authorization': `Bearer ${apiKey}` }
    }).then(res => res.json())
})
```

---

## 5-Minute Investor Demo Script

### Act 1: The Problem (30s)
"Traditional search is keyword-based. It fails on semantic meaning. Existing RAG systems use one embedding model - one-size-fits-all approach that degrades accuracy."

### Act 2: Our Solution (90s)
**[Show Search Interface]**

"LibraryOfBabel uses 5 specialized AI models with intelligent routing:

1. **Technical Query**: 'explain quantum entanglement'
   - Routes to `granite-embedding`
   - Shows 94%+ relevance physics passages

2. **Creative Query**: 'stories about human resilience'
   - Routes to `bge-m3`
   - Returns narrative-rich fiction excerpts

3. **Compare Results**: Same query, different models
   - Show how routing affects result quality
   - Highlight response time <200ms"

### Act 3: Scale & Performance (60s)
**[Show Browse + Metrics]**

- 8,673 books indexed
- 247,911 searchable chunks
- All 5 models running locally
- PostgreSQL-First architecture
- Production-ready with CI/CD

### Act 4: Business Model (45s)
- API-first architecture
- Per-query pricing or enterprise licensing
- Self-hosted = no per-token costs
- Expandable to custom document collections

### Act 5: The Ask (45s)
"This demo runs on $40k seed funding. We need $250k to:
- Scale to 100K+ documents
- Build enterprise features (SSO, multi-tenant)
- Go-to-market for legal/finance/research sectors"

---

## Development Timeline (6 Weeks with Claude Code)

| Week | Deliverable | Key Features |
|------|-------------|--------------|
| 1-2  | Search Interface | Multi-modal routing UI, result cards |
| 3    | Browse Library | Grid/list views, filtering |
| 4    | Admin Panel | Health dashboard, metrics |
| 5    | Polish & Responsive | Mobile optimization, animations |
| 6    | Demo Prep | Investor script, sample queries |

---

## Key Investor Talking Points

### Technical Moats
1. **5-Model Architecture**: Unique multi-modal approach
2. **PostgreSQL-First**: No expensive vector DB licensing
3. **Intelligent Routing**: Content-aware model selection
4. **Self-Hosted AI**: No per-token costs

### Market Position
- **vs. Perplexity**: They search the web, we search your proprietary docs
- **vs. Pinecone/Weaviate**: We're 10x cheaper (PostgreSQL-based)
- **vs. OpenAI Embeddings**: We use 5 specialized models, they use one

### Growth Path
1. **Phase 1** (Now): Prove technology with book corpus
2. **Phase 2** (6mo): Enterprise doc search (legal, finance)
3. **Phase 3** (12mo): PCI compliance automation integration
4. **Phase 4** (18mo): Multi-tenant SaaS platform

---

*Document prepared for investor presentation | LibraryOfBabel Multi-Modal AI Platform*
*Production API: https://api.ashortstayinhell.com:5562*
*Staging API: https://staging.ashortstayinhell.com:5568*
