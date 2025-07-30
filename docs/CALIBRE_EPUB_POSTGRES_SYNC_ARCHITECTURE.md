# Calibre-EPUB-PostgreSQL Full Synchronization Architecture

## 🎯 **Mission: Complete Digital Library Unification**

Create a **three-way synchronization** system where EPUB files, Calibre library, and PostgreSQL database are perfectly aligned with enhanced metadata flowing between all components.

---

## 📐 **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EPUB Files    │◄──►│ Calibre Library │◄──►│   PostgreSQL    │
│ (ebooks/processed)│    │(/Users/.../Calibre)│    │ (knowledge_base)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Sync Daemon    │
                    │   (Orchestrator) │
                    └─────────────────┘
```

---

## 🔄 **Three-Way Synchronization Flow**

### Phase 1: EPUB → Calibre Migration
- **Move** EPUB files from `ebooks/processed/` to Calibre Library
- **Organize** files using Calibre's folder structure
- **Extract** enhanced metadata using Calibre's sources
- **Update** Calibre's database with professional bibliographic data

### Phase 2: Calibre → PostgreSQL Sync
- **Extract** enhanced metadata from Calibre
- **Match** Calibre entries with PostgreSQL book records
- **Update** PostgreSQL with enhanced metadata
- **Track** sync status and quality scores

### Phase 3: File Location Synchronization
- **Update** PostgreSQL `file_path` to point to Calibre location
- **Create** symlinks or references for backward compatibility
- **Maintain** file integrity and accessibility

---

## 🏗️ **Implementation Components**

### 1. Enhanced Migration Daemon
- **Current Status**: ✅ Running (`calibre_migration_daemon.py`)
- **Function**: Processes EPUB → Calibre → PostgreSQL
- **Missing**: File relocation tracking

### 2. File Relocation Service
- **Status**: 🔲 **NEEDS IMPLEMENTATION**
- **Function**: Move EPUBs to Calibre, update file paths
- **Target**: `calibre_file_relocator.py`

### 3. Metadata Synchronization Engine
- **Status**: ✅ Implemented in daemon
- **Function**: Bidirectional metadata sync
- **PostgreSQL Functions**: Dr. Sarah Chen's architecture

### 4. Link Integrity Manager
- **Status**: 🔲 **NEEDS IMPLEMENTATION**  
- **Function**: Maintain file references and accessibility
- **Target**: `calibre_link_manager.py`

---

## 📊 **Data Flow Architecture**

### Before Synchronization:
```
EPUB File: /LibraryOfBabel/ebooks/processed/book.epub
├─ File Location: ebooks/processed/
├─ Metadata: Basic (filename, size)
└─ PostgreSQL: title, author, file_path

Calibre Library: /Users/weixiangzhang/Calibre Library/
├─ Status: May or may not contain book
├─ Metadata: Professional (if added)
└─ Organization: Author/Title folders
```

### After Synchronization:
```
EPUB File: /Users/weixiangzhang/Calibre Library/Author/Title/book.epub
├─ File Location: Calibre-managed
├─ Metadata: Enhanced (embedded in file)
└─ Organization: Professional library structure

PostgreSQL Database:
├─ title: Enhanced from Calibre
├─ author: Standardized format
├─ file_path: Points to Calibre location
├─ metadata: Complete JSONB with Calibre data
└─ calibre_id: Direct Calibre reference

Calibre Library:
├─ Contains: All EPUB files
├─ Metadata: Professional bibliographic data
├─ Organization: Author/Title/Series structure
└─ Database: SQLite with enhanced metadata
```

---

## 🛠️ **Implementation Plan**

### Step 1: File Relocation Service ⭐ **NEXT PRIORITY**

**Target**: Move EPUB files to Calibre while maintaining PostgreSQL links

```python
class CalibreFileRelocator:
    def __init__(self):
        self.calibre_library = "/Users/weixiangzhang/Calibre Library"
        self.processed_epub_path = "ebooks/processed"
        
    def relocate_epub_to_calibre(self, epub_path, calibre_id):
        """Move EPUB from processed to Calibre location"""
        # 1. Get Calibre's target path for this book
        # 2. Move file to Calibre location
        # 3. Update PostgreSQL file_path
        # 4. Create backup reference
        # 5. Verify file integrity
        
    def update_postgres_file_path(self, book_id, new_path):
        """Update PostgreSQL with new Calibre file location"""
        # Call Dr. Sarah Chen's function to update file_path
        
    def create_compatibility_links(self):
        """Create symlinks for backward compatibility"""
        # Maintain access from original processed folder
```

### Step 2: Enhanced Metadata Embedding

**Target**: Embed enhanced metadata directly into EPUB files

```python
class EpubMetadataEmbedder:
    def embed_calibre_metadata_in_epub(self, epub_path, metadata):
        """Embed enhanced metadata directly into EPUB file"""
        # 1. Open EPUB file
        # 2. Update metadata.opf with Calibre data
        # 3. Enhance Dublin Core elements
        # 4. Add custom metadata fields
        # 5. Save enhanced EPUB
