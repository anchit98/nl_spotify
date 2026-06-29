from __future__ import annotations

import argparse
import sys

from phase6_deploy.config import Settings
from phase6_deploy.deploy_smoke import smoke_deployments
from phase6_deploy.env_pairing import validate_env_pairing
from phase6_deploy.groq_smoke import run_groq_smoke
from phase6_deploy.migrations import load_manifest, validate_manifest, verify_schemas_reachable
from phase6_deploy.reconcile import reconcile_layers
from phase6_deploy.secret_scan import scan_repo


def cmd_secret_scan(settings: Settings) -> int:
    findings = scan_repo(settings.repo_root)
    if findings:
        print("SECRET SCAN FAILED:")
        for item in findings:
            print(f"  - {item}")
        return 1
    print("Secret scan passed.")
    return 0


def cmd_env_pairing(settings: Settings) -> int:
    errors = validate_env_pairing(settings)
    if errors:
        print("ENV PAIRING FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"Env pairing OK (APP_ENV={settings.app_env}).")
    return 0


def cmd_migrations_validate(settings: Settings) -> int:
    manifest = load_manifest(settings.phase6_root)
    errors = validate_manifest(settings.repo_root, settings.phase6_root)
    if errors:
        print("MIGRATION MANIFEST FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"Migration manifest OK ({len(manifest)} files).")
    return 0


def cmd_migrations_dry_run(settings: Settings) -> int:
    code = cmd_migrations_validate(settings)
    if code != 0:
        return code
    errors = verify_schemas_reachable(settings, settings.phase6_root)
    if errors:
        print("MIGRATION DRY-RUN WARNINGS:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Migration dry-run passed (schemas reachable).")
    return 0


def cmd_groq_smoke(settings: Settings) -> int:
    ok, message = run_groq_smoke(settings)
    print(message)
    return 0 if ok else 1


def cmd_deploy_smoke(settings: Settings) -> int:
    errors = smoke_deployments(settings.staging_api_url, settings.production_api_url)
    if errors:
        print("DEPLOY SMOKE FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Deploy smoke passed.")
    return 0


def cmd_reconcile(settings: Settings) -> int:
    warnings, counts = reconcile_layers(settings)
    print("Layer counts:", counts)
    if warnings:
        print("RECONCILE WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
        return 1
    print("Layer reconciliation OK.")
    return 0


def cmd_ci(settings: Settings) -> int:
    steps = [
        ("secret-scan", cmd_secret_scan),
        ("migrations-validate", cmd_migrations_validate),
        ("env-pairing", cmd_env_pairing),
    ]
    for name, fn in steps:
        print(f"--- {name} ---")
        if fn(settings) != 0:
            return 1
    print("Phase 6 CI checks passed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 6: Deployment, CI/CD and fail-proofing")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("secret-scan")
    sub.add_parser("env-pairing")
    sub.add_parser("migrations-validate")
    sub.add_parser("migrations-dry-run")
    sub.add_parser("groq-smoke")
    sub.add_parser("deploy-smoke")
    sub.add_parser("reconcile")
    sub.add_parser("ci")

    args = parser.parse_args()
    settings = Settings.from_env()
    handlers = {
        "secret-scan": cmd_secret_scan,
        "env-pairing": cmd_env_pairing,
        "migrations-validate": cmd_migrations_validate,
        "migrations-dry-run": cmd_migrations_dry_run,
        "groq-smoke": cmd_groq_smoke,
        "deploy-smoke": cmd_deploy_smoke,
        "reconcile": cmd_reconcile,
        "ci": cmd_ci,
    }
    sys.exit(handlers[args.command](settings))


if __name__ == "__main__":
    main()
