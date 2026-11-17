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


# Tracking findings
findings = {
    "publicly_accessible": [],
    "ssl_not_enforced": [],
    "not_encrypted": [],
    "no_backup": [],
    "no_deletion_protection": [],
    "no_iam_auth": [],
    "no_auto_upgrade": [],
    "default_master_user": [],
    "no_audit_logging": [],
    "no_enhanced_monitoring": [],
    "no_performance_insights": [],
    "outdated_engine": [],
    "public_snapshots": [],
}

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
    exit(1)

instances = rds_data.get("DBInstances", [])
print(f"  Found {len(instances)} RDS instance(s)")

# ============================================================
# 1. INSTANCE DETAILS & EXPOSURE
# ============================================================
print()
print("=" * 70)
print("1. RDS INSTANCES — EXPOSURE & ENCRYPTION")
print("=" * 70)
print()

DEFAULT_USERS = ["admin", "postgres", "root", "master", "sa", "administrator", "rdsadmin"]

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
    master_user = db.get("MasterUsername", "N/A")
    iam_auth = db.get("IAMDatabaseAuthenticationEnabled", False)
    auto_upgrade = db.get("AutoMinorVersionUpgrade", False)
    deletion_protection = db.get("DeletionProtection", False)
    backup_retention = db.get("BackupRetentionPeriod", 0)
    monitoring_interval = db.get("MonitoringInterval", 0)
    perf_insights = db.get("PerformanceInsightsEnabled", False)
    ca_cert = db.get("CACertificateIdentifier", "N/A")
    vpc_sgs = [sg["VpcSecurityGroupId"] for sg in db.get("VpcSecurityGroups", [])]
    subnet_group = db.get("DBSubnetGroup", {}).get("DBSubnetGroupName", "N/A")
    param_group = db.get("DBParameterGroups", [{}])[0].get("DBParameterGroupName", "N/A") if db.get("DBParameterGroups") else "N/A"

    print(f"  {db_id}")
    print(f"    Engine:              {engine} {engine_ver}")
    print(f"    Endpoint:            {address}:{port}")
    print(f"    Status:              {status}")
    print(f"    Master Username:     {master_user}")
    print(f"    Publicly Accessible: {public}")
    print(f"    Storage Encrypted:   {encrypted}")
    print(f"    IAM Auth Enabled:    {iam_auth}")
    print(f"    Auto Minor Upgrade:  {auto_upgrade}")
    print(f"    Deletion Protection: {deletion_protection}")
    print(f"    Backup Retention:    {backup_retention} days")
    print(f"    Enhanced Monitoring: {'Enabled' if monitoring_interval > 0 else 'Disabled'}")
    print(f"    Performance Insights:{perf_insights}")
    print(f"    CA Certificate:      {ca_cert}")
    print(f"    Subnet Group:        {subnet_group}")
    print(f"    Param Group:         {param_group}")
    print(f"    Security Groups:     {', '.join(vpc_sgs)}")

    # Flag findings
    if public:
        findings["publicly_accessible"].append(db_id)
        print(f"    ** FINDING: Publicly accessible **")
    if not encrypted:
        findings["not_encrypted"].append(db_id)
        print(f"    ** FINDING: Storage NOT encrypted **")
    if not iam_auth:
        findings["no_iam_auth"].append(db_id)
        print(f"    ** FINDING: IAM authentication disabled (password-only) **")
    if not auto_upgrade:
        findings["no_auto_upgrade"].append(db_id)
        print(f"    ** FINDING: Auto minor version upgrade disabled **")
    if not deletion_protection:
        findings["no_deletion_protection"].append(db_id)
        print(f"    ** FINDING: No deletion protection **")
    if backup_retention == 0:
        findings["no_backup"].append(db_id)
        print(f"    ** FINDING: Automated backups disabled **")
    if monitoring_interval == 0:
        findings["no_enhanced_monitoring"].append(db_id)
        print(f"    ** FINDING: Enhanced monitoring disabled **")
    if not perf_insights:
        findings["no_performance_insights"].append(db_id)
        print(f"    ** FINDING: Performance Insights disabled **")
    if master_user.lower() in DEFAULT_USERS:
        findings["default_master_user"].append(f"{db_id} ({master_user})")
        print(f"    ** FINDING: Default/common master username '{master_user}' **")

    # Check for enabled log exports
    log_exports = db.get("EnabledCloudwatchLogsExports", [])
    if not log_exports:
        findings["no_audit_logging"].append(db_id)
        print(f"    ** FINDING: No CloudWatch log exports enabled **")
    else:
        print(f"    Log Exports:         {', '.join(log_exports)}")

    print()

