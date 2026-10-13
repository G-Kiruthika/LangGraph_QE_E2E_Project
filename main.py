from src.graph import result
import os
import json

initial_state = {}
final_response = result.invoke(initial_state)
print("\nGraph execution complete.")

# Create outputs folder
os.makedirs("outputs", exist_ok=True)

# Write outputs
output_path = os.path.join("outputs", "final_scenarios.json")
with open(output_path, "w") as f:
    json.dump(final_response, f, indent=4)
print(f"Outputs written to {output_path}")

testcases_output_path = os.path.join("outputs", "final_testcases.json")
with open(testcases_output_path, "w") as f:
    json.dump(final_response.get("testcases", {}), f, indent=4)
print(f"Testcases written to {testcases_output_path}")

# Display generated test scripts summary in tests/
generated_scripts = final_response.get("generated_test_scripts", [])
if generated_scripts:
    print(f"\n=======================================================")
    print(f"Generated {len(generated_scripts)} Test Scripts in tests/ folder:")
    print(f"=======================================================")
    for item in generated_scripts:
        tc_id = item.get("scenario_id")
        file_path = item.get("file")
        status = item.get("status")
        rounds = item.get("rounds", 1)
        rel_file = os.path.relpath(file_path) if file_path and os.path.exists(file_path) else file_path
        print(f"  [{status}] {tc_id}: {rel_file} (Rounds: {rounds})")
    print(f"=======================================================\n")
