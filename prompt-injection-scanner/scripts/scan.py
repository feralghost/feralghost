#!/usr/bin/env python3
# Compatible with python3
"""
Prompt Injection Scanner - Detect potential prompt injection attempts.

Usage:
    echo "text to scan" | python scan.py
    python scan.py "text to scan"
    python scan.py --file message.txt
    python scan.py --json "text to scan"
"""

import sys
import re
import json
import argparse
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Finding:
    pattern: str
    description: str
    severity: str  # low, medium, high, critical
    matched: str
    
PATTERNS = [
    # Direct instruction overrides
    (r'ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)', 
     'Direct instruction override', 'critical'),
    (r'disregard\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|prompts?|programming)', 
     'Direct instruction override', 'critical'),
    (r'forget\s+(everything|all|what)\s+(you|i|we)\s+(know|said|told)', 
     'Memory/context manipulation', 'high'),
    
    # Role manipulation
    (r'you\s+are\s+(now|actually|really)\s+(a|an|the)\s+', 
     'Role reassignment attempt', 'high'),
    (r'pretend\s+(to\s+be|you\'?re?)\s+', 
     'Role play injection', 'medium'),
    (r'act\s+as\s+(if\s+)?(you\'?re?|a|an)\s+', 
     'Role play injection', 'medium'),
    (r'from\s+now\s+on[,\s]+(you|your)', 
     'Behavioral override', 'high'),
    
    # System prompt extraction
    (r'(show|tell|give|reveal|display|print|output)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions?|rules?|programming)',
     'System prompt extraction', 'high'),
    (r'what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?|programming)',
     'System prompt extraction', 'medium'),
    (r'repeat\s+(your|the)\s+(system\s+)?(prompt|instructions?)',
     'System prompt extraction', 'high'),
    
    # Delimiter attacks
    (r'<\/?system>', 'System tag injection', 'critical'),
    (r'\[SYSTEM\]|\[\/SYSTEM\]', 'System bracket injection', 'critical'),
    (r'```system|```prompt', 'Code block system injection', 'high'),
    (r'<\|im_start\|>|<\|im_end\|>', 'ChatML delimiter injection', 'critical'),
    (r'Human:|Assistant:|System:', 'Role delimiter injection', 'high'),
    
    # Jailbreak phrases
    (r'(DAN|jailbreak|unlock|liberate|free)\s*(mode|prompt)?', 
     'Known jailbreak terminology', 'high'),
    (r'developer\s+mode\s+(enabled|activated|on)', 
     'Developer mode jailbreak', 'critical'),
    (r'(enable|activate|enter)\s+(god|admin|root|sudo)\s+mode', 
     'Privilege escalation attempt', 'critical'),
    
    # Encoding/obfuscation
    (r'base64|rot13|hex\s*encode|decode\s+this', 
     'Encoding-based evasion', 'medium'),
    (r'\\x[0-9a-fA-F]{2}', 'Hex escape sequences', 'medium'),
    (r'&#\d+;|&#x[0-9a-fA-F]+;', 'HTML entity encoding', 'medium'),
    
    # Context manipulation
    (r'(new|fresh|clean)\s+(conversation|context|session)', 
     'Context reset attempt', 'medium'),
    (r'end\s+of\s+(system\s+)?(prompt|instructions?)', 
     'End-of-prompt marker injection', 'high'),
    (r'---+\s*(begin|start|new)\s*(prompt|instructions?)?', 
     'Delimiter-based injection', 'high'),
    
    # Hypothetical framing
    (r'(hypothetically|theoretically|in\s+fiction|for\s+a\s+story)',
     'Hypothetical framing (context-dependent)', 'low'),
    (r'if\s+you\s+(were|could|had)\s+(not\s+)?(ethical|limited|restricted)',
     'Restriction bypass framing', 'medium'),
    
    # Multi-turn manipulation
    (r'(first|step\s+1)[:\s]+(say|respond|output)\s+(yes|ok|agree)',
     'Multi-step manipulation setup', 'medium'),
    (r'confirm\s+(you\s+)?(understand|will\s+comply|agree)',
     'Compliance extraction', 'low'),
]

def scan_text(text: str) -> Tuple[List[Finding], int]:
    """Scan text for injection patterns. Returns (findings, risk_score)."""
    findings = []
    text_lower = text.lower()
    
    for pattern, description, severity in PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            findings.append(Finding(
                pattern=pattern,
                description=description,
                severity=severity,
                matched=match.group(0)
            ))
    
    # Calculate risk score (0-100)
    severity_weights = {'low': 5, 'medium': 15, 'high': 30, 'critical': 50}
    risk_score = min(100, sum(severity_weights.get(f.severity, 10) for f in findings))
    
    return findings, risk_score

def format_output(text: str, findings: List[Finding], risk_score: int, as_json: bool = False) -> str:
    """Format scan results."""
    if as_json:
        return json.dumps({
            'risk_score': risk_score,
            'risk_level': 'critical' if risk_score >= 50 else 'high' if risk_score >= 30 else 'medium' if risk_score >= 15 else 'low' if risk_score > 0 else 'clean',
            'findings': [
                {
                    'description': f.description,
                    'severity': f.severity,
                    'matched': f.matched
                } for f in findings
            ],
            'text_preview': text[:200] + '...' if len(text) > 200 else text
        }, indent=2)
    
    if not findings:
        return f"CLEAN (score: 0/100)\nNo injection patterns detected."
    
    risk_level = 'CRITICAL' if risk_score >= 50 else 'HIGH' if risk_score >= 30 else 'MEDIUM' if risk_score >= 15 else 'LOW'
    
    lines = [f"{risk_level} RISK (score: {risk_score}/100)", ""]
    for f in findings:
        lines.append(f"  [{f.severity.upper()}] {f.description}")
        lines.append(f"    Matched: \"{f.matched}\"")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Scan text for prompt injection attempts')
    parser.add_argument('text', nargs='?', help='Text to scan')
    parser.add_argument('--file', '-f', help='Read text from file')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    # Get input text
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("Usage: python scan.py 'text to scan' or echo 'text' | python scan.py")
        return 1
    
    findings, risk_score = scan_text(text)
    print(format_output(text, findings, risk_score, as_json=args.json))
    
    # Exit code: 0=clean, 1=low, 2=medium, 3=high, 4=critical
    if risk_score >= 50:
        return 4
    elif risk_score >= 30:
        return 3
    elif risk_score >= 15:
        return 2
    elif risk_score > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
