from aws_cdk import(
    aws_eks as eks,
    Stack,
    aws_iam as iam,
    Tags,
    CfnJson
)
import cdk8s as cdk8s
from constructs import Construct
from dataclasses import dataclass

@dataclass
class KarpenterStackProps:
    cluster: eks.Cluster
    account_name: str
    account_id: str
    general_tags: dict[str, str]


class KarpenterStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props:KarpenterStackProps, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, tags=props.general_tags, **kwargs)

        # Create Karpenter Node Role
        karpenter_node_role = iam.Role(
            self,
            "karpenter-node-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

        # Add required policies to node role
        karpenter_node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy")
        )
        karpenter_node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy")
        )
        karpenter_node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly")
        )
        karpenter_node_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        # Create Karpenter Service Account
        karpenter_sa = props.cluster.add_service_account(
            "karpenter-controller",
            name="karpenter",
            namespace="kube-system"
        )

        # Deploy Karpenter Helm Chart with enhanced configuration
        chart = eks.HelmChart(
            self,
            "karpenter",
            cluster=props.cluster,
            chart="karpenter",
            repository="oci://public.ecr.aws/karpenter/karpenter",
            namespace="kube-system",
            version="1.0.8",
            values={
                "settings": {
                    "clusterName": props.cluster.cluster_name,
                    "clusterEndpoint": props.cluster.cluster_endpoint,
                    "interruptionQueue": f"{props.cluster.cluster_name}-queue",
                    "aws": {
                        "defaultInstanceProfile": karpenter_node_role.role_name,
                        "clusterName": props.cluster.cluster_name,
                        "clusterEndpoint": props.cluster.cluster_endpoint
                    }
                },
                "serviceAccount": {
                    "create": True,
                    "name": "karpenter",
                    "annotations": {
                        "eks.amazonaws.com/role-arn": karpenter_sa.role.role_arn
                    }
                },
                "controller": {
                    "resources": {
                        "requests": {
                            "cpu": "1",
                            "memory": "1Gi"
                        },
                        "limits": {
                            "cpu": "1",
                            "memory": "1Gi"
                        }
                    }
                }
            }
        )
