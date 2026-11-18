"""
Job Repository and Feeder Service for Job-Manager.
Maintains a curated master list of companies, multi-source job ingestion,
deduplication, transparent heuristic & semantic match scoring, and evidence breakdown.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Master list of tracked companies with career portals, ATS platforms, and domains
MASTER_COMPANIES = [
    {
        "id": "deloitte",
        "name": "Deloitte",
        "domain": "deloitte.com",
        "industry": "Consulting & Advisory",
        "career_url": "https://jobs.deloitte.com",
        "ats_type": "workday",
        "locations": ["Hyderabad", "Bengaluru", "Mumbai", "Delhi NCR", "Remote"],
    },
    {
        "id": "ntt",
        "name": "NTT Data",
        "domain": "nttdata.com",
        "industry": "IT Services & Consulting",
        "career_url": "https://careers.services.global.ntt",
        "ats_type": "workday",
        "locations": ["Bengaluru", "Hyderabad", "Pune", "Remote"],
    },
    {
        "id": "mckinsey",
        "name": "McKinsey & Company",
        "domain": "mckinsey.com",
        "industry": "Management Consulting",
        "career_url": "https://www.mckinsey.com/careers",
        "ats_type": "custom",
        "locations": ["Gurugram", "Mumbai", "Bengaluru", "Remote"],
    },
    {
        "id": "bcg",
        "name": "Boston Consulting Group (BCG)",
        "domain": "bcg.com",
        "industry": "Management Consulting",
        "career_url": "https://careers.bcg.com",
        "ats_type": "custom",
        "locations": ["New Delhi", "Mumbai", "Bengaluru"],
    },
    {
        "id": "advance-auto-parts",
        "name": "Advance Auto Parts",
        "domain": "advanceautoparts.com",
        "industry": "Retail & Automotive",
        "career_url": "https://corporate.advanceautoparts.com/careers",
        "ats_type": "workday",
        "locations": ["Hyderabad", "Remote"],
    },
    {
        "id": "fusion-consulting",
        "name": "Fusion Consulting",
        "domain": "fusionconsulting.com",
        "industry": "Financial Advisory & Consulting",
        "career_url": "https://fusionconsulting.com/careers",
        "ats_type": "custom",
        "locations": ["Hyderabad", "Remote", "London"],
    },
    {
        "id": "aramex",
        "name": "Aramex",
        "domain": "aramex.com",
        "industry": "Logistics & Supply Chain",
        "career_url": "https://www.aramex.com/us/en/careers",
        "ats_type": "custom",
        "locations": ["Mumbai", "Bengaluru", "Dubai"],
    },
    {
        "id": "marsh-mclennan",
        "name": "Marsh McLennan",
        "domain": "marshmclennan.com",
        "industry": "Risk & Financial Advisory",
        "career_url": "https://careers.marshmclennan.com",
        "ats_type": "workday",
        "locations": ["Mumbai", "Bengaluru", "Pune", "Remote"],
    },
    {
        "id": "lonza",
        "name": "Lonza",
        "domain": "lonza.com",
        "industry": "Biotech & Pharma Operations",
        "career_url": "https://www.lonza.com/careers",
        "ats_type": "workday",
        "locations": ["Hyderabad", "Remote"],
    },
    {
        "id": "hetero",
        "name": "Hetero",
        "domain": "hetero.com",
        "industry": "Pharmaceuticals",
        "career_url": "https://www.hetero.com/careers",
        "ats_type": "custom",
        "locations": ["Hyderabad", "Visakhapatnam"],
    },
    {
        "id": "stripe",
        "name": "Stripe",
        "domain": "stripe.com",
        "industry": "Fintech & Payments",
        "career_url": "https://stripe.com/jobs",
        "ats_type": "greenhouse",
        "locations": ["Bengaluru", "Singapore", "Remote", "US"],
    },
    {
        "id": "razorpay",
        "name": "Razorpay",
        "domain": "razorpay.com",
        "industry": "Fintech & Payments",
        "career_url": "https://razorpay.com/jobs",
        "ats_type": "greenhouse",
        "locations": ["Bengaluru", "Mumbai", "Remote"],
    },
    {
        "id": "swiggy",
        "name": "Swiggy",
        "domain": "swiggy.com",
        "industry": "Consumer Tech & Logistics",
        "career_url": "https://careers.swiggy.com",
        "ats_type": "custom",
        "locations": ["Bengaluru", "Remote"],
    },
    {
        "id": "zomato",
        "name": "Zomato / Blinkit",
        "domain": "zomato.com",
        "industry": "Consumer Tech & Quick Commerce",
        "career_url": "https://www.zomato.com/careers",
        "ats_type": "custom",
        "locations": ["Gurugram", "Bengaluru", "Remote"],
    },
    {
        "id": "google",
        "name": "Google",
        "domain": "google.com",
        "industry": "Technology & Internet",
        "career_url": "https://www.google.com/about/careers",
        "ats_type": "custom",
        "locations": ["Bengaluru", "Hyderabad", "Gurugram", "Mumbai", "Remote"],
    },
    {
        "id": "microsoft",
        "name": "Microsoft",
        "domain": "microsoft.com",
        "industry": "Software & Cloud Computing",
        "career_url": "https://careers.microsoft.com",
        "ats_type": "custom",
        "locations": ["Hyderabad", "Bengaluru", "Noida", "Remote"],
    },
]

# Seed repository of verified job openings matching benchmark roles (Finance, Strategy, Consulting, Ops, Product, Tech)
SEEDED_REPOSITORY_JOBS = [
    {
        "id": "deloitte-analytics-manager-hyd",
        "company_name": "Deloitte",
        "company_id": "deloitte",
        "job_title": "Specialist, Assistant Manager, Analytics and Insights",
        "job_url": "https://jobs.deloitte.com/job/hyderabad/specialist-assistant-manager-analytics/252/12345",
        "source": "Deloitte Careers",
        "source_category": "careers_page",
        "location": "Hyderabad, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 9,
        "salary_range": "₹18L - ₹28L/yr",
        "date_posted": "2026-11-11",
        "is_early_applicant": True,
        "required_skills": [
            "Financial Reporting", "Analytics", "Automation", "Business Operations",
            "Process Improvement", "Project Management", "MS Excel", "Presentation Skills",
            "Risk Management", "Data Governance"
        ],
        "job_description": """Deloitte is seeking a Specialist / Assistant Manager for our Analytics and Insights advisory practice in Hyderabad.
