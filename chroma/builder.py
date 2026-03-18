from sentence_transformers import SentenceTransformer
from chroma.client import collection

model = SentenceTransformer("all-MiniLM-L6-v2")


def safe_join(items):
    return " ".join(str(i) for i in items if i) if items else ""


def build_embedding_text(subject, unit, text, tags, topics, marks):
    tag_text = safe_join(tags)
    topic_text = safe_join(topics)

    return (
        f"Subject: {subject}. "
        f"Unit: {unit}. "
        f"Marks: {marks}. "
        f"Question: {text}. "
        f"Concepts: {tag_text}. {tag_text}. "
        f"Syllabus: {topic_text}. {topic_text}."
    )


def insert_exam_to_chroma(data):

    paper_id = data.get("paper_id")
    meta = data.get("paper_metadata", {})

    subject = meta.get("subject_name")
    semester = meta.get("semester")
    exam_type = meta.get("exam_type")
    department = meta.get("department")
    academic_year = meta.get("academic_year")

    documents = []
    metadatas = []
    ids = []

    for q in data.get("questions", []):

        q_id = q.get("id")
        q_text = q.get("question_text")
        unit = q.get("unit")

        subparts = q.get("subparts", [])

        # -------- QUESTION --------
        if not subparts:

            doc = build_embedding_text(
                subject, unit, q_text,
                q.get("ai_tags"), q.get("syllabus_topics"),
                q.get("marks")
            )

            documents.append(doc)
            ids.append(q_id)

            metadatas.append({
                "paper_id": paper_id,
                "type": "question",
                "subject_name": subject,
                "semester": semester,
                "exam_type": exam_type,
                "department": department,
                "academic_year": academic_year,
                "unit": unit
            })

        # -------- SUBPARTS --------
        else:
            for sp in subparts:

                sp_id = sp.get("id")
                sp_text = sp.get("text")

                doc = build_embedding_text(
                    subject, unit, sp_text,
                    sp.get("ai_tags"), sp.get("syllabus_topics"),
                    sp.get("marks")
                )

                documents.append(doc)
                ids.append(sp_id)

                metadatas.append({
                    "paper_id": paper_id,
                    "type": "subpart",
                    "subject_name": subject,
                    "semester": semester,
                    "exam_type": exam_type,
                    "department": department,
                    "academic_year": academic_year,
                    "unit": unit
                })

    # Single batch insert
    embeddings = model.encode(documents).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Inserted {len(ids)} vectors into Chroma")
