-- Migration 001: Create tokenization_templates table
-- Service: tokenization
-- Purpose: Stores tokenization template catalog with metadata,
--          characteristics, token model config, and business rules.

CREATE TABLE IF NOT EXISTS tokenization_templates (
    id               UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(128)                NOT NULL UNIQUE,
    description      TEXT                        NOT NULL,
    category         VARCHAR(64)                 NOT NULL,
    strategy         VARCHAR(64)                 NOT NULL,
    token_standard   VARCHAR(16)                 NOT NULL,
    status           VARCHAR(20)                 NOT NULL DEFAULT 'draft',
    version_major    INTEGER                     NOT NULL DEFAULT 1,
    version_minor    INTEGER                     NOT NULL DEFAULT 0,
    version_patch    INTEGER                     NOT NULL DEFAULT 0,
    metadata         JSONB                       DEFAULT '{}',
    characteristics  JSONB                       DEFAULT '{}',
    token_model      JSONB                       DEFAULT '{}',
    business_rules   JSONB                       DEFAULT '[]',
    created_by       VARCHAR(128)                NOT NULL DEFAULT 'system',
    approved_by      VARCHAR(128),
    approved_at      TIMESTAMP WITH TIME ZONE,
    created_at       TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tokenization_templates_category ON tokenization_templates (category);
CREATE INDEX IF NOT EXISTS idx_tokenization_templates_strategy ON tokenization_templates (strategy);
CREATE INDEX IF NOT EXISTS idx_tokenization_templates_status ON tokenization_templates (status);
CREATE INDEX IF NOT EXISTS idx_tokenization_templates_token_standard ON tokenization_templates (token_standard);

COMMENT ON TABLE  tokenization_templates                IS 'Tokenization template catalog for smart contract deployments.';
COMMENT ON COLUMN tokenization_templates.name           IS 'Unique business key used as API identifier.';
COMMENT ON COLUMN tokenization_templates.metadata       IS 'JSON: author, license, audit info, tags.';
COMMENT ON COLUMN tokenization_templates.characteristics IS 'JSON: target_use_case, industry, jurisdiction, chain support.';
COMMENT ON COLUMN tokenization_templates.token_model    IS 'JSON: standard, symbol, decimals, supply, mintable, burnable.';
COMMENT ON COLUMN tokenization_templates.business_rules IS 'JSON array: configurable rules per template.';
