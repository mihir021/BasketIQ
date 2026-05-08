from django.urls import reverse


def test_expenses_api_requires_auth(client):
    response = client.get(reverse("expenses:api_expenses"))
    assert response.status_code == 401
