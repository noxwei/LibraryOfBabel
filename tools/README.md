# LibraryOfBabel Tools & Utilities

## 🛠️ **Organized Tool Collection**

This directory contains all utility scripts, analysis tools, and maintenance utilities for the LibraryOfBabel project, organized by function.

---

## **📂 DIRECTORY STRUCTURE**

### **🔧 Utilities** (`/tools/utilities/`)
Core utility scripts for common operations:

- **`simple_search.py`** - Basic search functionality testing
- **`mla_citation_verifier.py`** - MLA citation format validation
- **`word_counter.py`** - Text analysis and word counting
- **`reconstruct_book.py`** - Rebuild books from chunks
- **`process_new_books.py`** - Batch process new EPUB files
- **`process_reading_completion.py`** - Track reading progress
- **`mass_download_orchestrator.py`** - Coordinate bulk downloads

### **📊 Analysis** (`/tools/analysis/`)
Data analysis and visualization tools:

- **`knowledge_graph_explorer.py`** - Interactive knowledge graph navigation
- **`library_stats.py`** - Comprehensive library statistics and analytics

### **🧹 Maintenance** (`/tools/maintenance/`)
System maintenance and repair utilities:

- **`cyberpunk_data_fixer.py`** - Data corruption repair and cleanup
- **`safe_folder_cleanup.py`** - Secure file organization and cleanup

### **🧪 Testing** (`/tools/testing/`)
Testing and validation utilities:

- **`librarian_api_tester.py`** - API endpoint testing and validation
- **`qa_librarian_phd.py`** - PhD-level quality assurance testing

---

## **🚀 QUICK START GUIDE**

### **Common Operations**

#### **Search & Discovery**
```bash
# Basic search testing
python tools/utilities/simple_search.py "your query"

# Knowledge graph exploration
python tools/analysis/knowledge_graph_explorer.py

# Library statistics
python tools/analysis/library_stats.py
```

#### **Content Management**
```bash
# Process new books
python tools/utilities/process_new_books.py /path/to/epub/files

# Mass download coordination
python tools/utilities/mass_download_orchestrator.py

# Reconstruct book from chunks
python tools/utilities/reconstruct_book.py --book-id 123
```

#### **Quality Assurance**
```bash
# API testing
python tools/testing/librarian_api_tester.py

# PhD-level QA
python tools/testing/qa_librarian_phd.py

# Citation verification
python tools/utilities/mla_citation_verifier.py
```

#### **System Maintenance**
```bash
# Data corruption repair
python tools/maintenance/cyberpunk_data_fixer.py

# Safe folder cleanup
python tools/maintenance/safe_folder_cleanup.py
```

---

## **📋 TOOL DESCRIPTIONS**

### **🔧 Core Utilities**

#### **Simple Search** (`utilities/simple_search.py`)
- **Purpose**: Quick search functionality testing
- **Usage**: Test search algorithms and response times
- **Dependencies**: Database connection, search API

#### **MLA Citation Verifier** (`utilities/mla_citation_verifier.py`)
- **Purpose**: Validate academic citation formats
- **Usage**: Ensure proper MLA formatting for research
- **Output**: Citation format validation report

#### **Word Counter** (`utilities/word_counter.py`)
- **Purpose**: Comprehensive text analysis
- **Features**: Word count, reading time estimation, complexity analysis
- **Usage**: Analyze content statistics

#### **Book Reconstructor** (`utilities/reconstruct_book.py`)
- **Purpose**: Rebuild complete books from database chunks
- **Usage**: Export books for offline reading or backup
- **Output**: Complete EPUB or text file

#### **New Book Processor** (`utilities/process_new_books.py`)
- **Purpose**: Batch process newly added EPUB files
- **Features**: Automatic chunking, metadata extraction, database insertion
- **Usage**: Regular maintenance of book collection

#### **Reading Completion Tracker** (`utilities/process_reading_completion.py`)
- **Purpose**: Monitor and track reading progress
- **Features**: Progress analytics, reading recommendations
- **Output**: Reading progress reports

#### **Mass Download Orchestrator** (`utilities/mass_download_orchestrator.py`)
- **Purpose**: Coordinate large-scale book downloads
- **Features**: Queue management, parallel downloads, progress tracking
- **Integration**: Works with Anna's Archive API

### **📊 Analysis Tools**

#### **Knowledge Graph Explorer** (`analysis/knowledge_graph_explorer.py`)
- **Purpose**: Interactive exploration of concept relationships
- **Features**: Graph visualization, relationship mapping, concept clustering
- **Output**: Interactive knowledge graphs, relationship diagrams
- **Dependencies**: NetworkX, matplotlib, graph database

