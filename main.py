from src.graph import result
import os
import json
import sys

# User Input: Jira Issue Key
issue_key = input("Enter the Jira User Story Issue Key (e.g. AUT-1): ").strip()
if not issue_key:
    issue_key = "AUT-1"
    print(f"No input provided. Using default: {issue_key}")

print(f"\n[START] Starting pipeline for Jira story: {issue_key}\n")

# Invoke the Graph
initial_state = {"issue_key": issue_key}
final_response = result.invoke(initial_state)

# Check for Early Error Halt
if final_response.get("error"):
    print(f"\n=======================================================")
    print(f"[HALTED] PIPELINE STOPPED: {final_response['error']}")
    print(f"=======================================================\n")
    sys.exit(1)

print("\nGraph execution complete.")

# Write Outputs
os.makedirs("outputs", exist_ok=True)

# Write final scenarios
output_path = os.path.join("outputs", "final_scenarios.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_response, f, indent=4)
print(f"Outputs written to {output_path}")

# Write final test cases
testcases_output_path = os.path.join("outputs", "final_testcases.json")
with open(testcases_output_path, "w", encoding="utf-8") as f:
    json.dump(final_response.get("testcases", {}), f, indent=4)
print(f"Testcases written to {testcases_output_path}")

# Display Generated Test Scripts Summary
generated_scripts = final_response.get("generated_test_scripts", [])
if generated_scripts:
    print(f"\n=======================================================")
    print(f"Generated {len(generated_scripts)} Test Scripts in outputs/final_testscripts/:")
    print(f"=======================================================")
    for item in generated_scripts:
        tc_id = item.get("scenario_id")
        file_path = item.get("file")
        status = item.get("status")
        rounds = item.get("rounds", 1)
        rel_file = os.path.relpath(file_path) if file_path and os.path.exists(file_path) else file_path
        print(f"  [{status}] {tc_id}: {rel_file} (Rounds: {rounds})")
    print(f"=======================================================\n")
