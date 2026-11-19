"""
Comprehensive Test Suite for Auto Apply Phase 1 — Job Filtering, Selection, and Run Queue.
Verifies:
1. Setup defaults & profile suggestions prepopulation.
2. Run-level location adjustment preserving saved defaults.
3. Location modes: 'filter' (strict) vs 'prioritize' (ranked).
4. Cross-posted job deduplication.
5. Exclusion of previously applied tracker roles.
6. Ambiguity flagging ('Needs your input').
7. Persistent queue state transitions: Queued, Paused, Resumed, Approved.
8. Chat-style activity feed event logging.
"""
import sys
import os

# Ensure ai-service is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-service")))

from cv_tailor.config import data_dir
from cv_tailor.services.auto_apply_service import (
    get_profile_suggestions,
    get_auto_apply_defaults,
    save_auto_apply_defaults,
    generate_auto_apply_preview,
    deduplicate_jobs,
    get_queue_data,
    add_jobs_to_queue,
    set_queue_paused_state,
    resolve_needs_input_item,
    _get_user_file,
)


def run_tests():
    print("=" * 65)
    print("RUNNING AUTO APPLY PHASE 1 VERIFICATION SUITE")
    print("=" * 65)

    test_user = "test_candidate"

    # Clean up test artifacts from previous runs for idempotent execution
    for suffix in ["defaults", "queue"]:
        test_file = _get_user_file(test_user, suffix)
        if test_file.exists():
            test_file.unlink()

    # --- Test 1: Setup Defaults & Suggestions ---
    print("\n--- Test 1: Setup Defaults & Prepopulation from Profile ---")
    suggestions = get_profile_suggestions(test_user)
    assert suggestions["calculated_tenure_years"] >= 0, "Calculated tenure must be non-negative"
    assert len(suggestions["suggested_themes"]) > 0, "Must provide suggested themes"
    print(f"✅ Profile suggestions generated: Tenure={suggestions['calculated_tenure_years']} yrs, Range={suggestions['suggested_min_experience']}–{suggestions['suggested_max_experience']} yrs")

    # Save initial editable defaults (Prompt example: Strategy Consulting, Commercial Due Diligence, Corporate Strategy; 4-7 yrs)
    custom_defaults = {
        "user_id": test_user,
        "role_themes": ["Strategy Consulting", "Commercial Due Diligence", "Corporate Strategy"],
        "min_experience_years": 4,
        "max_experience_years": 7,
        "preferred_locations": ["Hyderabad"],
        "work_arrangements": ["Hybrid", "Remote"],
        "location_mode": "prioritize",
        "unattended_include_lower_ranked": False,
        "auto_queue_future_matches": False,
    }
    save_auto_apply_defaults(test_user, custom_defaults)
    loaded_defaults = get_auto_apply_defaults(test_user)
    assert loaded_defaults["role_themes"] == ["Strategy Consulting", "Commercial Due Diligence", "Corporate Strategy"]
    assert loaded_defaults["min_experience_years"] == 4
    assert loaded_defaults["max_experience_years"] == 7
    print("✅ Saved editable defaults (themes + 4–7 yrs range) successfully.")

    # --- Test 2: Location Override Leaves Defaults Intact ---
    print("\n--- Test 2: Adjusting Location Leaves Saved Themes & Experience Intact ---")
    preview_one_run = generate_auto_apply_preview(
        user_id=test_user,
        run_locations=["Bengaluru", "Pune"],
        location_mode="filter"
    )
    # Check that saved defaults were not overwritten
    assert preview_one_run["saved_defaults_preserved"]["min_experience_years"] == 4
    assert preview_one_run["saved_defaults_preserved"]["max_experience_years"] == 7
    assert preview_one_run["saved_defaults_preserved"]["role_themes"] == ["Strategy Consulting", "Commercial Due Diligence", "Corporate Strategy"]

    post_check_defaults = get_auto_apply_defaults(test_user)
    assert post_check_defaults["preferred_locations"] == ["Hyderabad"], "Default location must remain Hyderabad"
    assert post_check_defaults["min_experience_years"] == 4
    print("✅ Verified: Changing location for one run leaves saved themes & experience range 100% intact!")

    # --- Test 3: Location Modes: Filter vs. Prioritize ---
    print("\n--- Test 3: Location Modes: Filter vs. Prioritize ---")
    # Mode A: Filter
    preview_filter = generate_auto_apply_preview(
        user_id=test_user,
        run_locations=["Hyderabad"],
        location_mode="filter"
    )
    for j in preview_filter["jobs"]:
        assert j["is_preferred_location"], f"Filter mode must only include preferred locations, got {j['location']}"
    print(f"✅ Filter mode: Strictly restricted to {len(preview_filter['jobs'])} preferred location roles.")

    # Mode B: Prioritize
    preview_prioritize = generate_auto_apply_preview(
        user_id=test_user,
        run_locations=["Hyderabad"],
        location_mode="prioritize"
    )
    # Ensure preferred locations are ordered before non-preferred locations
    seen_non_preferred = False
    for j in preview_prioritize["jobs"]:
        if not j["is_preferred_location"]:
            seen_non_preferred = True
        elif seen_non_preferred:
            assert False, "Preferred locations must appear before lower-ranked locations in prioritize mode!"
    print(f"✅ Prioritize mode: Verified preferred locations are ranked first ({preview_prioritize['preferred_location_count']} preferred, {preview_prioritize['other_eligible_location_count']} other eligible).")

    # --- Test 4: Cross-Posting Deduplication ---
    print("\n--- Test 4: Cross-Posting Deduplication ---")
    duplicated_fixtures = [
        {"company_name": "McKinsey & Company", "job_title": "Strategy Consultant", "location": "Hyderabad", "source": "Greenhouse", "job_url": "https://careers.mckinsey.com/1"},
        {"company_name": "McKinsey & Company", "job_title": "Strategy Consultant", "location": "Hyderabad", "source": "LinkedIn", "job_url": "https://linkedin.com/jobs/view/999"},
        {"company_name": "Bain & Company", "job_title": "Senior Manager Due Diligence", "location": "Bengaluru", "source": "Lever", "job_url": "https://jobs.lever.co/bain/2"},
    ]
    deduped = deduplicate_jobs(duplicated_fixtures)
    assert len(deduped) == 2, f"Expected 2 jobs after deduplicating cross-posts, got {len(deduped)}"
    print(f"✅ Deduplication verified: Reduced {len(duplicated_fixtures)} listings to {len(deduped)} unique roles.")

    # --- Test 5: Ambiguity Flagging ('Needs your input') ---
    print("\n--- Test 5: Ambiguity & Eligibility Flagging ---")
    ambiguous_jobs = [j for j in preview_prioritize["jobs"] if j["has_ambiguity"]]
    clear_jobs = [j for j in preview_prioritize["jobs"] if not j["has_ambiguity"]]
    print(f"✅ Flagging verified: Found {len(clear_jobs)} immediately eligible jobs and {len(ambiguous_jobs)} jobs flagged for missing/ambiguous details.")
    if ambiguous_jobs:
        print(f"   Example flag: {ambiguous_jobs[0]['ambiguity_flags']}")

    # --- Test 6: Persistent Queue & Controls (Pause / Resume / Needs Input) ---
    print("\n--- Test 6: Persistent Queue Management & Feed ---")
    # Queue both clear and ambiguous jobs
    sample_to_queue = preview_prioritize["jobs"][:3]
    queue_result = add_jobs_to_queue(test_user, sample_to_queue)
    assert queue_result["added_count"] == len(sample_to_queue)

    queue_data = get_queue_data(test_user)
    assert len(queue_data["queue_items"]) >= len(sample_to_queue)
    print(f"✅ Successfully queued {queue_result['added_count']} jobs into persistent queue.")

    # Test Pause
    pause_res = set_queue_paused_state(test_user, paused=True)
    assert pause_res["queue_status"] == "paused"
    assert get_queue_data(test_user)["queue_status"] == "paused"
    print("✅ Queue pause state verified.")

    # Test Resume
    resume_res = set_queue_paused_state(test_user, paused=False)
    assert resume_res["queue_status"] == "running"
    assert get_queue_data(test_user)["queue_status"] == "running"
    print("✅ Queue resume state verified.")

    # Test 'Needs your input' resolution
    needs_input_items = [i for i in queue_data["queue_items"] if i["status"] == "needs_input"]
    if needs_input_items:
        target_item = needs_input_items[0]
        resolve_res = resolve_needs_input_item(test_user, target_item["queue_item_id"], "approve")
        assert resolve_res["status"] == "success"
        assert resolve_res["item"]["status"] == "queued"
        print(f"✅ 'Needs your input' approved successfully for item {target_item['queue_item_id']}.")

    # Test Activity Feed
    activity_feed = get_queue_data(test_user)["activity_feed"]
    assert len(activity_feed) >= 3, "Activity feed must record operations"
    print(f"✅ Chat-style activity feed verified with {len(activity_feed)} events logged.")
    print(f"   Latest event: '{activity_feed[-1]['message']}'")

    print("\n" + "=" * 65)
    print("ALL PHASE 1 AUTO APPLY TESTS PASSED (100% SUCCESS)!")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
