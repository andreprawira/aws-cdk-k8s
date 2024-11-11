from aws_cdk import(
    aws_eks as eks,
    lambda_layer_kubectl_v31,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass
from app_charts.deployment import Deployment
import os


@dataclass
class EKSStackProps:
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class EKSStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:EKSStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        # creating a master role for the cluster
        eks_role = iam.Role(
            self,
            "eks-role",
            assumed_by=iam.AnyPrincipal(),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonEKSClusterPolicy"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonEKSServicePolicy"
                )
            ]
        )

        # provisioning a cluster
        self.cluster = eks.Cluster(self, "eks-cluster",
            version=eks.KubernetesVersion.V1_31,
            kubectl_layer=lambda_layer_kubectl_v31.KubectlV31Layer(self, "kubectl"),
            cluster_name="eks-cluster",
            masters_role=eks_role
        )

        self.cluster.aws_auth.add_masters_role(
            iam.Role.from_role_name(self, "SSOAdminRole", "AWSReservedSSO_AdministratorAccess_0c90745618e18a74")
        )

        default_node_group = eks.Nodegroup(
            self,
            "default-node-group",
            cluster=self.cluster,
            nodegroup_name="cluster-default-node-group",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=2,
            max_size=3
        )

        namespace = self.cluster.add_manifest(
            "argocd",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "argocd"},
            },
        )

        sa = self.cluster.add_service_account(
            "argocd-repo-server",
            name="argocd-repo-server",
            namespace="argocd",
        )
        sa.node.add_dependency(namespace)

        chart = eks.HelmChart(
            self,
            "argocd",
            cluster=self.cluster,
            chart="argo-cd",
            repository="https://argoproj.github.io/argo-helm",
            namespace="argocd",
            version="5.53.0",
            values={
                "nameOverride": "argocd",
                "fullnameOverride": "argocd",
                "configs": {
                    "cmp": {
                        "create": True,
                        "plugins": {
                            "avp": {
                                "generate": {
                                    "command": ["argocd-vault-plugin", "generate", "."]
                                },
                            }
                        },
                    },
                },
                "repoServer": {
                    "serviceAccount": {
                        "create": False,
                        # do not try to use the name from sa, circular
                        "name": "argocd-repo-server",
                    },
                    "volumeMounts": [
                        {
                            "mountPath": "/usr/local/bin/argocd-vault-plugin",
                            "name": "custom-tools",
                            "subPath": "argocd-vault-plugin",
                        },
                        {
                            "mountPath": "/usr/local/bin/envsubst",
                            "name": "custom-tools",
                            "subPath": "envsubst",
                        },
                        {
                            "mountPath": "/usr/local/bin/kubectl",
                            "name": "custom-tools",
                            "subPath": "kubectl",
                        },
                    ],
                    "extraContainers": [
                        {
                            "name": "avp",
                            "command": ["/var/run/argocd/argocd-cmp-server"],
                            "image": "ubuntu:22.04",
                            "securityContext": {"runAsNonRoot": True, "runAsUser": 999},
                            "volumeMounts": [
                                {"mountPath": "/var/run/argocd", "name": "var-files"},
                                {
                                    "mountPath": "/home/argocd/cmp-server/plugins",
                                    "name": "plugins",
                                },
                                {"mountPath": "/tmp", "name": "avp-tmp"},
                                {
                                    "mountPath": "/usr/local/bin/argocd-vault-plugin",
                                    "name": "custom-tools",
                                    "subPath": "argocd-vault-plugin",
                                },
                                {
                                    "mountPath": "/usr/local/bin/envsubst",
                                    "name": "custom-tools",
                                    "subPath": "envsubst",
                                },
                                {
                                    "mountPath": "/usr/local/bin/kubectl",
                                    "name": "custom-tools",
                                    "subPath": "kubectl",
                                },
                                {
                                    "mountPath": "/usr/local/bin/helm",
                                    "name": "custom-tools",
                                    "subPath": "helm",
                                },
                                {
                                    "mountPath": "/home/argocd/cmp-server/config/plugin.yaml",
                                    "subPath": "avp.yaml",
                                    "name": "cmp-plugin",
                                },
                                {"mountPath": "/etc/ssl", "name": "ssl"},
                            ],
                        }
                    ],
                    "initContainers": [
                        {
                            "name": "download-tools",
                            "image": "ubuntu:22.04",
                            "command": ["sh", "-c"],
                            "env": [
                                {"name": "KUBECTL_VERSION", "value": "1.28.6"},
                                {"name": "HELM_VERSION", "value": "3.12.3"},
                                {"name": "AVP_VERSION", "value": "1.16.1"},
                            ],
                            "args": [
                                "apt-get update -y && apt-get install -y wget gettext-base ca-certificates && update-ca-certificates\ncp /usr/bin/envsubst /custom-tools/\nwget -O kubectl https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl && chmod +x kubectl && mv kubectl /custom-tools/\nwget https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz && tar xzvf helm*.tar.gz && mv linux-amd64/helm /custom-tools/\nwget -O argocd-vault-plugin https://github.com/argoproj-labs/argocd-vault-plugin/releases/download/v${AVP_VERSION}/argocd-vault-plugin_${AVP_VERSION}_linux_amd64 && chmod +x argocd-vault-plugin && mv argocd-vault-plugin /custom-tools/"
                            ],
                            "volumeMounts": [
                                {"mountPath": "/custom-tools", "name": "custom-tools"},
                                {"mountPath": "/etc/ssl", "name": "ssl"},
                            ],
                        }
                    ],
                    "volumes": [
                        {"name": "custom-tools", "emptyDir": {}},
                        {"name": "avp-tmp", "emptyDir": {}},
                        {"name": "avp-envsubst-tmp", "emptyDir": {}},
                        {"name": "avp-helm-tmp", "emptyDir": {}},
                        {"name": "avp-helm-envsubst-tmp", "emptyDir": {}},
                        {"name": "avp-helm-with-args-tmp", "emptyDir": {}},
                        {"name": "avp-helm-inline-tmp", "emptyDir": {}},
                        {"name": "envsubst-tmp", "emptyDir": {}},
                        {"name": "envsubst-kustomize-tmp", "emptyDir": {}},
                        {"name": "envsubst-helm-tmp", "emptyDir": {}},
                        {"name": "envsubst-helm-with-args-tmp", "emptyDir": {}},
                        {"name": "ssl", "emptyDir": {}},
                        {"configMap": {"name": "argocd-cmp-cm"}, "name": "cmp-plugin"},
                    ],
                },
            },
        )
        chart.node.add_dependency(sa)

         # Apply Nginx pod manifest from YAML file
        manifest_path = os.path.join(os.path.dirname(__file__), "../app_charts/nginx-pod.yaml")
        self.cluster.add_manifest("nginx-pod", *self.read_yaml_file(manifest_path))

        # # Apply Argo CD manifest from YAML file
        # argocd_manifest_path = os.path.join(os.path.dirname(__file__), "../app_charts/argo-cd/Chart.yaml")
        # self.cluster.add_manifest("argocd", *self.read_yaml_file(argocd_manifest_path))


    def read_yaml_file(self, file_path):
        import yaml
        with open(file_path, 'r') as file:
            return list(yaml.safe_load_all(file))
