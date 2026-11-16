import json, subprocess, os

PROFILE = "PROFILE_NAME"

os.makedirs(PROFILE, exist_ok=True)


def run_aws(args):
    cmd = ["aws"] + args + ["--profile", PROFILE, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr
    if not result.stdout.strip():
        return None, "Empty response"
    return json.loads(result.stdout), None


print("=" * 70)
print(f"ECR SECURITY AUDIT - {PROFILE}")
print("=" * 70)

# Step 1: List all ECR repositories
print("\n[*] Listing ECR repositories...")
repos, err = run_aws(["ecr", "describe-repositories"])

if err or not repos:
    print(f"  No ECR repositories found or access denied.")
    if err:
        print(f"  Error: {err.strip()[:200]}")
    exit(1)

repo_list = repos.get("repositories", [])
print(f"  Found {len(repo_list)} repository(ies)")

# Step 2: Check each repository
public_repos = []
pullable_repos = []
policy_findings = []

print()
print("=" * 70)
print("1. REPOSITORY DETAILS")
print("=" * 70)
print()

for repo in repo_list:
    repo_name = repo.get("repositoryName", "unnamed")
    repo_uri = repo.get("repositoryUri", "N/A")
    scan_on_push = repo.get("imageScanningConfiguration", {}).get("scanOnPush", False)
    tag_mutability = repo.get("imageTagMutability", "N/A")
    encryption = repo.get("encryptionConfiguration", {}).get("encryptionType", "N/A")

    print(f"  {repo_name}")
    print(f"    URI:            {repo_uri}")
    print(f"    Scan on Push:   {scan_on_push}")
    print(f"    Tag Mutability: {tag_mutability}")
    print(f"    Encryption:     {encryption}")

    if not scan_on_push:
        print(f"    ** No scan on push — vulnerabilities may go undetected **")
    if tag_mutability == "MUTABLE":
        print(f"    ** Mutable tags — images can be overwritten (supply chain risk) **")

    # Check repository policy
    policy, perr = run_aws(["ecr", "get-repository-policy", "--repository-name", repo_name])
    if policy:
        policy_text = policy.get("policyText", "{}")
        if isinstance(policy_text, str):
            try:
                policy_doc = json.loads(policy_text)
            except Exception:
                policy_doc = {}
        else:
            policy_doc = policy_text

        for stmt in policy_doc.get("Statement", []):
            if stmt.get("Effect") != "Allow":
                continue

            principal = stmt.get("Principal", {})
            principal_values = set()
            if isinstance(principal, str):
                principal_values.add(principal)
            elif isinstance(principal, dict):
                for val in principal.values():
                    if isinstance(val, str):
                        principal_values.add(val)
                    elif isinstance(val, list):
                        principal_values.update(val)

            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "*" in principal_values:
                print(f"    ** FINDING: Wildcard principal in policy — public access **")
                public_repos.append(repo_name)
                policy_findings.append({
                    "repo": repo_name,
                    "issue": "Wildcard principal (*)",
                    "actions": actions,
                })

            # Check for cross-account access
            for pv in principal_values:
                if pv != "*" and ":root" in str(pv):
                    print(f"    Cross-account trust: {pv}")
                    policy_findings.append({
                        "repo": repo_name,
                        "issue": f"Cross-account: {pv}",
                        "actions": actions,
                    })

        print(f"    Policy: Yes")
    else:
        print(f"    Policy: None (account-only access)")

    print()

# Step 3: Attempt to pull/list images from each repository
print()
print("=" * 70)
print("2. IMAGE ACCESS CHECK — PULL PERMISSIONS")
print("=" * 70)
print()

for repo in repo_list:
    repo_name = repo.get("repositoryName", "unnamed")

    # Try to list images
    images, ierr = run_aws(["ecr", "list-images", "--repository-name", repo_name, "--max-items", "10"])

    if images:
        image_ids = images.get("imageIds", [])
        print(f"  {repo_name} — CAN LIST ({len(image_ids)} image(s))")
        pullable_repos.append(repo_name)

        for img in image_ids[:5]:
            tag = img.get("imageTag", "untagged")
            digest = img.get("imageDigest", "N/A")
            print(f"    {tag:<30} {digest[:40]}")

        if len(image_ids) > 5:
            print(f"    ... and {len(image_ids) - 5} more")

        # Try to get download URL (proves pull access)
        if image_ids:
            test_image = image_ids[0]
            batch, berr = run_aws([
                "ecr", "batch-get-image",
                "--repository-name", repo_name,
                "--image-ids", json.dumps([test_image]),
                "--query", "images[0].imageManifest"
            ])
            if batch:
                print(f"    ** CAN PULL — manifest retrieved successfully **")
            else:
                print(f"    List access only — cannot pull manifests")
    else:
        if ierr and "AccessDeniedException" in str(ierr):
            print(f"  {repo_name} — ACCESS DENIED (cannot list images)")
        else:
            print(f"  {repo_name} — No images or error")
    print()

# Step 4: Check ECR Public repositories
print()
print("=" * 70)
print("3. ECR PUBLIC REPOSITORIES")
print("=" * 70)
print()

public_data, pub_err = run_aws(["ecr-public", "describe-repositories"])
if public_data and public_data.get("repositories"):
    pub_repos = public_data["repositories"]
    print(f"  Found {len(pub_repos)} public repository(ies):")
    print()
    for pr in pub_repos:
        pr_name = pr.get("repositoryName", "unnamed")
        pr_uri = pr.get("repositoryUri", "N/A")
        print(f"  {pr_name}")
        print(f"    URI: {pr_uri}")
        print(f"    ** PUBLIC — anyone on the internet can pull these images **")

        # List public images
        pub_images, pierr = run_aws([
            "ecr-public", "describe-images",
            "--repository-name", pr_name,
            "--max-items", "10"
        ])
        if pub_images:
            for img in pub_images.get("imageDetails", [])[:5]:
                tags = img.get("imageTags", ["untagged"])
                size = img.get("imageSizeInBytes", 0)
                pushed = img.get("imagePushedAt", "N/A")
                print(f"    {', '.join(tags):<30} {size/1024/1024:.1f}MB  pushed: {pushed}")
        print()
else:
    if pub_err and "not" in str(pub_err).lower():
        print("  ECR Public not enabled or not available in this region.")
    else:
        print("  No public ECR repositories found.")

# Summary
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Total private repositories:  {len(repo_list)}")
print(f"  With wildcard policy (*):    {len(public_repos)}")
print(f"  With pull access:            {len(pullable_repos)}")
print(f"  Policy findings:             {len(policy_findings)}")
if public_repos:
    print(f"\n  Publicly accessible repos:")
    for r in public_repos:
        print(f"    - {r}")
if policy_findings:
    print(f"\n  Policy findings:")
    for f in policy_findings:
        print(f"    - {f['repo']}: {f['issue']} — {', '.join(f['actions'][:3])}")
print()
