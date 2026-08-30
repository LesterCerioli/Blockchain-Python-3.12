CREATE TABLE IF NOT EXISTS public.report_narrative_sections
(
    id                   uuid         NOT NULL DEFAULT gen_random_uuid(),
    run_id               uuid         NOT NULL,
    organization_id      uuid         NOT NULL,
    section_id           varchar(100) NOT NULL,
    section_title        varchar(255),
    text                 text         NOT NULL,
    citations            jsonb        NOT NULL DEFAULT '[]'::jsonb,
    data_integrity_score double precision NOT NULL DEFAULT 0,
    is_flagged           boolean      NOT NULL DEFAULT false,
    flag_reason          text,
    created_at           timestamptz  NOT NULL DEFAULT NOW(),
    CONSTRAINT report_narrative_sections_pkey PRIMARY KEY (id),
    CONSTRAINT report_narrative_sections_org_fkey FOREIGN KEY (organization_id)
        REFERENCES public.organizations (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.report_narrative_sections
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_rns_run_id
    ON public.report_narrative_sections USING btree (run_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_rns_org_created
    ON public.report_narrative_sections USING btree
    (organization_id ASC NULLS LAST, created_at DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_rns_flagged
    ON public.report_narrative_sections USING btree (is_flagged ASC NULLS LAST)
    TABLESPACE pg_default
    WHERE is_flagged = true;

CREATE UNIQUE INDEX IF NOT EXISTS idx_rns_run_section
    ON public.report_narrative_sections USING btree (run_id ASC NULLS LAST, section_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
