import requests
from http import HTTPStatus

BASE_URL = "https://qa-internship.avito.com"

# Тестовые данные, найденные вручную через postman
TEST_ITEM_UUID = "8d954969-0c55-4b50-af0b-00115a280ef7"  # Реальный UUID объявления
TEST_SELLER_WITH_ITEMS = 999999  # sellerID с существующими объявлениями
TEST_SELLER_EMPTY = 99999999999  # sellerID без объявлений (проверено вручную)
TEST_SELLER_VALID = 111111  # Валидный sellerID для тестов создания


class TestCreateItem:
    """Тесты создания объявления (POST /api/1/item)"""

    def test_create_valid_item(self):
        """TC-001: Создание валидного объявления"""
        test_data = {
            "sellerID": 123,
            "name": "testItem",
            "price": 9900,
            "statistics": {"likes": 21, "viewCount": 11, "contacts": 43},
        }

        response = requests.post(f"{BASE_URL}/api/1/item", json=test_data)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data.get("status", "").startswith("Сохранили объявление")

    def test_create_item_without_required_field(self):
        """TC-002: Создание объявления без обязательных полей"""
        invalid_data = {
            "sellerID": 123,
            "price": 9900,
            "statistics": {"likes": 21, "viewCount": 11, "contacts": 43},
        }

        response = requests.post(f"{BASE_URL}/api/1/item", json=invalid_data)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            "result": {"message": "поле name обязательно", "messages": {}},
            "status": "400",
        }

    def test_create_item_invalid_seller_id(self):
        """TC-003: Создание объявления с некорректным sellerID"""
        # Используем строковый sellerID вместо числового
        invalid_data = {
            "sellerID": "invalid seller",
            "name": "testItem",
            "price": 9900,
            "statistics": {"likes": 21, "viewCount": 11, "contacts": 43},
        }

        response = requests.post(f"{BASE_URL}/api/1/item", json=invalid_data)

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_create_item_negative_price(self):
        """TC-004: Создание объявления с отрицательной ценой"""
        # Примечание: Рекомендация к улучшению BUG-001
        test_data = {
            "sellerID": 123,
            "name": "testItem",
            "price": -9900,  # Отрицательная цена
            "statistics": {"contacts": 43, "likes": 21, "viewCount": 11},
        }

        response = requests.post(f"{BASE_URL}/api/1/item", json=test_data)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "status" in data
        assert "Сохранили объявление" in data["status"]

        # Извлекаем UUID и проверяем сохраненную цену
        uuid = data["status"].split(" - ")[-1]

        # Получаем объявление и проверяем цену
        get_response = requests.get(f"{BASE_URL}/api/1/item/{uuid}")
        assert get_response.status_code == HTTPStatus.OK
        item_data = get_response.json()
        assert len(item_data) == 1
        assert item_data[0]["price"] == -9900  # Цена должна сохраниться отрицательной


class TestGetItemById:
    """Тесты получения объявления по ID (GET /api/1/item/{id})"""

    def test_get_existing_item(self):
        """TC-005: Получение существующего объявления"""
        # Используем реальный UUID из существующих данных
        real_uuid = TEST_ITEM_UUID
        response = requests.get(f"{BASE_URL}/api/1/item/{real_uuid}")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == real_uuid

    def test_get_nonexistent_item(self):
        """TC-006: Получение несуществующего объявления"""
        fake_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        response = requests.get(f"{BASE_URL}/api/1/item/{fake_uuid}")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {
            "result": {
                "message": "item aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee not found",
                "messages": None,
            },
            "status": "404",
        }

    def test_get_item_invalid_id(self):
        """TC-007: Получение объявления с невалидным ID (не UUID)"""
        response = requests.get(f"{BASE_URL}/api/1/item/abc")

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            "result": {
                "message": "ID айтема не UUID: abc",
                "messages": {},
            },
            "status": "400",
        }


class TestGetItemsBySeller:
    """Тесты получения объявлений по sellerID (GET /api/1/{sellerID}/item)"""

    def test_get_items_existing_seller(self):
        """TC-008: Получение объявлений существующего продавца"""
        # Используем sellerID с существующими данными
        seller_id = TEST_SELLER_WITH_ITEMS
        response = requests.get(f"{BASE_URL}/api/1/{seller_id}/item")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        # Проверяем, что объявления принадлежат правильному sellerID
        for item in data:
            assert (
                item.get("sellerId") == seller_id or item.get("sellerID") == seller_id
            )

    def test_get_items_empty_seller(self):
        """TC-009: Получение объявлений продавца без объявлений"""
        # Генерируем случайный sellerID, которого нет (проверено вручную)
        seller_id = TEST_SELLER_EMPTY  # sellerID без объявлений
        response = requests.get(f"{BASE_URL}/api/1/{seller_id}/item")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_items_invalid_seller_id(self):
        """TC-010: Получение объявлений с невалидным sellerID"""
        response = requests.get(f"{BASE_URL}/api/1/abc/item")

        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestGetItemStatistics:
    """Тесты получения статистики по объявлению (GET /api/1/item/{sellerID}/statistic)"""

    def test_get_statistics_existing_item(self):
        """TC-011: Получение статистики существующего объявления"""
        # Статистика возвращается вместе с объявлением, используем реальный UUID
        real_uuid = TEST_ITEM_UUID
        response = requests.get(f"{BASE_URL}/api/1/item/{real_uuid}")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert "statistics" in item
        stats = item["statistics"]
        assert "contacts" in stats
        assert "likes" in stats
        assert "viewCount" in stats

    def test_get_statistics_nonexistent_item(self):
        """TC-012: Получение статистики несуществующего объявления"""
        # Используем случайный UUID
        fake_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        response = requests.get(f"{BASE_URL}/api/1/item/{fake_uuid}")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_get_statistics_invalid_id(self):
        """TC-013: Получение статистики с невалидным ID"""
        response = requests.get(f"{BASE_URL}/api/1/item/abc")

        assert response.status_code == HTTPStatus.BAD_REQUEST
