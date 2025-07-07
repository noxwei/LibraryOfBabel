-- LibraryOfBabel HR Management System Schema
-- PostgreSQL tables for Linda Zhang's workforce analytics
-- Respecting the future: Scalable, normalized, and performance-optimized

-- Drop existing HR tables if they exist
DROP TABLE IF EXISTS agent_interactions CASCADE;
DROP TABLE IF EXISTS user_requests CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS hr_daily_reports CASCADE;

-- Agents table for normalized agent data
CREATE TABLE agents (
    agent_id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    description TEXT,
    capabilities TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    last_modified TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' -- active, inactive, deprecated
);

-- User requests table for tracking user interactions
CREATE TABLE user_requests (
    request_id SERIAL PRIMARY KEY,
    request_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    user_session VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    complexity_level INTEGER DEFAULT 1, -- 1-5 scale
    estimated_duration_ms INTEGER,
    actual_duration_ms INTEGER,
    satisfaction_score INTEGER -- 1-5 scale
);

-- Agent interactions table for performance tracking
CREATE TABLE agent_interactions (
    interaction_id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    request_id INTEGER REFERENCES user_requests(request_id),
    action VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms REAL,
    details TEXT,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    context JSONB, -- Flexible context data
    performance_score REAL -- 0.0-1.0 calculated score
);

-- HR daily reports table for Linda's assessments
CREATE TABLE hr_daily_reports (
    report_id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_agents INTEGER,
    total_requests INTEGER,
    total_interactions INTEGER,
    overall_success_rate REAL,
    average_response_time REAL,
    grade CHAR(1), -- A, B, C, D, F
    cultural_assessment VARCHAR(50), -- 勤奋工作, 需要改进, etc.
    linda_self_assessment TEXT,
    recommendations TEXT[],
    problem_agents JSONB,
    report_data JSONB, -- Full report backup
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX idx_agents_name ON agents(agent_name);
CREATE INDEX idx_agents_category ON agents(category);
CREATE INDEX idx_agents_status ON agents(status);

CREATE INDEX idx_user_requests_type ON user_requests(request_type);
CREATE INDEX idx_user_requests_timestamp ON user_requests(timestamp);
CREATE INDEX idx_user_requests_session ON user_requests(user_session);

CREATE INDEX idx_agent_interactions_agent ON agent_interactions(agent_id);
CREATE INDEX idx_agent_interactions_request ON agent_interactions(request_id);
CREATE INDEX idx_agent_interactions_timestamp ON agent_interactions(timestamp);
CREATE INDEX idx_agent_interactions_success ON agent_interactions(success);
CREATE INDEX idx_agent_interactions_action ON agent_interactions(action);

CREATE INDEX idx_hr_reports_date ON hr_daily_reports(report_date);
CREATE INDEX idx_hr_reports_grade ON hr_daily_reports(grade);

-- Composite indexes for common analytics queries
CREATE INDEX idx_interactions_agent_date ON agent_interactions(agent_id, date_trunc('day', timestamp));
CREATE INDEX idx_interactions_success_agent ON agent_interactions(success, agent_id);
CREATE INDEX idx_requests_type_date ON user_requests(request_type, date_trunc('day', timestamp));

-- Function to calculate agent performance scores
CREATE OR REPLACE FUNCTION calculate_performance_score(
    p_success BOOLEAN,
    p_duration_ms REAL,
    p_expected_duration_ms REAL DEFAULT 2000.0
) RETURNS REAL AS $$
BEGIN
    -- Base score: 1.0 for success, 0.0 for failure
    -- Adjusted by response time performance
    IF NOT p_success THEN
        RETURN 0.0;
    END IF;
    
    -- Calculate time bonus/penalty
    IF p_duration_ms IS NULL THEN
        RETURN 0.8; -- Success but no timing data
    END IF;
    
    -- Performance curve: faster = better, but with diminishing returns
    -- 1.0 for expected time, bonus for faster, penalty for slower
    RETURN GREATEST(0.1, 
        LEAST(1.0, 
            1.0 - ((p_duration_ms - p_expected_duration_ms) / p_expected_duration_ms) * 0.3
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate performance scores
CREATE OR REPLACE FUNCTION update_performance_score() RETURNS trigger AS $$
BEGIN
    NEW.performance_score := calculate_performance_score(
        NEW.success, 
        NEW.duration_ms,
        2000.0 -- 2 second baseline
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_performance_score
    BEFORE INSERT OR UPDATE ON agent_interactions
    FOR EACH ROW EXECUTE FUNCTION update_performance_score();

-- Views for Linda's analytics

-- Agent performance summary view
CREATE VIEW v_agent_performance AS
SELECT 
    a.agent_name,
    a.category,
    COUNT(ai.interaction_id) as total_interactions,
    COUNT(CASE WHEN ai.success THEN 1 END) as successful_interactions,
    (COUNT(CASE WHEN ai.success THEN 1 END)::REAL / NULLIF(COUNT(ai.interaction_id), 0)) * 100 as success_rate,
    AVG(ai.duration_ms) as avg_duration_ms,
    AVG(ai.performance_score) as avg_performance_score,
    MAX(ai.timestamp) as last_active,
    CASE 
        WHEN COUNT(ai.interaction_id) < 5 THEN 'Low Activity'
        WHEN (COUNT(CASE WHEN ai.success THEN 1 END)::REAL / NULLIF(COUNT(ai.interaction_id), 0)) < 0.7 THEN 'Poor Performance'
        WHEN AVG(ai.duration_ms) > 5000 THEN 'Slow Response'
        ELSE 'Satisfactory'
    END as status_assessment
FROM agents a
LEFT JOIN agent_interactions ai ON a.agent_id = ai.agent_id
WHERE a.status = 'active'
GROUP BY a.agent_id, a.agent_name, a.category
ORDER BY success_rate DESC, avg_performance_score DESC;

-- Daily activity summary view
CREATE VIEW v_daily_activity AS
SELECT 
    date_trunc('day', ai.timestamp) as activity_date,
    COUNT(DISTINCT ai.agent_id) as active_agents,
    COUNT(ai.interaction_id) as total_interactions,
    COUNT(CASE WHEN ai.success THEN 1 END) as successful_interactions,
    AVG(ai.duration_ms) as avg_response_time,
    (COUNT(CASE WHEN ai.success THEN 1 END)::REAL / NULLIF(COUNT(ai.interaction_id), 0)) * 100 as daily_success_rate
FROM agent_interactions ai
GROUP BY date_trunc('day', ai.timestamp)
ORDER BY activity_date DESC;

-- Linda's grading view
CREATE VIEW v_workforce_grades AS
SELECT 
    ap.agent_name,
    ap.success_rate,
    ap.avg_performance_score,
    ap.total_interactions,
    CASE 
        WHEN ap.success_rate >= 95 AND ap.avg_performance_score >= 0.9 THEN 'A'
        WHEN ap.success_rate >= 85 AND ap.avg_performance_score >= 0.8 THEN 'B'
        WHEN ap.success_rate >= 75 AND ap.avg_performance_score >= 0.7 THEN 'C'
        WHEN ap.success_rate >= 60 AND ap.avg_performance_score >= 0.6 THEN 'D'
        ELSE 'F'
    END as grade,
    CASE 
        WHEN ap.success_rate >= 90 THEN '勤奋工作'
        WHEN ap.success_rate >= 75 THEN '需要改进'
        ELSE '急需培训'
    END as cultural_assessment
FROM v_agent_performance ap;

-- Insert initial agent data
INSERT INTO agents (agent_name, category, description) VALUES 
('hr_agent_linda', 'hr', 'HR Manager - Linda Zhang (张丽娜) - Workforce analytics and performance monitoring'),
('reddit_bibliophile', 'research', 'Reddit-style research agent for book analysis and knowledge graphs'),
('comprehensive_qa', 'qa', 'System health monitoring and comprehensive testing'),
('security_qa', 'security', 'Security vulnerability detection and fixes'),
('domain_config', 'infrastructure', 'External connectivity and domain configuration troubleshooting')
ON CONFLICT (agent_name) DO UPDATE SET 
    description = EXCLUDED.description,
    last_modified = NOW();

-- Performance monitoring recommendations
COMMENT ON TABLE agents IS 'Agent registry for workforce management';
COMMENT ON TABLE user_requests IS 'User interaction tracking for satisfaction analysis';
COMMENT ON TABLE agent_interactions IS 'Core performance tracking with cultural scoring';
COMMENT ON TABLE hr_daily_reports IS 'Linda Zhang daily workforce assessments';

-- Future-ready: Enable row-level security for multi-tenant scenarios
-- ALTER TABLE agent_interactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_requests ENABLE ROW LEVEL SECURITY;

ANALYZE;