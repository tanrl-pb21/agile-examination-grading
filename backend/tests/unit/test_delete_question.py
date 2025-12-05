"""
Unit Tests for Delete Question Functionality
Tests the service layer and API endpoint with mocked database
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException


class TestDeleteQuestionService:
    """Unit tests for delete_question service method"""

    def test_delete_mcq_question_success(self):
        """Test successfully deleting an MCQ question"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act
            result = service.delete_question(1)
            
            # Assert
            assert result == {'id': 1}
            assert mock_cursor.execute.call_count == 2
            # Verify questionOption deleted first
            first_call = mock_cursor.execute.call_args_list[0]
            assert 'DELETE FROM "questionOption"' in first_call[0][0]
            assert first_call[0][1] == (1,)
            # Verify question deleted second
            second_call = mock_cursor.execute.call_args_list[1]
            assert 'DELETE FROM question' in second_call[0][0]
            assert second_call[0][1] == (1,)
            mock_conn.commit.assert_called_once()

    def test_delete_essay_question_success(self):
        """Test successfully deleting an essay question"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 2}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act
            result = service.delete_question(2)
            
            # Assert
            assert result == {'id': 2}
            assert mock_cursor.execute.call_count == 2
            mock_conn.commit.assert_called_once()

    def test_delete_question_not_found(self):
        """Test deleting a non-existent question raises ValueError"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act & Assert
            with pytest.raises(ValueError, match="Question with id 999 not found"):
                service.delete_question(999)
            
            # Verify commit was still called
            mock_conn.commit.assert_called_once()

    def test_delete_question_deletes_options_first(self):
        """Test that question options are deleted before the question"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act
            service.delete_question(1)
            
            # Assert - verify order of execution
            calls = mock_cursor.execute.call_args_list
            assert len(calls) == 2
            assert 'questionOption' in calls[0][0][0]
            assert 'question' in calls[1][0][0]

    def test_delete_question_transaction_rollback_on_error(self):
        """Test that transaction is handled properly on database error"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                service.delete_question(1)
            
            assert "Database error" in str(exc_info.value)

    def test_delete_question_with_zero_id(self):
        """Test deleting question with id 0"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act & Assert
            with pytest.raises(ValueError):
                service.delete_question(0)

    def test_delete_question_with_negative_id(self):
        """Test deleting question with negative id"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act & Assert
            with pytest.raises(ValueError):
                service.delete_question(-1)


class TestDeleteQuestionAPI:
    """Unit tests for delete question API endpoint"""

    def test_delete_question_endpoint_success(self):
        """Test DELETE endpoint returns success message"""
        # Arrange & Act
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 1}
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.main import app
            client = TestClient(app)
            response = client.delete("/questions/1")
            
            # Assert
            assert response.status_code == 200
            assert response.json() == {"message": "Question deleted successfully"}

    def test_delete_question_endpoint_not_found(self):
        """Test DELETE endpoint returns 404 for non-existent question"""
        # Arrange & Act
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.main import app
            client = TestClient(app)
            response = client.delete("/questions/999")
            
            # Assert
            assert response.status_code == 404
            assert "Question with id 999 not found" in response.json()["detail"]

    def test_delete_question_endpoint_invalid_id_type(self):
        """Test DELETE endpoint with invalid question id type"""
        from src.main import app
        client = TestClient(app)
        
        # Act
        response = client.delete("/questions/invalid")
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_delete_mcq_question_removes_all_options(self):
        """Test that deleting MCQ question removes all associated options"""
        # Arrange & Act
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 1}
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.main import app
            client = TestClient(app)
            response = client.delete("/questions/1")
            
            # Assert
            assert response.status_code == 200
            # Verify both deletes were called
            assert mock_cursor.execute.call_count == 2

    def test_delete_essay_question_no_options(self):
        """Test that deleting essay question works without options"""
        # Arrange & Act
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 2}
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.main import app
            client = TestClient(app)
            response = client.delete("/questions/2")
            
            # Assert
            assert response.status_code == 200
            assert response.json() == {"message": "Question deleted successfully"}


class TestDeleteQuestionEdgeCases:
    """Edge case tests for delete question functionality"""

    def test_delete_question_with_large_id(self):
        """Test deleting question with very large id"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 999999999}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act
            result = service.delete_question(999999999)
            
            # Assert
            assert result == {'id': 999999999}

    def test_delete_question_connection_context_manager(self):
        """Test that connection context manager is properly used"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        
        with patch('src.services.question_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            from src.services.question_service import QuestionService
            service = QuestionService()
            
            # Act
            service.delete_question(1)
            
            # Assert - verify context managers were used
            mock_get_conn.assert_called_once()
            mock_conn.cursor.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])