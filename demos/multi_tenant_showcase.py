"""Multi-tenant orchestration platform showcase demo.

This demo compresses the platform narrative into one run:
- three tenants
- tenant-scoped workflows
- tenant-scoped schedules
- tenant-scoped policies
- isolated orchestration results
"""

from __future__ import annotations

from orchestration.policy_engine import ExecutionQuota, PolicyEngine
from orchestration.scheduler import WorkflowScheduler
from orchestration.tenant import TenantRegistry
from orchestration.workflow_registry import WorkflowRegistry, WorkflowStage


def build_showcase() -> dict:
    """Build a deterministic multi-tenant orchestration showcase."""
    tenants = TenantRegistry()
    workflows = WorkflowRegistry()
    scheduler = WorkflowScheduler()
    policies = PolicyEngine()

    marketing = tenants.create_tenant(
        "Northstar Marketing Studio",
        metadata={"use_case": "content operations"},
    )
    robotics = tenants.create_tenant(
        "Orangewood Robotics Factory",
        metadata={"use_case": "robot deployment operations"},
    )
    research = tenants.create_tenant(
        "Atlas Research Lab",
        metadata={"use_case": "research automation"},
    )

    tenant_configs = [
        {
            "tenant": marketing,
            "workflow_name": "Content Research Pipeline",
            "namespace": "content",
            "cron": "0 9 * * MON",
            "quota": ExecutionQuota(
                max_concurrent_workflows=5,
                max_scheduled_workflows=10,
                max_replays_per_hour=20,
                max_plugin_executions_per_hour=50,
                max_workflow_executions_per_hour=100,
            ),
            "definition": {
                "steps": [
                    "collect_topic_brief",
                    "build_outline",
                    "draft_article",
                    "review_brand_fit",
                ]
            },
        },
        {
            "tenant": robotics,
            "workflow_name": "CNC Deployment Readiness Workflow",
            "namespace": "robotics",
            "cron": "0 */6 * * *",
            "quota": ExecutionQuota(
                max_concurrent_workflows=8,
                max_scheduled_workflows=15,
                max_replays_per_hour=40,
                max_plugin_executions_per_hour=80,
                max_workflow_executions_per_hour=150,
            ),
            "definition": {
                "steps": [
                    "inspect_cell_state",
                    "validate_robot_program",
                    "simulate_failure_modes",
                    "approve_deployment",
                ]
            },
        },
        {
            "tenant": research,
            "workflow_name": "Paper Review Automation Workflow",
            "namespace": "research",
            "cron": "0 18 * * FRI",
            "quota": ExecutionQuota(
                max_concurrent_workflows=3,
                max_scheduled_workflows=5,
                max_replays_per_hour=10,
                max_plugin_executions_per_hour=25,
                max_workflow_executions_per_hour=50,
            ),
            "definition": {
                "steps": [
                    "ingest_paper",
                    "extract_claims",
                    "compare_references",
                    "generate_review_notes",
                ]
            },
        },
    ]

    showcase_rows = []

    for config in tenant_configs:
        tenant = config["tenant"]
        policy = policies.register_policy(
            tenant_id=tenant.tenant_id,
            quotas=config["quota"],
        )

        workflow = workflows.create_workflow(
            name=config["workflow_name"],
            tenant_id=tenant.tenant_id,
            workflow_namespace=config["namespace"],
            description=f"Demo workflow for {tenant.name}.",
            metadata={"demo": True},
        )

        version = workflows.add_version(
            workflow_id=workflow.workflow_id,
            definition=config["definition"],
            stage=WorkflowStage.PRODUCTION,
            tenant_id=tenant.tenant_id,
        )

        schedule_decision = policies.evaluate_scheduling(
            tenant_id=tenant.tenant_id,
            active_schedule_count=len(
                scheduler.list_schedules(tenant_id=tenant.tenant_id)
            ),
        )

        schedule = None
        if schedule_decision.allowed:
            schedule = scheduler.schedule_workflow(
                workflow_id=workflow.workflow_id,
                tenant_id=tenant.tenant_id,
                workflow_namespace=config["namespace"],
                cron_expression=config["cron"],
                metadata={"demo": True},
            )

        showcase_rows.append(
            {
                "tenant": tenant.to_dict(),
                "policy": policy.to_dict(),
                "workflow": workflow.to_dict(),
                "active_version": version.to_dict(),
                "schedule_decision": schedule_decision.to_dict(),
                "schedule": schedule.to_dict() if schedule else None,
                "tenant_workflow_count": len(
                    workflows.list_workflows(tenant_id=tenant.tenant_id)
                ),
                "tenant_schedule_count": len(
                    scheduler.list_schedules(tenant_id=tenant.tenant_id)
                ),
                "tenant_namespaces": workflows.list_namespaces(tenant.tenant_id),
            }
        )

    return {
        "demo": "multi_tenant_orchestration_showcase",
        "tenant_count": len(tenants.list_tenants()),
        "tenants": tenants.list_tenants(),
        "showcase_rows": showcase_rows,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_showcase(), indent=2))
