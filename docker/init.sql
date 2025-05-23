CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE history (
     id VARCHAR PRIMARY KEY,
     content TEXT,
     "vector" vector(4096) NOT NULL
);
