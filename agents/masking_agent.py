import re

MASK_PATTERNS = [
    ("EMAIL", r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), 
    ("PHONE", r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    ("SSN", r'\d{3}-\d{2}-\d{4}'), 
    ("CREDIT_CARD", r'(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})'), # More accurate credit card regex
    ("API_KEY", r'[a-zA-Z0-9]{32,}'),
    # ("PASSWORD", r'(?<!\w)(?:[a-zA-Z0-9!@#$%^&*()_+{}\[\]:;<>,.?~\/-]{8,})(?!\w)'),    
    ("SECRET", r'[a-zA-Z0-9]{16,}'),
    ("OPENAI_KEY", r'sk-[a-zA-Z0-9]{24}'),
    ("UUID", r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'),
    ("TOKEN", r'[a-zA-Z0-9]{32,}'),
    ("AWS_KEY", r'AKIA[0-9A-Z]{16}')
]

def mask_content(text):
    mapping = {}
    masked_lines = []

    lines = text.splitlines()
    for i, line in enumerate(lines):
        masked_line = line
        for name, pattern in MASK_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE): #Use finditer to get all matches
                value = match.group(0)
                marker = f"ID_{name}_{i}_{match.start()}" # Added match start index for uniqueness
                mapping[marker] = value
                masked_line = masked_line.replace(value, marker, 1) #replace only first occurence of each match

        masked_lines.append(masked_line)

    return "\n".join(masked_lines), mapping


def unmask_content(text, mapping):
    lines = text.splitlines()
    unmasked_lines = []
    for line in lines:
        for marker, value in mapping.items():
            line = line.replace(marker, value)
        unmasked_lines.append(line)
    return "\n".join(unmasked_lines)