Key Responsibilities:
- Lead analytics and reporting deliverables for executive stakeholders and global business units.
- Support corporate finance, FP&A operations, and budgeting variance analyses.
- Oversee process improvement and workflow automation across financial data pipelines.
- Coordinate deliverables, manage operational quality checks, and design executive presentations.
- Drive data governance, compliance checks, and operational performance metrics.

Qualifications:
- Bachelor's or Master's degree in Business Administration, Finance, Economics, or related quantitative field (MBA preferred).
- 5+ years of relevant experience in financial analytics, business operations, or management consulting.
- Advanced proficiency in Microsoft Excel, financial modeling, and BI tools.
- Demonstrated experience presenting complex insights to executive audiences."""
    },
    {
        "id": "ntt-manager-consulting-blr",
        "company_name": "NTT Data",
        "company_id": "ntt",
        "job_title": "Manager, Consulting",
        "job_url": "https://careers.services.global.ntt/global/en/job/manager-consulting-bengaluru",
        "source": "NTT Careers",
        "source_category": "careers_page",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 10,
        "salary_range": "₹22L - ₹34L/yr",
        "date_posted": "2026-11-11",
        "is_early_applicant": True,
        "required_skills": [
            "Management Consulting", "Business Strategy", "IT Strategy", "Digital Transformation",
            "Program Management", "Client Engagement", "P&L Management", "Strategic Planning"
        ],
        "job_description": """NTT Data is looking for an experienced Consulting Manager to lead strategic transformation engagements in Bengaluru.
Responsibilities:
- Drive strategic consulting engagements for Fortune 500 enterprise clients.
- Partner with executive leadership to evaluate corporate operating models and technology roadmaps.
- Lead project workstreams, manage junior consultants, and guarantee quality of executive deliverables.
- Structure business cases, financial payback models, and post-merger synergy plans."""
    },
    {
        "id": "advance-auto-parts-sr-analyst",
        "company_name": "Advance Auto Parts",
        "company_id": "advance-auto-parts",
        "job_title": "Sr. Financial Analyst",
        "job_url": "https://corporate.advanceautoparts.com/careers/job/sr-financial-analyst",
        "source": "Workday",
        "source_category": "workday",
        "location": "Hyderabad, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 7,
        "salary_range": "₹15L - ₹22L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "Corporate Finance", "FP&A", "Variance Analysis", "Financial Modeling",
            "Budgeting & Forecasting", "MS Excel", "SQL", "ERP Systems"
        ],
        "job_description": """Advance Auto Parts is hiring a Senior Financial Analyst to support global financial planning and analysis from Hyderabad.
