-- Legacy raw queries bind UUID identifiers as text. Prisma sets search_path
-- to ats, so public-only operators are not visible to those connections.
CREATE OR REPLACE FUNCTION ats.uuid_eq_text(uuid, text) RETURNS boolean
LANGUAGE SQL IMMUTABLE AS $$ SELECT $1 = $2::uuid; $$;
CREATE OR REPLACE FUNCTION ats.text_eq_uuid(text, uuid) RETURNS boolean
LANGUAGE SQL IMMUTABLE AS $$ SELECT $1::uuid = $2; $$;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_operator WHERE oprnamespace='ats'::regnamespace AND oprname='=' AND oprleft='uuid'::regtype AND oprright='text'::regtype) THEN
    CREATE OPERATOR ats.= (LEFTARG=uuid, RIGHTARG=text, PROCEDURE=ats.uuid_eq_text);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_operator WHERE oprnamespace='ats'::regnamespace AND oprname='=' AND oprleft='text'::regtype AND oprright='uuid'::regtype) THEN
    CREATE OPERATOR ats.= (LEFTARG=text, RIGHTARG=uuid, PROCEDURE=ats.text_eq_uuid);
  END IF;
END $$;

-- Both the legacy backend normalization SQL and parser use category_id.
-- Preserve Prisma's category text column while adding the legacy reference.
ALTER TABLE ats.skills_master ADD COLUMN IF NOT EXISTS category_id INTEGER;
