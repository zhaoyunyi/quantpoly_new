"""camelCase 序列化与分页响应测试 — Red 阶段。"""
from platform_core.schema import CamelModel
from platform_core.response import paged_response


class TestCamelCaseSerialization:
    """Test对外API字段统一camelCase。"""

    def test_snake_case_to_camel_case(self):
        class SampleModel(CamelModel):
            created_at: str
            user_name: str

        obj = SampleModel(created_at="2025-01-01", user_name="test")
        dumped = obj.model_dump(by_alias=True)
        assert "createdAt" in dumped
        assert "userName" in dumped
        assert "created_at" not in dumped

    def test_camel_case_json_output(self):
        class SampleModel(CamelModel):
            order_id: int
            total_amount: float

        obj = SampleModel(order_id=42, total_amount=99.9)
        json_str = obj.model_dump_json(by_alias=True)
        assert "orderId" in json_str
        assert "totalAmount" in json_str


class TestPagedResponse:
    """Test分页响应。"""

    def test_paged_response_structure(self):
        items = [{"id": 1}, {"id": 2}]
        result = paged_response(items=items, total=10, page=1, page_size=2)
        assert result["success"] is True
        assert result["data"]["items"] == items
        assert result["data"]["total"] == 10
        assert result["data"]["page"] == 1
        assert result["data"]["pageSize"] == 2
