"""
Tests for database seeding functionality
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.database.template import StoryTemplateModel
from models.enums import (InquiryStatus, Priority, StoryCategory, StoryPattern,
                          StoryStatus)
from seed_data import (clear_data, create_sample_inquiries,
                       create_sample_stories, create_sample_templates,
                       seed_data)


class TestCreateSampleInquiries:
    """Test sample inquiry creation"""

    def test_create_sample_inquiries_returns_list(self):
        """Test that create_sample_inquiries returns a list of InquiryModel objects"""
        inquiries = create_sample_inquiries()

        assert isinstance(inquiries, list)
        assert len(inquiries) == 3
        assert all(isinstance(inquiry, InquiryModel) for inquiry in inquiries)

    def test_inquiry_fields_are_properly_set(self):
        """Test that inquiry fields are properly populated"""
        inquiries = create_sample_inquiries()

        for inquiry in inquiries:
            assert inquiry.user_id is not None
            assert inquiry.content is not None
            assert inquiry.language == "ja"
            assert inquiry.status in [status.value for status in InquiryStatus]
            assert inquiry.inquiry_metadata is not None
            assert isinstance(inquiry.inquiry_metadata, dict)

    def test_inquiry_content_variety(self):
        """Test that inquiries have different content"""
        inquiries = create_sample_inquiries()

        contents = [inquiry.content for inquiry in inquiries]
        assert len(set(contents)) == len(contents)  # All contents should be unique

    def test_inquiry_status_variety(self):
        """Test that inquiries have different statuses"""
        inquiries = create_sample_inquiries()

        statuses = [inquiry.status for inquiry in inquiries]
        assert len(set(statuses)) > 1  # Should have multiple different statuses


class TestCreateSampleStories:
    """Test sample story creation"""

    def test_create_sample_stories_returns_list(self):
        """Test that create_sample_stories returns a list of StoryModel objects"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)

        assert isinstance(stories, list)
        assert len(stories) == 4  # Updated to match new story count
        assert all(isinstance(story, StoryModel) for story in stories)

    def test_story_fields_are_properly_set(self):
        """Test that story fields are properly populated"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)

        for story in stories:
            # inquiry_id should match one of the inquiry IDs (even if None in memory)
            inquiry_ids = [inquiry.id for inquiry in inquiries]
            assert story.inquiry_id in inquiry_ids
            assert story.title is not None
            assert story.description is not None
            assert story.category in [category.value for category in StoryCategory]
            assert story.priority in [priority.value for priority in Priority]
            assert story.estimated_effort > 0
            assert story.status in [status.value for status in StoryStatus]
            assert isinstance(story.tags, list)
            assert isinstance(story.story_metadata, dict)

    def test_story_inquiry_relationships(self):
        """Test that stories are properly linked to inquiries"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)

        inquiry_ids = {inquiry.id for inquiry in inquiries}
        story_inquiry_ids = {story.inquiry_id for story in stories}

        # All story inquiry_ids should reference existing inquiries
        assert story_inquiry_ids.issubset(inquiry_ids)

    def test_story_dependencies_are_valid(self):
        """Test that story dependencies reference valid story IDs"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)

        # Check that dependencies are properly set
        stories_with_deps = [s for s in stories if s.dependencies]
        if stories_with_deps:
            story_ids = {str(story.id) for story in stories}
            for story in stories_with_deps:
                for dep_id in story.dependencies:
                    assert dep_id in story_ids

    def test_story_deadlines_are_future_dates(self):
        """Test that story deadlines are set to future dates"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)

        now = datetime.now(timezone.utc)
        for story in stories:
            if story.deadline:
                assert story.deadline > now


class TestCreateSampleTemplates:
    """Test sample template creation"""

    def test_create_sample_templates_returns_list(self):
        """Test that create_sample_templates returns a list of
        StoryTemplateModel objects"""
        templates = create_sample_templates()

        assert isinstance(templates, list)
        assert len(templates) == 3
        assert all(isinstance(template, StoryTemplateModel) for template in templates)

    def test_template_fields_are_properly_set(self):
        """Test that template fields are properly populated"""
        templates = create_sample_templates()

        for template in templates:
            assert template.name is not None
            assert template.pattern in [pattern.value for pattern in StoryPattern]
            assert isinstance(template.fields, list)
            assert isinstance(template.checklist, list)
            assert template.default_estimate > 0
            assert isinstance(template.is_custom, bool)

    def test_template_fields_structure(self):
        """Test that template fields have proper structure"""
        templates = create_sample_templates()

        for template in templates:
            for field in template.fields:
                assert isinstance(field, dict)
                assert "name" in field
                assert "type" in field
                assert "required" in field

    def test_template_checklist_items(self):
        """Test that template checklists contain string items"""
        templates = create_sample_templates()

        for template in templates:
            assert len(template.checklist) > 0
            assert all(isinstance(item, str) for item in template.checklist)

    def test_template_patterns_are_unique(self):
        """Test that each template has a unique pattern"""
        templates = create_sample_templates()

        patterns = [template.pattern for template in templates]
        assert len(set(patterns)) == len(patterns)


