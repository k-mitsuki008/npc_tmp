from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct


class ComputeConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        ami_id: str,
        instance_type: str,
        vpc_obj: object,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # アイレットIPアドレスリスト
        iret_ips = [
            # 本社VPN
            "134.238.4.83/32",
            "134.238.4.84/32",
            "114.141.120.185/32",
            "114.141.120.50/32",
            # バックエンド
            "172.234.85.115/32",
            "114.16.196.96/32",
        ]

        # マシンイメージ取得
        ami = ec2.GenericLinuxImage(ami_map={Stack.of(self).region: ami_id})

        # キーペア
        bastion_keypair = ec2.KeyPair(
            self,
            id="BastionKeypair",
            key_pair_name=f"{env_name}-{phase}-key-ec2-bastion",
            region=Stack.of(self).region,
            type=ec2.KeyPairType.RSA,
        )

        # 踏み台用ロール
        bastion_role = iam.Role(
            self,
            id="BastionRole",
            role_name=f"{env_name}-{phase}-role-ec2-bastion",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        bastion_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )

        # EC2用のセキュリティグループ作成
        bastion_sg = ec2.SecurityGroup(
            self,
            id="BastionSg",
            vpc=vpc_obj,
            security_group_name=f"{env_name}-{phase}-sg-ec2-bastion",
        )

        # EC2インスタンスの定義
        ec2.Instance(
            self,
            id="BastionEc2",
            instance_name=f"{env_name}-{phase}-ec2-bastion",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ami,
            key_pair=bastion_keypair,
            detailed_monitoring=True,
            disable_api_termination=True,
            vpc=vpc_obj,
            require_imdsv2=True,
            role=bastion_role,
            security_group=bastion_sg,
            vpc_subnets=ec2.SubnetSelection(
                availability_zones=[f"{Stack.of(self).region}a"],
                subnets=[vpc_obj.private_subnets[0]],
            ),
        )

        # インバウンドルールの追加
        for ip in iret_ips:
            bastion_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(ip),
                connection=ec2.Port.tcp(22),
                description="EC2 allows SSH connections from iret",
            )

        #############################################################
        #      他Constructで使用するインスタンスをOutput                #
        #############################################################
        self.bastion_sg = bastion_sg
