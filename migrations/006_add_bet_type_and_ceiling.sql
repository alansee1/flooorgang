-- Add bet_type and ceiling columns to support team totals (OVER/UNDER)

-- Add bet_type column (OVER or UNDER)
ALTER TABLE picks
ADD COLUMN bet_type TEXT DEFAULT 'OVER';

-- Add ceiling column for team UNDER bets
ALTER TABLE picks
ADD COLUMN ceiling DECIMAL;

-- Add comments
COMMENT ON COLUMN picks.bet_type IS 'OVER or UNDER - defaults to OVER for player props';
COMMENT ON COLUMN picks.ceiling IS 'Maximum value (used for team UNDER bets) - player ceiling or team ceiling';
