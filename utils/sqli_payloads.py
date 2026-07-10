SQL_ERROR_PATTERNS = [
    r"sqlite",
    r"sql syntax",
    r"syntax error",
    r"unclosed quotation",
    r"unterminated string",
    r"mysql",
    r"postgres",
    r"psql",
    r"odbc",
    r"sqlite_error",
    r"sequelize",
    r"database error",
    r"near \".*?\": syntax error",
]
SQLI_BASIC = [
    "'",
    "\"",
    "'--",
    "'#",
    "' OR 1=1--",
    "' OR '1'='1",
    "' UNION SELECT NULL--",
    "' UNION SELECT sqlite_version()--",
    "'; WAITFOR DELAY '0:0:5'--",
]
SQL_ERRORS = {
    "SQLite": [
        r"sqlite error",
        r"sqlite3\.operationalerror",
        r"database error",
        r"syntax error",
        r"unrecognized token",
        r"unterminated string",
        r"near\s+[\"']or",
        r"near\s+[\"']union",
    ],

    "MySQL": [
        r"you have an error in your sql syntax",
        r"warning.*mysql",
        r"mysql server version",
    ],

    "PostgreSQL": [
        r"pg_query",
        r"pg_exec",
        r"postgresql.*error",
        r"syntax error at or near",
    ],

    "MSSQL": [
        r"sql server",
        r"microsoft ole db",
        r"odbc sql server",
        r"incorrect syntax near",
    ],

    "Oracle": [
        r"ora-\d+",
        r"oracle error",
    ]
}
