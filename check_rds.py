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
print(f"RDS SECURITY AUDIT - {PROFILE}")
print("=" * 70)

# Step 1: Get all RDS instances
print("\n[*] Checking for RDS instances...")
rds_data, err = run_aws(["rds", "describe-db-instances"])

if err or not rds_data:
    print(f"  No RDS instances found or access denied.")
    if err:
        print(f"  Error: {err.strip()[:200]}")
else:
    instances = rds_data.get("DBInstances", [])
    print(f"  Found {len(instances)} RDS instance(s)")

    # Check each instance
    publicly_accessible = []
    ssl_not_enforced = []

    print()
    print("=" * 70)
    print("1. RDS INSTANCES")
    print("=" * 70)
    print()

    for db in instances:
        db_id = db.get("DBInstanceIdentifier", "unnamed")
        engine = db.get("Engine", "N/A")
        engine_ver = db.get("EngineVersion", "")
        endpoint = db.get("Endpoint", {})
        address = endpoint.get("Address", "N/A")
        port = endpoint.get("Port", "N/A")
        public = db.get("PubliclyAccessible", False)
        encrypted = db.get("StorageEncrypted", False)
        status = db.get("DBInstanceStatus", "N/A")
        vpc_sgs = [sg["VpcSecurityGroupId"] for sg in db.get("VpcSecurityGroups", [])]
        param_group = db.get("DBParameterGroups", [{}])[0].get("DBParameterGroupName", "N/A") if db.get("DBParameterGroups") else "N/A"

        print(f"  {db_id}")
        print(f"    Engine:     {engine} {engine_ver}")
        print(f"    Endpoint:   {address}:{port}")
        print(f"    Status:     {status}")
        print(f"    Public:     {public}")
        print(f"    Encrypted:  {encrypted}")
        print(f"    Param Group: {param_group}")
        print(f"    Security Groups: {', '.join(vpc_sgs)}")

        if public:
            publicly_accessible.append(db_id)
            print(f"    ** FINDING: Publicly accessible **")
        print()

    # Step 2: Check parameter groups for SSL enforcement
    print()
    print("=" * 70)
    print("2. SSL/TLS ENFORCEMENT CHECK")
    print("=" * 70)
    print()

    # Get unique parameter groups
    param_groups = set()
    for db in instances:
        for pg in db.get("DBParameterGroups", []):
            param_groups.add((pg.get("DBParameterGroupName", ""), db.get("Engine", "")))

    for pg_name, engine in param_groups:
        if not pg_name:
            continue

        print(f"  Parameter Group: {pg_name} ({engine})")

        # Check SSL parameters based on engine type
        ssl_params = []
        if "mysql" in engine.lower() or "mariadb" in engine.lower() or "aurora-mysql" in engine.lower():
            ssl_params = ["require_secure_transport"]
        elif "postgres" in engine.lower() or "aurora-postgres" in engine.lower():
            ssl_params = ["rds.force_ssl"]
        elif "sqlserver" in engine.lower():
            ssl_params = ["rds.force_ssl"]
        elif "oracle" in engine.lower():
            ssl_params = ["sqlnet.ssl_version"]

        for param_name in ssl_params:
            param_data, perr = run_aws([
                "rds", "describe-db-parameters",
                "--db-parameter-group-name", pg_name,
                "--query", f"Parameters[?ParameterName=='{param_name}']"
            ])

            if param_data and len(param_data) > 0:
                param = param_data[0]
                value = param.get("ParameterValue", "not set")
                print(f"    {param_name} = {value}")
                if value in ("0", "not set", None, ""):
                    ssl_not_enforced.append({"db_param_group": pg_name, "param": param_name, "value": value})
                    print(f"    ** FINDING: SSL/TLS NOT enforced **")
                elif value == "1":
                    print(f"    SSL/TLS enforced (good)")
            else:
                print(f"    {param_name} = not found/not set")
                ssl_not_enforced.append({"db_param_group": pg_name, "param": param_name, "value": "not found"})
                print(f"    ** FINDING: SSL/TLS parameter not configured **")
        print()

    # Step 3: Check RDS clusters (Aurora)
    print()
    print("=" * 70)
    print("3. RDS CLUSTERS (AURORA)")
    print("=" * 70)
    print()

    clusters, cerr = run_aws(["rds", "describe-db-clusters"])
    if clusters and clusters.get("DBClusters"):
        for cluster in clusters["DBClusters"]:
            c_id = cluster.get("DBClusterIdentifier", "unnamed")
            c_engine = cluster.get("Engine", "N/A")
            c_endpoint = cluster.get("Endpoint", "N/A")
            c_port = cluster.get("Port", "N/A")
            c_encrypted = cluster.get("StorageEncrypted", False)

            print(f"  {c_id}")
            print(f"    Engine:    {c_engine}")
            print(f"    Endpoint:  {c_endpoint}:{c_port}")
            print(f"    Encrypted: {c_encrypted}")
            print()
    else:
        print("  No Aurora clusters found.")

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total RDS instances:       {len(instances)}")
    print(f"  Publicly accessible:       {len(publicly_accessible)}")
    print(f"  SSL/TLS not enforced:      {len(ssl_not_enforced)}")
    if publicly_accessible:
        print(f"\n  Publicly accessible instances:")
        for db_id in publicly_accessible:
            print(f"    - {db_id}")
    if ssl_not_enforced:
        print(f"\n  SSL not enforced on:")
        for item in ssl_not_enforced:
            print(f"    - {item['db_param_group']}: {item['param']} = {item['value']}")
    print()
