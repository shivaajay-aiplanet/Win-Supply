-- Create cross_reference table for caching LLM product matches
-- Run this script in your PostgreSQL database

-- Create the cross_reference table
CREATE TABLE IF NOT EXISTS public.cross_reference (
    id SERIAL PRIMARY KEY,
    wise_item_number VARCHAR(255) NOT NULL UNIQUE,
    llm_matches JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on wise_item_number for fast lookups
CREATE INDEX IF NOT EXISTS idx_cross_reference_wise_item_number 
ON public.cross_reference(wise_item_number);

-- Add comment to table
COMMENT ON TABLE public.cross_reference IS 'Cache table for LLM product matching results';
COMMENT ON COLUMN public.cross_reference.wise_item_number IS 'Source product WISE item number';
COMMENT ON COLUMN public.cross_reference.llm_matches IS 'JSON array of matched products in compact format';

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cross_reference_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at on row update
DROP TRIGGER IF EXISTS update_cross_reference_timestamp ON public.cross_reference;
CREATE TRIGGER update_cross_reference_timestamp
    BEFORE UPDATE ON public.cross_reference
    FOR EACH ROW
    EXECUTE FUNCTION update_cross_reference_updated_at();

-- Verify table was created
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'cross_reference' 
AND table_schema = 'public'
ORDER BY ordinal_position;

