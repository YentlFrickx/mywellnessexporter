CREATE TABLE user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_pic TEXT NOT NULL,
    strava_id TEXT,
    strava_access_token TEXT,
    strava_expires TEXT,
    strava_refresh_token TEXT
);