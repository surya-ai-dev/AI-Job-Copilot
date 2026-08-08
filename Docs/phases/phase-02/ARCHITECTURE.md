# Phase 2 — Architecture

### 1. Overview
Phase 2 implements the stream ingestion layer for document files.

### 2. Component Diagram
```mermaid
graph TD
    User[User / File] --> API[Upload API]
    API --> Service[ResumeParserService]
    Service --> Parser[ResumeParserAgent]
    Parser --> PDF[pdfplumber (PDF)]
    Parser --> DOCX[python-docx (Word)]
    PDF --> Data[Structured Resume Data]
    DOCX --> Data
    Data --> Persistence[ResumeModel Database Save]
```

### 3. Data Flow
1.  **Ingestion**: Binary file stream uploaded via API.
2.  **Route Handler**: Verifies stream size limits (up to 10MB).
3.  **Parsing**: Agent extracts text using appropriate library (PDF/Word).
4.  **Persistence**: Saves metadata in `resumes` database table.

### 4. Component Responsibilities
*   `ResumeParserAgent`: Decodes stream buffers into raw text.
*   `ResumeParserService`: Manages file validation and persistence.

### 5. External Dependencies
*   `pdfplumber` (PDF metadata and text extractor).
*   `python-docx` (docx file parsing).

### 6. Database Interaction
*   Performs database insertion into the `resumes` table.