#### **Library Statistics** (`analysis/library_stats.py`)
- **Purpose**: Comprehensive library analytics
- **Features**: 
  - Collection size and growth metrics
  - Author and genre distribution
  - Reading pattern analysis
  - Content complexity analysis
- **Output**: Statistical reports, trend analysis, visualizations

### **🧹 Maintenance Tools**

#### **Cyberpunk Data Fixer** (`maintenance/cyberpunk_data_fixer.py`)
- **Purpose**: Repair data corruption and inconsistencies
- **Features**: 
  - Database integrity checks
  - Corrupted chunk repair
  - Metadata consistency validation
  - Automated data recovery
- **Usage**: Run when data issues detected
- **Safety**: Creates backups before repairs

#### **Safe Folder Cleanup** (`maintenance/safe_folder_cleanup.py`)
- **Purpose**: Organize and clean project directories
- **Features**:
  - Safe file movement and organization
  - Duplicate detection and removal
  - Directory structure optimization
  - Backup creation before changes
- **Usage**: Regular project maintenance

### **🧪 Testing Tools**

#### **Librarian API Tester** (`testing/librarian_api_tester.py`)
- **Purpose**: Comprehensive API endpoint testing
- **Features**:
  - Endpoint availability checking
  - Response time benchmarking
  - Authentication testing
  - Error handling validation
- **Output**: API health reports, performance metrics

#### **QA Librarian PhD** (`testing/qa_librarian_phd.py`)
- **Purpose**: PhD-level quality assurance testing
- **Features**:
  - Advanced academic query testing
  - Research methodology validation
  - Citation accuracy verification
  - Content quality assessment
- **Usage**: High-level quality validation

---

## **⚙️ CONFIGURATION**

### **Environment Setup**
```bash
# Set environment variables
export DB_HOST=localhost
export DB_NAME=knowledge_base
export DB_USER=your_username
export API_KEY=your_api_key

# Install dependencies
pip install -r requirements.txt
```

### **Common Configuration Files**
- **Database connection**: Uses standard DB_* environment variables
- **API endpoints**: Configurable via tool-specific config files
- **Output directories**: Most tools use `./outputs/` or `./reports/`

---

## **🔧 DEVELOPMENT GUIDELINES**

### **Adding New Tools**
1. **Choose appropriate category** (utilities/analysis/maintenance/testing)
2. **Follow naming convention**: `descriptive_tool_name.py`
3. **Include comprehensive docstring** with purpose and usage
4. **Add error handling** and logging
5. **Update this README** with tool description

### **Tool Structure Template**
```python
#!/usr/bin/env python3
"""
Tool Name - Brief Description
============================

Detailed description of purpose and functionality.
"""

import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolName:
    """Tool class with clear purpose and methods"""
    
    def __init__(self, config=None):
        self.config = config or {}
        logger.info("Tool initialized")
    
    def main_function(self):
        """Primary tool functionality"""
        pass

def main():
    """Main entry point"""
    tool = ToolName()
    result = tool.main_function()
    return result

if __name__ == "__main__":
    main()
```

### **Best Practices**
- **Error handling**: Always include try/catch blocks
- **Logging**: Use structured logging for debugging
- **Configuration**: Support environment variables and config files
- **Documentation**: Include usage examples and expected outputs
- **Testing**: Create basic tests for core functionality

---

## **🚨 DEPRECATION NOTICES**

### **Moved Tools**
The following tools have been moved from the root directory:
- `simple_search.py` → `tools/utilities/simple_search.py`
- `knowledge_graph_explorer.py` → `tools/analysis/knowledge_graph_explorer.py`
- All other utilities moved to appropriate subdirectories

### **Legacy Files**
Some legacy scripts may still exist in the root directory. These will be gradually moved or deprecated.

---

## **📊 TOOL USAGE STATISTICS**

### **Most Used Tools**
1. **Library Stats** - Daily analytics and reporting
2. **API Tester** - Continuous integration testing  
3. **Knowledge Graph Explorer** - Research and discovery
4. **New Book Processor** - Content management

### **Maintenance Schedule**
- **Daily**: Library stats, API testing
- **Weekly**: Data integrity checks, folder cleanup
- **Monthly**: Comprehensive QA, citation verification
- **As needed**: Data repair, book reconstruction

---

## **🔗 INTEGRATION**

### **With Main System**
- **Database**: All tools use standard database connection
- **APIs**: Tools test and interact with consolidated API
- **Agents**: Some tools are used by AI agents for automation

### **External Dependencies**
- **Anna's Archive**: Mass download orchestrator
- **Transmission**: Download management tools
- **PostgreSQL**: Database analysis tools
- **Network Services**: API testing tools

---

**Last Updated**: 2025-07-06
**Tool Count**: 12 organized tools
**Categories**: 4 functional categories
**Maintainer**: Development Team + Tool Maintenance Agent