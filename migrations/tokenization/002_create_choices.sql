
CREATE TABLE IF NOT EXISTS tokenization_choices (
    id                          UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     VARCHAR(128)                NOT NULL,
    business_type               VARCHAR(64)                 NOT NULL,
    description_tokenization    TEXT                        NOT NULL,
    tokenization_template       VARCHAR(256)                NOT NULL,
    chosen_at                   TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tokenization_choices_user_id ON tokenization_choices (user_id);
CREATE INDEX IF NOT EXISTS idx_tokenization_choices_business_type ON tokenization_choices (business_type);
CREATE INDEX IF NOT EXISTS idx_tokenization_choices_template ON tokenization_choices (tokenization_template);

COMMENT ON TABLE  tokenization_choices IS 'Final user choices after Groq reordering - isolated by user_id';
COMMENT ON COLUMN tokenization_choices.user_id IS 'Owner user_id - isolation mandatory, queried via parameterized :user_id';
COMMENT ON COLUMN tokenization_choices.business_type IS 'Business sector enum value';
COMMENT ON COLUMN tokenization_choices.description_tokenization IS 'Challenge text 10-2000 chars';
COMMENT ON COLUMN tokenization_choices.tokenization_template IS 'Chosen template name or custom:xxx';