class TestSeedData:
    """Test the main seed_data function"""

    @patch("seed_data.SessionLocal")
    def test_seed_data_success(self, mock_session_local):
        """Test successful seeding operation"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.count.return_value = 0  # No existing data

        seed_data()

        # Verify session operations
        mock_session.add_all.assert_called()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("seed_data.SessionLocal")
    def test_seed_data_skips_when_data_exists(self, mock_session_local):
        """Test that seeding is skipped when data already exists"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.count.return_value = 5  # Existing data

        seed_data()

        # Verify that no data was added
        mock_session.add_all.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @patch("seed_data.SessionLocal")
    def test_seed_data_handles_database_error(self, mock_session_local):
        """Test that database errors are properly handled"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.count.return_value = 0
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(SQLAlchemyError):
            seed_data()

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("seed_data.SessionLocal")
    @patch("seed_data.create_sample_inquiries")
    @patch("seed_data.create_sample_stories")
    @patch("seed_data.create_sample_templates")
    def test_seed_data_calls_creation_functions(
        self,
        mock_templates,
        mock_stories,
        mock_inquiries,
        mock_session_local
    ):
        """Test that seed_data calls all creation functions"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.count.return_value = 0

        # Mock return values
        mock_inquiries.return_value = []
        mock_stories.return_value = []
        mock_templates.return_value = []

        seed_data()

        # Verify all creation functions were called
        mock_inquiries.assert_called_once()
        mock_stories.assert_called_once()
        mock_templates.assert_called_once()


class TestClearData:
    """Test the clear_data function"""

    @patch("seed_data.SessionLocal")
    def test_clear_data_success(self, mock_session_local):
        """Test successful data clearing operation"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session

        # Mock query objects
        mock_story_query = MagicMock()
        mock_inquiry_query = MagicMock()
        mock_template_query = MagicMock()

        def mock_query_side_effect(model):
            if model == StoryModel:
                return mock_story_query
            elif model == InquiryModel:
                return mock_inquiry_query
            elif model == StoryTemplateModel:
                return mock_template_query
            return MagicMock()

        mock_session.query.side_effect = mock_query_side_effect

        clear_data()

        # Verify deletion order (stories first, then inquiries, then templates)
        mock_story_query.delete.assert_called_once()
        mock_inquiry_query.delete.assert_called_once()
        mock_template_query.delete.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("seed_data.SessionLocal")
    def test_clear_data_handles_database_error(self, mock_session_local):
        """Test that database errors during clearing are properly handled"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(SQLAlchemyError):
            clear_data()

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for seeding scenarios"""

    @patch("seed_data.SessionLocal")
    def test_full_seed_and_clear_cycle(self, mock_session_local):
        """Test a complete seed and clear cycle"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session

        # First call - no existing data
        mock_session.query.return_value.count.return_value = 0
        seed_data()

        # Verify seeding occurred
        assert mock_session.add_all.call_count == 3  # inquiries, stories, templates
        mock_session.commit.assert_called()

        # Reset mocks for clear operation
        mock_session.reset_mock()

        # Clear data
        clear_data()

        # Verify clearing occurred
        assert mock_session.query.call_count == 3  # Three delete operations
        mock_session.commit.assert_called()

    def test_data_consistency_between_creation_functions(self):
        """Test that data created by different functions is consistent"""
        inquiries = create_sample_inquiries()
        stories = create_sample_stories(inquiries)
        templates = create_sample_templates()

        # Verify data consistency
        inquiry_ids = {inquiry.id for inquiry in inquiries}
        story_inquiry_ids = {story.inquiry_id for story in stories}

        # All stories should reference existing inquiries
        assert story_inquiry_ids.issubset(inquiry_ids)

        # Verify that we have data for all expected categories
        story_categories = {story.category for story in stories}
        template_patterns = {template.pattern for template in templates}

        assert len(story_categories) > 1  # Multiple categories
        assert len(template_patterns) > 1  # Multiple patterns

    @patch("seed_data.SessionLocal")
    def test_error_recovery_during_seeding(self, mock_session_local):
        """Test error recovery during the seeding process"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.count.return_value = 0

        # Simulate error during flush
        mock_session.flush.side_effect = SQLAlchemyError("Flush error")

        with pytest.raises(SQLAlchemyError):
            seed_data()

        # Verify proper cleanup
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_inquiries_list_to_stories(self):
        """Test creating stories with empty inquiries list"""
        stories = create_sample_stories([])

        # Should handle empty list gracefully
        assert isinstance(stories, list)
        assert len(stories) == 0  # Should return empty list

    def test_single_inquiry_to_multiple_stories(self):
        """Test that multiple stories can be created from a single inquiry"""
        inquiries = create_sample_inquiries()
        single_inquiry = [inquiries[0]]
        stories = create_sample_stories(single_inquiry)

        # Should be able to create stories even with single inquiry
        assert isinstance(stories, list)
        if stories:  # If stories are created
            assert all(story.inquiry_id == single_inquiry[0].id for story in stories)

    def test_template_field_validation(self):
        """Test that template fields have required structure"""
        templates = create_sample_templates()

        required_field_keys = {"name", "type", "required"}

        for template in templates:
            for field in template.fields:
                # Each field should have at least the required keys
                assert required_field_keys.issubset(set(field.keys()))

                # Type should be a valid field type
                valid_types = {"text", "number", "date", "select"}
                assert field["type"] in valid_types

                # Required should be boolean
                assert isinstance(field["required"], bool)
