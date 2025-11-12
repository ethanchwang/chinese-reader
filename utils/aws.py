import os
import boto3

ENVIRONMENT = os.getenv("APP_ENV", "production")

_polly_client = None
_ssm_client = None

if ENVIRONMENT == "development":
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_POLLY_DEV_ACCESS_KEY = os.getenv("AWS_POLLY_DEV_ACCESS_KEY")
    AWS_POLLY_DEV_KEY_ID = os.getenv("AWS_POLLY_DEV_KEY_ID")
else:
    session = boto3.Session()
    AWS_REGION = session.region_name


def get_polly_client():
    global _polly_client
    if _polly_client is None:
        if ENVIRONMENT == "production":
            _polly_client = boto3.client(
                "polly",
                region_name=AWS_REGION,
            )
        else:
            _polly_client = boto3.client(
                "polly",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_POLLY_DEV_KEY_ID,
                aws_secret_access_key=AWS_POLLY_DEV_ACCESS_KEY,
            )
    return _polly_client


def get_ssm_parameter(parameter_name: str, with_decryption: bool = True) -> str:
    """
    Get a parameter from AWS Systems Manager Parameter Store.

    Args:
        parameter_name: The name of the parameter to retrieve
        with_decryption: Whether to decrypt SecureString parameters

    Returns:
        The parameter value

    Raises:
        RuntimeError: If the parameter cannot be retrieved
    """
    global _ssm_client
    if _ssm_client is None:
        _ssm_client = boto3.client("ssm")

    try:
        response = _ssm_client.get_parameter(
            Name=parameter_name, WithDecryption=with_decryption
        )
        return response["Parameter"]["Value"]
    except Exception as e:
        raise RuntimeError(
            f"Could not retrieve parameter {parameter_name} from SSM: {e}"
        )
