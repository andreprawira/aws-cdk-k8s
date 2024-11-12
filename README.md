
# Deploying AWS EKS and ArgoCD with AWS CDK!

## Prerequisites

Create aws sso profile

```
aws configure sso
```

Create a virtualenv

```
$ python -m venv .venv
```

Activate your virtualenv

```
$ .venv\Scripts\activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.


## CDK commands

 * `cdk ls -c account_name=<aws-account-name> -c account_id=<aws-account-id> --profile <aws-sso-profile-name>`          list all stacks in the app
 * `cdk synth -c account_name=<aws-account-name> -c account_id=<aws-account-id> --profile <aws-sso-profile-name>`       emits the synthesized CloudFormation template
 * `cdk deploy nonprod-cdk-pipeline/infrastructure-stage/eks-stack -c account_name=<aws-account-name> -c account_id=<aws-account-id> --profile <aws-sso-profile-name>`      deploy the EKS stack to your AWS account
 * `cdk diff -c account_name=<aws-account-name> -c account_id=<aws-account-id> --profile <aws-sso-profile-name>`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

 ## Connect to the cluster

 Go to the EKS stack deployed, if it succeed, there should be 2 nested stacks, open the parent stack and click Output, copy the first value of the key, it should have a command similar to this

 ```
 aws eks update-kubeconfig --name nonprod-eks-cluster --region us-east-1 --role-arn arn:aws:iam::123456789012:role/infrastructure-stage-eks-stack-eksrole
 ```

 Run the command in your local terminal and you should be able to connect to the cluster