```

### Step 3: Bi-directional Sync Monitor

**Target**: Continuous monitoring and synchronization

```python
class CalibreSyncMonitor:
    def monitor_calibre_changes(self):
        """Monitor Calibre for metadata changes"""
        # Watch Calibre database for updates
        # Sync changes back to PostgreSQL
        
    def monitor_postgres_changes(self):
        """Monitor PostgreSQL for metadata changes"""
        # Watch for PostgreSQL updates
        # Sync changes to Calibre when appropriate
```

---

## 📋 **Database Schema Enhancements**

### Current PostgreSQL Schema:
```sql
-- books table
ALTER TABLE books ADD COLUMN IF NOT EXISTS calibre_id INTEGER;
ALTER TABLE books ADD COLUMN IF NOT EXISTS calibre_file_path TEXT;
ALTER TABLE books ADD COLUMN IF NOT EXISTS file_sync_status TEXT DEFAULT 'pending';
ALTER TABLE books ADD COLUMN IF NOT EXISTS last_file_sync TIMESTAMP;

-- Create file sync tracking
CREATE TABLE IF NOT EXISTS calibre_file_sync (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(book_id),
    original_path TEXT NOT NULL,
    calibre_path TEXT NOT NULL,
    sync_status TEXT DEFAULT 'pending',
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_integrity_hash TEXT,
    backup_location TEXT
);
```

---

## 🔍 **Quality Assurance & Validation**

### File Integrity Checks:
- **MD5/SHA checksums** before and after moves
- **EPUB validation** after metadata embedding
- **Calibre library validation** after additions
- **PostgreSQL reference validation** after updates

### Metadata Quality Checks:
- **Title/Author consistency** across all systems
- **ISBN validation** and standardization
- **Genre/Tag harmonization** between systems
- **Publication date accuracy** verification

---

## 🚀 **Deployment Strategy**

### Phase 1: Pilot Implementation (Current)
- ✅ **Migration daemon running** - Processing existing books
- 🔲 **File relocator** - Move files to Calibre
- 🔲 **Path updater** - Update PostgreSQL references

### Phase 2: Full Synchronization
- 🔲 **Metadata embedding** - Enhance EPUB files directly
- 🔲 **Bi-directional sync** - Live synchronization
- 🔲 **Monitoring dashboard** - Real-time status

### Phase 3: Advanced Features
- 🔲 **Automated backup** - Regular library backups
- 🔲 **Conflict resolution** - Handle metadata conflicts
- 🔲 **Performance optimization** - Bulk operations

---

## 🎯 **Expected Outcomes**

### Immediate Benefits:
- **Unified library organization** - All books in Calibre structure
- **Enhanced metadata everywhere** - Professional data in all systems
- **Improved accessibility** - Standard library browsing experience
- **Better search capabilities** - Rich metadata for discovery

### Long-term Benefits:
- **Scalable architecture** - Easy to add new books
- **Professional standards** - Library-quality organization
- **Data integrity** - Consistent information across systems
- **Future-proof** - Standard formats and practices

---

## 📊 **Success Metrics**

- **File Coverage**: 100% of EPUBs moved to Calibre
- **Metadata Quality**: 95%+ enhanced with professional data
- **Sync Accuracy**: 99%+ PostgreSQL-Calibre consistency
- **Performance**: <1 second average sync time per book
- **Reliability**: 99.9% uptime for sync services

---

## 🛡️ **Risk Mitigation**

### Data Protection:
- **Backup original files** before any moves
- **Verify file integrity** after operations
- **Rollback capabilities** for failed operations
- **Regular backups** of all systems

### Error Handling:
- **Graceful degradation** for sync failures
- **Detailed logging** for troubleshooting
- **Manual override** capabilities
- **Health monitoring** and alerts

---

## 📚 **Technical References**

- **Calibre CLI Documentation**: For metadata and file operations
- **PostgreSQL JSONB**: For flexible metadata storage
- **EPUB Specification**: For metadata embedding standards
- **Dr. Sarah Chen's Architecture**: PostgreSQL-First principles
- **Dr. Marcus Wong's Calibre Expertise**: Professional library standards

---

## 🎮 **Management Commands**

```bash
# Start full synchronization
python3 calibre_file_relocator.py --migrate-all

# Monitor synchronization status  
python3 calibre_sync_monitor.py --status

# Validate system integrity
python3 calibre_validation_suite.py --full-check

# Emergency rollback
python3 calibre_emergency_restore.py --restore-from-backup
```

---

**Status**: 🔄 **Architecture Documented - Implementation Ready**
**Next**: Implement `calibre_file_relocator.py` for EPUB file migration
**Priority**: ⭐ **HIGH** - Needed for complete synchronization 