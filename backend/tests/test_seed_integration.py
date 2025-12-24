"""
Integration tests for database seeding with real database operations
"""
import pytest

from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.database.story_template import StoryTemplateModel
from models.enums import (InquiryStatus, Priority, StoryCategory, StoryPattern,
                          StoryStatus)
from seed_data import (create_sample_inquiries, create_sample_stories,
                       create_sample_templates)


class TestSeedDataIntegration:
    """Integration tests using real database operations"""

    def test_create_sample_inquiries_integration(self, clean_database):
        """Test creating sample inquiries with real database session"""
        session = clean_database

        # Create inquiries
        inquiries = create_sample_inquiries()

        # Add to database
        session.add_all(inquiries)
        session.commit()

        # Verify in database
        db_inquiries = session.query(InquiryModel).all()
        assert len(db_inquiries) == 3

        # Verify data integrity
        for inquiry in db_inquiries:
            assert inquiry.id is not None
            assert inquiry.user_id is not None
            assert inquiry.content is not None
            assert inquiry.language == "ja"
            assert inquiry.status in [status.value for status in InquiryStatus]

    def test_create_sample_stories_integration(self, clean_database):
        """Test creating sample stories with real database session"""
        session = clean_database

        # First create and save inquiries
        inquiries = create_sample_inquiries()
        session.add_all(inquiries)
        session.commit()  # Commit to get proper IDs

        # Create stories
        stories = create_sample_stories(inquiries)
        session.add_all(stories)
        session.commit()

        # Verify in database - should have 4 stories
        # (2 for first inquiry, 1 for second, 1 for third)
        db_stories = session.query(StoryModel).all()
        assert len(db_stories) == 4

        # Verify relationships
        inquiry_ids = {inquiry.id for inquiry in inquiries}
        for story in db_stories:
            assert story.inquiry_id in inquiry_ids
            assert story.title is not None
            assert story.description is not None

    def test_create_sample_templates_integration(self, clean_database):
        """Test creating sample templates with real database session"""
        session = clean_database

        # Create templates
        templates = create_sample_templates()

        # Add to database
        session.add_all(templates)
        session.commit()

        # Verify in database
        db_templates = session.query(StoryTemplateModel).all()
        assert len(db_templates) == 3

        # Verify data integrity
        patterns = set()
        for template in db_templates:
            assert template.id is not None
            assert template.name is not None
            assert template.pattern is not None
            patterns.add(template.pattern)

        # Verify unique patterns
        assert len(patterns) == 3

    def test_full_seed_data_integration(self, clean_database):
        """Test the complete seed_data function with real database"""
        session = clean_database

        # Mock SessionLocal to return our test session
        import seed_data as seed_module

        original_session_local = seed_module.SessionLocal

        def mock_session_local():
            return session

        seed_module.SessionLocal = mock_session_local

        try:
            # Run seeding
            seed_module.seed_data()

            # Verify all data was created
            inquiries = session.query(InquiryModel).all()
            stories = session.query(StoryModel).all()
            templates = session.query(StoryTemplateModel).all()

            assert len(inquiries) == 3
            assert len(stories) == 4  # Updated to match new story count
            assert len(templates) == 3

            # Verify relationships
            inquiry_ids = {inquiry.id for inquiry in inquiries}
            story_inquiry_ids = {story.inquiry_id for story in stories}
            assert story_inquiry_ids.issubset(inquiry_ids)

        finally:
            # Restore original SessionLocal
            seed_module.SessionLocal = original_session_local

    def test_clear_data_integration(self, clean_database):
        """Test the clear_data function with real database"""
        session = clean_database

        # First add inquiries and commit them to get proper IDs
        inquiries = create_sample_inquiries()
        session.add_all(inquiries)
        session.commit()

        # Now create stories with the committed inquiries
        stories = create_sample_stories(inquiries)
        templates = create_sample_templates()

        session.add_all(stories)
        session.add_all(templates)
        session.commit()

        # Verify data exists
        assert session.query(InquiryModel).count() == 3
        assert (
            session.query(StoryModel).count() == 4
        )  # Updated to match new story count
        assert session.query(StoryTemplateModel).count() == 3

        # Mock SessionLocal to return our test session
        import seed_data as seed_module

        original_session_local = seed_module.SessionLocal

        def mock_session_local():
            return session

        seed_module.SessionLocal = mock_session_local

        try:
            # Clear data
            seed_module.clear_data()

            # Verify all data was cleared
            assert session.query(InquiryModel).count() == 0
            assert session.query(StoryModel).count() == 0
            assert session.query(StoryTemplateModel).count() == 0

        finally:
            # Restore original SessionLocal
            seed_module.SessionLocal = original_session_local

    def test_seed_data_idempotency(self, clean_database):
        """Test that running seed_data multiple times doesn't create duplicates"""
        session = clean_database

        # Mock SessionLocal to return our test session
        import seed_data as seed_module

        original_session_local = seed_module.SessionLocal

        def mock_session_local():
            return session

        seed_module.SessionLocal = mock_session_local

        try:
            # Run seeding twice
            seed_module.seed_data()
            seed_module.seed_data()  # Should skip due to existing data

            # Verify only one set of data exists
            inquiries = session.query(InquiryModel).all()
            stories = session.query(StoryModel).all()
            templates = session.query(StoryTemplateModel).all()

            assert len(inquiries) == 3
            assert len(stories) == 4  # Updated to match new story count
            assert len(templates) == 3

        finally:
            # Restore original SessionLocal
            seed_module.SessionLocal = original_session_local


