from aws_cdk import(
    aws_eks as eks,
    lambda_layer_kubectl_v31,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass

from app_manifests.deployment import Deployment


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
        self.cluster = eks.Cluster(self, "hello-eks",
            version=eks.KubernetesVersion.V1_31,
            kubectl_layer=lambda_layer_kubectl_v31.KubectlV31Layer(self, "kubectl"),
            cluster_name="perfecta-nonprod-eks-cluster",
            masters_role=eks_role
        )

        self.cluster.aws_auth.add_masters_role(
            iam.Role.from_role_name(self, "SSOAdminRole", "AWSReservedSSO*")
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

        bucket = s3.Bucket(self, "Bucket")

        # create a cdk8s chart and use `cdk8s.App` as the scope.
        deployment = Deployment(cdk8s.App(), "MyChart", bucket=bucket)

        # add the cdk8s chart to the cluster
        self.cluster.add_cdk8s_chart("my-chart", deployment)