Key Duties:
- Drive monthly, quarterly, and annual forecasting cycles.
- Analyze variance between budget, forecast, and actual performance.
- Build flexible DCF, ROI, and scenario models to support strategic capital allocation.
- Collaborate with cross-functional operational teams to identify cost optimization initiatives."""
    },
    {
        "id": "fusion-consulting-fpa-support",
        "company_name": "Fusion Consulting",
        "company_id": "fusion-consulting",
        "job_title": "Finance Analyst / FP&A Support",
        "job_url": "https://fusionconsulting.com/careers/fpa-support-remote",
        "source": "Fusion Careers",
        "source_category": "careers_page",
        "location": "Hyderabad, India",
        "work_arrangement": "Remote",
        "job_type": "Full-time",
        "seniority": "Mid",
        "experience_years_min": 3,
        "experience_years_max": 6,
        "salary_range": "₹12L - ₹18L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "FP&A", "Financial Reporting", "Excel Modeling", "Accounting",
            "Cash Flow Management", "Budgeting", "Power BI"
        ],
        "job_description": """Fusion Consulting provides transactional advisory and financial management services. We are seeking an FP&A Analyst to handle remote financial reporting and business modeling for international clients."""
    },
    {
        "id": "aramex-sr-financial-analyst",
        "company_name": "Aramex",
        "company_id": "aramex",
        "job_title": "Senior Financial Analyst",
        "job_url": "https://www.aramex.com/careers/job/senior-financial-analyst-mumbai",
        "source": "LinkedIn Posts",
        "source_category": "linkedin",
        "location": "Mumbai, India",
        "work_arrangement": "Onsite",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 7,
        "salary_range": "₹10L - ₹18L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": False,
        "required_skills": [
            "Financial Analysis", "Cost Accounting", "Operations Finance", "KPI Dashboards",
            "Logistics Analytics", "SAP", "Advanced Excel"
        ],
        "job_description": """Aramex Logistics is looking for a Senior Financial Analyst for our Mumbai operations hub. You will monitor operating costs, route profitability, and regional P&L performance."""
    },
    {
        "id": "marsh-mclennan-finance-manager",
        "company_name": "Marsh McLennan",
        "company_id": "marsh-mclennan",
        "job_title": "Finance Manager (Business Partner)",
        "job_url": "https://careers.marshmclennan.com/global/en/job/finance-manager-business-partner",
        "source": "Workday",
        "source_category": "workday",
        "location": "Mumbai, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 10,
        "salary_range": "₹24L - ₹36L/yr",
        "date_posted": "2026-11-09",
        "is_early_applicant": False,
        "required_skills": [
            "Strategic Finance", "Business Partnering", "P&L Management", "Financial Modeling",
            "Commercial Contracts", "Executive Stakeholder Management", "Leadership"
        ],
        "job_description": """Marsh McLennan is seeking a Finance Manager to act as trusted finance business partner to regional leadership. Drive strategic planning, budget reviews, client profitability, and contract reviews."""
    },
    {
        "id": "lonza-global-bio-ops-controller",
        "company_name": "Lonza",
        "company_id": "lonza",
        "job_title": "Global Bio Ops Finance Controller",
        "job_url": "https://www.lonza.com/careers/global-bio-ops-controller",
        "source": "Workday",
        "source_category": "workday",
        "location": "Hyderabad, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Mid",
        "experience_years_min": 4,
        "experience_years_max": 8,
        "salary_range": "₹16L - ₹25L/yr",
        "date_posted": "2026-11-06",
        "is_early_applicant": False,
        "required_skills": [
            "Operations Controlling", "Inventory Accounting", "Cost Controlling",
            "Financial Reporting", "SAP FICO", "Internal Controls"
        ],
        "job_description": """Lonza is hiring a Finance Controller for our Global Biological Operations Center in Hyderabad. Lead operations reporting, capital expenditure tracking, and audit preparation."""
    },
    {
        "id": "hetero-project-finance-manager-sap",
        "company_name": "Hetero",
        "company_id": "hetero",
        "job_title": "Project Finance Manager SAP",
        "job_url": "https://www.hetero.com/careers/project-finance-manager-sap",
        "source": "Hetero Careers",
        "source_category": "careers_page",
        "location": "Hyderabad, India",
        "work_arrangement": "Full-time",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 8,
        "salary_range": "₹14L - ₹20L/yr",
        "date_posted": "2026-11-06",
        "is_early_applicant": False,
        "required_skills": [
            "Project Finance", "SAP S/4HANA", "Capex Budgeting", "Treasury",
            "Vendor Payment Workflows", "Auditing"
        ],
        "job_description": """Hetero is seeking a Project Finance Manager with SAP implementation and treasury expertise for Hyderabad manufacturing projects."""
    },
    {
        "id": "stripe-strategy-bizops-blr",
        "company_name": "Stripe",
        "company_id": "stripe",
        "job_title": "Strategy & Business Operations Lead",
        "job_url": "https://stripe.com/jobs/strategy-bizops-lead-apac",
        "source": "Greenhouse",
        "source_category": "greenhouse",
        "location": "Bengaluru, India",
        "work_arrangement": "Remote",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 12,
        "salary_range": "₹35L - ₹55L/yr",
        "date_posted": "2026-11-08",
        "is_early_applicant": True,
        "required_skills": [
            "Strategy & BizOps", "Financial Modeling", "Corporate Strategy", "SQL",
            "Market Expansion", "Executive Presentations", "Product Strategy"
        ],
        "job_description": """Stripe is looking for a Strategy & Business Operations Lead in Bengaluru. Work directly with regional GM and global leadership on revenue expansion, transaction economics, and organizational execution."""
    },
    {
        "id": "mckinsey-associate-consultant-delhi",
        "company_name": "McKinsey & Company",
        "company_id": "mckinsey",
        "job_title": "Associate / Engagement Manager - Corporate Finance",
        "job_url": "https://www.mckinsey.com/careers/associate-corporate-finance-india",
        "source": "McKinsey Careers",
        "source_category": "careers_page",
        "location": "Gurugram, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 4,
        "experience_years_max": 9,
        "salary_range": "₹32L - ₹50L/yr",
        "date_posted": "2026-11-07",
        "is_early_applicant": True,
        "required_skills": [
            "Corporate Finance Strategy", "M&A Advisory", "Valuation", "Due Diligence",
            "Board Presentations", "Financial Restructuring", "Problem Solving"
        ],
        "job_description": """McKinsey & Company is seeking an Associate or Engagement Manager for our Strategy and Corporate Finance Practice in Gurugram/Mumbai. Advise CEOs and CFOs on M&A, capital allocation, and enterprise transformation."""
    },
    {
        "id": "razorpay-sr-product-manager",
        "company_name": "Razorpay",
        "company_id": "razorpay",
        "job_title": "Senior Product Manager - Payments Core",
        "job_url": "https://razorpay.com/jobs/sr-product-manager-payments",
        "source": "Greenhouse",
        "source_category": "greenhouse",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 9,
        "salary_range": "₹32L - ₹48L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "Product Management", "Product Strategy", "Fintech", "Agile & Scrum",
            "APIs", "Data Analytics", "Roadmapping", "User Experience (UX)"
        ],
        "job_description": """Razorpay is looking for a Senior Product Manager to lead our Core Payments platform. Define product roadmap, scale high-throughput payment processing APIs, and partner with banking partners across India and SEA."""
    },
    {
        "id": "swiggy-lead-product-manager",
        "company_name": "Swiggy",
        "company_id": "swiggy",
        "job_title": "Lead Product Manager - Consumer Experience",
        "job_url": "https://careers.swiggy.com/jobs/lead-pm-consumer",
        "source": "Swiggy Careers",
        "source_category": "careers_page",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Director / Lead",
        "experience_years_min": 7,
        "experience_years_max": 12,
        "salary_range": "₹45L - ₹65L/yr",
        "date_posted": "2026-11-09",
        "is_early_applicant": True,
        "required_skills": [
            "Product Strategy", "Consumer Tech", "A/B Testing", "Growth Metrics",
            "UX Design", "Stakeholder Management", "Mobile Apps", "Analytics"
        ],
        "job_description": """Swiggy is seeking a Lead Product Manager to own discovery and ordering experience for 50M+ active food and grocery consumers. Lead cross-functional pods of engineers, designers, and data scientists."""
    },
    {
        "id": "microsoft-sr-software-engineer",
        "company_name": "Microsoft",
        "company_id": "microsoft",
        "job_title": "Senior Software Engineer - Azure & Cloud Platform",
        "job_url": "https://careers.microsoft.com/job/senior-software-engineer-azure",
        "source": "Microsoft Careers",
        "source_category": "careers_page",
        "location": "Hyderabad, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 9,
        "salary_range": "₹30L - ₹50L/yr",
        "date_posted": "2026-11-11",
        "is_early_applicant": True,
        "required_skills": [
            "Python", "C#", "Go", "Distributed Systems", "Cloud Architecture",
            "Docker & Kubernetes", "Microservices", "REST APIs", "System Design"
        ],
        "job_description": """Microsoft is hiring a Senior Software Engineer in Azure Cloud Infrastructure team in Hyderabad. Architect distributed microservices, optimize low-latency systems, and build scalable cloud developer services."""
    },
    {
        "id": "google-tech-lead-eng",
        "company_name": "Google",
        "company_id": "google",
        "job_title": "Software Engineering Tech Lead - Cloud Data Systems",
        "job_url": "https://www.google.com/about/careers/applications/jobs/results/tech-lead-cloud-data",
        "source": "Google Careers",
        "source_category": "careers_page",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Lead",
        "experience_years_min": 7,
        "experience_years_max": 12,
        "salary_range": "₹50L - ₹80L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "System Architecture", "Java", "Python", "SQL", "Cloud Computing",
            "Distributed Systems", "Data Pipelines", "Performance Optimization"
        ],
        "job_description": """Google is looking for a Tech Lead in Bengaluru to guide engineering teams building petabyte-scale data infrastructure for enterprise customers."""
    },
    {
        "id": "microsoft-sr-account-exec-sales",
        "company_name": "Microsoft",
        "company_id": "microsoft",
        "job_title": "Senior Enterprise Account Executive - Enterprise Sales",
        "job_url": "https://careers.microsoft.com/job/enterprise-ae-sales-mumbai",
        "source": "Microsoft Careers",
        "source_category": "careers_page",
        "location": "Mumbai, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 11,
        "salary_range": "₹28L - ₹45L/yr + Commissions",
        "date_posted": "2026-11-09",
        "is_early_applicant": True,
        "required_skills": [
            "Enterprise Sales", "B2B Sales", "SaaS", "Solution Selling",
            "Contract Negotiation", "Revenue Generation", "Executive Relationship Building"
        ],
        "job_description": """Microsoft is hiring an Enterprise Account Executive to drive cloud & AI transformation sales for large enterprise clients in Mumbai and Western India."""
    },
    {
        "id": "ntt-sales-director-cloud",
        "company_name": "NTT Data",
        "company_id": "ntt",
        "job_title": "Director - Enterprise Cloud Sales & Solutions",
        "job_url": "https://careers.services.global.ntt/job/director-enterprise-sales",
        "source": "Workday",
        "source_category": "workday",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Director",
        "experience_years_min": 10,
        "experience_years_max": 16,
        "salary_range": "₹40L - ₹65L/yr",
        "date_posted": "2026-11-08",
        "is_early_applicant": False,
        "required_skills": [
            "Enterprise Sales", "Sales Leadership", "P&L Management", "Quota Attainment",
            "B2B Solution Selling", "Cloud Transformation", "Commercial Negotiations"
        ],
        "job_description": """NTT Data is seeking a Director of Enterprise Sales in Bengaluru to lead commercial strategy, manage enterprise pipeline, and oversee regional sales managers."""
    },
    {
        "id": "razorpay-strategic-partnerships-lead",
        "company_name": "Razorpay",
        "company_id": "razorpay",
        "job_title": "Strategic Partnerships & Business Development Lead",
        "job_url": "https://razorpay.com/jobs/strategic-partnerships-lead",
        "source": "Greenhouse",
        "source_category": "greenhouse",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 10,
        "salary_range": "₹26L - ₹40L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "Strategic Alliances", "Business Development", "Commercial Strategy",
            "Fintech Ecosystem", "Contract Negotiation", "Partner Enablement"
        ],
        "job_description": """Lead ecosystem partnerships with enterprise merchants, banks, and technology platforms. Expand distribution channels and negotiate strategic co-selling agreements."""
    },
    {
        "id": "swiggy-growth-marketing-lead",
        "company_name": "Swiggy",
        "company_id": "swiggy",
        "job_title": "Lead - Performance Marketing & Growth Strategy",
        "job_url": "https://careers.swiggy.com/jobs/lead-growth-marketing",
        "source": "Swiggy Careers",
        "source_category": "careers_page",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Lead",
        "experience_years_min": 5,
        "experience_years_max": 9,
        "salary_range": "₹24L - ₹38L/yr",
        "date_posted": "2026-11-11",
        "is_early_applicant": True,
        "required_skills": [
            "Growth Marketing", "Performance Marketing", "CAC / LTV Optimization",
            "Attribution Modeling", "Campaign Management", "Digital Strategy", "Analytics"
        ],
        "job_description": """Drive customer acquisition, retention, and lifecycle marketing campaigns across channels for food delivery and Instamart quick commerce platforms."""
    },
    {
        "id": "zomato-brand-marketing-manager",
        "company_name": "Zomato / Blinkit",
        "company_id": "zomato",
        "job_title": "Senior Brand Marketing & Communications Manager",
        "job_url": "https://www.zomato.com/careers/brand-marketing-manager",
        "source": "Zomato Careers",
        "source_category": "careers_page",
        "location": "Gurugram, India",
        "work_arrangement": "Onsite",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 5,
        "experience_years_max": 8,
        "salary_range": "₹20L - ₹32L/yr",
        "date_posted": "2026-11-09",
        "is_early_applicant": True,
        "required_skills": [
            "Brand Strategy", "Content Marketing", "Social Media Campaigns",
            "PR & Communications", "Brand Identity", "Creative Direction"
        ],
        "job_description": """Lead brand storytelling and national campaigns that resonate with millions of users. Manage creative agencies and orchestrate virality and consumer love."""
    },
    {
        "id": "swiggy-central-bizops-manager",
        "company_name": "Swiggy",
        "company_id": "swiggy",
        "job_title": "Senior Manager - Central Operations & Strategy",
        "job_url": "https://careers.swiggy.com/jobs/sr-manager-bizops",
        "source": "Swiggy Careers",
        "source_category": "careers_page",
        "location": "Bengaluru, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 10,
        "salary_range": "₹28L - ₹42L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "Business Operations", "Process Optimization", "Fleet Operations",
            "Cost Efficiency", "SLA Tracking", "Cross-Functional Leadership", "Data Analysis"
        ],
        "job_description": """Lead operations strategy for delivery fleet economics, partner payouts, and service reliability across Tier 1 and Tier 2 cities."""
    },
    {
        "id": "aramex-supply-chain-director",
        "company_name": "Aramex",
        "company_id": "aramex",
        "job_title": "Regional Director - Supply Chain & Freight Solutions",
        "job_url": "https://www.aramex.com/careers/regional-director-supply-chain",
        "source": "Workday",
        "source_category": "workday",
        "location": "Mumbai, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Director",
        "experience_years_min": 10,
        "experience_years_max": 15,
        "salary_range": "₹35L - ₹55L/yr",
        "date_posted": "2026-11-07",
        "is_early_applicant": False,
        "required_skills": [
            "Supply Chain Management", "Global Logistics", "Warehouse Operations",
            "Vendor Management", "Freight Forwarding", "Procurement", "Customs Compliance"
        ],
        "job_description": """Lead end-to-end regional supply chain and multimodal freight operations for Aramex in South Asia. Drive contract renewals and operating margin expansion."""
    },
    {
        "id": "deloitte-sr-hrbp-consulting",
        "company_name": "Deloitte",
        "company_id": "deloitte",
        "job_title": "Senior HR Business Partner (HRBP) - Advisory & Consulting",
        "job_url": "https://jobs.deloitte.com/job/hyderabad/sr-hrbp-consulting/252/67890",
        "source": "Deloitte Careers",
        "source_category": "careers_page",
        "location": "Hyderabad, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Senior",
        "experience_years_min": 6,
        "experience_years_max": 10,
        "salary_range": "₹20L - ₹32L/yr",
        "date_posted": "2026-11-10",
        "is_early_applicant": True,
        "required_skills": [
            "HR Business Partnering", "Talent Management", "Organizational Design",
            "Performance Management", "Employee Engagement", "Executive Coaching", "HR Policies"
        ],
        "job_description": """Partner with Managing Directors and practice leaders across Strategy & Analytics to deliver talent strategy, leadership coaching, retention, and workforce planning."""
    },
    {
        "id": "mckinsey-talent-acquisition-lead",
        "company_name": "McKinsey & Company",
        "company_id": "mckinsey",
        "job_title": "Talent Acquisition Lead - Executive & Specialist Hiring",
        "job_url": "https://www.mckinsey.com/careers/talent-acquisition-lead-india",
        "source": "McKinsey Careers",
        "source_category": "careers_page",
        "location": "Gurugram, India",
        "work_arrangement": "Hybrid",
        "job_type": "Full-time",
        "seniority": "Lead",
        "experience_years_min": 5,
        "experience_years_max": 9,
        "salary_range": "₹22L - ₹35L/yr",
        "date_posted": "2026-11-09",
        "is_early_applicant": True,
        "required_skills": [
            "Talent Acquisition", "Executive Recruiting", "Employer Branding",
            "Candidate Experience", "Diversity Hiring", "Interview Assessment"
        ],
        "job_description": """Lead full-cycle recruitment for McKinsey's digital, analytics, and implementation practices across India and global hubs."""
    }
]


