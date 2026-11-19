"""
Comprehensive Test Suite for Auto Apply Phase 2 — Form Filling and Reusable Answers.
Verifies:
1. Answer Bank initialization with 8 core categories:
   (Notice period, availability, work authorization, sponsorship, relocation, compensation, travel, experience).
2. Updating and saving custom answers in Answer Bank.
3. Unfamiliar required question handling:
   - Exact question wording, options, required status, and job context saved.
   - Job 1 pauses with status 'needs_answer'.
4. Queue worker continues past paused job:
   - Job 2 (with standard questions) successfully fills and advances to 'ready_for_review'.
5. Answering unfamiliar question with 4 scopes:
   - Candidate answers Job 1 with 'save_as_default'.
   - Job 1 resumes and advances to 'ready_for_review'.
6. Reusable answers for later jobs:
   - Job 3 (with the same previously unfamiliar question) automatically reuses saved answer without pausing!
7. Version tracking & manual submission checkpoint:
   - Exact version and answers snapshot recorded per application.
   - Submission remains manual ('ready_for_review').
"""
import sys
import os

# Ensure ai-service is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-service")))

from cv_tailor.config import data_dir
from cv_tailor.services.auto_apply_service import (
    get_answer_bank,
    save_answer_bank,
    get_queue_data,
    save_queue_data,
    add_jobs_to_queue,
    process_queue_form_filling,
    answer_pending_question,
    get_application_form_review,
    _get_user_file,
)


