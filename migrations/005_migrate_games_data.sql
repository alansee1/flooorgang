-- Migration 005: Migrate games_reviewed data and drop old column
-- This assumes migration 004 has already been run

-- Migrate existing data: copy games_reviewed to games_scheduled
-- We assume old runs had props for all games (best guess for historical data)
UPDATE scanner_runs
SET games_scheduled = games_reviewed,
    games_with_props = games_reviewed
WHERE games_reviewed IS NOT NULL;

-- Drop the old deprecated column
ALTER TABLE scanner_runs
DROP COLUMN games_reviewed;
