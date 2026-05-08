import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_user_model_can_create_user():
    user = User.objects.create_user(username="tester", password="secret123")
    assert user.username == "tester"


def test_login_page_renders(client):
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
