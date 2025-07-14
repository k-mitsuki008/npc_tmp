from aws_cdk import Stack
from constructs import Construct

from src.common.constructs.iam_construct import IamConstruct
from src.common.constructs.network_construct import NetworkConstruct
from src.common.constructs.artifact_bucket import ArtifactBucketConstruct

# from src.constructs.compute_construct import ComputeConstruct
# from src.constructs.static_website_Construct import StaticWebHostingConstruct


class IntegrationStack(Stack):

    def __init__(self, scope: Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        #########################
        # 　 Construnt 共通定数   #
        #########################

        project = props.project
        env_name = props.env_name
        phase = props.phase

        #########################
        #         IAM           #
        #########################

        IamConstruct(
            scope=self,
            id="IamConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
            central_account_id=props.central_account_id,
        )

        #########################
        #       Network         #
        #########################

        network_construnt = NetworkConstruct(
            scope=self,
            id="NetworkConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
        )

        ############################
        #      ArtifactBucket      #
        ############################
        ArtifactBucketConstruct(
            scope=self,
            id="ArtifactBucketConstruct",
            project=project,
            env_name=env_name,
            phase=phase
        )

#        #########################
#        # Conpute(EC2, keypar)  #
#        #########################
#        ComputeConstruct(
#            scope=self,
#            id="ComputeConstruct",
#            project=project,
#            phase=phase,
#            ami_id=props.ami_id,  # 環境固有のパラメーター
#            vpc_obj=network_construnt.vpc_obj  # Conscruct共有リソース
#        )
#
#        #########################
#        #  Static Web Hosting   #
#        #########################
#        StaticWebHostingConstruct(
#            scope=self,
#            id="ComputeConstruct",
#            project=project,
#            env_name=env_name,
#            phase=phase,
#            certificate=props.certificate,
#            domain_name=props.domain_name,
#            sub_domain_name=props.sub_domain_name,
#            hosted_zone_id=props.hosted_zone_id,
#        )
