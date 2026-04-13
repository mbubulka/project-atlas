import json
pg_gen = {}
with open("tests/static_test_scenarios.json", "r") as f:
    scenarios = json.load(f)
    for s in scenarios["scenarios"]:
        pg = s.get("paygrade", "UNKNOWN")
        pg_gen[pg] = pg_gen.get(pg, 0) + 1

print("Generated Scenarios:")
print(f"  Total: {len(scenarios[\"scenarios\"])}")
print(f"  E-5: {pg_gen.get(\"E-5\", 0)}")
print(f"  E-6: {pg_gen.get(\"E-6\", 0)}")
print(f"  O-3: {pg_gen.get(\"O-3\", 0)}")
print(f"  E-9: {pg_gen.get(\"E-9\", 0)}")
