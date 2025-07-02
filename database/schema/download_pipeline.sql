-- LibraryOfBabel: Transmission + MAM Integration Schema
-- u/TransmissionHacker Implementation
-- Phase 1: Database Foundation

-- Download status enum
CREATE TYPE download_status AS ENUM (
    'initiated',        -- Request created
    'searching',        -- Searching MAM for torrent
    'found',           -- Torrent found, preparing download
    'downloading',     -- Active download in transmission
    'completed',       -- Download finished
    'seeding',         -- Seeding for compliance
    'failed',          -- Download failed
    'cancelled'        -- User cancelled
);

-- Main download requests table
CREATE TABLE download_requests (
    request_id SERIAL PRIMARY KEY,
    search_query VARCHAR(500) NOT NULL,
    book_title VARCHAR(500),
    book_author VARCHAR(300),
    
    -- MAM Integration
    mam_torrent_id VARCHAR(100),
    mam_search_results JSONB,
    torrent_url VARCHAR(1000),
    
    -- Transmission Integration  
    transmission_hash VARCHAR(64),
    transmission_id INTEGER,
    
    -- Download Status
    status download_status DEFAULT 'initiated',
    progress DECIMAL(5,2) DEFAULT 0.00,
    download_speed VARCHAR(50),
    upload_speed VARCHAR(50),
    eta VARCHAR(50),
    
    -- File Management
    file_path VARCHAR(1000),
    file_size BIGINT,
    file_format VARCHAR(20),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    searched_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    user_agent VARCHAR(200),
    ip_address INET
);

-- Download progress log for detailed tracking
CREATE TABLE download_progress_log (
    log_id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES download_requests(request_id),
    status download_status NOT NULL,
    progress DECIMAL(5,2),
    download_speed VARCHAR(50),
    upload_speed VARCHAR(50),
    peers_connected INTEGER,
    seeds_available INTEGER,
    eta VARCHAR(50),
    logged_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- MAM API rate limiting tracking
CREATE TABLE mam_api_usage (
    usage_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent VARCHAR(200)
);

-- Seeding compliance tracking
CREATE TABLE seeding_compliance (
    compliance_id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES download_requests(request_id),
    transmission_hash VARCHAR(64) NOT NULL,
    start_seeding_at TIMESTAMP DEFAULT NOW(),
    required_seed_time INTERVAL DEFAULT '336 hours', -- 2 weeks
    current_ratio DECIMAL(10,3),
    total_uploaded BIGINT DEFAULT 0,
    compliance_met BOOLEAN DEFAULT FALSE,
    checked_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_download_requests_status ON download_requests(status);
CREATE INDEX idx_download_requests_created ON download_requests(created_at);
CREATE INDEX idx_download_requests_transmission ON download_requests(transmission_hash);
CREATE INDEX idx_download_progress_request ON download_progress_log(request_id);
CREATE INDEX idx_mam_usage_window ON mam_api_usage(window_start);
CREATE INDEX idx_seeding_compliance_hash ON seeding_compliance(transmission_hash);

-- Triggers for automatic logging
CREATE OR REPLACE FUNCTION log_download_progress()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO download_progress_log (
        request_id, status, progress, download_speed, 
        upload_speed, eta, notes
    ) VALUES (
        NEW.request_id, NEW.status, NEW.progress, 
        NEW.download_speed, NEW.upload_speed, NEW.eta,
        CASE 
            WHEN OLD.status IS DISTINCT FROM NEW.status 
            THEN 'Status changed from ' || COALESCE(OLD.status::text, 'NULL') || ' to ' || NEW.status::text
            ELSE NULL
        END
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER download_progress_trigger
    AFTER UPDATE ON download_requests
    FOR EACH ROW
    EXECUTE FUNCTION log_download_progress();

-- Views for easy querying
CREATE VIEW active_downloads AS
SELECT 
    dr.request_id,
    dr.book_title,
    dr.book_author,
    dr.status,
    dr.progress,
    dr.download_speed,
    dr.eta,
    dr.created_at,
    dr.started_at
FROM download_requests dr
WHERE dr.status IN ('searching', 'found', 'downloading', 'seeding');

CREATE VIEW download_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/60) as avg_duration_minutes
FROM download_requests 
WHERE completed_at IS NOT NULL
GROUP BY status;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO libraryofbabel_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO libraryofbabel_user;

-- Insert test data
INSERT INTO download_requests (
    search_query, book_title, book_author, status
) VALUES 
    ('14 Miles AJ Gibson', '14 Miles', 'AJ Gibson', 'initiated'),
    ('1Q84 Haruki Murakami', '1Q84', 'Haruki Murakami', 'initiated');

COMMIT;