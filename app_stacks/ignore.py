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
class ComponentsStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class ComponentsStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:ComponentsStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        ui_namespace = props.cluster.add_manifest(
            "ui",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "ui"},
            },
        )

        ui_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/components/ui/ui.yaml")
        deploy_ui_pod = props.cluster.add_manifest("ui-pod", *self.read_yaml_file(ui_manifest_path))

        deploy_ui_pod.node.add_dependency(ui_namespace)

        # catalog_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/components/catalog.yaml")
        # props.cluster.add_manifest("components-pod", *self.read_yaml_file(catalog_manifest_path))



    def read_yaml_file(self, file_path):
            import yaml
            with open(file_path, 'r') as file:
                return list(yaml.safe_load_all(file))
