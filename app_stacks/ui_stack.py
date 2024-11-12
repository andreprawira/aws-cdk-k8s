from aws_cdk import(
    aws_eks as eks,
    Stack,
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass
import os
from app_configs.config import AppConfigs

@dataclass
class UiStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class UiStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:UiStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        ui_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/ui.yaml")
        props.cluster.add_manifest("ui", *self.read_yaml_file(ui_manifest_path))

    def read_yaml_file(self, file_path):
            import yaml
            with open(file_path, 'r') as file:
                return list(yaml.safe_load_all(file))
