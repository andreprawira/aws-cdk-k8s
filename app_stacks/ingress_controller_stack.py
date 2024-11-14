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
class IngressControllerStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class IngressControllerStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:IngressControllerStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        eks.HelmChart(
            self,
            'alb-controller-chart',
            cluster=props.cluster,
            chart='aws-load-balancer-controller',
            repository='https://aws.github.io/eks-charts',
            namespace='kube-system',
            values={
                "clusterName": "eks-cluster",
                "serviceAccount": {
                     "name": "aws-load-balancer-controller-sa"
                }
            }
        )

        ingress_resource_path = os.path.join(os.path.dirname(__file__), "../manifests/ingress-resource.yaml")
        props.cluster.add_manifest("ingress-resource", *self.read_yaml_file(ingress_resource_path))

    def read_yaml_file(self, file_path):
            import yaml
            with open(file_path, 'r') as file:
                return list(yaml.safe_load_all(file))
