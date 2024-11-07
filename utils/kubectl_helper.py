from aws_cdk import aws_eks as eks, aws_iam as iam


def get_kubectl_provider(scope, cluster) -> eks.IKubectlProvider:
    return eks.KubectlProvider.get_or_create(scope=scope, cluster=cluster)


def import_cluster(scope, cluster) -> eks.ICluster:
    cluster_name = cluster.cluster_name
    kubectl_role_arn = cluster.kubectl_role.role_arn
    kubectl_lambda_role = cluster.kubectl_lambda_role
    open_id_connect_provider_arn = (
        cluster.open_id_connect_provider.open_id_connect_provider_arn
    )
    kubectl_provider = get_kubectl_provider(scope, cluster)

    return eks.Cluster.from_cluster_attributes(
        scope,
        "imported-eks-cluster",
        cluster_name=cluster_name,
        kubectl_role_arn=kubectl_role_arn,
        open_id_connect_provider=iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            scope,
            "ImportedOpenIdConnectProvider",
            open_id_connect_provider_arn=open_id_connect_provider_arn,
        ),
        kubectl_provider=kubectl_provider,
        kubectl_lambda_role=kubectl_lambda_role,
    )