# ============================================================
# 2. SSL/TLS ENFORCEMENT
# ============================================================
print()
print("=" * 70)
print("2. SSL/TLS ENFORCEMENT CHECK")
print("=" * 70)
print()

param_groups = set()
for db in instances:
    for pg in db.get("DBParameterGroups", []):
        param_groups.add((pg.get("DBParameterGroupName", ""), db.get("Engine", "")))

for pg_name, engine in param_groups:
    if not pg_name:
        continue

    print(f"  Parameter Group: {pg_name} ({engine})")

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
                findings["ssl_not_enforced"].append({"db_param_group": pg_name, "param": param_name, "value": value})
                print(f"    ** FINDING: SSL/TLS NOT enforced **")
            elif value == "1":
                print(f"    SSL/TLS enforced (good)")
        else:
            print(f"    {param_name} = not found/not set")
            findings["ssl_not_enforced"].append({"db_param_group": pg_name, "param": param_name, "value": "not found"})
            print(f"    ** FINDING: SSL/TLS parameter not configured **")
    print()

# ============================================================
# 3. AURORA CLUSTERS
# ============================================================
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
        c_engine_ver = cluster.get("EngineVersion", "")
        c_endpoint = cluster.get("Endpoint", "N/A")
        c_port = cluster.get("Port", "N/A")
        c_encrypted = cluster.get("StorageEncrypted", False)
        c_iam_auth = cluster.get("IAMDatabaseAuthenticationEnabled", False)
        c_deletion = cluster.get("DeletionProtection", False)
        c_backup = cluster.get("BackupRetentionPeriod", 0)
        c_logs = cluster.get("EnabledCloudwatchLogsExports", [])

        print(f"  {c_id}")
        print(f"    Engine:              {c_engine} {c_engine_ver}")
        print(f"    Endpoint:            {c_endpoint}:{c_port}")
        print(f"    Encrypted:           {c_encrypted}")
        print(f"    IAM Auth:            {c_iam_auth}")
        print(f"    Deletion Protection: {c_deletion}")
        print(f"    Backup Retention:    {c_backup} days")
        print(f"    Log Exports:         {', '.join(c_logs) if c_logs else 'None'}")

        if not c_encrypted:
            print(f"    ** FINDING: Cluster NOT encrypted **")
        if not c_iam_auth:
            print(f"    ** FINDING: IAM auth disabled **")
        if not c_deletion:
            print(f"    ** FINDING: No deletion protection **")
        if c_backup == 0:
            print(f"    ** FINDING: No automated backups **")
        if not c_logs:
            print(f"    ** FINDING: No log exports **")
        print()
else:
    print("  No Aurora clusters found.")

# ============================================================
# 4. PUBLIC SNAPSHOTS
# ============================================================
print()
print("=" * 70)
print("4. PUBLIC RDS SNAPSHOTS")
print("=" * 70)
print()

