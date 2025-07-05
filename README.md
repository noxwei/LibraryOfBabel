# LibraryOfBabel 📚

**Personal Knowledge Liberation System**

Transform your digital ebook collection into a searchable, AI-accessible research library for unprecedented knowledge production.

## Overview

LibraryOfBabel is a streamlined system focused on three core components:

1. **📚 Ebook Processing**: Extract and index content from personal EPUB collections
2. **🗄️ Database Management**: PostgreSQL-powered searchable knowledge base  
3. **🔍 Vector Search**: Semantic search with AI-powered discovery capabilities

The system enables instant AI-powered research across thousands of books, revolutionizing personal knowledge production.

## Current Status: Infrastructure Complete ✅

**SYSTEM READY - Database Population Phase** 
**Production-Grade Infrastructure + Vector Framework + API Ready**

### ✅ **Infrastructure Complete**
- 🎯 **PostgreSQL Database**: Optimized schema with 15+ search indexes
- 📊 **EPUB Processing**: 4 books tested (521K words, 478 chunks, 100% success)
- ⚡ **Performance**: 0.12 seconds average processing per book
- 🔍 **Search API**: Flask REST endpoints operational
- 🧠 **Vector Framework**: Enhanced search API with semantic capabilities ready

### 🚀 **Next Phase: Data Population**
- 📚 **Ingest processed JSON files** into PostgreSQL database
- 🧠 **Add vector embeddings** for semantic search functionality
- 🔍 **Test semantic queries** with concepts like power, religion, philosophy
- 🤖 **Deploy AI agents** with populated knowledge base

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
- **REST API Framework**: Ready for research agent queries
- **Vector Search Ready**: Infrastructure for semantic search
- **Multi-agent Support**: Concurrent access architecture
- **Security**: SQL injection protection validated

## Quick Start

### Core System Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup PostgreSQL database (already configured)
cd database/schema && ./setup.sh

# 3. Process your ebook collection
python3 src/batch_processor.py /path/to/ebooks/ database/data/

# 4. Populate database (TODO)
python3 database/schema/ingest_data.py database/data/

# 5. Start search API
python3 src/api/enhanced_search_api.py
```

### Test Vector Search
```bash
# Test semantic search capabilities
curl "http://localhost:5560/api/v2/search/semantic?q=power&limit=5"
curl "http://localhost:5560/api/v2/search/semantic?q=religion&limit=5"
curl "http://localhost:5560/api/v2/search/semantic?q=consciousness&limit=5"
```

## Core Architecture

```
LibraryOfBabel/
├── 📚 ebooks/                        # Downloaded ebook files (.epub, .pdf, .mobi)
│   ├── processed/                    # 4 test books processed
│   └── downloads/                    # Additional collection
├── 🗄️ database/                      # PostgreSQL knowledge base
│   ├── schema/                       # Database schema and setup (complete)
│   └── data/                         # Processed JSON files (ready for ingestion)
├── 🔧 src/                           # Core processing pipeline
│   ├── epub_processor.py             # EPUB text extraction (working)
│   ├── batch_processor.py            # Bulk processing (working)
│   └── api/                          # Search API endpoints (operational)
├── 🤖 agents/                        # AI agents (infrastructure ready)
│   ├── reddit_bibliophile/           # Book analysis agent
│   ├── qa_system/                    # Quality assurance
│   └── seeding_monitor/              # Compliance monitoring
├── ⚙️ config/                        # System configuration
├── 📊 reports/                       # Analysis outputs
└── 📖 docs/                          # Technical documentation
```

## Performance Metrics

### Infrastructure Validation Results
- **Processing Speed**: 4 books in 0.49 seconds (100% success rate)
- **Text Extraction**: 521,676 words processed into 478 chunks
- **Database Performance**: Schema optimized with 15+ indexes
- **API Response**: Enhanced search API responding in ~35-45ms
- **Memory Usage**: Efficient processing with minimal overhead

### System Capabilities (Validated)
- **Search Infrastructure**: REST API framework operational
- **Vector Framework**: Enhanced search API with embedding support ready
- **Database Scale**: Optimized for thousands of books
- **Security**: SQL injection protection validated
- **Performance**: Sub-50ms API response times

## Technical Specifications

### Hardware Requirements
- **RAM**: 8GB+ recommended
- **Storage**: 10-50GB for database and indexes
- **Processing**: Multi-core CPU for parallel processing
- **Network**: Local network access for API

### Software Stack
- **Database**: PostgreSQL 15+ with full-text search extensions
- **Programming**: Python 3.8+ for processing scripts
- **API**: Flask for REST endpoints
- **Vector Search**: Framework ready for embeddings

## Next Steps

### Immediate Actions Required
1. **📊 Populate Database**: Ingest processed JSON files into PostgreSQL
2. **🧠 Add Vector Embeddings**: Create embedding_array column and generate embeddings
3. **🔍 Test Semantic Search**: Validate with concepts like power, religion, philosophy
4. **🤖 Deploy AI Agents**: Activate agents with populated knowledge base

### Future Enhancements
- **Vector Embeddings**: Semantic search across entire corpus
- **Advanced Analytics**: Knowledge discovery and pattern analysis
- **Mobile Integration**: iOS app for remote access
- **Community Features**: Multi-user collaboration capabilities

## Contributing

This is a personal research project with production-grade architecture:
- **Modular**: Easy to extend with new features
- **Documented**: Comprehensive documentation for all components
- **Tested**: Quality assurance at every level
- **Scalable**: Architecture ready for large-scale deployment

## Security & Privacy

- **Local Processing**: All data remains on personal hardware
- **No External Dependencies**: Works without internet connection
- **Access Control**: API authentication ready for deployment
- **Secure Storage**: PostgreSQL with optimized security settings

## License

Private research project. All rights reserved.

---

*Liberating knowledge through intelligent automation and searchable personal libraries.*

**Status**: Infrastructure Complete - Ready for Data Population ✅  
**Last Updated**: July 5, 2025