# Database Setup Guide

## PostgreSQL Installation and Configuration

### Installation on macOS

```bash
# Install PostgreSQL using Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Add PostgreSQL to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Create database user and initial database
createdb knowledge_base
psql knowledge_base
```

### Initial Database Setup

1. Install PostgreSQL (see above)
2. Run the schema initialization script:
   ```bash
   psql knowledge_base < database/schema/01_init_schema.sql
   ```
3. Run the indexes optimization script:
   ```bash
   psql knowledge_base < database/schema/02_indexes.sql
   ```
4. Configure full-text search:
   ```bash
   psql knowledge_base < database/schema/03_fulltext_search.sql
   ```

### Database Configuration

Recommended PostgreSQL configuration changes in `postgresql.conf`:

```
# Memory settings (adjust based on available RAM - system has 24GB)
shared_buffers = 4GB
effective_cache_size = 16GB
maintenance_work_mem = 1GB
work_mem = 256MB

# Query performance
random_page_cost = 1.1
effective_io_concurrency = 200

# Full-text search optimization
default_text_search_config = 'english'
```

### Performance Monitoring

Use the provided monitoring queries in `database/monitoring/` to track:
- Query performance
- Index usage
- Database size growth
- Connection statistics

### Backup Strategy

```bash
# Daily backup (automated via cron)
pg_dump knowledge_base > backups/knowledge_base_$(date +%Y%m%d).sql

# Incremental backup using WAL archiving (for production)
```