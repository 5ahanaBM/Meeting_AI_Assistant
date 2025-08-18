CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION app;
SET search_path TO public;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.meetings (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title      varchar(255) NOT NULL,
  meet_url   text,
  start_ts   timestamptz NOT NULL DEFAULT now(),
  end_ts     timestamptz
);

CREATE TABLE IF NOT EXISTS public.utterances (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id    uuid NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
  speaker_label varchar(64),
  start_time_ms bigint NOT NULL DEFAULT 0,
  end_time_ms   bigint NOT NULL DEFAULT 0,
  text          text NOT NULL,
  lang          varchar(16),
  is_final      boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_utterances_meeting_time
  ON public.utterances (meeting_id, start_time_ms);

CREATE INDEX IF NOT EXISTS idx_utterances_is_final
  ON public.utterances (is_final);

CREATE TABLE IF NOT EXISTS public.alembic_version (
  version_num varchar(32) PRIMARY KEY
);
TRUNCATE public.alembic_version;
INSERT INTO public.alembic_version(version_num) VALUES ('1541af67125b');

-- docker cp .\scripts\bootstrap.sql meetingai-postgres:/tmp/bootstrap.sql
-- docker exec -it meetingai-postgres psql -U app -d meeting_ai -v ON_ERROR_STOP=1 -f /tmp/bootstrap.sql
