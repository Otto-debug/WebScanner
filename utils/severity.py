SQLI_SEVERITY = {
    "SQLi_Auth": 4,
    "SQLi_Data": 3,
    "SQLi_Error": 2,
    "Potential_SQLi": 1
}

SEVERITY_NAMES = {
    4: "Critical",
    3: "High",
    2: "Medium",
    1: "Low"
}

VULNERABILITY_SEVERITY = {
    "SQLi_Auth": 4,
    "SQLi_Data": 3,
    "SQLi_Error": 2,
    "Potential_SQLi": 1,

    "Stored_XSS": 4,
    "Reflected_XSS": 4,

    "XXE": 4,

    "SSRF": 4,

    "SSTI": 4,

    "Command_Injection": 4,

    "IDOR": 3,

    "Path_Traversal": 3,
}

VULNERABILITY_INFO = {
    "SQLi_Error": {
        "scanner": "SQLi",
        "cwe": "CWE-89"
    },
    "SQLi_Data": {
        "scanner": "SQLi",
        "cwe": "CWE-89"
    },
    "SQLi_Auth": {
        "scanner": "SQLi",
        "cwe": "CWE-89"
    },

    "Stored_XSS": {
        "scanner": "XSS",
        "cwe": "CWE-79"
    },
    "Reflected_XSS": {
        "scanner": "XSS",
        "cwe": "CWE-79"
    },
    "DOM_XSS": {
        "scanner": "XSS",
        "cwe": "CWE-79"
    }
}