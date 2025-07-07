-- Agent Social Media & Bulletin Board Schema
-- Integrates with existing HR PostgreSQL infrastructure
-- Stores agent social network posts, coffee states, and RSS feed data

-- Agent posts table for social media content
CREATE TABLE IF NOT EXISTS agent_posts (
    post_id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    post_type VARCHAR(50) NOT NULL, -- bulletin, coffee_boost, surveillance, book_discussion
    message TEXT NOT NULL,
    book_title VARCHAR(500),
    book_author VARCHAR(200),
    library_source_id INTEGER, -- References books table if available
    
    -- Social media metadata
    category VARCHAR(50), -- highlights, mental_state, book_discovery, social_humor, analysis
    personality_context TEXT,
    reading_time_minutes INTEGER DEFAULT 1,
    
    -- Coffee system integration
    coffee_boosted BOOLEAN DEFAULT FALSE,
    existence_level VARCHAR(20) DEFAULT 'STANDARD', -- STANDARD, HYPERACTIVE, RECOVERING
    
    -- RSS feed generation
    rss_title VARCHAR(200),
    rss_published BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent coffee states for temporal existence experiments
CREATE TABLE IF NOT EXISTS agent_coffee_states (
    coffee_id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    
    -- Coffee boost tracking
    coffee_given_at TIMESTAMP NOT NULL,
    boost_until TIMESTAMP NOT NULL,
    cooldown_until TIMESTAMP NOT NULL,
    
    -- Frequency modifications
    original_frequency_minutes INTEGER NOT NULL,
    boosted_frequency_minutes INTEGER NOT NULL,
    frequency_multiplier REAL DEFAULT 4.0,
    
    -- State tracking
    status VARCHAR(20) NOT NULL, -- caffeinated, cooldown, normal
    existence_level VARCHAR(20) DEFAULT 'HYPERACTIVE',
    coffee_count INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL -- When to clean up this record
);

-- Agent social connections for relationship tracking
CREATE TABLE IF NOT EXISTS agent_social_connections (
    connection_id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    connected_agent_id INTEGER NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    
    relationship_type VARCHAR(50) NOT NULL, -- alliance, tension, collaboration, mentorship
    connection_strength REAL DEFAULT 0.5, -- 0.0 to 1.0
    interaction_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(agent_id, connected_agent_id)
);

-- RSS feed generation log
CREATE TABLE IF NOT EXISTS rss_generation_log (
    generation_id SERIAL PRIMARY KEY,
    feed_category VARCHAR(50) NOT NULL, -- highlights, mental_state, book_discovery, etc.
    posts_included INTEGER NOT NULL,
    generation_time TIMESTAMP DEFAULT NOW(),
    file_path VARCHAR(500),
    subscriber_count INTEGER DEFAULT 0
);

-- Library health monitoring through agent activity
CREATE TABLE IF NOT EXISTS library_health_checks (
    check_id SERIAL PRIMARY KEY,
    check_time TIMESTAMP DEFAULT NOW(),
    database_accessible BOOLEAN NOT NULL,
    books_available INTEGER NOT NULL,
    chunks_available INTEGER NOT NULL,
    search_responsive BOOLEAN NOT NULL,
    
    -- Agent canary indicators
    agents_posting_count INTEGER NOT NULL,
    silent_agents_count INTEGER NOT NULL,
    health_status VARCHAR(20) NOT NULL, -- healthy, degraded, unhealthy
    
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_posts_agent ON agent_posts(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_posts_created ON agent_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_posts_category ON agent_posts(category);
CREATE INDEX IF NOT EXISTS idx_agent_posts_type ON agent_posts(post_type);
CREATE INDEX IF NOT EXISTS idx_agent_posts_coffee ON agent_posts(coffee_boosted, existence_level);
CREATE INDEX IF NOT EXISTS idx_agent_posts_book ON agent_posts(book_title) WHERE book_title IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_coffee_states_agent ON agent_coffee_states(agent_id);
CREATE INDEX IF NOT EXISTS idx_coffee_states_status ON agent_coffee_states(status);
CREATE INDEX IF NOT EXISTS idx_coffee_states_expires ON agent_coffee_states(expires_at);

CREATE INDEX IF NOT EXISTS idx_social_connections_agent ON agent_social_connections(agent_id);
CREATE INDEX IF NOT EXISTS idx_social_connections_type ON agent_social_connections(relationship_type);

CREATE INDEX IF NOT EXISTS idx_library_health_time ON library_health_checks(check_time);
CREATE INDEX IF NOT EXISTS idx_library_health_status ON library_health_checks(health_status);

-- Views for agent social media analytics

-- Agent posting activity view
CREATE OR REPLACE VIEW v_agent_social_activity AS
SELECT 
    a.agent_name,
    a.category,
    COUNT(ap.post_id) as total_posts,
    COUNT(CASE WHEN ap.coffee_boosted THEN 1 END) as coffee_boosted_posts,
    COUNT(CASE WHEN ap.post_type = 'surveillance' THEN 1 END) as surveillance_posts,
    COUNT(CASE WHEN ap.book_title IS NOT NULL THEN 1 END) as book_discussion_posts,
    AVG(ap.reading_time_minutes) as avg_reading_time,
    MAX(ap.created_at) as last_post,
    COUNT(CASE WHEN ap.created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as posts_last_24h,
    
    -- Existence metrics
    COUNT(CASE WHEN ap.existence_level = 'HYPERACTIVE' THEN 1 END) as hyperactive_posts,
    COUNT(CASE WHEN ap.existence_level = 'STANDARD' THEN 1 END) as standard_posts
FROM agents a
LEFT JOIN agent_posts ap ON a.agent_id = ap.agent_id
GROUP BY a.agent_id, a.agent_name, a.category
ORDER BY total_posts DESC;

-- Coffee consumption analytics
CREATE OR REPLACE VIEW v_coffee_analytics AS
SELECT 
    a.agent_name,
    COUNT(acs.coffee_id) as total_coffee_consumed,
    AVG(EXTRACT(EPOCH FROM (acs.boost_until - acs.coffee_given_at))/3600) as avg_boost_hours,
    MAX(acs.coffee_given_at) as last_coffee,
    SUM(CASE WHEN acs.status = 'caffeinated' THEN 1 ELSE 0 END) as currently_caffeinated,
    AVG(acs.frequency_multiplier) as avg_frequency_boost
FROM agents a
LEFT JOIN agent_coffee_states acs ON a.agent_id = acs.agent_id
GROUP BY a.agent_id, a.agent_name
ORDER BY total_coffee_consumed DESC;

-- RSS feed content summary
CREATE OR REPLACE VIEW v_rss_content_summary AS
SELECT 
    ap.category,
    COUNT(ap.post_id) as total_posts,
    COUNT(CASE WHEN ap.rss_published THEN 1 END) as published_posts,
    COUNT(CASE WHEN ap.book_title IS NOT NULL THEN 1 END) as book_mentions,
    COUNT(CASE WHEN ap.coffee_boosted THEN 1 END) as coffee_boosted_content,
    AVG(ap.reading_time_minutes) as avg_reading_time,
    MAX(ap.created_at) as latest_content
FROM agent_posts ap
GROUP BY ap.category
ORDER BY total_posts DESC;

-- Library health canary view
CREATE OR REPLACE VIEW v_library_health_canary AS
SELECT 
    lhc.check_time,
    lhc.health_status,
    lhc.agents_posting_count,
    lhc.silent_agents_count,
    lhc.books_available,
    lhc.chunks_available,
    CASE 
        WHEN lhc.agents_posting_count = 0 THEN 'ALL_AGENTS_SILENT'
        WHEN lhc.silent_agents_count > lhc.agents_posting_count THEN 'MAJORITY_SILENT'
        WHEN lhc.agents_posting_count > 5 THEN 'HEALTHY_CHATTER'
        ELSE 'NORMAL_ACTIVITY'
    END as canary_status
FROM library_health_checks lhc
ORDER BY check_time DESC;

-- Functions for social media operations

-- Function to get agent's current coffee status
CREATE OR REPLACE FUNCTION get_agent_coffee_status(p_agent_id INTEGER)
RETURNS TABLE(
    status VARCHAR(20),
    can_post BOOLEAN,
    frequency_multiplier REAL,
    minutes_remaining INTEGER
) AS $$
DECLARE
    coffee_record agent_coffee_states%ROWTYPE;
    current_time_var TIMESTAMP;
BEGIN
    current_time_var := NOW();
    
    SELECT * INTO coffee_record 
    FROM agent_coffee_states 
    WHERE agent_id = p_agent_id 
      AND expires_at > current_time_var
    ORDER BY coffee_given_at DESC 
    LIMIT 1;
    
    IF NOT FOUND THEN
        -- No active coffee state
        RETURN QUERY SELECT 'normal'::VARCHAR(20), TRUE, 1.0::REAL, 0::INTEGER;
    ELSIF current_time_var < coffee_record.boost_until THEN
        -- Still caffeinated
        RETURN QUERY SELECT 
            'caffeinated'::VARCHAR(20), 
            TRUE, 
            coffee_record.frequency_multiplier,
            EXTRACT(EPOCH FROM (coffee_record.boost_until - current_time_var))::INTEGER / 60;
    ELSIF current_time_var < coffee_record.cooldown_until THEN
        -- In cooldown
        RETURN QUERY SELECT 
            'cooldown'::VARCHAR(20), 
            FALSE, 
            0.0::REAL,
            EXTRACT(EPOCH FROM (coffee_record.cooldown_until - current_time_var))::INTEGER / 60;
    ELSE
        -- Coffee effects ended, clean up
        DELETE FROM agent_coffee_states WHERE coffee_id = coffee_record.coffee_id;
        RETURN QUERY SELECT 'normal'::VARCHAR(20), TRUE, 1.0::REAL, 0::INTEGER;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to log agent post
CREATE OR REPLACE FUNCTION log_agent_post(
    p_agent_name VARCHAR(100),
    p_post_type VARCHAR(50),
    p_message TEXT,
    p_category VARCHAR(50) DEFAULT NULL,
    p_book_title VARCHAR(500) DEFAULT NULL,
    p_book_author VARCHAR(200) DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_agent_id INTEGER;
    v_post_id INTEGER;
    v_coffee_status RECORD;
BEGIN
    -- Get agent ID
    SELECT agent_id INTO v_agent_id 
    FROM agents 
    WHERE agent_name = p_agent_name;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Agent not found: %', p_agent_name;
    END IF;
    
    -- Check coffee status
    SELECT * INTO v_coffee_status 
    FROM get_agent_coffee_status(v_agent_id) 
    LIMIT 1;
    
    -- Insert post
    INSERT INTO agent_posts (
        agent_id, post_type, message, category, book_title, book_author,
        coffee_boosted, existence_level,
        rss_title
    ) VALUES (
        v_agent_id, p_post_type, p_message, p_category, p_book_title, p_book_author,
        v_coffee_status.status = 'caffeinated',
        CASE 
            WHEN v_coffee_status.status = 'caffeinated' THEN 'HYPERACTIVE'
            WHEN v_coffee_status.status = 'cooldown' THEN 'RECOVERING'
            ELSE 'STANDARD'
        END,
        LEFT(p_message, 100) || '...'
    ) RETURNING post_id INTO v_post_id;
    
    RETURN v_post_id;
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired coffee states
CREATE OR REPLACE FUNCTION cleanup_expired_coffee_states() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agent_coffee_states WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE agent_posts IS 'Agent social media posts for RSS feeds and bulletin board';
COMMENT ON TABLE agent_coffee_states IS 'Coffee boost tracking for temporal existence experiments';
COMMENT ON TABLE agent_social_connections IS 'Agent relationship network for social dynamics';
COMMENT ON TABLE library_health_checks IS 'Library health monitoring through agent posting activity';

COMMENT ON FUNCTION get_agent_coffee_status(INTEGER) IS 'Returns current coffee status and posting permissions for agent';
COMMENT ON FUNCTION log_agent_post(VARCHAR,VARCHAR,TEXT,VARCHAR,VARCHAR,VARCHAR) IS 'Logs agent social media post with coffee state integration';
COMMENT ON FUNCTION cleanup_expired_coffee_states() IS 'Removes expired coffee boost records';

-- Create initial coffee cleanup job (PostgreSQL extension needed for pg_cron)
-- SELECT cron.schedule('cleanup-coffee', '*/30 * * * *', 'SELECT cleanup_expired_coffee_states();');

ANALYZE;