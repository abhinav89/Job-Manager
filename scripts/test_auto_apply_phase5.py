"""
Verification suite for DealOS Jobs Auto Apply — Phase 5:
Hiring alerts, social/WhatsApp post intake, Gmail OAuth connection, and applications by email.
"""

import sys
import os
import json
from pathlib import Path

# Add project root and ai-service to path
REPO_ROOT = Path(__file__).resolve().parent.parent
AI_SERVICE_DIR = REPO_ROOT / "ai-service"
sys.path.insert(0, str(AI_SERVICE_DIR))

from cv_tailor.services.auto_apply_service import (
    get_auto_apply_defaults,
    save_auto_apply_defaults,
    get_queue_data,
    save_queue_data,
    connect_gmail_account,
    disconnect_gmail_account,
    get_gmail_status,
    parse_and_ingest_message,
    draft_email_application,
    approve_and_send_email,
    process_queue_with_approvals,
)
from cv_tailor.database import SessionLocal
from cv_tailor.models.database_models import JobApplication

TEST_USER_ID = "test_candidate_phase5"


def clean_test_artifacts():
    """Removes test artifacts from disk before and after runs."""
    for suffix in ["defaults", "queue", "answer_bank"]:
        path = REPO_ROOT / f"test_candidate_phase5_{suffix}.json"
        if path.exists():
            path.unlink()
        local_path = AI_SERVICE_DIR / f"test_candidate_phase5_{suffix}.json"
        if local_path.exists():
            local_path.unlink()


