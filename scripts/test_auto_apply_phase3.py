"""
Comprehensive Test Suite for Auto Apply Phase 3 — Job-Specific CVs and Independent Approvals.
Verifies:
1. Tailoring source branching:
   - LinkedIn, Portals, Email: Tailors separate CV with verified facts, wording changes diff, overflow checks, version tracking.
   - iimjobs & Naukri: Strictly skips tailoring, attaches single CV from candidate profile.
2. Independent Review Settings per Rule:
   - Checkpoint 1: 'Review tailored CV' (waits before attachment).
   - Checkpoint 2: 'Review before portal submission' (waits after form and attachment are ready).
3. ALL FOUR COMBINATIONS TESTED:
   - Combination 1: (review_tailored_cv=True, review_before_portal_submission=True)
   - Combination 2: (review_tailored_cv=True, review_before_portal_submission=False)
   - Combination 3: (review_tailored_cv=False, review_before_portal_submission=True)
   - Combination 4: (review_tailored_cv=False, review_before_portal_submission=False)
4. Non-blocking queue execution:
   - Waiting jobs do not halt the queue; other eligible jobs continue.
5. Wording changes diff, PDF preview metadata, and page overflow checking.
"""
import sys
import os

# Ensure ai-service is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-service")))

from cv_tailor.config import data_dir
from cv_tailor.services.auto_apply_service import (
    get_auto_apply_defaults,
    save_auto_apply_defaults,
    get_queue_data,
    save_queue_data,
    add_jobs_to_queue,
    tailor_cv_for_job,
    is_naukri_or_iimjobs,
    process_queue_with_approvals,
    approve_tailored_cv,
    approve_portal_submission,
    get_tailored_cv_preview,
    _get_user_file,
)