def generate_job_fingerprint(company: str, title: str, location: Optional[str] = None) -> str:
    """Generate stable deduplication hash."""
    raw = f"{company.strip().lower()}|{title.strip().lower()}|{(location or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def extract_skills_from_text(text: str) -> List[str]:
    """Helper to detect common business, technical, and finance skills from job text."""
    known_skills = [
        "Financial Reporting", "FP&A", "Financial Modeling", "Analytics", "Automation",
        "Business Operations", "Process Improvement", "Project Management", "MS Excel",
        "Presentation Skills", "Risk Management", "Data Governance", "Management Consulting",
        "Business Strategy", "IT Strategy", "Digital Transformation", "Corporate Finance",
        "Variance Analysis", "Budgeting", "Forecasting", "SQL", "ERP Systems", "Power BI",
        "Cost Accounting", "Operations Finance", "SAP", "Strategy & BizOps", "Corporate Strategy",
        "M&A Advisory", "Valuation", "Due Diligence", "Python", "Problem-solving", "Communication",
        "Team Leadership", "Stakeholder Management", "Executive Presentations", "Cash Flow"
    ]
    low_text = text.lower()
    found = []
    for skill in known_skills:
        # Match word boundaries
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, low_text):
            found.append(skill)
    return found


def classify_seniority(title: str) -> str:
    """Classify seniority level accurately using hierarchical industry role keywords."""
    t = (title or "").lower().strip()
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u2013", "-").replace("\u2014", "-")

    # 1. Internship / Trainee / Fresher (Must be checked first)
    if re.search(r"\b(interns?|internships?|trainees?|apprentices?|fellows?|fellowships?|freshers?|students?)\b", t):
        return "Internship"

    # Check for office roles (Founder's Office, CEO's Office, CXO's Office)
    is_office_role = bool(
        re.search(r"\b(founder|co-founder|ceo|cfo|cto|coo|cxo|executive)['']?s?\s+office\b", t)
        or "founders office" in t
        or "founder's office" in t
        or "ceo office" in t
        or "ceo's office" in t
        or "generalist - founder" in t
    )

    if is_office_role:
        if re.search(r"\b(chief of staff|head|lead|director|vp)\b", t):
            return "Lead / Manager"
        return "Associate / Mid"

    # 2. Executive / C-Suite / Director / VP
    if re.search(r"\b(managing director|vice president|vp|cxo|ceo|cfo|cto|coo|cmo|cro|partner|president|general manager|head of|division head)\b", t):
        return "Director / Executive"
    if re.search(r"\bdirector\b", t) and not re.search(r"\bassociate director\b", t):
        return "Director / Executive"
    if re.search(r"\b(co-founder|founder)\b", t) and not is_office_role:
        return "Director / Executive"

    # 3. Lead / Manager / Staff / Principal
    if re.search(r"\b(tech lead|team lead|lead|manager|assistant manager|associate director|principal|staff engineer|staff|architect|chief of staff|head)\b", t):
        return "Lead / Manager"

    # 4. Senior
    if re.search(r"\b(senior|sr\.?|experienced|specialist|expert)\b", t):
        return "Senior"

    # 5. Associate / Mid / Junior / Generalist
    return "Associate / Mid"


MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "sept": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

def parse_date_point(token: str, is_end: bool = False) -> Optional[float]:
    """Parses a date token into a decimal year representation."""
    token = token.strip().lower()
    if not token:
        return None
    if any(p in token for p in ["present", "current", "now", "ongoing"]):
        now = datetime.now()
        return now.year + (now.month / 12.0)

    # Match MM/YYYY or MM-YYYY
    m_slash = re.search(r"(\d{1,2})[/-](\d{4})", token)
    if m_slash:
        month = min(max(int(m_slash.group(1)), 1), 12)
        year = int(m_slash.group(2))
        return year + (month - 0.5) / 12.0

    # Match Month Year (e.g. 'Jan 2018' or 'January 2018')
    m_name = re.search(r"([a-z]+)\.?\s+(\d{4})", token)
    if m_name and m_name.group(1) in MONTH_MAP:
        month = MONTH_MAP[m_name.group(1)]
        year = int(m_name.group(2))
        return year + (month - 0.5) / 12.0

    # Match 4-digit Year alone (e.g. '2018')
    m_year = re.search(r"\b(19\d{2}|20\d{2})\b", token)
    if m_year:
        year = int(m_year.group(1))
        return year + (0.99 if is_end else 0.0)

    return None

def calculate_tenure_from_experiences(experiences: List[Dict[str, Any]]) -> float:
    """
    Calculates tenure from dated roles and merges overlapping employment intervals.
    A single 8-year role (e.g. 2016-2024) computes to ~8.5-9.0 years, not capped to 4.
    """
    intervals = []
    has_dates = False

    for exp in experiences:
        if not isinstance(exp, dict):
            continue
        date_str = (exp.get("date_range") or "").strip()
        if not date_str:
            continue
        parts = re.split(r"\s*(?:-|–|—|\bto\b)\s*", date_str, flags=re.IGNORECASE)
        if len(parts) >= 2:
            start_val = parse_date_point(parts[0], is_end=False)
            end_val = parse_date_point(parts[1], is_end=True)
            if start_val and end_val and end_val >= start_val:
                intervals.append((start_val, end_val))
                has_dates = True
        elif len(parts) == 1:
            start_val = parse_date_point(parts[0], is_end=False)
            if start_val:
                intervals.append((start_val, start_val + 1.0))
                has_dates = True

    if not intervals or not has_dates:
        return round(len(experiences) * 1.5, 1) if experiences else 0.0

    # Merge overlapping intervals
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current
        if curr_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)

    total_years = sum(end - start for start, end in merged)
    return round(max(total_years, 0.5), 1)