print("  [*] Checking for publicly shared snapshots...")
snapshots, serr = run_aws(["rds", "describe-db-snapshots", "--snapshot-type", "manual"])
if snapshots and snapshots.get("DBSnapshots"):
    for snap in snapshots["DBSnapshots"]:
        snap_id = snap.get("DBSnapshotIdentifier", "unnamed")

        attrs, aerr = run_aws([
            "rds", "describe-db-snapshot-attributes",
            "--db-snapshot-identifier", snap_id
        ])

        if attrs:
            for attr in attrs.get("DBSnapshotAttributesResult", {}).get("DBSnapshotAttributes", []):
                if attr.get("AttributeName") == "restore":
                    values = attr.get("AttributeValues", [])
                    if "all" in values:
                        findings["public_snapshots"].append(snap_id)
                        print(f"  {snap_id}")
                        print(f"    ** FINDING: Snapshot is PUBLIC — anyone can restore it **")
                        print()
    if not findings["public_snapshots"]:
        print("  No publicly shared snapshots found.")
else:
    print("  No manual snapshots found or access denied.")

# ============================================================
# 5. ENGINE VERSION CHECK
# ============================================================
print()
print("=" * 70)
print("5. ENGINE VERSIONS")
print("=" * 70)
print()

for db in instances:
    db_id = db.get("DBInstanceIdentifier", "unnamed")
    engine = db.get("Engine", "N/A")
    engine_ver = db.get("EngineVersion", "")

    # Check for available upgrades
    upgrades, uerr = run_aws([
        "rds", "describe-db-engine-versions",
        "--engine", engine,
        "--engine-version", engine_ver,
        "--query", "DBEngineVersions[0].ValidUpgradeTarget[?IsMajorVersionUpgrade==`false`].EngineVersion"
    ])

    minor_upgrades = upgrades if upgrades else []

    print(f"  {db_id}: {engine} {engine_ver}")
    if minor_upgrades:
        latest = minor_upgrades[-1] if minor_upgrades else "N/A"
        print(f"    Available minor upgrades: {len(minor_upgrades)} (latest: {latest})")
        if len(minor_upgrades) > 1:
            findings["outdated_engine"].append(f"{db_id} ({engine} {engine_ver}, {len(minor_upgrades)} updates behind)")
            print(f"    ** FINDING: Behind on patches ({len(minor_upgrades)} versions) **")
    else:
        print(f"    Up to date (no minor upgrades available)")
    print()

# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Total RDS instances:             {len(instances)}")
print()
print(f"  Exposure:")
print(f"    Publicly accessible:           {len(findings['publicly_accessible'])}")
print(f"    Public snapshots:              {len(findings['public_snapshots'])}")
print()
print(f"  Encryption:")
print(f"    Storage not encrypted:         {len(findings['not_encrypted'])}")
print(f"    SSL/TLS not enforced:          {len(findings['ssl_not_enforced'])}")
print()
print(f"  Authentication:")
print(f"    IAM auth disabled:             {len(findings['no_iam_auth'])}")
print(f"    Default master username:       {len(findings['default_master_user'])}")
print()
print(f"  Logging & Monitoring:")
print(f"    No audit logging:              {len(findings['no_audit_logging'])}")
print(f"    No enhanced monitoring:        {len(findings['no_enhanced_monitoring'])}")
print(f"    No Performance Insights:       {len(findings['no_performance_insights'])}")
print()
print(f"  Backup & Recovery:")
print(f"    Backups disabled:              {len(findings['no_backup'])}")
print(f"    No deletion protection:        {len(findings['no_deletion_protection'])}")
print()
print(f"  Versioning:")
print(f"    Auto upgrade disabled:         {len(findings['no_auto_upgrade'])}")
print(f"    Outdated engine version:       {len(findings['outdated_engine'])}")
print()

# Detail for key findings
for key, label in [
    ("publicly_accessible", "Publicly accessible"),
    ("not_encrypted", "Not encrypted"),
    ("no_backup", "Backups disabled"),
    ("public_snapshots", "Public snapshots"),
    ("default_master_user", "Default master username"),
    ("outdated_engine", "Outdated engine"),
]:
    if findings[key]:
        print(f"  {label}:")
        for item in findings[key]:
            print(f"    - {item}")
        print()
                    
