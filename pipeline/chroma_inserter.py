import logging
from sentence_transformers import SentenceTransformer

# Adjust this import based on your exact folder structure
from chroma.client import collection 

# Load the exact same model used in your search.py
model = SentenceTransformer("all-MiniLM-L6-v2")

def insert_into_chroma(enriched_data):
    """
    Takes the JSON from the pipeline, generates vector embeddings, 
    and inserts them into ChromaDB for semantic search.
    """
    try:
        paper_id = enriched_data["paper_id"]
        meta = enriched_data["paper_metadata"]
        
        ids = []
        documents = []
        metadatas = []
        
        # Helper function to flatten lists into strings for ChromaDB compatibility
        def flatten_list(lst):
            return ", ".join(lst) if isinstance(lst, list) else ""

        # 1. Gather all questions
        for q in enriched_data.get("questions", []):
            q_id = f"{paper_id}_{q['question_id']}"
            q_text = q.get("question_text", "").strip()
            
            # Only index questions that actually have text
            if q_text:
                ids.append(q_id)
                documents.append(q_text)
                metadatas.append({
                    "paper_id": paper_id,
                    "subject_code": meta.get("subject_code", ""),
                    "academic_year": meta.get("academic_year", ""),
                    "exam_type": meta.get("exam_type", ""),
                    "type": "question",
                    "unit": q.get("unit", "") or "UNKNOWN",
                    "ai_tags": flatten_list(q.get("ai_tags")),
                    "syllabus_topics": flatten_list(q.get("syllabus_topics"))
                })
                
            # 2. Gather all subparts as independent searchable chunks
            for sp in q.get("subparts", []):
                s_id = f"{q_id}_{sp['subpart_id']}"
                sp_text = sp.get("text", "").strip()
                
                if sp_text:
                    ids.append(s_id)
                    documents.append(sp_text)
                    metadatas.append({
                        "paper_id": paper_id,
                        "subject_code": meta.get("subject_code", ""),
                        "academic_year": meta.get("academic_year", ""),
                        "exam_type": meta.get("exam_type", ""),
                        "type": "subpart",
                        "parent_question": q["question_id"],
                        "ai_tags": flatten_list(sp.get("ai_tags")),
                        "syllabus_topics": flatten_list(sp.get("syllabus_topics"))
                    })

        # 3. Batch Encode and Insert
        if ids:
            logging.info(f"Generating embeddings for {len(ids)} items in {paper_id}...")
            # Generate all embeddings at once (much faster than a loop)
            embeddings = model.encode(documents).tolist()
            
            # Use 'upsert' instead of 'add'. If you re-process a paper, 
            # upsert updates the existing records instead of crashing.
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logging.info(f"Successfully indexed {paper_id} into ChromaDB.")
            
    except Exception as e:
        logging.error(f"Failed to insert {enriched_data.get('paper_id')} into ChromaDB: {e}")
        raise e
