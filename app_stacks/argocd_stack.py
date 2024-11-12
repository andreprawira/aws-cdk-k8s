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

        namespace = props.cluster.add_manifest(
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
        sa.node.add_dependency(namespace)

        chart = eks.HelmChart(
            self,
            "argocd",
            cluster=props.cluster,
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
