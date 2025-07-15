from aws_cdk import Stack
from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ses as ses
from aws_cdk import aws_route53 as route53
from aws_cdk import Duration
from constructs import Construct


class AuthConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        project: str,
        env_name: str,
        phase: str,
        domain_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        hosted_zone = route53.PublicHostedZone.from_lookup(
            self,
            "AuthHostZone",
            domain_name=f"{env_name}.{domain_name}"
        )

        ############
        #    SES   #
        ############
        identity = ses.EmailIdentity(
            self,
            "Identity",
            identity=ses.Identity.public_hosted_zone(hosted_zone),
            mail_from_domain=f"mail.{env_name}.{domain_name}"
        )
        route53.TxtRecord(self,
            "DmarcRecord",
            zone=hosted_zone,
            record_name=f"_dmarc.{env_name}.{domain_name}",
            values=[
                f"v=DMARC1; p=none; rua=mailto:dmarcreports@{env_name}.{domain_name}"
            ],
            ttl=Duration.hours(1)
        )

        ###################################
        #    AuthTokenValidatorFunction   #
        ###################################
        auth_token_validator_function_path = f"src/{env_name}/handlers/auth_token_validator"

        auth_token_validator_function_log = logs.LogGroup(
            self,
            id="AuthTokenValidatorFunctionLog",
            log_group_name=f"/aws/lambda/{env_name}-{phase}-auth-token-validator",
            retention=logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.RETAIN
        )

        auth_token_validator_function_role = iam.Role(
            self,
            id="AuthTokenValidatorFunctionRole",
            role_name=f"{project}-{env_name}-{phase}-auth-token-validator-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        auth_token_validator_function = _lambda.Function(
            self,
            id="AuthTokenValidatorFunction",
            function_name=f"{env_name}-{phase}-auth-token-validator",
            runtime=_lambda.Runtime.PYTHON_3_13,
            code=_lambda.Code.from_asset(auth_token_validator_function_path),
            handler="lambda_function.lambda_handler",
            role=auth_token_validator_function_role,
            environment={
                "SAMPLE": "SAMPLE"
            },
            timeout=Duration.seconds(60),
            log_group=auth_token_validator_function_log
        )

        ###################################
        #     AccessTokenClaimFunction    #
        ###################################
        access_token_claim_function_path = f"src/{env_name}/handlers/access_token_claim"

        access_token_claim_function_log = logs.LogGroup(
            self,
            id="AccessTokenClaimFunctionLog",
            log_group_name=f"/aws/lambda/{env_name}-{phase}-access-token-claim",
            retention=logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.RETAIN
        )

        access_token_claim_function_role = iam.Role(
            self,
            id="AccessTokenClaimFunctionRole",
            role_name=f"{project}-{env_name}-{phase}-access-token-claim-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        access_token_claim_function = _lambda.Function(
            self,
            id="AccessTokenClaimFunction",
            function_name=f"{env_name}-{phase}-access-token-claim",
            runtime=_lambda.Runtime.PYTHON_3_13,
            code=_lambda.Code.from_asset(access_token_claim_function_path),
            handler="lambda_function.lambda_handler",
            role=access_token_claim_function_role,
            environment={
                "SAMPLE": "SAMPLE"
            },
            timeout=Duration.seconds(60),
            log_group=access_token_claim_function_log
        )

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
            auto_verify=cognito.AutoVerifiedAttrs(
                email=False
            ),
            # サインインに使用できる属性
            sign_in_aliases=cognito.SignInAliases(
                email=True
            ),
            # 標準属性の必須設定
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=False, mutable=True),
                family_name=cognito.StandardAttribute(required=False, mutable=True),
            ),
            # パスワードポリシー
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
                password_history_size=1
            ),
            # アカウント復旧設定
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # メール設定
            email=cognito.UserPoolEmail.with_ses(
                from_email=f"no-reply@{env_name}.{domain_name}",
                from_name=f"{project.upper()} Authentication",
                ses_verified_domain=f"{env_name}.{domain_name}",
                ses_region=Stack.of(self).region,
            ),
            # 削除ポリシー
            removal_policy=(
                RemovalPolicy.DESTROY if phase == "dev" else RemovalPolicy.RETAIN
            ),
            # mfa=cognito.Mfa.REQUIRED,
            # mfa_second_factor=cognito.MfaSecondFactor(sms=False, otp=False, email=True),
            feature_plan=cognito.FeaturePlan.PLUS,
            standard_threat_protection_mode=cognito.StandardThreatProtectionMode.FULL_FUNCTION,
            custom_threat_protection_mode=cognito.CustomThreatProtectionMode.FULL_FUNCTION,
            lambda_triggers=cognito.UserPoolTriggers(
                pre_sign_up=auth_token_validator_function,
                pre_token_generation=access_token_claim_function
            )
        )

        cognito.CfnUserPoolRiskConfigurationAttachment(
            self,
            id="RiskConfigAttachment",
            user_pool_id=user_pool.user_pool_id,
            # この設定を全てのアプリクライアントに適用します
            client_id="ALL",
            # リスクレベルごとのアクションを定義
            account_takeover_risk_configuration=cognito.CfnUserPoolRiskConfigurationAttachment.AccountTakeoverRiskConfigurationTypeProperty(
                actions=cognito.CfnUserPoolRiskConfigurationAttachment.AccountTakeoverActionsTypeProperty(
                    # リスク「低」の場合のアクション
                    low_action=cognito.CfnUserPoolRiskConfigurationAttachment.AccountTakeoverActionTypeProperty(
                        event_action="NO_ACTION",  # 何もしない (MFAをスキップ)
                        notify=False
                    ),
                    # リスク「中」の場合のアクション
                    medium_action=cognito.CfnUserPoolRiskConfigurationAttachment.AccountTakeoverActionTypeProperty(
                        event_action="MFA_REQUIRED",  # MFAを要求
                        notify=False
                    ),
                    # リスク「高」の場合のアクション
                    high_action=cognito.CfnUserPoolRiskConfigurationAttachment.AccountTakeoverActionTypeProperty(
                        event_action="MFA_REQUIRED",  # MFAを要求
                        notify=False
                    )
                )
            )
        )

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
            generate_secret=False,
            # トークン設定
            id_token_validity=Duration.minutes(5),
            access_token_validity=Duration.minutes(5),
            refresh_token_validity=Duration.days(3650),
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