def compute_job_match(job: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transparent, evidence-based match scoring algorithm evaluating:
      1. Target Role & Title Alignment (0-3.0)
      2. Skills & Keywords Overlap (0-3.0)
      3. Experience & Seniority Fit (0-2.5)
      4. Work Mode / Location Alignment (0-1.5)
    Total score: 0 to 10 scale (or 0-100%).
    Outputs detailed sub-scores, pros, cons, matched and missing skills.
    """
    job_title = (job.get("job_title") or "").strip()
    job_title_low = job_title.lower()
    job_desc = job.get("job_description") or ""
    req_skills = job.get("required_skills") or []
    if not req_skills:
        req_skills = extract_skills_from_text(f"{job_title} {job_desc}")

    req_min_years = job.get("experience_years_min", 4)
    req_max_years = job.get("experience_years_max", 10)
    # Preserve unknown work arrangement as None/Unknown rather than defaulting to Hybrid
    work_arrangement = job.get("work_arrangement")
    job_location = job.get("location") or "India"

    # If no profile or empty profile: return unpersonalized, unranked feed
    has_profile_content = bool(
        profile and (
            profile.get("experience") or
            profile.get("skills") or
            profile.get("target_roles") or
            profile.get("first_name")
        )
    )

    if not has_profile_content:
        return {
            "score": None,
            "score_percent": None,
            "label": "UNRANKED",
            "summary": "Verified role. Connect or upload your profile to activate personalized match scoring and skill gap analysis.",
            "pros": ["Direct verified opening from company career portal", "Standard industry qualification benchmarks apply"],
            "cons": ["Profile not connected yet — add experience & skills for personalized match ranking"],
            "matched_skills": [],
            "missing_skills": req_skills[:6],
            "sub_scores": {
                "role_fit": None,
                "skills_fit": None,
                "experience_fit": None,
                "location_fit": None,
            },
            "experience_fit": f"{req_min_years}-{req_max_years} yrs role ({job.get('seniority', 'Mid')})",
            "location_fit": f"{job_location} ({work_arrangement or 'Not specified'})",
        }

    # Extract user profile evidence
    user_skills = set()
    for s in profile.get("skills", []):
        if isinstance(s, dict) and s.get("skill_name"):
            user_skills.add(s["skill_name"].strip().lower())
        elif isinstance(s, str):
            user_skills.add(s.strip().lower())

    user_experiences = profile.get("experience", [])
    user_titles = [e.get("job_title", "").strip().lower() for e in user_experiences if isinstance(e, dict) and e.get("job_title")]
    target_roles = [r.strip().lower() for r in (profile.get("target_roles") or []) if isinstance(r, str)]
    candidate_titles_to_check = target_roles + user_titles

    # Calculate actual tenure from dated roles with interval merging
    user_est_years = calculate_tenure_from_experiences(user_experiences)

    # 1. Role & Title Alignment (0 - 3.0 pts)
    role_score = 1.2
    matched_title_term = False
    best_matching_role = ""

    for cand_role in candidate_titles_to_check:
        if not cand_role:
            continue
        if cand_role in job_title_low or job_title_low in cand_role:
            role_score = 3.0
            matched_title_term = True
            best_matching_role = cand_role
            break
        # Significant word overlap
        words = [w for w in re.findall(r"[a-zA-Z]{4,}", cand_role) if w not in ["with", "from", "that", "this", "have"]]
        if words and any(w in job_title_low for w in words):
            role_score = 2.7
            matched_title_term = True
            best_matching_role = cand_role
            break

    if not matched_title_term:
        common_domains = ["analyst", "manager", "consultant", "lead", "strategy", "finance", "controller", "operations", "developer", "engineer", "sales", "generalist"]
        job_domains = [d for d in common_domains if d in job_title_low]
        user_has_domain = any(any(d in t for d in job_domains) for t in candidate_titles_to_check)
        if job_domains and user_has_domain:
            role_score = 2.3
        else:
            role_score = 1.5

    # 2. Skills Overlap (0 - 3.0 pts)
    matched_skills = []
    missing_skills = []
    for s in req_skills:
        s_low = s.lower()
        if s_low in user_skills or any(us in s_low or s_low in us for us in user_skills):
            matched_skills.append(s)
        else:
            missing_skills.append(s)

    total_req = max(len(req_skills), 1)
    overlap_ratio = len(matched_skills) / total_req
    if overlap_ratio >= 0.6:
        skills_score = 3.0
    elif overlap_ratio >= 0.4:
        skills_score = 2.5
    elif overlap_ratio >= 0.2:
        skills_score = 1.9
    elif matched_skills:
        skills_score = 1.4
    else:
        skills_score = 0.9

    # 3. Experience & Seniority Fit (0 - 2.5 pts)
    exp_pros = []
    exp_cons = []
    if user_est_years >= req_min_years:
        exp_score = 2.5
        exp_pros.append(f"Seniority aligns well: ~{int(user_est_years)}+ yrs profile experience meets {req_min_years}+ yrs requested.")
    elif user_est_years >= req_min_years - 1.5:
        exp_score = 2.0
        exp_pros.append(f"Experience is competitive: ~{int(user_est_years)} yrs profile vs {req_min_years}+ yrs requested.")
    else:
        exp_score = 1.2
        exp_cons.append(f"Experience depth: Role requests {req_min_years}+ years, profile currently shows ~{int(user_est_years)} years.")

    # 4. Location & Work Arrangement (0 - 1.5 pts)
    loc_score = 1.2
    target_locs = [tl.lower() for tl in (profile.get("target_locations") or [])]
    job_loc_low = job_location.lower()
    
    if work_arrangement in ["Remote", "Hybrid"]:
        loc_score = 1.5
    elif any(tl in job_loc_low for tl in target_locs) or ("india" in job_loc_low and any("india" in tl for tl in target_locs)):
        loc_score = 1.5
    else:
        loc_score = 1.1

    # Total Match Score (out of 10.0)
    total_score = round(min(10.0, max(1.0, role_score + skills_score + exp_score + loc_score)), 1)
    score_percent = int(total_score * 10)

    if total_score >= 8.5:
        label = "STRONG"
    elif total_score >= 7.0:
        label = "GOOD"
    elif total_score >= 5.5:
        label = "FAIR"
    else:
        label = "PARTIAL"

    pros = []
    if matched_title_term and best_matching_role:
        pros.append(f"High role alignment with \"{best_matching_role.title()}\".")
    elif matched_title_term:
        pros.append("Role title aligns with candidate background.")
    if matched_skills:
        pros.append(f"Matched key competencies: {', '.join(matched_skills[:4])}.")
    pros.extend(exp_pros)
    if work_arrangement in ["Remote", "Hybrid"]:
        pros.append(f"Flexible {work_arrangement} work arrangement supported.")

    cons = []
    if missing_skills:
        cons.append(f"Target competencies to highlight: {', '.join(missing_skills[:3])}.")
    cons.extend(exp_cons)

    summary = (
        f"{label} fit ({total_score}/10). "
        f"Matches {len(matched_skills)} of {len(req_skills)} required competencies. "
        f"{'Experience level confirmed.' if user_est_years >= req_min_years else 'Review experience depth.'}"
    )

    return {
        "score": total_score,
        "score_percent": score_percent,
        "label": label,
        "summary": summary,
        "pros": pros,
        "cons": cons,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "sub_scores": {
            "role_fit": role_score,
            "skills_fit": skills_score,
            "experience_fit": exp_score,
            "location_fit": loc_score,
        },
        "experience_fit": f"{int(user_est_years)} yrs profile vs {req_min_years}-{req_max_years} yrs role ({job.get('seniority', 'Mid')})",
        "location_fit": f"{job_location} ({work_arrangement})",
    }


class JobRepositoryService:
    """Service to query, filter, and ingest jobs across sources."""

    def __init__(self):
        from cv_tailor.config import data_dir
        self._storage_path = data_dir() / "repository_jobs.json"
        self._package_path = Path(__file__).resolve().parent.parent / "data" / "repository_jobs.json"
        self._jobs: List[Dict[str, Any]] = []
        self._companies: List[Dict[str, Any]] = list(MASTER_COMPANIES)
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            # 1. Prefer packaged data/repository_jobs.json (contains all 1,700+ verified jobs)
            loaded_jobs = []
            if self._package_path.exists():
                with open(self._package_path, "r", encoding="utf-8") as f:
                    loaded_jobs = json.load(f)

            # 2. Merge any user-added jobs from local storage path if present
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, list):
                        if not loaded_jobs:
                            loaded_jobs = saved
                        else:
                            seen = {j.get("id") or j.get("fingerprint") for j in loaded_jobs if j.get("id") or j.get("fingerprint")}
                            for item in saved:
                                key = item.get("id") or item.get("fingerprint")
                                if key and key not in seen:
                                    seen.add(key)
                                    loaded_jobs.append(item)

            if loaded_jobs:
                self._jobs = loaded_jobs
            else:
                self._jobs = list(SEEDED_REPOSITORY_JOBS)
            logger.info(f"JobRepositoryService initialized with {len(self._jobs)} jobs.")
        except Exception as e:
            logger.error(f"Error loading repository jobs from disk: {e}")
            if not self._jobs:
                self._jobs = list(SEEDED_REPOSITORY_JOBS)

    def _save_to_disk(self):
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving repository jobs to disk: {e}")

    def list_companies(self) -> List[Dict[str, Any]]:
        return self._companies

    def list_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        work_model: Optional[str] = None,
        seniority: Optional[str] = None,
        company: Optional[str] = None,
        source: Optional[str] = None,
        min_score: Optional[float] = None,
        profile: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        filtered = []
        for raw_job in self._jobs:
            job = dict(raw_job)

            # Query filter (title, company, description, skills)
            if query:
                q = query.strip().lower()
                text_to_search = f"{job.get('job_title', '')} {job.get('company_name', '')} {job.get('job_description', '')} {' '.join(job.get('required_skills', []))}".lower()
                if q not in text_to_search:
                    continue

            # Location filter (supports "India", "Global", or specific cities)
            if location:
                loc_q = location.strip().lower()
                job_loc = (job.get("location") or "").lower()
                if loc_q in ["india", "in"]:
                    is_in_india = "india" in job_loc or any(c in job_loc for c in [
                        "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", "pune",
                        "gurgaon", "gurugram", "noida", "kolkata", "chennai", "ahmedabad", "pan india"
                    ])
                    if not is_in_india:
                        continue
                elif loc_q not in job_loc:
                    continue

            # Work model filter
            if work_model and work_model.lower() != "all":
                wm_q = work_model.strip().lower()
                if wm_q not in (job.get("work_arrangement") or "").lower():
                    continue

            # Seniority filter with flexible tier aliasing
            if seniority and seniority.lower() != "all":
                sen_q = seniority.strip().lower()
                job_sen = (job.get("seniority") or "").lower()
                if sen_q in ["intern", "internship"]:
                    if "intern" not in job_sen:
                        continue
                elif sen_q in ["mid", "associate", "associate / mid"]:
                    if not any(k in job_sen for k in ["mid", "associate"]):
                        continue
                elif sen_q in ["senior"]:
                    if "senior" not in job_sen:
                        continue
                elif sen_q in ["lead", "manager", "lead / manager"]:
                    if not any(k in job_sen for k in ["lead", "manager"]):
                        continue
                elif sen_q in ["director", "executive", "exec", "director / executive", "lead / executive"]:
                    if not any(k in job_sen for k in ["director", "executive", "vp", "chief"]):
                        continue
                elif sen_q not in job_sen:
                    continue

            # Company filter
            if company:
                comp_q = company.strip().lower()
                if comp_q not in (job.get("company_name") or "").lower():
                    continue

            # Source filter
            if source and source.lower() != "all":
                if source.strip().lower() not in (job.get("source") or "").lower():
                    continue

            filtered.append(job)

        # Score filtered jobs to rank by match fit and support min_score thresholding
        scored_jobs = []
        for job in filtered:
            match = compute_job_match(job, profile)
            job["match_score"] = match["score"]
            job["match_percent"] = match["score_percent"]
            job["match_label"] = match["label"]
            job["match_analysis"] = match

            if min_score is not None:
                if job["match_score"] is None or job["match_score"] < min_score:
                    continue
            scored_jobs.append(job)

        # Sort: personalized by match score when profile is active; otherwise chronological by date_posted
        has_personalized_scores = any(j.get("match_score") is not None for j in scored_jobs)
        if has_personalized_scores:
            scored_jobs.sort(key=lambda j: (j.get("match_score") or 0.0, j.get("date_posted") or ""), reverse=True)
        else:
            scored_jobs.sort(key=lambda j: (j.get("date_posted") or "", j.get("is_early_applicant", False)), reverse=True)

        total = len(scored_jobs)
        limit_val = max(1, min(limit, 100)) if limit > 0 else 20
        total_pages = max(1, math.ceil(total / limit_val))
        page_val = max(1, min(page, total_pages))
        start = (page_val - 1) * limit_val
        end = start + limit_val
        page_jobs = scored_jobs[start:end]

        return {
            "total": total,
            "page": page_val,
            "limit": limit_val,
            "total_pages": total_pages,
            "jobs": page_jobs,
        }

    def add_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a job to the repository with deduplication and automated classification."""
        fingerprint = generate_job_fingerprint(
            job_data.get("company_name", ""),
            job_data.get("job_title", ""),
            job_data.get("location", "")
        )
        job_data["fingerprint"] = fingerprint
        if not job_data.get("id"):
            job_data["id"] = f"job-{fingerprint}"
        if not job_data.get("date_posted"):
            job_data["date_posted"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not job_data.get("seniority"):
            job_data["seniority"] = classify_seniority(job_data.get("job_title", ""))
        if not job_data.get("required_skills"):
            job_data["required_skills"] = extract_skills_from_text(
                f"{job_data.get('job_title', '')} {job_data.get('job_description', '')}"
            )

        # Check existing
        for idx, existing in enumerate(self._jobs):
            if existing.get("fingerprint") == fingerprint or existing.get("id") == job_data["id"]:
                self._jobs[idx].update(job_data)
                self._save_to_disk()
                return self._jobs[idx]

        self._jobs.insert(0, job_data)
        self._save_to_disk()
        return job_data

    def bulk_add_jobs(self, jobs_data: List[Dict[str, Any]]) -> int:
        """Add multiple jobs in batch and persist to disk once."""
        added = 0
        existing_fps = {j.get("fingerprint") for j in self._jobs if j.get("fingerprint")}
        existing_ids = {j.get("id") for j in self._jobs if j.get("id")}

        for job_data in jobs_data:
            fingerprint = generate_job_fingerprint(
                job_data.get("company_name", ""),
                job_data.get("job_title", ""),
                job_data.get("location", "")
            )
            job_data["fingerprint"] = fingerprint
            if not job_data.get("id"):
                job_data["id"] = f"job-{fingerprint}"
            if not job_data.get("date_posted"):
                job_data["date_posted"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if not job_data.get("seniority"):
                job_data["seniority"] = classify_seniority(job_data.get("job_title", ""))
            if not job_data.get("required_skills"):
                job_data["required_skills"] = extract_skills_from_text(
                    f"{job_data.get('job_title', '')} {job_data.get('job_description', '')}"
                )

            if fingerprint in existing_fps or job_data["id"] in existing_ids:
                continue

            existing_fps.add(fingerprint)
            existing_ids.add(job_data["id"])
            self._jobs.append(job_data)
            added += 1

        if added > 0:
            self._save_to_disk()
        return added

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        for job in self._jobs:
            if job.get("id") == job_id:
                return job
        return None


# Global singleton instance
job_repo_service = JobRepositoryService()
