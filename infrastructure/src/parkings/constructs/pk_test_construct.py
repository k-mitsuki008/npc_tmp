import aws_cdk as cdk
from aws_cdk import aws_sns as sns
from aws_cdk.aws_sns import SubscriptionProtocol as subscpro
from constructs import Construct


class snsConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        construct_id: str,
        project: str,
        env_name: str,
        phase: str,
        other_account_ids: dict,
        iam_groups: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        snstopic = sns.Topic(
            scope=self,
            id="snstopic",
            display_name="hogehoge",
            # fifo=False,
            logging_configs=[
                sns.LoggingConfig(
                    protocol=sns.LoggingProtocol.SQS,
                    failure_feedback_role=f"{project}-parkings-{env_name}-role-sns-logs",
                    success_feedback_role=f"{project}-parkings-{env_name}-role-sns-logs",
                    success_feedback_sample_rate=100,
                )
            ],
            enforce_ssl=False,
        )

        snssub = sns.Subscription(
            self,
            id="topicsub",
            protocol=subscpro.SQS,
            endpoint="hogehoge",  # 自動復旧基盤のep？
        )

        snstopic.add_subscription(snssub)
