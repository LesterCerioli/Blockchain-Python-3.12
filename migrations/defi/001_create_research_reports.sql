-- Migration 001: Create research_reports table
-- Service: defi
-- Purpose: Persists impersonal, versioned market research reports.
--          Includes a tsvector column for full-text search (FTS).
-- Note: gen_random_uuid() is built-in since PostgreSQL 13. For older
--       versions enable pgcrypto first: CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS research_reports (
    report_id      UUID                        PRIMARY KEY,
    slug           VARCHAR(250)                NOT NULL UNIQUE,
    title          VARCHAR(200)                NOT NULL,
    body_markdown  TEXT                        NOT NULL,
    summary        VARCHAR(500)                NOT NULL,
    published_at   TIMESTAMP WITH TIME ZONE    NOT NULL,
    categories     TEXT                        NOT NULL,
    tags           TEXT                        NOT NULL,
    version        INTEGER                     NOT NULL DEFAULT 1,
    author_type    VARCHAR(20)                 NOT NULL,
    search_vector  TSVECTOR                    NOT NULL DEFAULT ''::tsvector,
    created_at     TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW()
);

-- GIN index for full-text search on the tsvector column
CREATE INDEX IF NOT EXISTS idx_research_reports_fts
    ON research_reports
    USING GIN (search_vector);

-- Unique index for slug lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_research_reports_slug
    ON research_reports (slug);

-- Index for filtering by author type
CREATE INDEX IF NOT EXISTS idx_research_reports_author_type
    ON research_reports (author_type);

-- Index for filtering by publication date
CREATE INDEX IF NOT EXISTS idx_research_reports_published_at
    ON research_reports (published_at DESC);

-- Trigger to keep search_vector in sync with title, summary, body, categories, tags
CREATE OR REPLACE FUNCTION research_reports_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', NEW.title), 'A') ||
        setweight(to_tsvector('english', NEW.summary), 'B') ||
        setweight(to_tsvector('english', NEW.body_markdown), 'C') ||
        setweight(to_tsvector('english', NEW.categories), 'D') ||
        setweight(to_tsvector('english', NEW.tags), 'D');
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_research_reports_search_vector
    BEFORE INSERT OR UPDATE ON research_reports
    FOR EACH ROW
    EXECUTE FUNCTION research_reports_search_vector_update();

COMMENT ON TABLE  research_reports IS 'Impersonal, versioned market research reports. No user-specific or personalized content.';
COMMENT ON COLUMN research_reports.report_id     IS 'UUID v4 — application-generated (never user-derived).';
COMMENT ON COLUMN research_reports.author_type    IS 'editorial | automated — never "user".';
COMMENT ON COLUMN research_reports.search_vector  IS 'tsvector for full-text search across title, summary, body, categories, tags.';
COMMENT ON COLUMN research_reports.categories     IS 'JSON-encoded array of category strings.';
COMMENT ON COLUMN research_reports.tags           IS 'JSON-encoded array of tag strings.';
