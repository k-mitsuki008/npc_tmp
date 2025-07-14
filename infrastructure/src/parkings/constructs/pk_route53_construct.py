import aws_cdk as cdk
from aws_cdk import aws_route53 as route53
from aws_cdk import Duration
from constructs import Construct


class PkRoute53Construct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        hosted_zone_id: str, 
        domain_name: str,
        sub_domains: dict,
        sub_domain_nameservers: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        ###############################
        # 各サブドメインのNSレコード追加 #
        ###############################

        # parkingsのホストゾーン取得
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "ImportedHostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=domain_name
        )

        # 各アカウントのNSレコード追加
        for sub_domain in sub_domains:
            sub_domain_nameserver = sub_domain_nameservers[sub_domain]

            route53.NsRecord(
                self,
                f"{sub_domain.capitalize()}SubDomainNsRecord",
                zone=hosted_zone,
                record_name=f"{sub_domain}.{domain_name}",
                values=sub_domain_nameserver,
                ttl=Duration.minutes(5)
            )
