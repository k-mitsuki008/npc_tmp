from dataclasses import dataclass
from typing import Optional

import aws_cdk as cdk
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_s3 as s3
from constructs import Construct


@dataclass
class StaticWebHostingConstructProps:
    """Properties for the StaticWebHostingConstruct."""

    create_acm_for_hosted_zone: bool
    certificate: acm.ICertificate
    domain_name: str
    hosted_zone_id: str
    sub_domain_name: Optional[str] = None


class StaticWebHostingConstruct(Construct):
    """A construct for creating a static website hosting with S3 and CloudFront."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        project,
        env_name,
        phase,
        certificate,
        domain_name,
        sub_domain_name,
        hosted_zone_id,
        **kwargs,
    ) -> None:
        """
        :param scope: The scope in which to define this construct.
        :param id: The logical ID of this construct.
        :param props: The properties for this construct.
        """
        super().__init__(scope, id, **kwargs)

        # S3バケットの作成
        bucket_name = (
            f"{sub_domain_name}.{domain_name}" if sub_domain_name else domain_name
        )
        bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            bucket_name=bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # CloudFrontディストリビューションの引数を構築
        distribution_args = {
            "default_root_object": "index.html",
            "default_behavior": cloudfront.BehaviorOptions(
                # S3OriginはOAC(Origin Access Control)を自動で作成・設定します
                origin=origins.S3Origin(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
            ),
        }

        # カスタムドメインと証明書を条件付きで設定
        if create_acm_for_hosted_zone:
            distribution_args["domain_names"] = [bucket_name]
            distribution_args["certificate"] = certificate

        # CloudFrontディストリビューションの作成
        distribution = cloudfront.Distribution(
            self, "Distribution", **distribution_args
        )

        # OACを使用する場合、S3バケットポリシーはCDKが自動的に設定するため、
        # 手動での `bucket.add_to_resource_policy` は不要です。
        # もしOAI(古い方式)を使う場合や、手動で設定したい場合は以下のコードが必要です。
        #
        # bucket.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         actions=["s3:GetObject"],
        #         resources=[bucket.arn_for_objects("*")],
        #         principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        #         conditions={
        #             "StringEquals": {
        #                 "AWS:SourceArn": f"arn:aws:cloudfront::{cdk.Stack.of(self).account}:distribution/{distribution.distribution_id}"
        #             }
        #         }
        #     )
        # )

        # 暗号化通信を行わない場合は、ここで処理を終了
        if not create_acm_for_hosted_zone:
            return

        if not hosted_zone_id:
            raise ValueError(
                "hosted_zone_id must be provided when create_acm_for_hosted_zone is True"
            )

        # 既存のホストゾーンを参照
        # 注意: この実装ではホストゾーン名は常に domain_name になります。
        # サブドメイン(例: sub.example.com)を独立したホストゾーンで管理している場合は、
        # 前の回答で提案したように、zone_nameを明示的に指定できるpropsを追加する修正が必要です。
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "ImportedHostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=domain_name,
        )

        # Route 53にALIASレコードを作成
        route53.ARecord(
            self,
            "AliasRecord",
            zone=hosted_zone,
            # サブドメインがない場合はNoneになり、Apexドメイン(ルート)のレコードになる
            record_name=sub_domain_name,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
