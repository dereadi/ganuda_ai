import os
import re
from typing import List, Tuple

# Define the patterns to search for
PATTERNS = [
    r'password\s*=\s*[\'"].*[\'"]',
    r'api_key\s*=\s*[\'"].*[\'"]',
    r'token\s*=\s*[\'"].*[\'"]',
    r'secret\s*=\s*[\'"].*[\'"]',
    r'PASSWORD\s*=\s*[\'"].*[\'"]',
    r'API_KEY\s*=\s*[\'"].*[\'"]',
    r'Bearer\s+[\'"].*[\'"]',
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+password\s*=\s*[\'"].*[\'"]'
]

# Define the file types to scan
FILE_TYPES = ['*.py', '*.env', '*.json', '*.yaml', '*.yml', '*.toml', '*.cfg', '*.ini']

# Define the directories and files to exclude
EXCLUDE_DIRS = ['/ganuda/config/secrets.env', '*.backup*', '__pycache__']

def find_files_to_scan(base_dir: str) -> List[str]:
    """Find all files to scan based on file types and exclusions."""
    files_to_scan: List[str] = []
    for root, dirs, files in os.walk(base_dir):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if not any(exclude in os.path.join(root, d) for exclude in EXCLUDE_DIRS)]
        
        for file in files:
            if any(file.endswith(ft) for ft in FILE_TYPES) and not any(exclude in file for exclude in EXCLUDE_DIRS):
                files_to_scan.append(os.path.join(root, file))
    return files_to_scan

def scan_file_for_credentials(file_path: str) -> List[Tuple[str, int, str]]:
    """Scan a single file for credential patterns."""
    matches: List[Tuple[str, int, str]] = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line_number, line in enumerate(lines, start=1):
            for pattern in PATTERNS:
                if re.search(pattern, line):
                    # Redact the actual value
                    redacted_line = re.sub(r'[\'"].*[\'"]', '"***"', line)
                    matches.append((file_path, line_number, redacted_line.strip()))
    return matches

def main() -> None:
    """Main function to run the credential audit."""
    base_dir = '/ganuda/'
    files_to_scan = find_files_to_scan(base_dir)
    all_matches: List[Tuple[str, int, str]] = []

    for file in files_to_scan:
        matches = scan_file_for_credentials(file)
        all_matches.extend(matches)

    if all_matches:
        print("Credential Audit Report:")
        for file_path, line_number, matched_pattern in all_matches:
            print(f"File: {file_path}, Line: {line_number}, Pattern: {matched_pattern}")
    else:
        print("No hardcoded credentials found.")

if __name__ == "__main__":
    main()