import re


# =========================
# HELPERS
# =========================

def content_to_text(content):
    """
    Convert structured content → text for regex parsing.
    Tables are flattened carefully.
    """
    lines = []

    for block in content:

        if block["type"] == "paragraph":
            lines.append(block["text"])

        elif block["type"] == "table":
            for row in block["rows"]:
                row_text = " | ".join(cell for cell in row if cell)
                if row_text.strip():
                    lines.append(row_text)

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

    for line in text.split("\n"):

        line = line.strip()
        if not line:
            continue

        upper = line.upper()

        if upper.startswith("UNIT"):
            parts = upper.split()
            if len(parts) >= 2:
                current_unit = f"UNIT {parts[1]}"
                units.setdefault(current_unit, [])
            continue

        units.setdefault(current_unit, []).append(line)

    return units


# =========================
# QUESTION SPLITTING
# =========================

def split_questions(units):

    questions = []

    for unit, lines in units.items():

        current_qid = None
        buffer = []

        for line in lines:

            if re.match(r'^Q\d+', line):

                if current_qid:
                    questions.append({
                        "question_id": current_qid,
                        "unit": unit,
                        "raw_text": " ".join(buffer).strip()
                    })

                parts = line.split(maxsplit=1)
                current_qid = parts[0]
                buffer = [parts[1]] if len(parts) > 1 else []

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
# QUESTION PARSING
# =========================

def parse_question(q):

    raw = q["raw_text"]
    marks = None

    # -------- MARKS --------
    for m in re.findall(r'\(([^)]*)\)', raw):
        expr = m.replace(" ", "")
        try:
            if '=' in expr:
                marks = float(expr.split('=')[-1])
            elif '+' in expr or '*' in expr:
                marks = float(eval(expr))
            elif expr.isdigit():
                marks = float(expr)
            if marks:
                break
        except:
            pass

    # -------- SUBPARTS --------
    subparts = []
    sub_match = re.search(r'(^|\s)([a-h])\)', raw)

    if sub_match:

        subs = list(re.finditer(
            r'(^|\s)([a-h])\)\s*(.*?)(?=(\s[a-h]\)|$))',
            raw,
            re.S
        ))

        per = marks / len(subs) if marks else None

        for sp in subs:
            text = re.sub(r'\([^)]*\)|CO\d+', '', sp.group(3))
            text = re.sub(r'\s+', ' ', text).strip()

            subparts.append({
                "subpart_id": sp.group(2),
                "text": text,
                "marks": per
            })

        question_text = "Attempt all parts."

    else:
        clean = re.sub(r'\([^)]*\)|CO\d+', '', raw)
        question_text = re.sub(r'\s+', ' ', clean).strip()

    return {
        "question_id": q["question_id"],
        "unit": q["unit"],
        "question_text": question_text,
        "marks": marks,
        "subparts": subparts
    }


# =========================
# MAIN FUNCTION
# =========================

def parse_exam(extracted_data):
    """
    INPUT: ingestion output
    OUTPUT: structured JSON (ready for AI tagging)
    """

    content = extracted_data["content"]

    text = content_to_text(content)

    metadata = extract_metadata(text)

    if "subject_code" not in metadata:
        raise ValueError("Missing subject_code")

    year_match = re.search(r'(20\d{2})', text)
    if not year_match:
        raise ValueError("Missing year")

    paper_id = (
        metadata["subject_code"]
        + "_"
        + str(int(year_match.group(1)) + 1)
        + "_"
        + metadata.get("exam_type", "UNKNOWN").upper()
    )

    units = split_by_units(text)
    raw_questions = split_questions(units)
    questions = [parse_question(q) for q in raw_questions]

    return {
        "paper_id": paper_id,
        "paper_metadata": metadata,
        "questions": questions
    }
