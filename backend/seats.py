import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "seats"


class SeatAlreadyTaken(Exception):
    pass


def get_table():
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(TABLE_NAME)


def claim_seat(seat_id: str, buyer_id: str) -> None:
    table = get_table()
    try:
        table.update_item(
            Key={"seat_id": seat_id},
            UpdateExpression="SET buyer_id = :b",
            ConditionExpression="attribute_exists(seat_id) AND attribute_not_exists(buyer_id)",
            ExpressionAttributeValues={":b": buyer_id},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise SeatAlreadyTaken(seat_id)
        raise

