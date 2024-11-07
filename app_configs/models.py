from dataclasses import dataclass


@dataclass
class InfrastructureSpec:
    account_name: str
    # account_id: str
    repository_name: str
    pipeline_branch_name: str
    instance_type: str
    region: str
    project_tags: dict[str, str]
