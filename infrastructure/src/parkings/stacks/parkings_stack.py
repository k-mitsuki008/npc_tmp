from aws_cdk import Stack
from constructs import Construct

from src.common.constructs.compute_construct import ComputeConstruct
from src.common.constructs.database_construct import DatabaseConstruct
from src.common.constructs.iam_construct import IamConstruct
from src.common.constructs.network_construct import NetworkConstruct
from src.parkings.constructs.pk_iam_construct import PkIamConstruct

# from src.constructs.static_website_Construct import StaticWebHostingConstruct


class ParkingsStack(Stack):

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

        iam_construct = IamConstruct(
            scope=self,
            id="IamConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
            central_account_id=props.central_account_id,
        )

        #########################
        #         PK_IAM        #
        #########################

        iam_groups = {
            "admin": iam_construct.administrators_group_obj,
            "readonly": iam_construct.readonly_group_obj,
            "data_viewing": iam_construct.data_viewing_group_obj,
            "operators": iam_construct.operators_group_obj,
            "developers": iam_construct.developers_group_obj,
        }

        PkIamConstruct(
            scope=self,
            id="PkIamConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
            other_account_ids=props.other_account_ids,
            iam_groups=iam_groups,
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

        #########################
        # Conpute(EC2, keypar)  #
        #########################
        compute_construnt = ComputeConstruct(
            scope=self,
            id="ComputeConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
            ami_id=props.ami_id,  # 環境固有のパラメーター
            instance_type=props.instance_type,  # 環境固有のパラメーター
            vpc_obj=network_construnt.vpc_obj,  # Conscruct共有リソース
        )

        #########################
        #       Database        #
        #########################
        DatabaseConstruct(
            scope=self,
            id="DatabaseConstruct",
            project=project,
            env_name=env_name,
            phase=phase,
            vpc_obj=network_construnt.vpc_obj,  # Conscruct共有リソース
            bastion_sg=compute_construnt.bastion_sg,
        )


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
