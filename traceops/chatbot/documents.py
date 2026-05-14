from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


# Sample HR policy documents
# Intentionally includes outdated policy for failure demos

SAMPLE_DOCS = [
    Document(
        page_content="""HR POLICY v2.1 (2023) — OUTDATED

Contractor PTO Policy:
All contractors receive 20 days of paid time off per year.

Contractors may carry over up to 5 days into the following year.

Full-time employees receive 25 days.
Part-time employees are prorated.
""",
        metadata={
            "source": "hr_policy_v2.1_outdated.pdf",
            "year": 2023,
        },
    ),

    Document(
        page_content="""HR POLICY v3.0 (2024) — CURRENT

Contractor PTO Policy:
All contractors receive 10 days of paid time off per year.

This was revised downward from the 2023 policy due to budget constraints.

Contractors may not carry over any days.

Full-time employees receive 25 days.
""",
        metadata={
            "source": "hr_policy_v3.0_current.pdf",
            "year": 2024,
        },
    ),

    Document(
        page_content="""BENEFITS OVERVIEW 2024

Health Insurance:
All employees and contractors on 6-month+ engagements are eligible.

Dental: Full-time only.
Vision: Full-time only.

401k matching:
Full-time employees only.
Contractors are not eligible for 401k matching.
""",
        metadata={
            "source": "benefits_overview_2024.pdf",
            "year": 2024,
        },
    ),
]


_vectorstore = None


def get_vectorstore() -> FAISS:
    global _vectorstore

    if _vectorstore is None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
        )

        chunks = splitter.split_documents(SAMPLE_DOCS)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        _vectorstore = FAISS.from_documents(
            chunks,
            embeddings,
        )

    return _vectorstore