class TestDataValidation:
    """Test data validation and constraints"""

    def test_inquiry_data_validation(self, clean_database):
        """Test that inquiry data meets validation requirements"""
        session = clean_database

        inquiries = create_sample_inquiries()
        session.add_all(inquiries)
        session.commit()

        for inquiry in inquiries:
            # Test required fields
            assert inquiry.user_id is not None and inquiry.user_id != ""
            assert inquiry.content is not None and inquiry.content != ""
            assert inquiry.language in ["ja", "en"]

            # Test metadata structure
            assert isinstance(inquiry.inquiry_metadata, dict)
            assert "source" in inquiry.inquiry_metadata

    def test_story_data_validation(self, clean_database):
        """Test that story data meets validation requirements"""
        session = clean_database

        inquiries = create_sample_inquiries()
        session.add_all(inquiries)
        session.commit()  # Commit to get proper IDs

        stories = create_sample_stories(inquiries)
        session.add_all(stories)
        session.commit()

        for story in stories:
            # Test required fields
            assert story.title is not None and story.title != ""
            assert story.description is not None and story.description != ""
            assert story.estimated_effort > 0

            # Test enum values
            assert story.category in [cat.value for cat in StoryCategory]
            assert story.priority in [pri.value for pri in Priority]
            assert story.status in [stat.value for stat in StoryStatus]

            # Test metadata structure
            assert isinstance(story.story_metadata, dict)
            assert "original_inquiry" in story.story_metadata
            assert "generation_log" in story.story_metadata

    def test_template_data_validation(self, clean_database):
        """Test that template data meets validation requirements"""
        session = clean_database

        templates = create_sample_templates()
        session.add_all(templates)
        session.commit()

        for template in templates:
            # Test required fields
            assert template.name is not None and template.name != ""
            assert template.pattern in [pat.value for pat in StoryPattern]
            assert template.default_estimate > 0

            # Test field structure
            assert isinstance(template.fields, list)
            assert len(template.fields) > 0

            for field in template.fields:
                assert isinstance(field, dict)
                assert "name" in field
                assert "type" in field
                assert "required" in field

            # Test checklist
            assert isinstance(template.checklist, list)
            assert len(template.checklist) > 0
            assert all(isinstance(item, str) for item in template.checklist)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_foreign_key_constraints(self, clean_database):
        """Test that foreign key constraints are properly handled"""
        session = clean_database

        # Try to create a story without a corresponding inquiry
        from uuid import uuid4

        story = StoryModel(
            inquiry_id=uuid4(),  # Non-existent inquiry ID
            title="Test Story",
            description="Test Description",
            category=StoryCategory.DEVELOPMENT.value,
            priority=Priority.MEDIUM.value,
            estimated_effort=4.0,
            status=StoryStatus.PENDING_REVIEW.value,
            story_metadata={"test": "data"},
        )

        session.add(story)

        # This should raise an integrity error due to foreign key constraint
        with pytest.raises(Exception):
            # SQLAlchemy will raise an integrity error
            session.commit()

    def test_data_consistency_after_partial_failure(self, clean_database):
        """Test data consistency when partial operations fail"""
        session = clean_database

        # Add valid inquiries
        inquiries = create_sample_inquiries()
        session.add_all(inquiries)
        session.commit()

        # Verify inquiries were added
        assert session.query(InquiryModel).count() == 3

        # Even if subsequent operations fail, inquiries should remain
        initial_count = session.query(InquiryModel).count()

        # Try to add invalid data (this might fail)
        try:
            invalid_story = StoryModel(
                inquiry_id=None,  # Invalid
                title="",  # Invalid
                description="",  # Invalid
                category="invalid_category",
                priority="invalid_priority",
                estimated_effort=-1,  # Invalid
                status="invalid_status",
                story_metadata={},
            )
            session.add(invalid_story)
            session.commit()
        except Exception:
            session.rollback()

        # Original inquiries should still exist
        assert session.query(InquiryModel).count() == initial_count
