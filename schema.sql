CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_pic TEXT NOT NULL,
    strava_id TEXT,
    strava_access_token TEXT,
    strava_expires TEXT,
    strava_refresh_token TEXT,
    mywellness_cookie TEXT
);

CREATE TABLE IF NOT EXISTS activity (
    mywellness_href     TEXT PRIMARY KEY,
    user_id TEXT,
    FOREIGN KEY(user_id) REFERENCES user(id)
)

CREATE TABLE IF NOT EXISTS error (
    mywellness_href     TEXT PRIMARY KEY,
    user_id TEXT,
    FOREIGN KEY(user_id) REFERENCES user(id)
)