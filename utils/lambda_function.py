import os
import boto3


def lambda_handler(event, context):
    region = os.getenv("region")
    partial_asg_name = "eks-cluster-default-node-group"
    tag_key = "spot-enabled"
    tag_value = "true"

    autoscaling_client = boto3.client("autoscaling", region_name=region)

    try:
        response = autoscaling_client.describe_auto_scaling_groups()
        asg_list = response["AutoScalingGroups"]

        # Finding the ASG based on partial name
        matching_asgs = [
            asg for asg in asg_list if partial_asg_name in asg["AutoScalingGroupName"]
        ]

        if not matching_asgs:
            print(f"No matching ASGs found for partial name: {partial_asg_name}")
            return

        # Finding the ASG based on the matching ASG then tag it
        target_asg_name = matching_asgs[0]["AutoScalingGroupName"]
        response = autoscaling_client.create_or_update_tags(
            Tags=[
                {
                    "ResourceId": target_asg_name,
                    "ResourceType": "auto-scaling-group",
                    "Key": tag_key,
                    "Value": tag_value,
                    "PropagateAtLaunch": False,
                },
            ]
        )
        print(f"Tag added successfully to ASG {target_asg_name}")
    except Exception as e:
        print(f"Error adding tag: {e}")
