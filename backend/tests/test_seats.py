import boto3
import pytest
from moto import mock_aws

from seats import claim_seat, SeatAlreadyTaken


@pytest.fixture
def table(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        t = dynamodb.create_table(
            TableName="seats",
            KeySchema=[{"AttributeName": "seat_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "seat_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        t.put_item(Item={"seat_id": "A1"})
        yield t


def test_claim_free_seat(table):
    claim_seat("A1", "alice")
    item = table.get_item(Key={"seat_id": "A1"})["Item"]
    assert item["buyer_id"] == "alice"


def test_cannot_claim_taken_seat(table):
    claim_seat("A1", "alice")
    with pytest.raises(SeatAlreadyTaken):
        claim_seat("A1", "bob")

from concurrent.futures import ThreadPoolExecutor


def test_many_buyers_only_one_wins(table):
    def try_claim(n):
        try:
            claim_seat("A1", f"buyer-{n}")
            return True
        except SeatAlreadyTaken:
            return False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(try_claim, range(100)))

    assert results.count(True) == 1