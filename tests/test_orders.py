from django.urls import reverse


def test_cart_page_renders(client):
    response = client.get(reverse("orders:cart"))
    assert response.status_code == 200


def test_cart_api_responds(client):
    response = client.get(reverse("orders:api_cart"))
    assert response.status_code == 200
