import json
import os
from os.path import dirname, join

from aws_cdk import Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct

# from dotenv import load_dotenv
#
# load_dotenv(verbose=True)
# dotenv_path = join(dirname(__file__), ".env")
# load_dotenv(dotenv_path)


class DatabaseConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        vpc_obj: object,
        bastion_sg: object,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        #########################
        #    Security Group     #
        #########################

        # RDS用のセキュリティグループ
        rds_sg = ec2.SecurityGroup(
            self,
            id="RdsSg",
            security_group_name=f"{env_name}-{phase}-sg-rds",
            vpc=vpc_obj,
        )
        #        rds_sg.add_ingress_rule(
        #            peer=lambda_sg,
        #            connection=ec2.Port.tcp(5432),
        #            description="Allow Lambda to access RDS"
        #        )
        #        rds_sg.add_ingress_rule(
        #            peer=ecs_sg,
        #            connection=ec2.Port.tcp(5432),
        #            description="Allow ECS to access RDS"
        #        )
        rds_sg.add_ingress_rule(
            peer=bastion_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow EC2 to access RDS",
        )

        #########################
        #          RDS          #
        #########################

        # サブネットグループ
        rds_subnet_group = rds.SubnetGroup(
            self,
            id="RdsSubnetGroup",
            description="RDS subnet group",
            vpc=vpc_obj,
            subnet_group_name=f"{env_name}-{phase}-rds-subgrp",
            vpc_subnets=ec2.SubnetSelection(
                availability_zones=["ap-northeast-1a", "ap-northeast-1c"],
                one_per_az=False,
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        )

        # 接続用シークレット
        rds_secret = rds.DatabaseSecret(
            self,
            id="RdsSecret",
            secret_name=f"{env_name}-{phase}-rds-secret",
            dbname=f"{env_name}_{phase}_rds",
            username="AdminUser",
        )

        # クラスター／インスタンス作成
        aurora = rds.DatabaseCluster(
            self,
            id="Aurora",
            cluster_identifier=f"{env_name}-{phase}-rds-cluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_17_4
            ),
            credentials=rds.Credentials.from_secret(secret=rds_secret),
            vpc=vpc_obj,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            writer=rds.ClusterInstance.provisioned(
                "writer",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.LARGE
                ),
                instance_identifier=f"{env_name}-{phase}-rds-instance-01",
                preferred_maintenance_window="Tue:15:30-Tue:16:30",
            ),
            readers=[
                rds.ClusterInstance.provisioned(
                    "reader",
                    instance_type=ec2.InstanceType.of(
                        ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.LARGE
                    ),
                    instance_identifier=f"{env_name}-{phase}-rds-instance-02",
                    preferred_maintenance_window="Tue:15:30-Tue:16:30",
                )
            ],
            security_groups=[rds_sg],
            subnet_group=rds_subnet_group,
            backup=rds.BackupProps(
                retention=Duration.days(7), preferred_window="20:30-21:00"
            ),
            auto_minor_version_upgrade=False,
            storage_encrypted=True,
            deletion_protection=True,
            monitoring_interval=Duration.seconds(60),
            enable_cluster_level_enhanced_monitoring=True,
            preferred_maintenance_window="Tue:15:30-Tue:16:30",
        )

        #########################
        #       RDS Proxy       #
        #########################

        # RDS Proxy用のIAMロール作成
        proxy_role = iam.Role(
            self,
            "RdsProxyRole",
            assumed_by=iam.ServicePrincipal("rds.amazonaws.com"),
            role_name=f"{project}-{env_name}-{phase}-role-rds-proxy",
            description=f"Role for RDS Proxy in {env_name}-{phase}",
        )

        # Secret Managerへのアクセス権限を付与
        rds_secret.grant_read(proxy_role)

        # RDS Proxyの作成
        proxy = rds.DatabaseProxy(
            self,
            "RdsProxy",
            db_proxy_name=f"{env_name}-{phase}-rds-proxy",
            proxy_target=rds.ProxyTarget.from_cluster(aurora),
            secrets=[rds_secret],
            vpc=vpc_obj,
            vpc_subnets=ec2.SubnetSelection(
                subnets=[vpc_obj.private_subnets[0], vpc_obj.private_subnets[1]]
            ),
            role=proxy_role,
            require_tls=True,
            idle_client_timeout=Duration.seconds(1800),
            debug_logging=True,
        )

        # 明示的な依存関係を追加
        proxy.node.add_dependency(aurora)

        # プロキシエンドポイントの作成
        proxy_endpoint = rds.CfnDBProxyEndpoint(
            self,
            "ProxyEndpoint",
            db_proxy_endpoint_name=f"{env_name}-{phase}-rds-proxy-endpoint",
            db_proxy_name=proxy.db_proxy_name,
            vpc_subnet_ids=[
                vpc_obj.private_subnets[0].subnet_id,
                vpc_obj.private_subnets[1].subnet_id,
            ],
            # target_role=rds.ProxyEndpointTargetRole.READ_WRITE,
            vpc_security_group_ids=[rds_sg.security_group_id],
        )
        # エンドポイントもproxyに依存させる
        proxy_endpoint.node.add_dependency(proxy)


#        #シークレット
#        secret_aurora_read_only = secretsmanager.Secret(
#            self,
#            id=f"{env_name}-{phase}-db-read-only-user-secret",
#            secret_name=f"{env_name}-{phase}-db-read-only-user-secret",
#            generate_secret_string=secretsmanager.SecretStringGenerator(
#                secret_string_template=json.dumps(
#                    {
#                        "READONLYUSER-SECRET": os.getenv(f"READONLYUSER-{phase}"),
#                    },
#                ),
#                generate_string_key="password"
#            )
#        )
