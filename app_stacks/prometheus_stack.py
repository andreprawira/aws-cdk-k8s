from aws_cdk import(
    aws_eks as eks,
    Stack,
)
from constructs import Construct
from dataclasses import dataclass
import yaml
import os

@dataclass
class PrometheusStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class PrometheusStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:PrometheusStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        # # Read the YAML file
        # yaml_path = os.path.join('chart', 'root-app', 'template', 'prometheus.yaml')
        # with open(yaml_path, 'r') as file:
        #     manifest_data = yaml.safe_load(file)

        # chart = eks.KubernetesManifest(
        #     self,
        #     'chart',
        #     cluster=props.cluster,
        #     manifest=[manifest_data]  # Note: manifest expects a list of manifests
        # )

        # Deploy Prometheus Helm Chart with enhanced configuration
        chart = eks.HelmChart(
            self,
            "prometheus-helm-chart",
            cluster=props.cluster,
            chart="prometheus",
            repository="https://prometheus-community.github.io/helm-charts",
        )
