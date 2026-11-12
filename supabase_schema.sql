-- ==============================================================================
-- Job-Manager Dedicated Supabase Schema
-- Target: Dedicated Supabase Project for jobs.dealos.in
-- Safe execution: Uses IF NOT EXISTS to prevent clobbering existing structures
-- ==============================================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Workspaces
CREATE TABLE IF NOT EXISTS workspaces (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO workspaces (id, created_at)
VALUES (1, NOW())
ON CONFLICT (id) DO NOTHING;

-- 3. Profiles
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL UNIQUE REFERENCES workspaces(id) ON DELETE CASCADE,
    revision INTEGER NOT NULL DEFAULT 1,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    mobile_no VARCHAR(20),
    email VARCHAR(100),
    linkedin VARCHAR(255),
    github VARCHAR(255),
    portfolio VARCHAR(255),
    preferred_template VARCHAR(50) DEFAULT 'classic',
    preset_slug VARCHAR(50) DEFAULT 'blank'
);

-- 4. Workspace Preferences
CREATE TABLE IF NOT EXISTS workspace_preferences (
    workspace_id INTEGER PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    revision INTEGER NOT NULL DEFAULT 1,
    workspace_uuid VARCHAR(32) NOT NULL DEFAULT replace(uuid_generate_v4()::text, '-', ''),
    resume_template VARCHAR(50),
    tracking_connection JSONB,
    calendar_connections JSONB NOT NULL DEFAULT '[]'::jsonb
);

-- 5. Education
CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    school_name VARCHAR(150),
    course VARCHAR(150),
    location VARCHAR(100),
    date_range VARCHAR(50),
    description TEXT
);
CREATE INDEX IF NOT EXISTS ix_education_profile_id ON education(profile_id);

-- 6. Experience
CREATE TABLE IF NOT EXISTS experience (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    job_title VARCHAR(100),
    company VARCHAR(100),
    location VARCHAR(100),
    description TEXT,
    date_range VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_experience_profile_id ON experience(profile_id);

-- 7. Projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    name VARCHAR(100),
    description TEXT,
    date_range VARCHAR(50),
    link TEXT
);
CREATE INDEX IF NOT EXISTS ix_projects_profile_id ON projects(profile_id);

-- 8. Skills Bank
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    skill_name VARCHAR(50),
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_skills_profile_id ON skills(profile_id);

-- 9. Certifications
CREATE TABLE IF NOT EXISTS certifications (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    name VARCHAR(150),
    issuer VARCHAR(150),
    date_issued VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_certifications_profile_id ON certifications(profile_id);

-- 10. Job Applications Pipeline
CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL DEFAULT 1 REFERENCES workspaces(id) ON DELETE CASCADE,
    revision INTEGER NOT NULL DEFAULT 1,
    company_name VARCHAR(150) NOT NULL,
    job_title VARCHAR(150) NOT NULL,
    job_url TEXT,
    job_source VARCHAR(250),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    short_description TEXT,
    job_description TEXT,
    pdf_data BYTEA,
    pdf_generated_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'Saved',
    date_applied DATE,
    follow_up_date DATE,
    job_type VARCHAR(50),
    location VARCHAR(150),
    salary_range VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'Medium',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    latex_source TEXT,
    cover_letter TEXT,
    template_id VARCHAR(50) NOT NULL DEFAULT 'classic',
    match_score INTEGER,
    match_analysis JSONB
);
CREATE INDEX IF NOT EXISTS ix_job_applications_user_created ON job_applications(workspace_id, created_at);
CREATE INDEX IF NOT EXISTS ix_job_applications_user_status ON job_applications(workspace_id, status);

-- 11. Assistant Conversations & Messages
CREATE TABLE IF NOT EXISTS assistant_conversations (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL DEFAULT 1 REFERENCES workspaces(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES job_applications(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'General conversation',
    active_request_key VARCHAR(80),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_assistant_user_job UNIQUE(workspace_id, job_id)
);

CREATE TABLE IF NOT EXISTS assistant_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    request_key VARCHAR(80),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_assistant_message_request UNIQUE(conversation_id, request_key)
);

CREATE TABLE IF NOT EXISTS assistant_drafts (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    type VARCHAR(40) NOT NULL,
    content TEXT NOT NULL,
    pdf_data BYTEA,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assistant_turns (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    request_key VARCHAR(80) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_assistant_turn_request UNIQUE(conversation_id, request_key)
);

-- 12. Operation Receipts & Presets
CREATE TABLE IF NOT EXISTS operation_receipts (
    request_id VARCHAR(100) PRIMARY KEY,
    fingerprint VARCHAR(64) NOT NULL,
    result JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS resume_presets (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    target_summary_prompt TEXT NOT NULL,
    core_skills_bank JSONB NOT NULL,
    metric_prompts JSONB NOT NULL,
    section_order JSONB NOT NULL,
    recommended_template VARCHAR(50) NOT NULL DEFAULT 'classic',
    lever_guidance TEXT NOT NULL
);

-- 13. Supabase Storage: Create 'resumes' Bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS policy allowing public read access to uploaded resumes
CREATE POLICY "Public Resume Access" ON storage.objects
FOR SELECT USING (bucket_id = 'resumes');

-- Storage RLS policy allowing authenticated / service_role uploads
CREATE POLICY "Allow Resume Uploads" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'resumes');
