import aws_cdk as cdk
from aws_cdk import aws_cloudtrail as cloudtrail
from aws_cdk import aws_s3 as s3
from constructs import Construct


class cltConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        construct_id: str,
        project: str,
        env_name: str,
        phase: str,
        other_account_ids: dict,
        iam_groups: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cltbucket = s3.Bucket(
            self,
            "cltbucket",
            bucket_name=f"{project}-s3cloudtrail",
        )

        myclt = cloudtrail.Trail(
            self,
            "mycldtrail",
            trail_name=f"{env_name}-trail",
            bucket=cltbucket,
            s3_key_prefix="/AWSLogs/{accountID}",
            encryption_key=False,
            enable_file_validation=True,
            sns_topic=False,
        )

        cloudtrail.AddEventSelectorOptions(
            read_write_type=cloudtrail.ReadWriteType.ALL,
        )
