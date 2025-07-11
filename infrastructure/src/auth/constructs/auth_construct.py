from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from constructs import Construct


class AuthConstruct(Construct):
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
        #     User Pool         #
        #########################
        # ユーザープールの作成
        user_pool = cognito.UserPool(
            self,
            id="UserPool",
            user_pool_name=f"{env_name}-{phase}-user-pool",
            # 自己サインアップを許可
            self_sign_up_enabled=True,
            # ユーザー名の属性
            # user_name_attributes=[cognito.username_attributes.EMAIL],
            # サインインに使用できる属性
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            # 標準属性の必須設定
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                # given_name=cognito.StandardAttribute(required=True, mutable=True),
                # family_name=cognito.StandardAttribute(required=True, mutable=True),
            ),
            # パスワードポリシー
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
            ),
            # アカウント復旧設定
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # メール設定
            email=cognito.UserPoolEmail.with_cognito(
                # from_email=f"no-reply@{env_name}.example.com",
                # from_name=f"{project.upper()} Authentication",
                reply_to="support@example.com",
            ),
            # 削除ポリシー
            removal_policy=(
                RemovalPolicy.DESTROY if phase == "dev" else RemovalPolicy.RETAIN
            ),
            # mfa=cognito.Mfa.REQUIRED,
            # mfa_second_factor=cognito.MfaSecondFactor(sms=False, otp=False, email=True),
        )

        # # MFAの設定
        # user_pool.add_client_authentication(
        #     cognito.UserPoolClientIdentityProvider.COGNITO
        # )
        # user_pool.set_mfa_config(
        #     mfa=cognito.Mfa.OPTIONAL,
        #     mfa_second_factor=cognito.MfaSecondFactor(
        #         sms=True,
        #         otp=True,
        #     ),
        # )

        # ドメイン設定
        domain = user_pool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{project}-{env_name}-{phase}",
            ),
        )

        #########################
        #  User Pool Client     #
        #########################
        # ユーザープールクライアントの作成
        user_pool_client = user_pool.add_client(
            id="UserPoolClient",
            user_pool_client_name=f"{env_name}-{phase}-client",
            # OAuth設定
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[
                    "http://localhost:3000/callback",
                    "https://example.com/callback",
                ],
                logout_urls=[
                    "http://localhost:3000/logout",
                    "https://example.com/logout",
                ],
            ),
            # 認証フロー
            auth_flows=cognito.AuthFlow(
                admin_user_password=True,
                custom=True,
                user_password=True,
                user_srp=True,
            ),
            # トークン設定
            id_token_validity=Duration.days(1),
            access_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            enable_token_revocation=True,
            prevent_user_existence_errors=True,
        )

        #########################
        #    Identity Pool      #
        #########################
        # IDプールの作成
        identity_pool = cognito.CfnIdentityPool(
            self,
            id="IdentityPool",
            identity_pool_name=f"{env_name}-{phase}-identity-pool",
            # Cognitoの認証を許可
            allow_unauthenticated_identities=False,
            # ユーザープールとの連携
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=user_pool_client.user_pool_client_id,
                    provider_name=user_pool.user_pool_provider_name,
                )
            ],
        )

        # 認証済みロールの作成
        authenticated_role = iam.Role(
            self,
            id="AuthenticatedRole",
            role_name=f"{project}-{env_name}-{phase}-authenticated-role",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        # 未認証ロールの作成
        unauthenticated_role = iam.Role(
            self,
            id="UnauthenticatedRole",
            role_name=f"{project}-{env_name}-{phase}-unauthenticated-role",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "unauthenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        # 認証済みロールに基本的な権限を付与
        authenticated_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "mobileanalytics:PutEvents",
                    "cognito-sync:*",
                ],
                resources=["*"],
            )
        )

        # 未認証ロールに制限された権限を付与
        unauthenticated_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "mobileanalytics:PutEvents",
                    "cognito-sync:*",
                ],
                resources=["*"],
            )
        )

        # IDプールにロールをアタッチ
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            id="IdentityPoolRoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn,
                "unauthenticated": unauthenticated_role.role_arn,
            },
        )

        #########################
        #  User Pool Groups     #
        #########################
        # 管理者グループの作成
        admin_group = cognito.CfnUserPoolGroup(
            self,
            id="AdminGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="Administrators",
            description="Group for administrators",
            precedence=0,  # 優先度（低いほど優先）
        )

        # 一般ユーザーグループの作成
        user_group = cognito.CfnUserPoolGroup(
            self,
            id="UserGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="Users",
            description="Group for regular users",
            precedence=10,
        )

        #############################################################
        #      他Constructで使用するインスタンスをOutput                #
        #############################################################
        self.user_pool = user_pool
        self.user_pool_client = user_pool_client
        self.identity_pool = identity_pool
        self.user_pool_domain = domain
