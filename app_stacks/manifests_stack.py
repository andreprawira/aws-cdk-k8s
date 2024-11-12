from aws_cdk import(
    aws_eks as eks,
    Stack,
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass
import os


@dataclass
class ManifestsStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class ManifestsStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:ManifestsStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)


        # # Adding Nginx pod manifest from YAML file
        nginx_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/nginx-pod.yaml")
        props.cluster.add_manifest("nginx-pod", *self.read_yaml_file(nginx_manifest_path))


        namespace = props.cluster.add_manifest(
            "ns",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "guestbook"},
            },
        )

        # Adding ArgoCD application manifest from YAML file
        argocd_manifest_path = os.path.join(os.path.dirname(__file__), "../manifests/argocd-application.yaml")
        props.cluster.add_manifest("argocd-application", *self.read_yaml_file(argocd_manifest_path))

        # for manifest in os.path.join(os.path.dirname(__file__), "../manifests/"):
        #     props.cluster.add_manifest("argocd-application", *self.read_yaml_file(manifest))


    def read_yaml_file(self, file_path):
        import yaml
        with open(file_path, 'r') as file:
            return list(yaml.safe_load_all(file))
