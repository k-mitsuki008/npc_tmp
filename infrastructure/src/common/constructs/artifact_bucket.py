import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct

class ArtifactBucketConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project,
        env_name,
        phase,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(
            self,
            "ArtifactBucket",
            bucket_name=f"{project}-{env_name}-{phase}-s3-artifact",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )