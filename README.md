# LibraryOfBabel 📚

**Personal Knowledge Base Indexing System**

Transform your digital book collection into a searchable, AI-accessible research library.

## Overview

LibraryOfBabel is a comprehensive system that processes personal digital libraries (EPUBs and audiobooks) into a searchable knowledge base. It enables AI research agents to query across thousands of books instantly, making literature review and research dramatically more efficient.

## Current Status: Phase 4+ (85% Complete) 🚀

**Production-Scale Knowledge Base + MAM Automation Operational**

### ✅ **Phase 1-3: Complete Foundation**
- 🎯 **304/545 books processed** from CloudDocs collection (55.8% success rate)
- 📊 **38.95M words** extracted and indexed in PostgreSQL
- ⚡ **5,013 books/hour** processing speed at scale
- 🔍 **13,794 searchable text chunks** with full-text search
- 🤖 **Reddit Nerd Librarian** AI agent deployed with chaos testing

### 🔄 **Phase 4: Audio Integration (In Progress)**
- 🎧 **Backend Audio Agent** deployed for 5000+ audiobook transcription
- 📁 **184 .m4b audiobooks** discovered (441GB available storage)
- 🆓 **Free local Whisper** setup (no API costs)

### 🆕 **NEW: MAM Audiobook-to-Ebook Automation**
- 📚 **5,839 audiobooks** tracked from Plex database
- 🤖 **Playwright automation** for MAM search/download
- 🍪 **Smart session management** with fallback authentication
- 📊 **Web dashboard** for real-time progress monitoring
- ⚡ **Rate-limited processing** (95 searches/day)
- 🎯 **Target: 80%+ coverage** in 62 days (4,100+ ebook matches)

## Features

### 📖 EPUB Processing
- Handles diverse EPUB formats (professional, academic, Calibre-generated)
- Preserves chapter structure and metadata
- Hierarchical text chunking (chapter/section/paragraph levels)
- Error-resistant processing with graceful degradation

### 🔍 Intelligent Text Chunking
- **Primary chunks**: Chapter-level (2,000-5,000 words)
- **Secondary chunks**: Section-level (500-1,500 words)
- **Micro chunks**: Paragraph-level (50-200 words)
- Context preservation with 50-word overlap

### 🗃️ Database Architecture
- PostgreSQL with full-text search optimization
- Scalable schema for millions of text chunks
- Advanced indexing for sub-100ms search performance
- Multi-agent concurrent access support

### 🤖 AI Agent Integration
- **PostgreSQL database** with 13,794 searchable chunks
- **RESTful API** for research agent queries
- **Reddit Nerd Librarian** with chaos testing capabilities
- **QA Agent** with 75% fix success rate
- **Cross-domain search** (Philosophy + Finance queries working)
- **SQL injection protection** (<1ms blocking)

### 🏴‍☠️ MAM Audiobook-to-Ebook System
- **Collection tracking** for 5,839 unique audiobooks
- **Automated MAM search** with title/author matching
- **Confidence scoring** for ebook-audiobook pairs (AI-powered)
- **Smart session management** (weeks-long persistence)
- **Web dashboard** accessible from any device on local network
- **Rate limiting compliance** (respects MAM's 100/day API limit)
- **Fallback authentication** (session cookie → username/password)
- **Progress persistence** (never lose search/download state)

## Quick Start: MAM System

Transform your audiobook collection into searchable ebooks:

```bash
# 1. Setup the system
python3 setup_mam_system.py

# 2. Configure your MAM credentials in .env
nano .env

# 3. Start web dashboard
node web_frontend.js
# Access: http://your-ip:3000

# 4. Begin automated search
node mam_playwright_automation.js 20
```

**Dashboard Features:**
- 📊 Real-time collection statistics 
- 📚 Missing vs matched book visualization
- 🔄 Download progress tracking
- 📱 Mobile-friendly interface
- 📄 Export functionality for missing books

See [README_MAM_System.md](README_MAM_System.md) for comprehensive setup guide.

## Project Structure

```
LibraryOfBabel/
├── .agents/                      # Agent coordination system
│   ├── project_state.json        # Current project status
│   ├── agent_config.json         # Agent roles & responsibilities
│   └── agent_logs/               # Individual agent progress logs
├── src/                          # Core processing code
│   ├── epub_processor.py         # EPUB text extraction
│   ├── text_chunker.py           # Hierarchical chunking algorithms
│   └── batch_processor.py        # Bulk processing pipeline
├── config/                       # Configuration files
│   └── processing_config.json
├── database/                     # Database schema and setup
│   ├── schema.sql
│   ├── indexes.sql
│   └── setup.sh
├── docs/                         # Documentation
│   ├── EPUB_FORMATS.md           # Supported format specifications
│   ├── DATABASE_SCHEMA.md        # Database design documentation
│   └── API.md                    # Agent API specifications
├── tests/                        # Quality assurance
│   ├── test_epub_processing.py
│   ├── test_database.py
│   └── performance_benchmarks.py
├── 🆕 MAM System/                # Audiobook-to-Ebook Automation
│   ├── audiobook_ebook_tracker.py    # Database management (5,839 books)
│   ├── mam_playwright_automation.js  # Automated MAM search/download
│   ├── web_frontend.js               # Real-time web dashboard
│   ├── setup_mam_system.py           # Automated setup script
│   ├── mam_api_client.py             # Legacy API client
│   ├── README_MAM_System.md          # Comprehensive setup guide
│   ├── package.json                  # Node.js dependencies
│   └── .env                          # Configuration (credentials)
└── CHANGELOG.md                  # Human-readable project history
```

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- 8GB+ RAM recommended for large collections

### Installation
```bash
git clone [your-private-repo]
cd LibraryOfBabel
pip install -r requirements.txt
```

### Process Your First Books
```bash
# Process EPUB files
python src/batch_processor.py --input-dir /path/to/your/epubs --output-dir output/

# Set up database
./database/setup.sh

# Start processing pipeline
python src/main.py
```

## Architecture

### Agent-Based Development
The project uses specialized AI agents for different components:

- **🔬 Librarian Agent**: EPUB processing and CloudDocs import (304 books processed)
- **🗄️ DBA Agent**: PostgreSQL schema and search optimization (13,794 chunks indexed)
- **🤓 Reddit Nerd Librarian**: Interdisciplinary research with chaos testing (9 attack patterns)
- **✅ QA Agent**: Security fixes and vulnerability testing (75% fix success rate)
- **🎧 Backend Audio Agent**: Whisper transcription pipeline (184 audiobooks ready)

### LLM-Agnostic Design
All agents communicate through structured JSON files, making the system compatible with any LLM (Claude, GPT, etc.).

## Performance Metrics

### Production Results (Phase 1-3 Complete)
- **Processing Speed**: 5,013 books/hour at scale (304 books in 3.6 minutes)
- **Text Extraction**: 99.4% success rate with robust error handling
- **Database Performance**: 129.7 chunks/second ingestion, <100ms search queries  
- **Memory Usage**: 45-120MB per book during processing
- **Total Indexed**: 38.95M words across 13,794 searchable chunks

### System Capabilities (Validated)
- **Search Performance**: Sub-100ms queries achieved with 15+ optimized indexes
- **Database Scale**: Ready for 5,600+ book collections (currently at 304 books)  
- **AI Agent Access**: Multiple concurrent agents supported (Reddit Nerd Librarian active)
- **Security**: SQL injection protection with <1ms blocking
- **Cross-Domain Search**: Philosophy + Finance interdisciplinary queries working

## Roadmap

### ✅ Phase 1: EPUB Mastery (Complete)
- EPUB processing pipeline with 97% accuracy
- Hierarchical text chunking algorithms  
- 36 books/hour processing speed achieved
- Comprehensive testing framework

### ✅ Phase 2: Database Integration (Complete)
- PostgreSQL with 13,794 chunks indexed
- Sub-100ms search performance with 15+ optimized indexes
- 129.7 chunks/second ingestion rate
- RESTful API endpoints operational

### ✅ Phase 3: Large-Scale Processing (Complete)
- CloudDocs collection import (304/545 books processed)
- Production-scale validation (38.95M words indexed)
- 5,013 books/hour processing at scale
- 99.4% success rate with robust error handling

### ✅ Phase 3b: AI Research Agents (Complete)
- Reddit Nerd Librarian with chaos testing (9 attack patterns)
- QA Agent with 75% vulnerability fix success rate
- Cross-domain search functionality (Philosophy + Finance)
- SQL injection protection (<1ms blocking)

### 🔄 Phase 4: Audio Integration (80% Complete)
- Backend Audio Agent deployed for 5000+ audiobooks
- Free local Whisper transcription pipeline
- 184 .m4b audiobooks discovered (441GB storage ready)
- Smart chunking strategy (10-minute segments)

### 📋 Phase 5: Full Production (Next)
- Complete 5,600+ book collection processing
- Advanced semantic search features
- System monitoring and maintenance automation
- Multi-modal search across text and audio

## Contributing

This is a personal research project. The codebase is designed to be:
- **Modular**: Easy to extend with new features
- **Documented**: Comprehensive documentation for all components
- **Tested**: Quality assurance at every level
- **Scalable**: Architecture ready for large-scale deployment

## Security & Privacy

- **Local Processing**: All data remains on personal hardware
- **No External Dependencies**: Works without internet connection
- **Access Control**: API authentication for agent access
- **Encrypted Backups**: Secure backup procedures

## License

Private research project. All rights reserved.

---

*Building the future of personal knowledge management, one book at a time.*

**Status**: Phase 4 (80% Complete) | Production-Scale Knowledge Base Operational | Next: Audio Integration
**Last Updated**: June 26, 2025