import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from constructs import Construct


class PkIamConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        other_account_ids: dict,
        iam_groups: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        #########################
        #      管理者用設定       #
        #########################

        # 管理者用 IAMグループにアタッチする IAMポリシー
        other_administrators_switch_policy = iam.Policy(
            self,
            id="OtherAdministratorsSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-switch-other-administrators",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[
                        f"arn:aws:iam::{other_account_ids["members"]}:role/{project}-members-{phase}-role-administrators",
                        f"arn:aws:iam::{other_account_ids["payments"]}:role/{project}-payments-{phase}-role-administrators",
                        f"arn:aws:iam::{other_account_ids["auth"]}:role/{project}-auth-{phase}-role-administrators",
                        f"arn:aws:iam::{other_account_ids["integration"]}:role/{project}-integration-{phase}-role-administrators",
                    ],
                )
            ],
        )

        # 管理者用 IAMグループ IAMロールに IAMポリシーをアタッチ
        iam_groups["admin"].attach_inline_policy(other_administrators_switch_policy)

        #########################
        #    ReadOnly用設定      #
        #########################

        # ReadOnly用 IAMグループにアタッチする IAMポリシー
        other_readonly_switch_policy = iam.Policy(
            self,
            id="OtherReadOnlySwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-other-switch-readonly",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[
                        f"arn:aws:iam::{other_account_ids["members"]}:role/{project}-members-{phase}-role-readonly",
                        f"arn:aws:iam::{other_account_ids["payments"]}:role/{project}-payments-{phase}-role-readonly",
                        f"arn:aws:iam::{other_account_ids["auth"]}:role/{project}-auth-{phase}-role-readonly",
                        f"arn:aws:iam::{other_account_ids["integration"]}:role/{project}-integration-{phase}-role-readonly",
                    ],
                )
            ],
        )

        # ReadOnly用 IAMグループ IAMロールに IAMポリシーをアタッチ
        iam_groups["readonly"].attach_inline_policy(other_readonly_switch_policy)

        #########################
        #    データ閲覧可能用設定  #
        #########################

        # データ閲覧可能 IAMグループにアタッチする IAMポリシー
        other_data_viewing_switch_policy = iam.Policy(
            self,
            id="OtherDataViewingSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-other-switch-data-viewing",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[
                        f"arn:aws:iam::{other_account_ids["members"]}:role/{project}-members-{phase}-role-data-viewing",
                        f"arn:aws:iam::{other_account_ids["payments"]}:role/{project}-payments-{phase}-role-data-viewing",
                        f"arn:aws:iam::{other_account_ids["auth"]}:role/{project}-auth-{phase}-role-data-viewing",
                        f"arn:aws:iam::{other_account_ids["integration"]}:role/{project}-integration-{phase}-role-data-viewing",
                    ],
                )
            ],
        )

        # データ閲覧可能 IAMグループ IAMロールに IAMポリシーをアタッチ
        iam_groups["data_viewing"].attach_inline_policy(
            other_data_viewing_switch_policy
        )

        #########################################
        #     作業ロール用設定                     #
        #     必要に応じて、ポリシーを追加してください #
        #########################################

        # 作業ロール IAMグループにアタッチする IAMポリシー
        other_operators_switch_policy = iam.Policy(
            self,
            id="OtherOperatorsSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-other-switch-operators",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[
                        f"arn:aws:iam::{other_account_ids["members"]}:role/{project}-members-{phase}-role-operators",
                        f"arn:aws:iam::{other_account_ids["payments"]}:role/{project}-payments-{phase}-role-operators",
                        f"arn:aws:iam::{other_account_ids["auth"]}:role/{project}-auth-{phase}-role-operators",
                        f"arn:aws:iam::{other_account_ids["integration"]}:role/{project}-integration-{phase}-role-operators",
                    ],
                )
            ],
        )

        # 作業ロール IAMグループ IAMロールに IAMポリシーをアタッチ
        iam_groups["operators"].attach_inline_policy(other_operators_switch_policy)

        ##############################################
        #     閲覧不可ロール用設定                       #
        #     必要に応じて、本番環境払い出し後作成して下さい #
        ##############################################

        #########################
        #      開発者用設定       #
        #########################

        # 開発者用 IAMグループにアタッチする IAMポリシー
        other_developers_switch_policy = iam.Policy(
            self,
            id="OtherDevelopersSwitchPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-other-switch-developers",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[
                        f"arn:aws:iam::{other_account_ids["members"]}:role/{project}-members-{phase}-role-developers",
                        f"arn:aws:iam::{other_account_ids["payments"]}:role/{project}-payments-{phase}-role-developers",
                        f"arn:aws:iam::{other_account_ids["auth"]}:role/{project}-auth-{phase}-role-developers",
                        f"arn:aws:iam::{other_account_ids["integration"]}:role/{project}-integration-{phase}-role-developers",
                    ],
                )
            ],
        )

        # 開発者用 IAMグループ IAMロールに IAMポリシーをアタッチ
        iam_groups["developers"].attach_inline_policy(other_developers_switch_policy)

        ##############################
        #     GitHub Actions用設定    #
        ##############################
        # GitHub Actions用 IDプロバイダ
        github_id_provider = iam.OpenIdConnectProvider(
            self,
            id="GithubIdProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )
        # GitHub用 IAMロール
        github_actions_role = iam.Role(
            self,
            id="GithubActionsRole",
            role_name=f"{project}-{env_name}-{phase}-role-github-actions",
            assumed_by=iam.FederatedPrincipal(
                federated=github_id_provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:team-agile-div/npc-members-service:*"
                    }
                },
            ),
        )
        # IAMポリシーの定義
        github_actions_policy = iam.Policy(
            self,
            id="GithubActionsPolicy",
            policy_name=f"{project}-{env_name}-{phase}-policy-github-actions",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "apigateway:*",
                        "cloudformation:*",
                        "ec2:*",
                        "iam:*",
                        "lambda:*",
                        "logs:*",
                        "s3:*",
                        "vpc:*",
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
                        "iam:DeleteGroupPolicy",
                        "iam:DetachUserPolicy",
                        "iam:PutGroupPolicy",
                        "iam:PutRolePermissionsBoundary",
                        "iam:PutUserPolicy",
                        "iam:RemoveUserFromGroup",
                    ],
                    resources=["*"],
                ),
            ],
        )
        github_actions_role.attach_inline_policy(github_actions_policy)
