#!/usr/bin/env python3

import sys

import aws_cdk as cdk

from config.config import DEV_ACCOUNTS_PARAMS
from src.auth.stacks.auth_stack import AuthStack
from src.integration.stacks.integration_stack import IntegrationStack
from src.members.stacks.members_stack import MembersStack
from src.parkings.stacks.parkings_stack import ParkingsStack
from src.payments.stacks.payments_stack import PaymentsStack

app = cdk.App()

# コマンドライン引数（コンテキスト）から環境を取得
phase = app.node.try_get_context("phase")
env_name = app.node.try_get_context("env_name")
account = app.node.try_get_context("account")

# コンテキスト値の検証
try:
    # 必須パラメータの存在チェック
    if not phase:
        raise ValueError(
            "Missing required context parameter: phase (e.g. -c phase=DEV)"
        )
except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)

# 環境ごとのパラメータを読み込む
try:
    if phase not in ["DEV", "STG", "PROD"]:
        raise ValueError(f"Unsupported phase: {phase}")
    props = globals().get(f"{phase}_ACCOUNTS_PARAMS", {})
    if not props:
        raise ValueError(f"No configuration found for {phase}")
except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)

# スタック作成
members_props = props.get("members")
MembersStack(
    app,
    "MembersStack",
    props=members_props,
    env={"account": members_props.account_id, "region": members_props.region},
)

parkings_props = props.get("parkings")
ParkingsStack(
    app,
    "ParkingsStack",
    props=parkings_props,
    env={"account": parkings_props.account_id, "region": parkings_props.region},
)

payments_props = props.get("payments")
PaymentsStack(
    app,
    "PaymentsStack",
    props=payments_props,
    env={"account": payments_props.account_id, "region": payments_props.region},
)

auth_props = props.get("auth")
AuthStack(
    app,
    "AuthStack",
    props=auth_props,
    env={"account": auth_props.account_id, "region": auth_props.region},
)

integration_props = props.get("integration")
IntegrationStack(
    app,
    "IntegrationStack",
    props=integration_props,
    env={"account": integration_props.account_id, "region": integration_props.region},
)

app.synth()
