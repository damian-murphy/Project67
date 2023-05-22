-- Initialize the database.
-- Drop any existing data and create empty tables.
-- Only use this to start from scratch, natch.

DROP TABLE IF EXISTS projects;

CREATE TABLE projects (
  number INTEGER PRIMARY KEY AUTOINCREMENT,
  idea TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  done TIMESTAMP,
  started_on TIMESTAMP,
  stopped_on TIMESTAMP,
  continuous INT,
  links TEXT,
  memoranda TEXT,
  last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);