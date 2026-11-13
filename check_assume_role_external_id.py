import json, subprocess

PROFILE = "PROFILE_NAME"
CURRENT_ACCOUNT = "ACCOUNT_ID"

print("Do not forget to update the account number in this script")
print(" ")
print("Getting all role details...")
result = subprocess.run(
    ["aws", "iam", "get-account-authorization-details", "--filter", "Role", "--profile", PROFILE, "--output", "json"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)

missing = []
has_it = []

for role in data.get("RoleDetailList", []):
    name = role["RoleName"]
    for stmt in role.get("AssumeRolePolicyDocument", {}).get("Statement", []):
        if stmt.get("Effect") != "Allow" or "AssumeRole" not in str(stmt.get("Action", "")):
            continue
        principal = stmt.get("Principal", {})
        if "Service" in principal and "AWS" not in principal:
            continue
        aws_p = principal.get("AWS", [])
        if isinstance(aws_p, str):
            aws_p = [aws_p]
        for p in aws_p:
            if CURRENT_ACCOUNT in p:
                continue
            cond = stmt.get("Condition", {})
            entry = (name, p, json.dumps(cond, indent=2) if cond else "NONE")
            if "sts:ExternalId" in json.dumps(cond):
                has_it.append(entry)
            else:
                missing.append(entry)

print()
print("=" * 60)
print(f"MISSING EXTERNAL ID - Findings ({len(missing)}):")
print("=" * 60)
for m in missing:
    print(f"  [MISSING] {m[0]}")
    print(f"            Trusted: {m[1]}")
    print(f"            Conditions: {m[2]}")
    print()
if not missing:
    print("  None found")

print()
print("=" * 60)
print(f"HAS EXTERNAL ID - OK ({len(has_it)}):")
print("=" * 60)
for h in has_it:
    print(f"  [OK] {h[0]}")
    print(f"        Trusted: {h[1]}")
if not has_it:
    print("  None")
