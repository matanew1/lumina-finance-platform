def test_upload_transactions_endpoint_persists_valid_csv(
    client,
    fake_upload_session,
    override_db,
) -> None:
    override_db(fake_upload_session)
    csv_body = (
        "ClientId,TransactionId,ISIN,Action,Quantity,Price,Timestamp\n"
        "C001,T1001,US1234567890,Buy,10,100,2024-01-01T10:00:00\n"
    ).encode()

    response = client.post(
        "/upload-transactions",
        files={"file": ("transactions.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["persisted_rows"] == 1
    assert fake_upload_session.committed is True
