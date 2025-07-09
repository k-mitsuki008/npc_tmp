# 記載内容
1. [環境構築](#環境構築)
   1. [使用ツール](#使用ツール)
   1. [Toolバージョン](#Toolバージョン)
   1. [フォルダ構成 (随時更新中)](#フォルダ構成 (随時更新中))
   1. [事前準備](#事前準備)
   1. [仮想環境の構築](#仮想環境の構築)
   1. [デプロイ手順](#デプロイ手順)

1. [開発コーディング規約](#開発コーディング規約)

<br>
<br>
<br>

# 環境構築

## 使用ツール
- **Linter**： `flake8`
- **Formatter**： `black`


## Toolバージョン
* **AWS CDK:** 2.1018.1
* **Python:** 3.13.0

## フォルダ構成 (随時更新中)
```
```

## 事前準備

1. Python 3 系、pip がインストールされていることを確認。

   ```
   python3 --version
   pip --version
   ```

1. [AWS CDK CLI](https://aws.amazon.com/jp/getting-started/guides/setup-cdk/module-two/) をインストール。

   ```
   npm install -g aws-cdk@2.1018.1
   ```


## 仮想環境の構築

1. `infrastructure` ディレクトリ配下に `.venv` がない場合は、以下のコマンドを実行し、 virtualenv を作成。

   MacOS/Linux

   ```
   python3 -m venv .venv
   ```

   Windows

   ```
   py -3 -m venv .venv
   ```

1. `.venv` が作成できたら、以下のコマンドを実行し、仮想環境をアクティブ化。

   MacOS/Linux

   ```
   source .venv/bin/activate
   ```

   Windows

   ```
   .venv\Scripts\activate.bat
   ```

   停止コマンド

   ```
   deactivate
   ```

1. 各モジュールのインストール。

   ```
   pip install -r requirements.txt
   ```


## デプロイ手順
- `CDKToolkit` スタックが、デプロイ環境にすでに存在する場合は不要

- 以下の内容で、IAM Policyを作成する
   - ポリシー名：`CdkExecutionPolicy`
   - 権限内容
      ```json
      {
      	"Version": "2012-10-17",
      	"Statement": [
      		{
      			"Action": [
      				"acm:*",
      				"apigateway:*",
      				"codebuild:*",
      				"codecommit:*",
      				"codepipeline:*",
      				"cloudfront:*",
      				"cloudformation:*",
      				"cloudwatch:*",
      				"dynamodb:*",
      				"ec2:*",
      				"guardduty:*",
      				"iam:*",
      				"lambda:*",
      				"logs:*",
      				"rds:*",
      				"route53:*",
      				"s3:*",
      				"secretsmanager:*",
      				"ssm:*",
      				"states:*",
      				"wafv2:*",
      				"kinesis:*",
      				"firehose:*",
      				"iot:*",
      				"route53resolver:*",
      				"events:*",
      				"kms:*",
      				"cloudtrail:*",
      				"sns:*",
      				"sqs:*",
      				"chatbot:*",
                  "ram:*",
                  "cognito-idp:*",
                  "cognito-identity:*"
      			],
      			"Resource": "*",
      			"Effect": "Allow",
      			"Sid": "AllowExecute"
      		},
      		{
      			"Action": [
      				"iam:AddUserToGroup",
      				"iam:AttachGroupPolicy",
      				"iam:AttachUserPolicy",
      				"iam:CreateUser",
      				"iam:DeleteLoginProfile",
      				"iam:DeleteUser",
      				"iam:DetachUserPolicy",
      				"iam:PutRolePermissionsBoundary",
      				"iam:PutUserPolicy",
      				"iam:RemoveUserFromGroup"
      			],
      			"Resource": "*",
      			"Effect": "Deny",
      			"Sid": "DenyExecute"
      		}
      	]
      }
      ```


- デフォルトの Toolkit では、CloudFormationExecutionRoleの権限が広すぎる等 ため、以下の CFn テンプレートを利用することで権限を制限する
   - LookupRole
      - AWS CDKがCloudFormationスタックを作成・変更する時に既存のAWSリソース  の情報を取得するために使用するロール
         - ReadOnlyAccess → ReadOnlyAccess + 参照権限を拡大
   - CloudFormationExecutionRole
      - AWS CloudFormationがスタックの作成や更新を行うために使用するロール
         - AdministratorAccess → 明示的にリソースを指定

   - 実行コマンド
      ```sh
      cdk bootstrap aws://<TAGET ACCOUNT ID>/ap-northeast-1 --trust <PARKINGS ACCOUNT ID> --template customize-bootstrap.yml  --profile <TAGET ACCOUNT PROFILE> -c phase=DEV --cloudformation-execution-policies arn:aws:iam::<ACCOUNT ID>:policy/CdkExecutionPolicy
      ```

### アカウントIDを環境変数に設定
```sh
export NPC_MEMBERS_DEV_ACCOUNT=XXXXXXXXXXXX
export NPC_PARKINGS_DEV_ACCOUNT=XXXXXXXXXXXX
export NPC_PAYMENTS_DEV_ACCOUNT=XXXXXXXXXXXX
export NPC_AUTH_DEV_ACCOUNT=XXXXXXXXXXXX
export NPC_INTEGRATION_DEV_ACCOUNT=XXXXXXXXXXXX
```


### CFn 作成

```
cdk synth -c phase={ DEV or STG or PRD} --profile <PARKINGS ACCOUNT PROFILE>
```


### スタックの差分比較

```
cdk diff -c phase={ DEV or STG or PRD}  --profile <PARKINGS ACCOUNT PROFILE>
```

- デプロイされているスタックと、ローカルを比較。
- 対象のアカウントのプロファイルを指定する必要あり。

### スタックのデプロイ

```
cdk deploy -c phase={ DEV or STG or PRD}  --profile <PARKINGS ACCOUNT PROFILE>
```


<br>
<br>
<br>

# 開発コーディング規約

## コード品質管理ツール

以下のツールを使用してコードの品質を管理しています：

- **Formatter**：
  - `black`: コードの自動整形
  - `isort`: インポート文の整形

- **Linter**：
  - `flake8`: コードの静的解析

## セットアップ方法

1. 開発環境のセットアップ:

   ```bash
   # 仮想環境をアクティブ化した後
   make install        # 必要なツールをインストール
   ```

2. 手動でのコード品質チェック:

   ```bash
   make format         # blackによるコード整形
   make isort          # isortによるインポート整形
   make lint           # flake8によるリンティング
   make check          # 上記すべてを実行
   ```

## コーディング規約

- **行の長さ**: 最大120文字
- **インデント**: 4スペース
- **インポート順**: isortによる自動整形（標準ライブラリ、サードパーティ、ローカル）

## 設定ファイル

- `.black`: blackの設定
- `.flake8`: flake8の設定
- `Makefile`: 各種コマンドの定義

### リソース ID (CDK 内部 ID) 、変数・プロパティの例
| リソース | CDK ID (内部 ID) | 変数・プロパティ |
|----------|----------------|----------------|
| **VPC** | `MyVpc` | `my_vpc` |
| **サブネット** | `PublicSubnetA`, `PrivateSubnetB` | `public_subnet_a`, `private_subnet_b` |
| **ルートテーブル** | `PublicRouteTable`, `PrivateRouteTable` | `public_route_table`, `private_route_table` |
| **S3 バケット** | `AppBucket`, `LogsBucket` | `app_bucket`, `logs_bucket` |
| **IAM ロール** | `LambdaExecutionRole`, `Ec2InstanceRole` | `lambda_execution_role`, `ec2_instance_role` |
| **セキュリティグループ** | `WebServerSG`, `DatabaseSG` | `web_server_sg`, `database_sg` |
| **RDS インスタンス** | `AppDatabase`, `ProdDatabase` | `app_database`, `prod_database` |
| **Lambda 関数** | `DataProcessorLambda`, `ImageResizerLambda` | `data_processor_lambda`, `image_resizer_lambda` |
| **API Gateway** | `AppApiGateway`, `PublicApiGateway` | `app_api_gateway`, `public_api_gateway` |

<br>
<br>
<br>

### リソース ID (AWS 物理リソース名)
| AWSリソース           | 命名規則の例                     | 説明・用途                                      |
|----------------------|------------------------------|----------------------------------------------|
| VPC                | `hoge-dev-vpc`               | VPC（Virtual Private Cloud）                 |
| Subnet             | `hoge-dev-subnet-public-a`  | 可用性ゾーンaのパブリックサブネット           |
| Security Group     | `hoge-dev-sg-ecs`           | ECS用のセキュリティグループ                   |
| EC2                | `hoge-dev-ec2-app`          | アプリケーションサーバ                         |
| RDS                | `hoge-dev-rds-mysql`        | MySQL RDS インスタンス                        |
| S3                 | `hoge-dev-s3-logs`          | ログ格納用S3                                  |
| CloudWatch Logs    | `hoge-dev-cwlogs-lambda-app` | Lambda (app) のログ用CloudWatch Logs         |
| CloudWatch Logs    | `hoge-dev-cwlogs-ec2-system` | EC2のシステムログ用CloudWatch Logs           |
| CloudWatch Logs    | `hoge-dev-cwlogs-kinesis-streaming` | Kinesis Data Streams のログ用CloudWatch Logs |
| Lambda             | `hoge-dev-lambda-auth`      | 認証処理を担当するLambda                      |
| Kinesis Data Stream | `hoge-dev-kds-analytics`   | Kinesis Data Streams (分析用)                 |
| DynamoDB           | `hoge-dev-dynamodb-user`    | ユーザーデータを保持するDynamoDB              |
| CloudFront         | `hoge-dev-cf-web`           | Web配信用CloudFront                          |
| ALB                | `hoge-dev-alb-public`       | Public向けのALB       

<br>
<br>
<br>

## 環境ごとのパラメータ、秘匿情報の取り扱い
- 環境ごとのパラメータは`./paramter.py`にて定義する
- その他、用途に応じたパラメータの使い分けは下記とする

| **用途**                                          | **環境変数 (`os.getenv()`)** | **GitHub Secrets (`secrets`)** | **`./paramter.py`** | **AWS Secrets Manager/Parameter Store**              |
| ------------------------------------------------- | ---------------------------- | ------------------------------ | ------------------- | ------------------------------------ |
| **機密情報 (APIキー, IAM認証情報, DBパスワード)** | -                            | ✅ **CI/CD 用**                | -                   | ✅ **AWS環境での機密情報管理**       |
| **環境ごとの設定 (dev/stg/prd 切り替え)**         | -                            | -                              | ✅                  | -                                    |
| **CI/CD での認証情報管理**                        | -                            | ✅                             | -                   | -                                    |
| **CDK のデフォルト設定**                          | -                            | -                              | ✅                  | -                                    |
| **AWS Lambda / EC2 での機密情報**                 | -                            | -                              | -                   | ✅ |

<br>
<br>
<br>
