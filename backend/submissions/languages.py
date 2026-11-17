"""Languages a student may submit in, and the entry file each one uses.

The ERD has no language column: the language is read from the entry point's
file name, which is also what an execution worker will need.
"""

ENTRY_FILES = {
    'python': 'main.py',
    'java': 'Main.java',
    'cpp': 'main.cpp',
    'javascript': 'main.js',
    'html': 'index.html',
    'css': 'style.css',
}

LANGUAGE_BY_FILE = {path: language for language, path in ENTRY_FILES.items()}

LANGUAGE_CHOICES = list(ENTRY_FILES)
