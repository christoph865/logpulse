-- Database Migration: Add Features Tables
-- This script creates tables for Saved Views and Anomaly Alerts features

-- ====================================================
-- TABLE: saved_views
-- Purpose: Store user's saved filter configurations
-- ====================================================
CREATE TABLE IF NOT EXISTS saved_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL DEFAULT '{}',
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_view_name_per_user UNIQUE(user_id, name)
);

-- Performance indexes for saved_views
CREATE INDEX IF NOT EXISTS idx_saved_views_user_id 
    ON saved_views(user_id);

CREATE INDEX IF NOT EXISTS idx_saved_views_user_pinned 
    ON saved_views(user_id, is_pinned);

CREATE INDEX IF NOT EXISTS idx_saved_views_created_at 
    ON saved_views(created_at);

-- ====================================================
-- TABLE: anomaly_alerts
-- Purpose: Store detected anomalies with statistics
-- ====================================================
CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(255) NOT NULL,
    event_type VARCHAR(255),
    severity VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    baseline_value NUMERIC(10, 2),
    observed_value NUMERIC(10, 2),
    deviation_percent NUMERIC(8, 2),
    z_score NUMERIC(8, 3),
    is_acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Performance indexes for anomaly_alerts
CREATE INDEX IF NOT EXISTS idx_anomalies_source_created 
    ON anomaly_alerts(source, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomalies_ack_created 
    ON anomaly_alerts(is_acknowledged, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomalies_severity 
    ON anomaly_alerts(severity);

CREATE INDEX IF NOT EXISTS idx_anomalies_type 
    ON anomaly_alerts(anomaly_type);

CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at 
    ON anomaly_alerts(detected_at DESC);

-- ====================================================
-- Verify tables were created
-- ====================================================
-- SELECT EXISTS(
--     SELECT 1 FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'saved_views'
-- ) AS saved_views_exists,
-- EXISTS(
--     SELECT 1 FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'anomaly_alerts'
-- ) AS anomaly_alerts_exists;
