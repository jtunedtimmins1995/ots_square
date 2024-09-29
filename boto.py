import boto3
from botocore.exceptions import ClientError
import json

def get_google_secret():
    return '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'
    # secret_name = "google_service_account"
    # region_name = "eu-north-1"

    # # Create a Secrets Manager client
    # session = boto3.session.Session()
    # client = session.client(
    #     service_name='secretsmanager',
    #     region_name=region_name
    # )

    # try:
    #     get_secret_value_response = client.get_secret_value(
    #         SecretId=secret_name
    #     )
    # except ClientError as e:
    #     # For a list of exceptions thrown, see
    #     # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    #     raise e

    # # Decrypts secret using the associated KMS key.
    # secret = get_secret_value_response['SecretString']
    
    # return json.loads(secret)


def get_square_secret():
    try:
        secret_name = "SQUARE_ACCESS_TOKEN"
        region_name = "eu-north-1"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']

        return json.loads(secret)
    except:
        return 'EAAAFO_dqOOnvRZCLDvOtKfBGznlxPy5zb4anviDPIJBjXjXGkmo5d6w1jxoxtCn'
