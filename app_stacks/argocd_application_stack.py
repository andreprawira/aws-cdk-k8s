from aws_cdk import(
    aws_eks as eks,
    Stack,
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass
import os


@dataclass
class ArgoCDStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class ArgoCDStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:ArgoCDStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        # Adding ArgoCD application manifest from YAML file
        argocd_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/argocd-application.yaml")
        argocd_application = props.cluster.add_manifest("argocd-application", self.app_config.read_yaml_file(argocd_manifest_path))
