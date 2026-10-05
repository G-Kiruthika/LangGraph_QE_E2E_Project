from src.graph import result
import os
import json

# from langchain_core.globals import set_debug
# set_debug(True)

initial_state={}
final_response=result.invoke(initial_state)
print("Graph execution complete.")

# Create outputs folder
os.makedirs("outputs", exist_ok=True)

# Write output to file
output_path = os.path.join("outputs", "final_scenarios.json")
with open(output_path, "w") as f:
    json.dump(final_response, f, indent=4)

print(f"Outputs written to {output_path}")
