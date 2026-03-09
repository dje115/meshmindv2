-- job_kind for downstream dispatch (docproc, image, etc.)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_kind worker_capability;
