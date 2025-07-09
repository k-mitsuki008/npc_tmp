from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from constructs import Construct


class AcmConstruct(Construct):
    """A construct to manage ACM certificates."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name,
        sub_domain_name,
        hostedzone_id,
        project=None,
        phase=None,
        **kwargs,
    ) -> None:
        """
        :param scope: The scope in which to define this construct.
        :param id: The logical ID of this construct.
        :param domain_name: The domain name for the certificate.
        :param sub_domain_name: The subdomain name for the certificate.
        :param hostedzone_id: The ID of the hosted zone.
        :param project: The project name.
        :param phase: The deployment phase.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id)

        # hosted_zone_idが指定されている必要がある
        if not hostedzone_id:
            raise ValueError(
                "hosted_zone_id must be provided when create_acm_for_hosted_zone is True"
            )

        zone_name = domain_name

        if sub_domain_name:
            zone_name = f"{sub_domain_name}.{zone_name}"
        # 既存のホストゾーンを参照
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "ImportedHostedZone",
            hosted_zone_id=hostedzone_id,
            zone_name=zone_name,
        )

        # サブドメイン名が指定されている場合は配列に追加
        alt_names = []
        if zone_name != domain_name:
            alt_names.append(zone_name)

        # ACM証明書の作成
        self.certificate = acm.Certificate(
            self,
            id="Certificate",
            domain_name=domain_name,
            subject_alternative_names=alt_names,  # 空の配列または要素を含む配列
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )
