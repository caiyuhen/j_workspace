CREATE TABLE IF NOT EXISTS trial_extensions (
    id UUID PRIMARY KEY,
    trial_id UUID UNIQUE REFERENCES trials(id) ON DELETE CASCADE,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_trial_extensions_trial_id ON trial_extensions (trial_id);
