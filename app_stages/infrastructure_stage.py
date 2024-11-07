from dataclasses import dataclass
from aws_cdk import Stage
from constructs import Construct
from app_stacks.eks_stack import EKSStack
from app_stacks.eks_stack import EKSStackProps


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

        eks = EKSStack(
            self,
            "eks-stack",
            props=EKSStackProps(
                account_name=props.account_name,
                account_id=props.account_id,
                general_tags=props.general_tags
            ),
        )
