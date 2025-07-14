import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from constructs import Construct


class IamConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        central_account_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # ポリシー・ロールの使用を許可するIPアドレス
        allow_ips = [
            "210.227.234.114/32",
            "134.238.4.83/32",
            "134.238.4.84/32",
            "114.141.120.50/32",
            "114.141.120.185/32",
        ]

        #########################
        #      共通ポリシー       #
        #########################

        # 各ロールにアタッチする共通のIAM信頼ポリシーの定義
        common_trusted_policy = iam.ArnPrincipal(
            f"arn:aws:iam::{central_account_id}:root"
        ).with_conditions(
            conditions={
                "IpAddress": {"aws:SourceIp": allow_ips},
                "BoolIfExists": {
                    "aws:MultiFactorAuthPresent": "true",
                    "aws:ViaAWSService": "false",
                },
            }
        )
        # ユーザーの共通のIAMポリシーの定義
        iam.ManagedPolicy(
            self,
            id="CommonUsersPolicy",
            managed_policy_name=f"{project}-{phase}-policy-common-users",
            statements=[
                iam.PolicyStatement(
                    sid="AllowViewAccountInfo",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:GetAccountPasswordPolicy",
                        "iam:ListVirtualMFADevices",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnPasswords",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:ChangePassword",
                        "iam:GetUser",
                        "iam:CreateLoginProfile",
                        "iam:DeleteLoginProfile",
                        "iam:GetLoginProfile",
                        "iam:UpdateLoginProfile",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnAccessKeys",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:CreateAccessKey",
                        "iam:DeleteAccessKey",
                        "iam:ListAccessKeys",
                        "iam:UpdateAccessKey",
                        "iam:GetAccessKeyLastUsed",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnSigningCertificates",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:DeleteSigningCertificate",
                        "iam:ListSigningCertificates",
                        "iam:UpdateSigningCertificate",
                        "iam:UploadSigningCertificate",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnSSHPublicKeys",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:DeleteSSHPublicKey",
                        "iam:GetSSHPublicKey",
                        "iam:ListSSHPublicKeys",
                        "iam:UpdateSSHPublicKey",
                        "iam:UploadSSHPublicKey",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnGitCredentials",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:CreateServiceSpecificCredential",
                        "iam:DeleteServiceSpecificCredential",
                        "iam:ListServiceSpecificCredentials",
                        "iam:ResetServiceSpecificCredential",
                        "iam:UpdateServiceSpecificCredential",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnVirtualMFADevice",
                    effect=iam.Effect.ALLOW,
                    actions=["iam:CreateVirtualMFADevice"],
                    resources=["arn:aws:iam::*:mfa/*"],
                ),
                iam.PolicyStatement(
                    sid="AllowManageOwnUserMFA",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:DeactivateMFADevice",
                        "iam:EnableMFADevice",
                        "iam:ListMFADevices",
                        "iam:ResyncMFADevice",
                    ],
                    resources=["arn:aws:iam::*:user/${aws:username}"],
                ),
                iam.PolicyStatement(
                    sid="DenyAllExceptListedIfNoMFA",
                    effect=iam.Effect.DENY,
                    not_actions=[
                        "iam:CreateVirtualMFADevice",
                        "iam:EnableMFADevice",
                        "iam:ChangePassword",
                        "iam:GetUser",
                        "iam:GetMFADevice",
                        "iam:CreateLoginProfile",
                        "iam:DeleteLoginProfile",
                        "iam:GetLoginProfile",
                        "iam:UpdateLoginProfile",
                        "iam:ListMFADevices",
                        "iam:ListVirtualMFADevices",
                        "iam:ResyncMFADevice",
                        "iam:DeleteVirtualMFADevice",
                        "iam:GetAccountPasswordPolicy",
                        "sts:GetSessionToken",
                    ],
                    resources=["*"],
                    conditions={
                        "BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}
                    },
                ),
            ],
        )

        #########################
        #      管理者用設定       #
        #########################
        # 管理者用 IAMグループ
        administrators_group = iam.Group(
            self, id="AdministratorsGroup", group_name="Administrators"
        )

        # 管理者用 IAMロール
        administrators_role = iam.Role(
            self,
            id="AdministratorsRole",
            role_name=f"{project}-{env_name}-{phase}-role-administrators",
            assumed_by=common_trusted_policy,
        )

        # 管理者用 IAMグループにアタッチする IAMポリシー
        administrators_switch_policy = iam.Policy(
            self,
            id="AdministratorsSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-administrators",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[administrators_role.role_arn],
                )
            ],
        )

        # 管理者用 IAMグループ IAMロールに IAMポリシーをアタッチ
        administrators_group.attach_inline_policy(administrators_switch_policy)
        administrators_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
        )

        # 管理者IAMロールにGitHub用信頼ポリシーをアタッチ
        assume_role_statement = iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            principals=[iam.AccountPrincipal(central_account_id)],
            conditions={
                "StringEquals": {
                    "sts:ExternalId": f"{env_name}"
                }
            }
        )
        tag_session_statement = iam.PolicyStatement(
            actions=["sts:TagSession"],
            principals=[iam.AccountPrincipal(central_account_id)]
        )
        administrators_role.assume_role_policy.add_statements(assume_role_statement)
        administrators_role.assume_role_policy.add_statements(tag_session_statement)

        #########################
        #    ReadOnly用設定      #
        #########################

        # ReadOnly用 IAMグループ
        readonly_group = iam.Group(self, id="ReadOnlyGroup", group_name="ReadOnly")

        # ReadOnly用 IAMロール
        readonly_role = iam.Role(
            self,
            id="ReadOnlyRole",
            role_name=f"{project}-{env_name}-{phase}-role-readonly",
            assumed_by=common_trusted_policy,
        )

        # ReadOnly用 IAMグループにアタッチする IAMポリシー
        readonly_switch_policy = iam.Policy(
            self,
            id="ReadOnlySwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-readonly",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[readonly_role.role_arn],
                )
            ],
        )

        # ReadOnly用 IAMグループ IAMロールに IAMポリシーをアタッチ
        readonly_group.attach_inline_policy(readonly_switch_policy)
        readonly_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("ReadOnlyAccess")
        )

        #########################
        #    データ閲覧可能用設定  #
        #########################

        # データ閲覧可能用 ポリシー
        data_viewing_policy = iam.ManagedPolicy(
            self,
            id="DataVewingPolicy",
            managed_policy_name=f"{project}-{env_name}-{phase}-data-viewing",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["ssm:StartSession"],
                    resources=[
                        "arn:aws:ssm:ap-northeast-1::document/AWS-StartSSHSession",
                        f"arn:aws:ec2:ap-northeast-1:{cdk.Aws.ACCOUNT_ID}:instance/*",
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=["ssm:TerminateSession", "ssm:ResumeSession"],
                    resources=["arn:aws:ssm:*:*:session/botocore-session-*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=[
                        "secretsmanager:GetResourcePolicy",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:ListSecretVersionIds",
                    ],
                    resources=["*"],
                ),
            ],
        )

        # データ閲覧可能用 IAMグループ
        data_viewing_group = iam.Group(
            self, id="DataViewingGroup", group_name="DataViewing"
        )

        # データ閲覧可能用 IAMロール
        data_viewing_role = iam.Role(
            self,
            id="DataViewingRole",
            role_name=f"{project}-{env_name}-{phase}-role-data-viewing",
            assumed_by=common_trusted_policy,
        )

        # データ閲覧可能 IAMグループにアタッチする IAMポリシー
        data_viewing_switch_policy = iam.Policy(
            self,
            id="DataViewingSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-data-viewing",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[data_viewing_role.role_arn],
                )
            ],
        )

        # データ閲覧可能 IAMグループ IAMロールに IAMポリシーをアタッチ
        data_viewing_group.attach_inline_policy(data_viewing_switch_policy)
        data_viewing_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("ReadOnlyAccess")
        )
        data_viewing_role.add_managed_policy(data_viewing_policy)

        #########################################
        #     作業ロール用設定                     #
        #     必要に応じて、ポリシーを追加してください #
        #########################################

        # 作業ロール用 IAMグループ
        operators_group = iam.Group(self, id="OperatorsGroup", group_name="Operators")

        # 作業ロール用 IAMロール
        operators_role = iam.Role(
            self,
            id="OperatorsRole",
            role_name=f"{project}-{env_name}-{phase}-role-operators",
            assumed_by=common_trusted_policy,
        )
        # 作業ロール IAMグループにアタッチする IAMポリシー
        operators_switch_policy = iam.Policy(
            self,
            id="OperatorsSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-operators",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[operators_role.role_arn],
                )
            ],
        )

        # 作業ロール IAMグループ IAMロールに IAMポリシーをアタッチ
        operators_group.attach_inline_policy(operators_switch_policy)
        operators_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("ReadOnlyAccess")
        )
        # データ閲覧可能ポリシーのアタッチ
        operators_role.add_managed_policy(data_viewing_policy)

        ##############################################
        #     閲覧不可ロール用設定                       #
        #     必要に応じて、本番環境払い出し後作成して下さい #
        ##############################################

        #########################
        #      開発者用設定       #
        #########################

        # 開発者用 ポリシー
        developers_policy = iam.ManagedPolicy(
            self,
            id="DevelopersPolicy",
            managed_policy_name=f"{project}-{env_name}-{phase}-policy-developers",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "apigateway:*",
                        "cloudformation:*",
                        "cloudwatch:*",
                        "codebuild:*",
                        "codecommit:*",
                        "codepipeline:*",
                        "dbqms:*",
                        "dynamodb:*",
                        "ecr:*",
                        "ec2:*",
                        "events:*",
                        "iam:*",
                        "kms:*",
                        "lambda:*",
                        "logs:*",
                        "rds:*",
                        "rds-data:*",
                        "secretsmanager:*",
                        "ssm:*",
                        "sts:*",
                        "states:*",
                        "s3:*",
                        "cognito-identity:*",
                        "cognito-idp:*",
                        "cognito-sync:*",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=[
                        "iam:AddUserToGroup",
                        "iam:AttachGroupPolicy",
                        "iam:AttachUserPolicy",
                        "iam:CreateGroup",
                        "iam:CreateUser",
                        "iam:DeleteGroup",
                        "iam:DeleteGroupPolicy",
                        "iam:DeleteLoginProfile",
                        "iam:DeleteUser",
                        "iam:DeleteUserPolicy",
                        "iam:DetachGroupPolicy",
                        "iam:DetachUserPolicy",
                        "iam:PutGroupPolicy",
                        "iam:PutRolePermissionsBoundary",
                        "iam:PutUserPolicy",
                        "iam:RemoveUserFromGroup",
                        "iam:DeleteAccountPasswordPolicy",
                        "iam:UpdateAccountPasswordPolicy",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=[
                        "iam:AttachRolePolicy",
                        "iam:DeleteRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:PutRolePolicy",
                    ],
                    resources=[
                        f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:role/{project}-{env_name}-{phase}-role-administrators",
                        f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:role/{project}-{env_name}-{phase}-role-operators",
                        f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:role/{project}-{env_name}-{phase}-role-security",
                        f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:role/{project}-{env_name}-{phase}-role-developers",
                    ],
                ),
            ],
        )

        # 開発者用 IAMグループ
        developers_group = iam.Group(
            self, id="DevelopersGroup", group_name="Developers"
        )

        # 開発者用 IAMロール
        developers_role = iam.Role(
            self,
            id="DevelopersRole",
            role_name=f"{project}-{env_name}-{phase}-role-developers",
            assumed_by=common_trusted_policy,
        )

        # 開発者用 IAMグループにアタッチする IAMポリシー
        developers_switch_policy = iam.Policy(
            self,
            id="DevelopersSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-developers",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[developers_role.role_arn],
                )
            ],
        )

        # 開発者用 IAMグループ IAMロールに IAMポリシーをアタッチ
        developers_group.attach_inline_policy(developers_switch_policy)
        developers_role.add_managed_policy(developers_policy)

        #############################################################
        #      他Constructで使用するインスタンスをOutput                #
        #############################################################
        self.administrators_group_obj = administrators_group
        self.readonly_group_obj = readonly_group
        self.data_viewing_group_obj = data_viewing_group
        self.operators_group_obj = operators_group
        self.developers_group_obj = developers_group