def run_phase5_tests():
    print("=" * 70)
    print("RUNNING AUTO APPLY PHASE 5 VERIFICATION SUITE")
    print("=" * 70)

    clean_test_artifacts()

    # Seed baseline defaults for Phase 5 test
    baseline_defaults = {
        "user_id": TEST_USER_ID,
        "role_themes": [
            "Corporate Strategy & CEO Office",
            "FP&A and Strategic Finance",
            "Commercial Due Diligence"
        ],
        "min_experience_years": 8,
        "max_experience_years": 16,
        "preferred_locations": ["Bengaluru", "Hyderabad", "Dubai", "Remote"],
        "location_mode": "prioritize",
        "unattended_include_lower_ranked": True,
        "review_tailored_cv": False,
        "review_before_portal_submission": False,
        "review_before_email_send": True,
        "allow_unattended_submission": True,
        "daily_submission_limit": 10,
        "allow_workday_account_creation": True,
        "gmail_connected": False,
        "gmail_account_email": None,
        "gmail_scopes_granted": []
    }
    save_auto_apply_defaults(TEST_USER_ID, baseline_defaults)

    # -------------------------------------------------------------------------
    # Test 1: Gmail OAuth Connection & Separate Scope Management
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Gmail OAuth Connection & Separate Scope Management ---")
    conn_res = connect_gmail_account(
        user_id=TEST_USER_ID,
        code_or_token="mock_oauth_code_xyz",
        enable_inbox_access=False,
        test_email="abhinava2015@email.iimcal.ac.in"
    )
    assert conn_res["status"] == "connected", "Gmail connection failed"
    assert conn_res["gmail_connected"] is True
    assert conn_res["gmail_account_email"] == "abhinava2015@email.iimcal.ac.in"
    assert "https://www.googleapis.com/auth/gmail.send" in conn_res["gmail_scopes_granted"]
    assert "https://www.googleapis.com/auth/gmail.readonly" not in conn_res["gmail_scopes_granted"]
    print("✅ Gmail connected with drafting & send scopes. Inbox read scope safely isolated.")

    # Request inbox access separately
    conn_inbox = connect_gmail_account(
        user_id=TEST_USER_ID,
        code_or_token="mock_oauth_code_xyz",
        enable_inbox_access=True,
        test_email="abhinava2015@email.iimcal.ac.in"
    )
    assert "https://www.googleapis.com/auth/gmail.readonly" in conn_inbox["gmail_scopes_granted"]
    print("✅ Inbox read scope granted separately for alert intake & Workday verification.")

    status = get_gmail_status(TEST_USER_ID)
    assert status["gmail_connected"] is True
    assert len(status["gmail_scopes_granted"]) == 3

    # -------------------------------------------------------------------------
    # Test 2: Multi-Channel Intake Parser (WhatsApp Hiring Message)
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Multi-Channel Intake Parser (WhatsApp Post) ---")
    whatsapp_post = """
    Urgent opening for Head of Corporate Strategy at Peak XV Partners in Bengaluru.
    Looking for 10-14 years leadership experience.
    Instructions: Send updated CV to careers@peakxv.com with subject 'Application - Head of Strategy'.
    """
    intake_res = parse_and_ingest_message(
        user_id=TEST_USER_ID,
        raw_text=whatsapp_post,
        source="whatsapp",
        sender_info="+91 98110 XXXXX (WhatsApp VC Group)"
    )
    assert intake_res["status"] == "success"
    assert intake_res["initial_status"] == "queued"
    assert intake_res["has_ambiguity"] is False
    q_item = intake_res["queue_item"]
    assert q_item["company_name"] == "Peak XV Partners"
    assert q_item["job_title"] == "Head of Corporate Strategy"
    assert q_item["matched_theme"] == "Corporate Strategy & CEO Office"
    assert q_item["location"] == "Bengaluru"
    assert q_item["intake_metadata"]["recipient_email"] == "careers@peakxv.com"
    assert q_item["intake_metadata"]["recipient_type"] == "careers_inbox"
    print("✅ WhatsApp post parsed: extracted 'Head of Corporate Strategy' at 'Peak XV Partners'.")
    print(f"   Recipient: {q_item['intake_metadata']['recipient_email']} | Theme: {q_item['matched_theme']}")

    # -------------------------------------------------------------------------
    # Test 3: Ambiguity Flagging & Missing Information Routing to 'Needs Input'
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Ambiguity Flagging & Routing to 'Needs Input' ---")
    ambiguous_post = """
    We are looking for someone to lead strategy. Remote / India.
    Immediate start preferred. DM for details.
    """
    ambig_res = parse_and_ingest_message(
        user_id=TEST_USER_ID,
        raw_text=ambiguous_post,
        source="social_post"
    )
    assert ambig_res["initial_status"] == "needs_input", "Ambiguous post must route to needs_input"
    assert ambig_res["has_ambiguity"] is True
    assert any("Missing application email" in f for f in ambig_res["ambiguity_flags"])
    print("✅ Incomplete message safely held at 'needs_input':")
    print(f"   Flags: {ambig_res['ambiguity_flags']}")

    # -------------------------------------------------------------------------
    # Test 4: Email Application Tailoring & Attachment with Review ON
    # -------------------------------------------------------------------------
    print("\n--- Test 4: Email Application Tailoring & Attachment (Review ON) ---")
    draft_res = draft_email_application(
        user_id=TEST_USER_ID,
        queue_item_id=q_item["queue_item_id"]
    )
    assert draft_res["status"] == "waiting_email_review", "Must pause for email review when setting is ON"
    pkg = draft_res["email_package"]
    assert pkg["recipient_email"] == "careers@peakxv.com"
    assert "Application - Head of Strategy" in pkg["subject"]
    assert "Peak XV Partners" in pkg["body"]
    assert "attached_cv_version" in pkg
    assert pkg["attached_cv_filename"].endswith(".pdf")
    print("✅ Tailored email drafted with attached job-specific CV PDF:")
    print(f"   Subject: '{pkg['subject']}'")
    print(f"   Attachment: {pkg['attached_cv_filename']}")
    print(f"   Queue status: {draft_res['queue_item']['status']} (Paused at Checkpoint)")

    # -------------------------------------------------------------------------
    # Test 5: Hiring-Manager Outreach Check (Mandatory Review)
    # -------------------------------------------------------------------------
    print("\n--- Test 5: Hiring-Manager Outreach Check (Mandatory Review) ---")
    linkedin_hm_post = """
    My team at FalconX is expanding. Hiring Director of Strategic Finance in Dubai (10-15 yrs).
    Please email your profile directly to vikram.anand@falconx.io.
    """
    hm_res = parse_and_ingest_message(
        user_id=TEST_USER_ID,
        raw_text=linkedin_hm_post,
        source="linkedin_post"
    )
    hm_item = hm_res["queue_item"]
    assert hm_item["intake_metadata"]["recipient_type"] == "hiring_manager"
    assert hm_item["intake_metadata"]["is_hiring_manager_outreach"] is True

    # Temporarily set review_before_email_send to FALSE
    defs = get_auto_apply_defaults(TEST_USER_ID)
    defs["review_before_email_send"] = False
    save_auto_apply_defaults(TEST_USER_ID, defs)

    # Draft email for hiring manager outreach
    hm_draft = draft_email_application(
        user_id=TEST_USER_ID,
        queue_item_id=hm_item["queue_item_id"]
    )
    # Rule requirement: "For hiring-manager outreach, show the source for the work email and ask for review when the recipient’s connection to the role is uncertain."
    assert hm_draft["status"] == "waiting_email_review", "Must enforce review for uncertain hiring-manager outreach even when review is OFF!"
    print("✅ Hiring-manager outreach detected (vikram.anand@falconx.io).")
    print("   Verified: Forced pause at 'waiting_email_review' because individual connection requires review.")

    # -------------------------------------------------------------------------
    # Test 6: Candidate Approval & Strict Tracker Sync as 'Applied by email'
    # -------------------------------------------------------------------------
    print("\n--- Test 6: Candidate Approval & Strict Tracker Sync ---")
    send_res = approve_and_send_email(
        user_id=TEST_USER_ID,
        queue_item_id=q_item["queue_item_id"]
    )
    assert send_res["status"] == "applied"
    assert send_res["confirmation_ref"].startswith("EML-")
    conf_id = send_res["confirmation_ref"]
    print(f"✅ Email sent via connected Gmail. Confirmation ID: {conf_id}")

    # Verify SQLite Job Tracker state
    db = SessionLocal()
    try:
        app_record = db.query(JobApplication).filter(JobApplication.notes.contains(conf_id)).first()
        if not app_record:
            # Check by company name
            app_record = db.query(JobApplication).filter(JobApplication.company == "Peak XV Partners").order_by(JobApplication.id.desc()).first()

        assert app_record is not None, "Application must be recorded in SQLite JobApplication tracker"
        assert app_record.status == "Applied", f"Expected 'Applied', got '{app_record.status}'"
        assert "careers@peakxv.com" in (app_record.notes or "")
        print(f"✅ Tracker record confirmed in SQLite: ID={app_record.id} | Status={app_record.status}")
        print(f"   Notes: {app_record.notes}")
    finally:
        db.close()

    # Clean up test artifacts
    clean_test_artifacts()

    print("\n" + "=" * 70)
    print("ALL AUTO APPLY PHASE 5 TESTS PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase5_tests()
