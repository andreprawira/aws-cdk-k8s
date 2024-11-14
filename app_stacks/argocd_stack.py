from aws_cdk import(
    aws_eks as eks,
    Stack,
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass


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

        argocd_namespace = props.cluster.add_manifest(
            "argocd",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "argocd"},
            },
        )

        sa = props.cluster.add_service_account(
            "argocd-repo-server",
            name="argocd-repo-server",
            namespace="argocd",
        )
        sa.node.add_dependency(argocd_namespace)

        chart = eks.HelmChart(
            self,
            "argocd",
            cluster=props.cluster,
            chart="argo-cd",
            repository="https://argoproj.github.io/argo-helm",
            namespace="argocd",
            version="7.7.1",
        )
        chart.node.add_dependency(sa)
