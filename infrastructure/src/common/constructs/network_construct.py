from aws_cdk import Aspects, RemovalPolicy, Tag
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkConstruct(Construct):

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

        #########################
        #          VPC          #
        #########################
        # VPC
        my_vpc = ec2.Vpc(
            self,
            id="MyVpc",
            vpc_name=f"{env_name}-{phase}-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,  # 必要になったら2にする
            # VPC作成時デフォルトで生成されるセキュリティグループを作成しないようにする設定
            restrict_default_security_group=True,
            subnet_configuration=[
                # パブリックサブネット
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name=f"{env_name}-{phase}-public-subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
                # プライベートサブネット with NatGateway
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name=f"{env_name}-{phase}-protected-subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
                # プライベートサブネット
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name=f"{env_name}-{phase}-private-subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                ),
            ],
        )
        my_vpc.apply_removal_policy(RemovalPolicy.DESTROY)

        # 各サブネットを取得
        cfn_public_subnet_a = my_vpc.public_subnets[0].node.default_child
        cfn_public_subnet_b = my_vpc.public_subnets[1].node.default_child
        cfn_privete_egress_subnet_a = my_vpc.private_subnets[0].node.default_child
        cfn_privete_egress_subnet_b = my_vpc.private_subnets[1].node.default_child
        cfn_private_subnet_a = my_vpc.isolated_subnets[0].node.default_child
        cfn_private_subnet_b = my_vpc.isolated_subnets[1].node.default_child

        # 各サブネットのNameタグを上書き
        Aspects.of(cfn_public_subnet_a).add(
            Tag("Name", f"{env_name}-{phase}-subnet-public-1a")
        )
        Aspects.of(cfn_public_subnet_b).add(
            Tag("Name", f"{env_name}-{phase}-subnet-public-1c")
        )
        Aspects.of(cfn_privete_egress_subnet_a).add(
            Tag("Name", f"{env_name}-{phase}-subnet-protected-1a")
        )
        Aspects.of(cfn_privete_egress_subnet_b).add(
            Tag("Name", f"{env_name}-{phase}-subnet-protected-1c")
        )
        Aspects.of(cfn_private_subnet_a).add(
            Tag("Name", f"{env_name}-{phase}-subnet-private-1a")
        )
        Aspects.of(cfn_private_subnet_b).add(
            Tag("Name", f"{env_name}-{phase}-subnet-private-1c")
        )

        # 各サブネットに明示的なCIDRを上書き
        cfn_public_subnet_a.add_property_override("CidrBlock", "10.0.0.0/24")
        cfn_public_subnet_b.add_property_override("CidrBlock", "10.0.1.0/24")
        cfn_privete_egress_subnet_a.add_property_override("CidrBlock", "10.0.10.0/24")
        cfn_privete_egress_subnet_b.add_property_override("CidrBlock", "10.0.11.0/24")
        cfn_private_subnet_a.add_property_override("CidrBlock", "10.0.20.0/24")
        cfn_private_subnet_b.add_property_override("CidrBlock", "10.0.21.0/24")

        #########################
        #    Security Group     #
        #########################

        # VPCEndPoint用のセキュリティグループ
        vpc_endpoint_sg = ec2.SecurityGroup(
            self,
            id="VpcEndpointSg",
            vpc=my_vpc,
            security_group_name=f"{env_name}-{phase}-sg-vpc-endpoint",
        )

        #########################
        #      VPC EndPoint     #
        #########################

        # VPCエンドポイント（Secrets Manager）
        # my_vpc.add_interface_endpoint(
        #    id="VpcEndpointSecrets",
        #    service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        #    subnets=ec2.SubnetSelection(
        #        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        #    ),
        #    security_groups=[vpc_endpoint_sg]
        # )

        ## VPCエンドポイント（ECR）
        # my_vpc.add_interface_endpoint(
        #    id="VpcEndpointEcr",
        #    service=ec2.InterfaceVpcEndpointAwsService.ECR,
        #    subnets=ec2.SubnetSelection(
        #        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        #    ),
        #    security_groups=[vpc_endpoint_sg]
        # )

        # VPCエンドポイント（s3）
        my_vpc.add_gateway_endpoint(
            id="VpcEndpointS3",
            service=ec2.GatewayVpcEndpointAwsService("s3"),
            subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ],
        )

        #############################################################
        #      他Constructで使用するインスタンスをOutput                #
        #############################################################
        self.vpc_obj = my_vpc