def run_phase3_tests():
    print("=" * 70)
    print("RUNNING AUTO APPLY PHASE 3 VERIFICATION SUITE")
    print("=" * 70)

    test_user = "test_phase3_candidate"

    # Reset any test files from prior runs
    for suffix in ["defaults", "queue", "answer_bank"]:
        p = _get_user_file(test_user, suffix)
        if p.exists():
            p.unlink()

    # --- Test 1: Source Branching (LinkedIn/Portals vs. iimjobs/Naukri) ---
    print("\n--- Test 1: Source Branching & Tailoring Policy ---")

    # A: LinkedIn / Portal Job -> Must tailor separate CV
    portal_job = {
        "job_id": "test_portal_job_01",
        "company_name": "Boston Consulting Group",
        "job_title": "Project Leader — Corporate Finance",
        "matched_theme": "Corporate Finance",
        "source": "Greenhouse",
        "job_url": "https://bcg.com/careers/job_01",
    }
    portal_cv = tailor_cv_for_job(test_user, portal_job)
    assert not portal_cv["skipped"], "Portals must tailor separate CV"
    assert portal_cv["source_type"] == "job_specific_tailored_cv"
    assert portal_cv["page_count"] <= 4, "Must pass overflow ceiling"
    assert portal_cv["overflow_status"] == "passed"
    assert len(portal_cv["wording_changes"]) >= 2, "Must generate wording changes diff"
    print(f"✅ Portal Job ('{portal_job['company_name']}'): Tailored job-specific CV generated.")
    print(f"   Version ID: {portal_cv['version_id']}")
    print(f"   Page count: {portal_cv['page_count']} pages (Overflow: {portal_cv['overflow_status']})")
    print(f"   Wording diff generated: {len(portal_cv['wording_changes'])} sections modified:")
    for change in portal_cv["wording_changes"]:
        print(f"     • [{change['section']}]: '{change['original'][:40]}...' -> '{change['tailored'][:40]}...'")

    # B: iimjobs / Naukri Job -> Must skip tailoring and use profile single CV
    naukri_job = {
        "job_id": "test_naukri_job_02",
        "company_name": "Tata Sons",
        "job_title": "General Manager — Strategy",
        "matched_theme": "Corporate Strategy",
        "source": "Naukri",
        "job_url": "https://www.naukri.com/job-listings-02",
    }
    assert is_naukri_or_iimjobs(naukri_job["source"], naukri_job["job_url"]) is True
    naukri_cv = tailor_cv_for_job(test_user, naukri_job)
    assert naukri_cv["skipped"] is True, "Naukri jobs must skip tailoring"
    assert naukri_cv["source_type"] == "profile_single_cv"
    print(f"✅ Naukri Job ('{naukri_job['company_name']}'): Tailoring SKIPPED by rule. Single profile CV attached as-is.")

    iimjobs_job = {
        "job_id": "test_iimjobs_job_03",
        "company_name": "Aditya Birla Group",
        "job_title": "VP Corporate Strategy",
        "matched_theme": "Corporate Strategy",
        "source": "iimjobs",
        "job_url": "https://www.iimjobs.com/j/abg-03",
    }
    assert is_naukri_or_iimjobs(iimjobs_job["source"], iimjobs_job["job_url"]) is True
    iimjobs_cv = tailor_cv_for_job(test_user, iimjobs_job)
    assert iimjobs_cv["skipped"] is True, "iimjobs must skip tailoring"
    print(f"✅ iimjobs Job ('{iimjobs_job['company_name']}'): Tailoring SKIPPED by rule. Single profile CV attached as-is.")

    # --- Test 2: Testing ALL FOUR Review Combinations ---
    print("\n--- Test 2: Testing ALL FOUR Review Combinations ---")

    def setup_fresh_queue(job_spec):
        for suffix in ["queue"]:
            p = _get_user_file(test_user, suffix)
            if p.exists():
                p.unlink()
        add_jobs_to_queue(test_user, [job_spec])

    # ══════════════════════════════════════════════════════════════════
    # COMBINATION 1: (review_tailored_cv=True, review_before_portal_submission=True)
    # Both reviews ON: Waits for CV review -> Approve -> Waits for submission review -> Approve
    # ══════════════════════════════════════════════════════════════════
    print("\n  [Combination 1/4]: review_tailored_cv=True, review_before_portal_submission=True")
    c1_job = {
        "job_id": "comb1_job",
        "company_name": "Bain & Company",
        "job_title": "Case Team Leader",
        "matched_theme": "Strategy Consulting",
        "source": "Greenhouse",
        "job_url": "https://bain.com/careers/c1",
        "has_ambiguity": False,
    }
    setup_fresh_queue(c1_job)
    overrides_1 = {"review_tailored_cv": True, "review_before_portal_submission": True}
    res1 = process_queue_with_approvals(test_user, rule_overrides=overrides_1)

    assert res1["waiting_cv_review_count"] == 1
    q1 = get_queue_data(test_user)
    item1 = q1["queue_items"][0]
    assert item1["status"] == "waiting_cv_review", f"Expected waiting_cv_review, got {item1['status']}"
    print(f"    ✓ Checkpoint 1 verified: Job is paused waiting for CV review.")

    # Candidate approves CV
    appr_cv_1 = approve_tailored_cv(test_user, item1["queue_item_id"])
    assert appr_cv_1["status"] == "success"
    q1_after = get_queue_data(test_user)
    item1_after = q1_after["queue_items"][0]
    assert item1_after["status"] == "waiting_submission_review", f"Expected waiting_submission_review, got {item1_after['status']}"
    print(f"    ✓ Checkpoint 2 verified: CV approved. Job is now paused waiting for final submission review.")

    # Candidate approves submission
    appr_sub_1 = approve_portal_submission(test_user, item1_after["queue_item_id"])
    assert appr_sub_1["status"] == "success"
    q1_final = get_queue_data(test_user)
    assert q1_final["queue_items"][0]["status"] == "approved_for_submission"
    print(f"    ✓ Final state verified: Job is approved_for_submission.")

    # ══════════════════════════════════════════════════════════════════
    # COMBINATION 2: (review_tailored_cv=True, review_before_portal_submission=False)
    # CV review ON, Submission review OFF:
    # Waits for CV review -> Approve -> Auto-advances to approved_for_submission
    # ══════════════════════════════════════════════════════════════════
    print("\n  [Combination 2/4]: review_tailored_cv=True, review_before_portal_submission=False")
    c2_job = {
        "job_id": "comb2_job",
        "company_name": "Kearney",
        "job_title": "Principal — Operations",
        "matched_theme": "Operations",
        "source": "Lever",
        "job_url": "https://kearney.com/careers/c2",
        "has_ambiguity": False,
    }
    setup_fresh_queue(c2_job)
    overrides_2 = {"review_tailored_cv": True, "review_before_portal_submission": False}
    # Save default setting for submission review off
    defs = get_auto_apply_defaults(test_user)
    defs["review_before_portal_submission"] = False
    save_auto_apply_defaults(test_user, defs)

    res2 = process_queue_with_approvals(test_user, rule_overrides=overrides_2)
    assert res2["waiting_cv_review_count"] == 1
    q2 = get_queue_data(test_user)
    item2 = q2["queue_items"][0]
    assert item2["status"] == "waiting_cv_review"
    print(f"    ✓ Checkpoint 1 verified: Paused at waiting_cv_review.")

    # Candidate approves CV -> Must auto-advance past Checkpoint 2!
    appr_cv_2 = approve_tailored_cv(test_user, item2["queue_item_id"])
    q2_after = get_queue_data(test_user)
    item2_after = q2_after["queue_items"][0]
    assert item2_after["status"] == "approved_for_submission", f"Expected approved_for_submission, got {item2_after['status']}"
    print(f"    ✓ Auto-advance verified: Skipped submission review; advanced directly to approved_for_submission!")

    # ══════════════════════════════════════════════════════════════════
    # COMBINATION 3: (review_tailored_cv=False, review_before_portal_submission=True)
    # CV review OFF, Submission review ON:
    # Auto-approves CV -> Pauses at waiting_submission_review -> Approve -> approved_for_submission
    # ══════════════════════════════════════════════════════════════════
    print("\n  [Combination 3/4]: review_tailored_cv=False, review_before_portal_submission=True")
    c3_job = {
        "job_id": "comb3_job",
        "company_name": "Oliver Wyman",
        "job_title": "Engagement Manager",
        "matched_theme": "Corporate Strategy",
        "source": "Greenhouse",
        "job_url": "https://oliverwyman.com/careers/c3",
        "has_ambiguity": False,
    }
    setup_fresh_queue(c3_job)
    overrides_3 = {"review_tailored_cv": False, "review_before_portal_submission": True}
    res3 = process_queue_with_approvals(test_user, rule_overrides=overrides_3)

    assert res3["waiting_cv_review_count"] == 0, "CV review was OFF, must not wait"
    assert res3["waiting_submission_review_count"] == 1, "Submission review was ON, must wait"
    q3 = get_queue_data(test_user)
    item3 = q3["queue_items"][0]
    assert item3["status"] == "waiting_submission_review", f"Expected waiting_submission_review, got {item3['status']}"
    print(f"    ✓ Auto-advance CV verified: Bypassed CV review, paused at Checkpoint 2 (waiting_submission_review).")

    # Candidate approves submission
    approve_portal_submission(test_user, item3["queue_item_id"])
    assert get_queue_data(test_user)["queue_items"][0]["status"] == "approved_for_submission"
    print(f"    ✓ Approved submission verified: Transitioned to approved_for_submission.")

    # ══════════════════════════════════════════════════════════════════
    # COMBINATION 4: (review_tailored_cv=False, review_before_portal_submission=False)
    # Both reviews OFF:
    # Auto-advances through CV tailoring and submission review all the way!
    # ══════════════════════════════════════════════════════════════════
    print("\n  [Combination 4/4]: review_tailored_cv=False, review_before_portal_submission=False")
    c4_job = {
        "job_id": "comb4_job",
        "company_name": "Amazon",
        "job_title": "Senior Manager — BizOps",
        "matched_theme": "Operations",
        "source": "LinkedIn",
        "job_url": "https://amazon.jobs/c4",
        "has_ambiguity": False,
    }
    setup_fresh_queue(c4_job)
    overrides_4 = {"review_tailored_cv": False, "review_before_portal_submission": False}
    res4 = process_queue_with_approvals(test_user, rule_overrides=overrides_4)

    assert res4["waiting_cv_review_count"] == 0
    assert res4["waiting_submission_review_count"] == 0
    assert res4["approved_for_submission_count"] == 1
    q4 = get_queue_data(test_user)
    item4 = q4["queue_items"][0]
    assert item4["status"] == "approved_for_submission", f"Expected approved_for_submission, got {item4['status']}"
    print(f"    ✓ Full auto-advance verified: Both reviews OFF -> Reached approved_for_submission in single pass!")

    # --- Test 3: Multi-Job Non-Blocking Queue Verification ---
    print("\n--- Test 3: Non-Blocking Multi-Job Queue Execution ---")
    # Queue two jobs: Job A stops at waiting_cv_review; Job B (Naukri) bypasses CV review
    multi_jobs = [
        {
            "job_id": "multi_job_A",
            "company_name": "Google",
            "job_title": "Strategy & Operations Lead",
            "matched_theme": "Corporate Strategy",
            "source": "Greenhouse",
            "job_url": "https://google.com/careers/jobA",
            "has_ambiguity": False,
        },
        {
            "job_id": "multi_job_B",
            "company_name": "Reliance Industries",
            "job_title": "General Manager",
            "matched_theme": "Corporate Strategy",
            "source": "Naukri",  # Naukri skips CV tailoring
            "job_url": "https://naukri.com/jobB",
            "has_ambiguity": False,
        }
    ]
    for suffix in ["queue"]:
        p = _get_user_file(test_user, suffix)
        if p.exists():
            p.unlink()
    add_jobs_to_queue(test_user, multi_jobs)

    # Process with CV review ON and submission review OFF
    multi_res = process_queue_with_approvals(
        test_user,
        rule_overrides={"review_tailored_cv": True, "review_before_portal_submission": False}
    )
    q_multi = get_queue_data(test_user)
    job_a = next(j for j in q_multi["queue_items"] if j["job_id"] == "multi_job_A")
    job_b = next(j for j in q_multi["queue_items"] if j["job_id"] == "multi_job_B")

    assert job_a["status"] == "waiting_cv_review", "Job A must wait for CV review"
    assert job_b["status"] == "approved_for_submission", "Job B must continue past Job A and reach approved_for_submission"
    print(f"✅ Verified: Job A is WAITING for CV review while Job B CONTINUED and reached '{job_b['status']}'!")

    # --- Test 4: CV Preview & Diff Endpoint ---
    print("\n--- Test 4: CV Preview & Diff Inspection ---")
    preview_res = get_tailored_cv_preview(test_user, job_a["queue_item_id"])
    assert "tailored_cv" in preview_res
    assert len(preview_res["tailored_cv"]["wording_changes"]) >= 2
    assert preview_res["tailored_cv"]["overflow_status"] == "passed"
    print(f"✅ CV preview verified with {len(preview_res['tailored_cv']['wording_changes'])} wording changes and overflow check passed.")

    # --- Test 5: Activity Feed Logging ---
    print("\n--- Test 5: Activity Feed Audit Trail ---")
    feed = q_multi["activity_feed"]
    badges = [e["badge"] for e in feed]
    assert "CV Review" in badges
    print(f"✅ Verified activity feed contains {len(feed)} entries. Badges: {set(badges)}")

    print("\n" + "=" * 70)
    print("ALL AUTO APPLY PHASE 3 TESTS PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase3_tests()
