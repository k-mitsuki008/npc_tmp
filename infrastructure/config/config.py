import os
from dataclasses import asdict, dataclass
from typing import Type, TypeVar

#########################
# 　 全環境共通の型定義    #
#########################

# 関数の戻り値の型を動的にするための設定
T = TypeVar("T")


@dataclass(frozen=True)
class AppParameter:
    """アプリケーションの環境全体で共通のパラメータ."""

    project: str
    phase: str
    region: str


@dataclass(frozen=True)
class ServiceParameter(AppParameter):
    """全基盤で共通の、アカウントに紐づくパラメータ."""

    env_name: str
    account_id: str


#############################
# 　   基盤固有の型定義        #
#############################
@dataclass(frozen=True)
class MembersServiceParameter(ServiceParameter):
    """Members基盤固有のパラメータを持つクラス."""

    central_account_id: str
    ami_id: str
    instance_type: str
    # user_pool_id: str


@dataclass(frozen=True)
class ParkingsServiceParameter(ServiceParameter):
    """Parkings基盤固有のパラメータを持つクラス."""

    central_account_id: str
    other_account_ids: dict
    hosted_zone_id: str 
    domain_name: str
    sub_domains: dict
    sub_domain_nameservers: dict
    ami_id: str
    instance_type: str
    # dynamodb_table_name: str


@dataclass(frozen=True)
class PaymentsServiceParameter(ServiceParameter):
    """Paymentes基盤固有のパラメータを持つクラス."""

    central_account_id: str
    # dynamodb_table_name: str


@dataclass(frozen=True)
class AuthServiceParameter(ServiceParameter):
    """Auth基盤固有のパラメータを持つクラス."""

    central_account_id: str
    # dynamodb_table_name: str


@dataclass(frozen=True)
class IntegrationServiceParameter(ServiceParameter):
    """Integration基盤固有のパラメータを持つクラス."""

    central_account_id: str
    # dynamodb_table_name: str


#############################
# 　  共通パラメータ定義       #
#############################
BASE_PARAMS = {
    "dev": AppParameter(project="npc", phase="dev", region="ap-northeast-1"),
    # stg, prdも同様
}


#########################
#      ヘルパー関数       #
#########################
# パラメータ生成処理
def create_param(
    param_class: Type[T],
    base_params: AppParameter,
    env_name: str,
    account_id: str,
    **specific_params: any,
) -> T:
    """指定されたデータクラスのインスタンスを生成する、超汎用ファクトリ関数。

    Args:
        param_class: 生成したいデータクラス (例: MembersServiceParameter)
        base_params: 共通のベースパラメータ
        env_name: サービス/環境名
        account_id: アカウントID
        **specific_params: サービス固有のパラメータ (例: user_pool_id="...")

    Returns:
        param_classのインスタンス

    """
    base_dict = asdict(base_params)

    # 全てのパラメータを一つの辞書にマージ
    all_params = {
        **base_dict,
        "env_name": env_name,
        "account_id": account_id,
        **specific_params,  # サービス固有のパラメータを展開
    }

    # 辞書を展開して、指定されたクラスのインスタンスを生成
    return param_class(**all_params)


# アカウントID用環境変数取得処理
def get_env_var(name: str) -> str:
    """環境変数を取得し、存在しない場合はエラーを発生させる.

    Args:
        name: 環境変数名

    Returns:
        環境変数の値

    Raises:
        ValueError: 環境変数が設定されていない場合

    """
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"環境変数 {name} が設定されていません")
    return value


#############################
# 　 基盤固有パラメータ定義     #
#############################

DEV_ACCOUNTS_PARAMS = {
    "members": create_param(
        param_class=MembersServiceParameter,
        base_params=BASE_PARAMS["dev"],
        env_name="members",
        account_id=get_env_var("NPC_MEMBERS_DEV_ACCOUNT"),
        **{
            "central_account_id": get_env_var("NPC_PARKINGS_DEV_ACCOUNT"),
            "ami_id": "ami-03598bf9d15814511",
            "instance_type": "t2.micro",
        },
    ),
    "parkings": create_param(
        param_class=ParkingsServiceParameter,
        base_params=BASE_PARAMS["dev"],
        env_name="parkings",
        account_id=get_env_var("NPC_PARKINGS_DEV_ACCOUNT"),
        **{
            "central_account_id": get_env_var("NPC_PARKINGS_DEV_ACCOUNT"),
            "other_account_ids": {
                "members": get_env_var("NPC_MEMBERS_DEV_ACCOUNT"),
                "payments": get_env_var("NPC_PAYMENTS_DEV_ACCOUNT"),
                "auth": get_env_var("NPC_AUTH_DEV_ACCOUNT"),
                "integration": get_env_var("NPC_INTEGRATION_DEV_ACCOUNT"),
            },
            "hosted_zone_id": "Z0880119245A91RB6NNGO", 
            "domain_name": "npc24dev.click",
            "sub_domains": ["auth","members","payments","integration"],
            "sub_domain_nameservers": {
                "auth": [
                    "ns-484.awsdns-60.com.",
                    "ns-1042.awsdns-02.org.",
                    "ns-1962.awsdns-53.co.uk.",
                    "ns-989.awsdns-59.net."
                ],
                "members":[
                    "ns-333.awsdns-41.com.",
                    "ns-1519.awsdns-61.org.",
                    "ns-1801.awsdns-33.co.uk.",
                    "ns-1010.awsdns-62.net."
                ],
                "payments":[
                    "ns-252.awsdns-31.com.",
                    "ns-1733.awsdns-24.co.uk.",
                    "ns-898.awsdns-48.net.",
                    "ns-1138.awsdns-14.org."
                ],
                "integration":[
                    "ns-69.awsdns-08.com.",
                    "ns-1326.awsdns-37.org.",
                    "ns-1885.awsdns-43.co.uk.",
                    "ns-535.awsdns-02.net."
                ],
            },
            "ami_id": "ami-03598bf9d15814511",
            "instance_type": "t2.micro",
        },
    ),
    "payments": create_param(
        param_class=PaymentsServiceParameter,
        base_params=BASE_PARAMS["dev"],
        env_name="payments",
        account_id=get_env_var("NPC_PAYMENTS_DEV_ACCOUNT"),
        **{"central_account_id": get_env_var("NPC_PARKINGS_DEV_ACCOUNT")},
    ),
    "auth": create_param(
        param_class=AuthServiceParameter,
        base_params=BASE_PARAMS["dev"],
        env_name="auth",
        account_id=get_env_var("NPC_AUTH_DEV_ACCOUNT"),
        **{"central_account_id": get_env_var("NPC_PARKINGS_DEV_ACCOUNT")},
    ),
    "integration": create_param(
        param_class=IntegrationServiceParameter,
        base_params=BASE_PARAMS["dev"],
        env_name="integration",
        account_id=get_env_var("NPC_INTEGRATION_DEV_ACCOUNT"),
        **{"central_account_id": get_env_var("NPC_PARKINGS_DEV_ACCOUNT")},
    ),
}
