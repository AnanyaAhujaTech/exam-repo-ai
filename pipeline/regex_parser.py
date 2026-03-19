import re

# =========================
# SAFE MARKS EVALUATION
# =========================

def safe_eval_marks(expr):
    expr = re.sub(r'\s+', '', expr.lower().replace('x', '*'))

    if '=' in expr:
        try:
            return float(expr.split('=')[-1])
        except Exception:
            return None

    try:
        if '*' in expr:
            a, b = expr.split('*')
            return float(a) * float(b)
        elif '+' in expr:
            return sum(float(x) for x in expr.split('+'))
        elif expr.isdigit():
            return float(expr)
    except Exception:
        pass

    return None


# =========================
# CONTENT → TEXT
# =========================

def content_to_text(content):
    lines = []

    for block in content:

        if block["type"] == "paragraph":
            lines.append(block["text"])

        elif block["type"] == "table":
            rows = block["rows"]
            if not rows:
                continue
            
            # Extract header row
            header = " | ".join(str(cell).strip() if cell else " " for cell in rows[0])
            lines.append(f"| {header} |")
            
            # Create Markdown separator row (e.g., |---|---|)
            separator = " | ".join("---" for _ in rows[0])
            lines.append(f"| {separator} |")
            
            # Extract data rows
            for row in rows[1:]:
                row_text = " | ".join(str(cell).strip() if cell else " " for cell in row)
                lines.append(f"| {row_text} |")
            
            lines.append("") # Add a blank line after the table for spacing

    return "\n".join(lines)


# =========================
# METADATA EXTRACTION
# =========================

def extract_metadata(text):

    metadata = {}

    code_match = re.search(r'Subject Code: ([A-Z]{3})\-?\s?(\d{3})', text, re.I)
    if code_match:
        metadata["subject_code"] = code_match.group(1) + code_match.group(2)

    name_match = re.search(r'Subject: ([a-zA-Z\- ]+)', text, re.I)
    if name_match:
        metadata["subject_name"] = name_match.group(1).strip()

    program_match = re.search(r'Course Name\s?:\s?(.+?)\s*Semester', text, re.I)
    if program_match:
        metadata["program"] = program_match.group(1).strip()

    sem_match = re.search(r'Semester\s?:\s?<?(\d)>?', text, re.I)
    if sem_match:
        metadata["semester"] = int(sem_match.group(1))

    year_match = re.search(r'(20\d{2})', text)
    if year_match:
        year = int(year_match.group(1))
        metadata["academic_year"] = f"{year}-{year+1}"

    exam_match = re.search(r'(Mid|End)[ -]?Term Examination', text, re.I)
    if exam_match:
        t = exam_match.group(1)
        metadata["exam_type"] = f"{t}Sem"
        metadata["exam_name"] = f"{t}-Term Examination"

    time_match = re.search(r'(\d+\s*Hours?)', text, re.I)
    if time_match:
        metadata["time_duration"] = time_match.group(1)

    marks_match = re.search(r'Maximum Marks\s?:\s?(\d{1,3})', text, re.I)
    if marks_match:
        metadata["max_marks"] = int(marks_match.group(1))

    return metadata


# =========================
# UNIT SPLITTING
# =========================

def split_by_units(text):

    units = {None: []}
    current_unit = None

    unit_pattern = re.compile(
        r'^(?:UNIT|MODULE|SECTION|PART)[\s\-:]*([A-ZIVX\d]+)',
        re.I
    )

    for line in text.split("\n"):

        line = line.strip()
        if not line:
            continue

        match = unit_pattern.match(line)

        if match:
            current_unit = f"UNIT {match.group(1).upper()}"
            units.setdefault(current_unit, [])
            continue

        units.setdefault(current_unit, []).append(line)

    return units


# =========================
# QUESTION SPLITTING
# =========================

def split_questions(units):

    questions = []

    q_pattern = re.compile(
        r'^(?:Q\.?\s*|Question\s*)?(\d{1,2})[\.\)]\s+(.*)',
        re.I
    )

    for unit, lines in units.items():

        current_qid = None
        buffer = []

        for line in lines:

            match = q_pattern.match(line)

            if match:

                if current_qid:
                    questions.append({
                        "question_id": current_qid,
                        "unit": unit,
                        "raw_text": " ".join(buffer).strip()
                    })

                # 🔥 FIXED: Q1 format
                current_qid = f"Q{match.group(1)}"
                buffer = [match.group(2)] if match.group(2) else []

            elif current_qid:
                buffer.append(line)

        if current_qid:
            questions.append({
                "question_id": current_qid,
                "unit": unit,
                "raw_text": " ".join(buffer).strip()
            })

    return questions


# =========================
# SUBPART NORMALIZATION
# =========================

ROMAN_MAP = {
    "i": "a",
    "ii": "b",
    "iii": "c",
    "iv": "d",
    "v": "e",
    "vi": "f",
    "vii": "g",
    "viii": "h"
}


# =========================
# QUESTION PARSING
# =========================

def parse_question(q):

    raw = q["raw_text"]
    marks = None

    # -------- MARKS --------
    for m in re.findall(r'[\(\[]([^)\]]*)[\)\]]', raw):
        val = safe_eval_marks(m)
        if val is not None:
            marks = val
            break

    # -------- SUBPARTS --------
    subparts = []

    sub_pattern = re.compile(
        r'(?:^|\s)\(?([a-h]|[ivx]{1,4})\)\s',
        re.I
    )

    matches = list(sub_pattern.finditer(raw))

    if matches:

        per_mark = round(marks / len(matches), 2) if marks else None

        for i, match in enumerate(matches):

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)

            chunk = raw[start:end]

            clean = re.sub(r'[\(\[][^)\]]*[\)\]]|CO\d+', '', chunk)
            clean = re.sub(r'\s+', ' ', clean).strip()

            raw_id = match.group(1).lower()

            # 🔥 FIXED: Roman → alphabet
            sub_id = ROMAN_MAP.get(raw_id, raw_id)

            subparts.append({
                "subpart_id": sub_id,
                "text": clean,
                "marks": per_mark
            })

        question_text = "Attempt all parts."

    else:
        clean = re.sub(r'[\(\[][^)\]]*[\)\]]|CO\d+', '', raw)
        question_text = re.sub(r'\s+', ' ', clean).strip()

    return {
        "question_id": q["question_id"],
        "unit": q["unit"],
        "question_text": question_text,
        "marks": marks,
        "subparts": subparts
    }


# =========================
# MAIN ENTRY FUNCTION
# =========================

def parse_exam(extracted_data):

    content = extracted_data["content"]

    text = content_to_text(content)

    metadata = extract_metadata(text)

    # Fallbacks for critical metadata to prevent pipeline crashes
    subj = metadata.get("subject_code", "UNKNOWN_SUBJ")
    
    year_match = re.search(r'(20\d{2})', text)
    if year_match:
        year_val = str(int(year_match.group(1)) + 1)
    else:
        year_val = "UNKNOWN_YEAR"
        
    exam_type = metadata.get("exam_type", "UNKNOWN_EXAM").upper()

    paper_id = f"{subj}_{year_val}_{exam_type}"

    units = split_by_units(text)
    raw_questions = split_questions(units)
    questions = [parse_question(q) for q in raw_questions]

    return {
        "paper_id": paper_id,
        "paper_metadata": metadata,
        "questions": questions
    }
