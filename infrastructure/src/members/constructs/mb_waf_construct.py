import aws_cdk as cdk
from aws_cdk import aws_wafv2 as waf
from constructs import Construct



class MembersWafConstruct(Construct):

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
        
        #ipアドレスの指定

        ip_map={
            "prd":{
                "members":[],
            },
            "stg":{
                "members":[
                    "27.86.89.88/32",
                    "27.86.89.89/32",
                    "27.86.90.48/32",
                    "27.86.96.88/32",
                    "27.86.96.160/32",
                    "27.86.96.161/32",
                    "66.159.192.125/32",
                    "66.159.192.6/32",
                    "66.159.193.130/32",
                    "111.107.247.49/32",
                    "111.107.247.50/32",
                    "113.43.220.10/32",
                    "114.141.120.50/32",
                    "114.141.120.185/32",
                    "114.141.123.119/32",
                    "114.141.123.123/32",
                    "114.141.123.40/32",
                    "128.77.80.168/32",
                    "134.238.4.83/32",
                    "134.238.4.84/32",
                    "160.86.107.51/32",
                    "165.85.181.4/32",
                    "208.127.164.253/32",
                    "210.196.211.49/32",
                    "218.225.124.130/32",
                    "222.3.140.116/32",
                    "222.3.140.122/32",
                ]
            },
            "dev":{
                "members":[
                    "113.43.220.10/32",
                    "114.141.120.50/32",
                    "114.141.120.185/32",
                    "134.238.4.83/32",
                    "134.238.4.84/32",
                ]
            },
        }

        ip_list=ip_map.get(env_name,{}).get(phase,[])
        
        myIPSet=waf.CfnIPSet(
            self,
            "IPset",
            name=f"{env_name}-{phase}-webacl-admin-ips",
            addresses=ip_list,
            ip_address_version="IPV4",
            scope="CLOUDFRONT"
        )

        #ホスティング用webacl
        mywaf=waf.CfnWebACL(
            self,
            "mywaf",
            name=f"{env_name}-{phase}-webacl-hosting",
            default_action=waf.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            scope="CLOUDFRONT",
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="Webacl-Metric"
            ),
            rules=[
                waf.CfnWebACL.RuleProperty(
                    name="AllowAccessFromDevelopers",
                    priority=0,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesAmazonIpReputationList",
                            vendor_name="AWS"
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        none={}
                        ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AllowAccess",
                        sampled_requests_enabled=True
                        )
                ),
                waf.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesSQLiRuleSet",
                    priority=1,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesAmazonIpReputationList",
                            vendor_name="AWS"
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        none={}
                        ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWS-AWSManaged",
                        sampled_requests_enabled=True
                        )
                ),
                waf.CfnWebACL.RuleProperty(
                    name=f"{env_name}-{phase}-webacl-ips-rule",
                    priority=2,
                    action=waf.CfnWebACL.RuleActionProperty(
                        block={}
                    ),
                    statement=waf.CfnWebACL.StatementProperty(
                        ip_set_reference_statement=waf.CfnWebACL.IPSetReferenceStatementProperty(
                            arn=myIPSet.attr_arn
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="CumstomWebaclIpsRule",
                        sampled_requests_enabled=True
                        )
                )
            ]
        )