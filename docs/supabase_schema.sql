-- ═══════════════════════════════════════════════════════
-- SAAQ Database Schema (Supabase / PostgreSQL)
-- ═══════════════════════════════════════════════════════
-- Run this in Supabase SQL Editor to set up the database.
-- The backend works without this (in-memory) for local dev.

-- Intakes: survey submissions
CREATE TABLE IF NOT EXISTS intakes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    email TEXT,
    version TEXT NOT NULL DEFAULT '15Q',
    responses JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Reports: generated diagnostic reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intake_id UUID NOT NULL REFERENCES intakes(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    report_data JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_intakes_status ON intakes(status);
CREATE INDEX IF NOT EXISTS idx_intakes_created ON intakes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_intake ON reports(intake_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER intakes_updated_at
    BEFORE UPDATE ON intakes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
