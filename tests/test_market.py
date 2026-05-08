from django.urls import reverse


def test_home_page_renders(client):
    response = client.get(reverse("market:home"))
    assert response.status_code == 200


def test_products_api_responds(client):
    response = client.get(reverse("market:api_products"))
    assert response.status_code == 200
