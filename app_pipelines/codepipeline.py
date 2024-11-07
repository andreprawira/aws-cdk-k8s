from dataclasses import dataclass
from constructs import Construct
from aws_cdk import (
    Stack,
    Environment,
    Tags,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_codecommit as codecommit,
    pipelines as pipelines,
    aws_codepipeline_actions as cp_action,
    aws_s3 as s3,
)
from app_configs.config import AppConfigs
from app_stages.infrastructure_stage import InfrastructureStage, InfrastructureStageProps


@dataclass
class PipelineStackProps:
    account_name: str
    account_id: str

class PipelineStack(Stack):
    def __init__(
        self, scope: Construct, id: str, props: PipelineStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.app_config = AppConfigs()
        infra = self.app_config.get_infrastructure_info(props.account_name)

        # Define the pipeline
        pipeline = pipelines.CodePipeline(
            self,
            f"{props.account_name}-pipeline",
            pipeline_name=f"{props.account_name}-cdk-pipeline",
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    privileged=True,
                    compute_type=codebuild.ComputeType.LARGE,
                ),
                partial_build_spec=codebuild.BuildSpec.from_object(
                    {
                        "env": {
                            "git-credential-helper": "yes",
                        }
                    }
                ),
            ),
            synth=pipelines.CodeBuildStep(
                "Synth",
                input=pipelines.CodePipelineSource.s3(
                    bucket=s3.Bucket.from_bucket_name(self, 'bucket-repository', 'aws-cdk-k8s'),
                    object_key="aws-cdk-k8s.zip",
                    trigger=cp_action.S3Trigger.EVENTS
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "npx cdk synth -c account=$account",
                ],
                env={"account": props.account_name},
                role_policy_statements=[
                    iam.PolicyStatement(
                        actions=["sts:AssumeRole"],
                        resources=["*"],
                        conditions={
                            "StringEquals": {
                                "iam:ResourceTag/aws-cdk:bootstrap-role": "lookup"
                            }
                        },
                    )
                ],
            ),
            self_mutation=True,
            cross_account_keys=True,
            enable_key_rotation=True,
            use_change_sets=False,
            docker_enabled_for_synth=True,
            docker_enabled_for_self_mutation=True,
        )

        Tags.of(pipeline).add("map-migrated", "123")


        ################ Infrastructure stage #########################
        infrastructure_props = InfrastructureStageProps(
            account_name=props.account_name,
            account_id=props.account_id,
            region=infra.region,
            general_tags=infra.project_tags,
        )

        infrastructure_stage = InfrastructureStage(
            self,
            "infrastructure-stage",
            props=infrastructure_props,
            env=Environment(account=props.account_id, region=infra.region),
        )

        pipeline.add_stage(infrastructure_stage)
        pipeline.build_pipeline()
