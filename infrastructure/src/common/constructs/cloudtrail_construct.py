import aws_cdk as cdk
from aws_cdk import aws_cloudtrail as cloudtrail
from aws_cdk import aws_s3 as s3
from constructs import Construct


class cloudtrailConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        cltbucket = s3.Bucket(
            self,
            "cltbucket",
            bucket_name=f"{project}-{env_name}-{phase}-s3-cloudtrail",
        )

        mycloudtrail = cloudtrail.Trail(
            scope=self,
            id="mycloudtrail",
            trail_name=f"{env_name}-{phase}-trail",
            bucket=cltbucket,
            s3_key_prefix="/AWSLogs/{accountID}",
            encryption_key=None,
            enable_file_validation=True,
            sns_topic=None,
        )
