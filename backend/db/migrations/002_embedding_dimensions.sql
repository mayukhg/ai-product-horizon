-- Migrate asset embeddings from 384-dim (nomic-embed-text) to 1536-dim (text-embedding-3-small)
UPDATE assets SET embedding = NULL WHERE embedding IS NOT NULL;

DO $$
BEGIN
  ALTER TABLE assets ALTER COLUMN embedding TYPE vector(1536);
EXCEPTION
  WHEN others THEN
    NULL;
END $$;
