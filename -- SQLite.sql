-- SQLite
-- Create users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

-- CREATE AN INDEX FOR UNIQUE COLUMN username
CREATE UNIQUE INDEX username ON users (username);

-- Create transactions table
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    category TEXT NOT NULL DEFAULT "NOT SET",
    date TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