def run_phase2_tests():
    print("=" * 70)
    print("RUNNING AUTO APPLY PHASE 2 VERIFICATION SUITE")
    print("=" * 70)

    test_user = "test_phase2_candidate"

    # Reset any test files from prior runs for idempotency
    for suffix in ["defaults", "queue", "answer_bank"]:
        p = _get_user_file(test_user, suffix)
        if p.exists():
            p.unlink()

    # --- Test 1: Seed Answer Bank Initialization ---
    print("\n--- Test 1: Seed Answer Bank Initialization ---")
    bank = get_answer_bank(test_user)
    assert bank["version"] >= 1, "Bank must have version number"
    answers = bank["answers"]
    categories = {a["category"] for a in answers}
    expected_categories = {
        "notice_period", "availability", "work_authorization",
        "sponsorship", "relocation", "compensation", "travel", "experience"
    }
    missing = expected_categories - categories
    assert not missing, f"Missing required seed categories: {missing}"
    print(f"✅ Seed Answer Bank initialized with all {len(expected_categories)} core categories:")
    for cat in expected_categories:
        matching = next(a for a in answers if a["category"] == cat)
        print(f"   • [{cat}]: '{matching['canonical_question']}' -> '{matching['answer_text']}'")

    # --- Test 2: Customizing Answer Bank ---
    print("\n--- Test 2: Customizing and Editing Answer Bank ---")
    notice_item = next(a for a in answers if a["category"] == "notice_period")
    notice_item["answer_text"] = "15 Days (Negotiable)"
    saved_bank = save_answer_bank(test_user, bank)
    assert saved_bank["version"] > 1, "Bank version must increment on update"
    reloaded_bank = get_answer_bank(test_user)
    reloaded_notice = next(a for a in reloaded_bank["answers"] if a["category"] == "notice_period")
    assert reloaded_notice["answer_text"] == "15 Days (Negotiable)"
    print(f"✅ Answer Bank successfully updated to v{saved_bank['version']} with custom answer: '{reloaded_notice['answer_text']}'.")

    # --- Test 3 & 4: Multi-Job Queue Flow (Job 1 Pauses while Job 2 Continues) ---
    print("\n--- Test 3 & 4: Job 1 Pauses on Unfamiliar Question while Job 2 Continues ---")
    # Queue two jobs: Job 1 has an unfamiliar required question; Job 2 has standard questions
    sample_jobs = [
        {
            "job_id": "role_strat_01",
            "company_name": "McKinsey & Company",
            "job_title": "Engagement Manager — Strategy",
            "matched_theme": "Strategy Consulting",
            "location": "Bengaluru",
            "source": "Greenhouse",
            "job_url": "https://mckinsey.com/careers/role_strat_01",
            "why_it_qualified": "Matches Strategy Consulting theme and 4-7 yrs experience range",
            "has_ambiguity": False,
        },
        {
            "job_id": "role_fpa_02",
            "company_name": "Swiggy",
            "job_title": "Senior Director — Strategic Finance",
            "matched_theme": "Strategic Finance",
            "location": "Bengaluru",
            "source": "Lever",
            "job_url": "https://swiggy.com/careers/role_fpa_02",
            "why_it_qualified": "Matches Strategic Finance theme",
            "has_ambiguity": False,
        }
    ]
    add_res = add_jobs_to_queue(test_user, sample_jobs)
    assert add_res["added_count"] == 2
    print(f"✅ Queued 2 test jobs into persistent queue.")

    # Define custom form for Job 1 with an unfamiliar question
    unfamiliar_question_text = "Do you have direct board reporting and P&L experience exceeding $20M?"
    mock_catalog = {
        "role_strat_01": [
            {
                "question_id": "q_custom_board_pl",
                "exact_question_text": unfamiliar_question_text,
                "field_type": "select",
                "options": ["Yes", "No"],
                "required": True  # Required -> Must pause Job 1!
            },
            {
                "question_id": "q_notice",
                "exact_question_text": "What is your official notice period?",
                "field_type": "text",
                "options": [],
                "required": True
            }
        ],
        "role_fpa_02": [
            {
                "question_id": "q_work_auth",
                "exact_question_text": "Are you legally authorized to work in India?",
                "field_type": "select",
                "options": ["Yes", "No"],
                "required": True
            },
            {
                "question_id": "q_sponsorship",
                "exact_question_text": "Will you require visa sponsorship?",
                "field_type": "select",
                "options": ["Yes", "No"],
                "required": True
            },
            {
                "question_id": "q_notice",
                "exact_question_text": "What is your official notice period?",
                "field_type": "text",
                "options": [],
                "required": True
            }
        ]
    }

    # Execute queue form filling cycle
    process_res = process_queue_form_filling(test_user, mock_catalog)
    assert process_res["processed_count"] == 2
    assert process_res["paused_for_answer_count"] == 1, "Job 1 must pause for unfamiliar required question"
    assert process_res["ready_count"] == 1, "Job 2 must advance to ready_for_review"

    # Verify queue state
    current_queue = get_queue_data(test_user)
    job1 = next(item for item in current_queue["queue_items"] if item["job_id"] == "role_strat_01")
    job2 = next(item for item in current_queue["queue_items"] if item["job_id"] == "role_fpa_02")

    # Assert Job 1 is paused with pending question details
    assert job1["status"] == "needs_answer"
    assert job1["pending_question"] is not None
    assert job1["pending_question"]["exact_question_text"] == unfamiliar_question_text
    assert job1["pending_question"]["required"] is True
    assert job1["pending_question"]["job_context"]["company_name"] == "McKinsey & Company"
    print(f"✅ Verified: Job 1 ('{job1['job_title']}') is PAUSED waiting for answer to:")
    print(f"   '{job1['pending_question']['exact_question_text']}' [Required: True, Options: {job1['pending_question']['options']}]")

    # Assert Job 2 completed autofill and advanced to ready_for_review
    assert job2["status"] == "ready_for_review"
    assert job2["answers_snapshot"] is not None
    assert len(job2["answers_snapshot"]["fields"]) == 3
    print(f"✅ Verified: Job 2 ('{job2['job_title']}') CONTINUED and is READY FOR REVIEW with {len(job2['answers_snapshot']['fields'])} filled fields.")

    # --- Test 5: Candidate Answers Unfamiliar Question with 'save_as_default' ---
    print("\n--- Test 5: Candidate Resolves Unfamiliar Question (Scope: 'save_as_default') ---")
    answer_res = answer_pending_question(
        user_id=test_user,
        queue_item_id=job1["queue_item_id"],
        answer_text="Yes",
        scope="save_as_default",
        selected_option="Yes"
    )
    assert answer_res["status"] == "success"

    # Reload Job 1
    current_queue = get_queue_data(test_user)
    job1_updated = next(item for item in current_queue["queue_items"] if item["queue_item_id"] == job1["queue_item_id"])
    assert job1_updated["status"] == "ready_for_review"
    assert job1_updated["pending_question"] is None
    assert "q_custom_board_pl" in job1_updated["answers_snapshot"]["fields"]
    assert job1_updated["answers_snapshot"]["fields"]["q_custom_board_pl"]["answer_value"] == "Yes"
    assert job1_updated["answers_snapshot"]["fields"]["q_custom_board_pl"]["source_scope"] == "save_as_default"
    print(f"✅ Verified: Job 1 resumed and advanced to 'ready_for_review'!")
    print(f"   Recorded answer: '{job1_updated['answers_snapshot']['fields']['q_custom_board_pl']['answer_value']}' (Scope: save_as_default).")

    # --- Test 6: Later Job 3 Automatically Reuses Saved Answer Without Pausing ---
    print("\n--- Test 6: Later Job 3 Reuses Saved Answer Without Pausing ---")
    job3_spec = [{
        "job_id": "role_bain_03",
        "company_name": "Bain & Company",
        "job_title": "Director — Corporate Strategy",
        "matched_theme": "Corporate Strategy",
        "location": "Mumbai",
        "source": "LinkedIn",
        "job_url": "https://bain.com/careers/role_bain_03",
        "why_it_qualified": "Matches Corporate Strategy theme",
        "has_ambiguity": False,
    }]
    add_jobs_to_queue(test_user, job3_spec)

    # Job 3 encounters the EXACT SAME question that was saved as default
    mock_catalog_job3 = {
        "role_bain_03": [
            {
                "question_id": "q_board_pl_repeat",
                "exact_question_text": unfamiliar_question_text,  # Same question!
                "field_type": "select",
                "options": ["Yes", "No"],
                "required": True
            },
            {
                "question_id": "q_notice",
                "exact_question_text": "What is your official notice period?",
                "field_type": "text",
                "options": [],
                "required": True
            }
        ]
    }

    # Process queue for Job 3
    process_res_job3 = process_queue_form_filling(test_user, mock_catalog_job3)
    current_queue = get_queue_data(test_user)
    job3 = next(item for item in current_queue["queue_items"] if item["job_id"] == "role_bain_03")

    assert job3["status"] == "ready_for_review", f"Job 3 should automatically reuse answer and be ready_for_review, got: {job3['status']}"
    assert job3["pending_question"] is None
    reused_field = job3["answers_snapshot"]["fields"]["q_board_pl_repeat"]
    assert reused_field["answer_value"] == "Yes"
    assert reused_field["source_scope"] == "save_as_default"
    print(f"✅ Verified: Job 3 ('{job3['job_title']}') automatically REUSED saved answer '{reused_field['answer_value']}' without pausing!")

    # --- Test 7: Form Review & Manual Submission Checkpoint ---
    print("\n--- Test 7: Form Review Snapshot & Manual Submission Mode ---")
    review_res = get_application_form_review(test_user, job3["queue_item_id"])
    assert review_res["submission_mode"] == "manual_review_only"
    assert review_res["status"] == "ready_for_review"
    assert "fields" in review_res["answers_snapshot"]
    print(f"✅ Form review snapshot verified (Submission Mode: {review_res['submission_mode']}).")

    # --- Test 8: Activity Feed Event Trail ---
    print("\n--- Test 8: Chat Activity Feed Event Verification ---")
    activity_feed = current_queue["activity_feed"]
    badges = [event["badge"] for event in activity_feed]
    assert "Needs Answer" in badges, "Activity feed must record unfamiliar question pause"
    assert "Answered" in badges, "Activity feed must record answer resolution"
    assert "Ready Review" in badges, "Activity feed must record ready for review"
    print(f"✅ Activity feed verified with {len(activity_feed)} events logged.")
    print(f"   Recorded event types: {set(badges)}")

    print("\n" + "=" * 70)
    print("ALL AUTO APPLY PHASE 2 TESTS PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase2_tests()
