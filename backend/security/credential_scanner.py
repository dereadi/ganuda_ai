# /ganuda/backend/security/credential_scanner.py

import os
import re
from typing import List, Dict, Tuple

class CredentialScanner:
    """
    Scans files and directories for potential credentials and sensitive information.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.sensitive_patterns = [
            r'(password|pwd|pass|token|secret|key)\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'(password|pwd|pass|token|secret|key)\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'(password|pwd|pass|token|secret|key)\s*=\s*(\w+)',
            r'(password|pwd|pass|token|secret|key)\s*:\s*(\w+)',
        ]

    def scan_directory(self) -> List[Tuple[str, str]]:
        """
        Recursively scans the directory for files containing sensitive information.
        Returns a list of tuples containing the file path and the matched pattern.
        """
        results = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                matches = self.scan_file(file_path)
                if matches:
                    results.extend([(file_path, match) for match in matches])
        return results

    def scan_file(self, file_path: str) -> List[str]:
        """
        Scans a single file for sensitive information.
        Returns a list of matched patterns.
        """
        matches = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in self.sensitive_patterns:
                    for match in re.findall(pattern, content, re.IGNORECASE):
                        matches.append(match[0] + ' = ' + match[1])
        except UnicodeDecodeError:
            # Skip binary files
            pass
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return matches

    def report_results(self, results: List[Tuple[str, str]]) -> None:
        """
        Prints the results of the scan.
        """
        for file_path, match in results:
            print(f"Sensitive information found in {file_path}: {match}")

if __name__ == "__main__":
    scanner = CredentialScanner('/path/to/scan')
    results = scanner.scan_directory()
    scanner.report_results(results)