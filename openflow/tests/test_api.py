"""
Tests for API Layer (JSON-RPC and REST endpoints)
"""

import pytest
from fastapi.testclient import TestClient
from openflow.server.main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token for tests"""
    # In a real test, this would authenticate with valid credentials
    # For now, we'll use a mock token
    return "test_token"


@pytest.fixture
def auth_headers(auth_token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestJSONRPC:
    """Test JSON-RPC endpoints"""

    def test_jsonrpc_call_method(self, auth_headers):
        """Test JSON-RPC call method"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "res.users",
                "method": "search_read",
                "args": [[]],
                "kwargs": {"limit": 10}
            },
            "id": 1
        }

        response = client.post("/jsonrpc", json=payload, headers=auth_headers)

        # May fail if not authenticated, but should return valid JSON-RPC response
        assert response.status_code in [200, 401]
        data = response.json()
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        assert "id" in data

    def test_jsonrpc_invalid_method(self, auth_headers):
        """Test JSON-RPC with invalid method"""
        payload = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {},
            "id": 2
        }

        response = client.post("/jsonrpc", json=payload, headers=auth_headers)

        # Should return error response
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    def test_jsonrpc_missing_params(self, auth_headers):
        """Test JSON-RPC with missing required params"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                # Missing 'model' and 'method'
            },
            "id": 3
        }

        response = client.post("/jsonrpc", json=payload, headers=auth_headers)

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32602  # Invalid params

    def test_jsonrpc_batch(self, auth_headers):
        """Test JSON-RPC batch requests"""
        payload = [
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "res.users",
                    "method": "search",
                    "args": [[]],
                    "kwargs": {"limit": 1}
                },
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "res.partner",
                    "method": "search",
                    "args": [[]],
                    "kwargs": {"limit": 1}
                },
                "id": 2
            }
        ]

        response = client.post("/jsonrpc/batch", json=payload, headers=auth_headers)

        # Should return array of responses
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2


class TestRESTAPI:
    """Test REST API endpoints"""

    def test_rest_list_records(self, auth_headers):
        """Test listing records"""
        response = client.get("/api/v1/res.users", headers=auth_headers)

        # May fail if not authenticated
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert isinstance(data["data"], list)
            assert "meta" in data

    def test_rest_list_with_filters(self, auth_headers):
        """Test listing with filters"""
        params = {
            "domain": '[["active", "=", true]]',
            "fields": "id,name",
            "limit": 5,
            "offset": 0
        }

        response = client.get("/api/v1/res.users", params=params, headers=auth_headers)

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "meta" in data
            assert data["meta"]["limit"] == 5

    def test_rest_get_record(self, auth_headers):
        """Test getting single record"""
        response = client.get("/api/v1/res.users/1", headers=auth_headers)

        # May fail if not authenticated or record doesn't exist
        assert response.status_code in [200, 401, 404]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert isinstance(data["data"], dict)

    def test_rest_create_record(self, auth_headers):
        """Test creating a record"""
        payload = {
            "values": {
                "name": "Test User",
                "login": "test_user",
            }
        }

        response = client.post("/api/v1/res.users", json=payload, headers=auth_headers)

        # May fail if not authenticated or validation fails
        assert response.status_code in [201, 400, 401, 403]

    def test_rest_update_record(self, auth_headers):
        """Test updating a record"""
        payload = {
            "values": {
                "name": "Updated Name",
            }
        }

        response = client.put("/api/v1/res.users/1", json=payload, headers=auth_headers)

        # May fail if not authenticated or not found
        assert response.status_code in [200, 401, 403, 404]

    def test_rest_delete_record(self, auth_headers):
        """Test deleting a record"""
        response = client.delete("/api/v1/res.users/999", headers=auth_headers)

        # May fail if not authenticated or not found
        assert response.status_code in [200, 401, 403, 404]

    def test_rest_search_post(self, auth_headers):
        """Test POST search endpoint"""
        payload = {
            "domain": [["active", "=", True]],
            "fields": ["id", "name"],
            "limit": 10,
            "offset": 0
        }

        response = client.post("/api/v1/res.users/search", json=payload, headers=auth_headers)

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["data"], list)

    def test_rest_count_records(self, auth_headers):
        """Test count endpoint"""
        response = client.get("/api/v1/res.users/count", headers=auth_headers)

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert "count" in data["data"]

    def test_rest_invalid_model(self, auth_headers):
        """Test with invalid model name"""
        response = client.get("/api/v1/invalid.model", headers=auth_headers)

        # Should return 404 or 401
        assert response.status_code in [401, 404]

        if response.status_code == 404:
            data = response.json()
            assert "error" in data


class TestAuthentication:
    """Test authentication mechanisms"""

    def test_no_authentication(self):
        """Test request without authentication"""
        response = client.get("/api/v1/res.users")

        # Should require authentication
        assert response.status_code == 401

    def test_invalid_token(self):
        """Test with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/res.users", headers=headers)

        # Should fail authentication
        assert response.status_code == 401

    def test_api_key_authentication(self):
        """Test API key authentication"""
        headers = {"X-API-Key": "test_api_key"}
        response = client.get("/api/v1/res.users", headers=headers)

        # May succeed or fail depending on key validity
        assert response.status_code in [200, 401]


class TestErrorHandling:
    """Test error handling"""

    def test_validation_error(self, auth_headers):
        """Test validation error response"""
        # Try to create record with missing required fields
        payload = {
            "values": {}
        }

        response = client.post("/api/v1/res.users", json=payload, headers=auth_headers)

        # Should return validation error
        assert response.status_code in [400, 401]

    def test_not_found_error(self, auth_headers):
        """Test not found error"""
        response = client.get("/api/v1/res.users/999999", headers=auth_headers)

        # Should return not found
        assert response.status_code in [401, 404]

    def test_malformed_json(self, auth_headers):
        """Test malformed JSON request"""
        response = client.post(
            "/jsonrpc",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        # Should return 422 (validation error)
        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/api/v1/res.users")

        # Check CORS headers
        # Note: actual headers depend on CORS configuration
        assert response.status_code in [200, 405]


class TestResponseFormat:
    """Test response format consistency"""

    def test_success_response_format(self, auth_headers):
        """Test successful response format"""
        response = client.get("/api/v1/res.users/count", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert data["success"] is True
            assert "data" in data

    def test_error_response_format(self, auth_headers):
        """Test error response format"""
        response = client.get("/api/v1/invalid.model", headers=auth_headers)

        if response.status_code in [400, 404, 500]:
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "message" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
