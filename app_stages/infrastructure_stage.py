from dataclasses import dataclass
from aws_cdk import Stage
from constructs import Construct
from app_stacks.argocd_stack import ArgoCDStack, ArgoCDStackProps
from app_stacks.eks_stack import EKSStack,EKSStackProps
from app_stacks.ingress_controller_stack import IngressControllerStack, IngressControllerStackProps
from app_stacks.ui_stack import UiStack, UiStackProps


@dataclass
class InfrastructureStageProps:
    account_name: str
    account_id: str
    region: str
    general_tags: dict[str, str]

class InfrastructureStage(Stage):
    def __init__(
        self, scope: Construct, id: str, props: InfrastructureStageProps, **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        eks_stack = EKSStack(
            self,
            "eks-stack",
            props=EKSStackProps(
                account_name=props.account_name,
                account_id=props.account_id,
                general_tags=props.general_tags
            ),
        )

        argocd_stack = ArgoCDStack(
            self,
            "argocd-stack",
            props=ArgoCDStackProps(
                account_name=props.account_name,
                account_id=props.account_id,
                general_tags=props.general_tags,
                cluster=eks_stack.EKSCluster
            ),
        )

        ingress_controller_stack = IngressControllerStack(
            self,
            "ingress-controller-stack",
            props=IngressControllerStackProps(
                account_name=props.account_name,
                account_id=props.account_id,
                general_tags=props.general_tags,
                cluster=eks_stack.EKSCluster
            ),
        )

        ui_stack = UiStack(
            self,
            "manifests-stack",
            props=UiStackProps(
                account_name=props.account_name,
                account_id=props.account_id,
                general_tags=props.general_tags,
                cluster=eks_stack.EKSCluster
            ),
        )
