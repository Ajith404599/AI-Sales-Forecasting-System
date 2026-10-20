-- Apply once to add the optional signup display name; existing accounts remain valid.
ALTER TABLE users
    ADD COLUMN full_name VARCHAR(120) NULL;