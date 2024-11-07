from aws_cdk import aws_s3 as s3
import constructs as constructs
import cdk8s as cdk8s
import cdk8s_plus_25 as kplus

class MyChart(cdk8s.Chart):
    def __init__(self, scope, id, *, bucket):
        super().__init__(scope, id)

        kplus.Pod(self, "Pod",
            metadata={
                "name": "bob"
            },
            containers=[kplus.ContainerProps(
                image="redis",
                name="redis1",
                env_variables={
                    "BUCKET_NAME": kplus.EnvValue.from_value(bucket.bucket_name)
                },
                security_context=kplus.ContainerSecurityContextProps(
                    user=1000
                ),
            )
            ]
        )

        kplus.Deployment(self, "deployment",
            containers=[kplus.ContainerProps(
                image="nginx",
                name="nginx",
                security_context=kplus.ContainerSecurityContextProps(
                    user=1000
                )
            )
            ],
            replicas=2,
        )
