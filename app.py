#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Tags
from app_pipelines.codepipeline import PipelineStack,PipelineStackProps


app = cdk.App()

account_name = app.node.try_get_context("account_name")
account_id = app.node.try_get_context("account_id")
deployment_account_id = app.node.try_get_context("deployment-account-id")
deployment_account_region = app.node.try_get_context("deployment-account-region")

PipelineStack(
    app,
    f"{account_name}-cdk-pipeline",
    props=PipelineStackProps(account_name=account_name, account_id=account_id),
    env=cdk.Environment(
        account=deployment_account_id, region=deployment_account_region
    ),
)

app.synth()
