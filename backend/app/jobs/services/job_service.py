# backend/app/jobs/services/job_service.py
# Application Service Layer orchestrating ingestion, scrapers, OCR, & unified schema parsing

import uuid
import re
from datetime import datetime
from typing import List, Optional
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.domain.job import Job, JobSource, ParsedJob
from backend.app.jobs.models.job_model import JobModel
from backend.app.shared.exceptions import ValidationException, NotFoundException, BusinessRuleException

class JobService:
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def ingest_job_from_url(self, user_id: uuid.UUID, url: str) -> JobModel:
        """Ingest and scrape job description from URLs."""
        # 1. Basic URL validation check
        if not url.startswith("http"):
            raise ValidationException("Invalid URL schema.")

        # 2. Simulate Playwright scraper output for MVP
        # In a real system, this runs Playwright to scrape page content
        company = "TargetCompany"
        title = "Staff Software Engineer"
        description = f"Scraped job posting from {url}. Required: Python, System Design, 8+ years experience."
        location = "Remote, US"
        recruiter_email = "hiring@targetcompany.com"

        # Check for specific domains for mock details
        if "linkedin.com" in url:
            company = "LinkedIn Client"
            title = "Senior Backend Engineer"
        elif "greenhouse.io" in url:
            company = "Greenhouse Client"

        source = JobSource(source_type="url", source_url=url)
        parsed_data = ParsedJob(
            company_name=company,
            job_title=title,
            description=description,
            recruiter_email=recruiter_email,
            location=location
        )
        
        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=description
        )

        return await self.job_repo.create_job(domain_job)

    async def ingest_job_from_text(self, user_id: uuid.UUID, raw_text: str) -> JobModel:
        """Ingest job description from plain text pastes."""
        if not raw_text.strip():
            raise ValidationException("Ingest payload text must not be empty.")

        # Parse company and title using simple regex patterns or splits
        # Format expectation: "Company: [Name]\nRole: [Title]\n[Description]"
        company = "Unknown Company"
        title = "Unknown Role"
        
        company_match = re.search(r"Company:\s*(.*)", raw_text, re.IGNORECASE)
        if company_match:
            company = company_match.group(1).strip()
            
        role_match = re.search(r"(Role|Title):\s*(.*)", raw_text, re.IGNORECASE)
        if role_match:
            title = role_match.group(2).strip()

        # Fallback to lines if no keys match
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if len(lines) >= 2 and (company == "Unknown Company" or title == "Unknown Role"):
            company = lines[0]
            title = lines[1]

        source = JobSource(source_type="text")
        parsed_data = ParsedJob(
            company_name=company,
            job_title=title,
            description=raw_text
        )

        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=raw_text
        )

        return await self.job_repo.create_job(domain_job)

    async def ingest_job_from_pdf(self, user_id: uuid.UUID, file_name: str, file_content: bytes) -> JobModel:
        """Ingest job description from PDF file attachments."""
        if len(file_content) == 0:
            raise ValidationException("PDF file content is empty.")

        # Simulate PDF text extraction (e.g. using pdfplumber)
        extracted_text = f"Parsed PDF Document: {file_name}\nCompany: PDF Group\nRole: Python Lead\nRequirements: 5+ years, FastAPI."
        
        source = JobSource(source_type="pdf")
        parsed_data = ParsedJob(
            company_name="PDF Group",
            job_title="Python Lead",
            description=extracted_text
        )

        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=extracted_text
        )

        return await self.job_repo.create_job(domain_job)

    async def ingest_job_from_image(self, user_id: uuid.UUID, file_name: str, file_content: bytes) -> JobModel:
        """Ingest job description from screenshots using OCR engines."""
        if len(file_content) == 0:
            raise ValidationException("Image file content is empty.")

        # Simulate Tesseract OCR output
        ocr_text = f"Parsed OCR Screenshot: {file_name}\nCompany: Screenshot Corp\nRole: Design Engineer\nRequirements: CSS, Figma."

        source = JobSource(source_type="image")
        parsed_data = ParsedJob(
            company_name="Screenshot Corp",
            job_title="Design Engineer",
            description=ocr_text
        )

        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=ocr_text
        )

        return await self.job_repo.create_job(domain_job)

    async def ingest_job_from_email(self, user_id: uuid.UUID, subject: str, body: str) -> JobModel:
        """Ingest job details from recruiter emails."""
        if not body.strip():
            raise ValidationException("Email body content must not be empty.")

        # Extract contact information
        recruiter_email = "recruiter@jobemail.com"
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", body)
        if email_match:
            recruiter_email = email_match.group(0)

        source = JobSource(source_type="email")
        parsed_data = ParsedJob(
            company_name="Email Recruiter",
            job_title=subject or "Job Opportunity",
            description=body,
            recruiter_email=recruiter_email
        )

        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=f"Subject: {subject}\n\n{body}"
        )

        return await self.job_repo.create_job(domain_job)

    async def ingest_job_from_whatsapp(self, user_id: uuid.UUID, message: str) -> JobModel:
        """Ingest job details from WhatsApp messages."""
        if not message.strip():
            raise ValidationException("WhatsApp message body must not be empty.")

        source = JobSource(source_type="whatsapp")
        parsed_data = ParsedJob(
            company_name="WhatsApp Referral",
            job_title="Referral Role",
            description=message
        )

        domain_job = Job(
            user_id=user_id,
            source=source,
            parsed_data=parsed_data,
            raw_content=message
        )

        return await self.job_repo.create_job(domain_job)

    async def get_job_details(self, user_id: uuid.UUID, job_id: uuid.UUID) -> JobModel:
        """Retrieve parsed job details."""
        db_job = await self.job_repo.get_by_id(job_id)
        if not db_job or db_job.user_id != user_id:
            raise NotFoundException("Job posting record not found.", "JOB_NOT_FOUND")
        return db_job

    async def list_user_jobs(self, user_id: uuid.UUID) -> List[JobModel]:
        """List all parsed jobs for a user."""
        return await self.job_repo.list_jobs(user_id)

    async def delete_user_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
        """Remove parsed job posting from database logs."""
        db_job = await self.job_repo.get_by_id(job_id)
        if not db_job or db_job.user_id != user_id:
            raise NotFoundException("Job posting record not found.", "JOB_NOT_FOUND")
        await self.job_repo.delete_job(db_job)
