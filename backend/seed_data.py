"""
Database seed data for development and testing
"""
import uuid
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database import SessionLocal
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.database.template import StoryTemplateModel
from models.enums import (
    InquiryStatus,
    StoryStatus,
    Priority,
    StoryCategory,
    StoryPattern
)


def create_sample_inquiries() -> List[InquiryModel]:
    """Create sample inquiries for development"""
    inquiries = [
        InquiryModel(
            user_id="dev_user_1",
            content="ユーザー登録機能を追加したいです。メールアドレスとパスワードでの認証が必要です。",
            language="ja",
            status=InquiryStatus.COMPLETED.value,
            inquiry_metadata={
                "source": "web_form",
                "processing_time": 45.2,
                "ai_model": "gpt-4"
            }
        ),
        InquiryModel(
            user_id="dev_user_2", 
            content="バグ報告：ログイン画面でパスワードを忘れた場合のリンクが動作しません。緊急で修正が必要です。",
            language="ja",
            status=InquiryStatus.TASK_WORKING.value,
            inquiry_metadata={
                "source": "support_ticket",
                "processing_time": 23.1,
                "ai_model": "gpt-4"
            }
        ),
        InquiryModel(
            user_id="dev_user_1",
            content="データベースのパフォーマンス調査をお願いします。最近レスポンスが遅くなっています。",
            language="ja", 
            status=InquiryStatus.PROCESSING.value,
            inquiry_metadata={
                "source": "web_form",
                "ai_model": "gpt-4"
            }
        )
    ]
    return inquiries


def create_sample_stories(inquiries: List[InquiryModel]) -> List[StoryModel]:
    """Create sample stories linked to inquiries"""
    stories = [
        # Stories for first inquiry (user registration)
        StoryModel(
            inquiry_id=inquiries[0].id,
            title="ユーザー登録APIエンドポイントの実装",
            description="メールアドレスとパスワードを受け取るユーザー登録APIを実装する。バリデーション、重複チェック、パスワードハッシュ化を含む。",
            category=StoryCategory.DEVELOPMENT.value,
            priority=Priority.HIGH.value,
            estimated_effort=8.0,
            deadline=datetime.utcnow() + timedelta(days=7),
            status=StoryStatus.APPROVED.value,
            tags=["api", "authentication", "backend"],
            story_metadata={
                "original_inquiry": "ユーザー登録機能を追加したいです。メールアドレスとパスワードでの認証が必要です。",
                "generation_log": [
                    "Analyzed inquiry for user registration requirements",
                    "Identified need for API endpoint",
                    "Applied development template"
                ],
                "applied_template": "api_development",
                "confidence": 0.95
            }
        ),
        StoryModel(
            inquiry_id=inquiries[0].id,
            title="ユーザー登録フォームのUI実装",
            description="フロントエンドにユーザー登録フォームを実装する。入力バリデーション、エラーハンドリング、UXを考慮した設計。",
            category=StoryCategory.DEVELOPMENT.value,
            priority=Priority.MEDIUM.value,
            estimated_effort=6.0,
            deadline=datetime.utcnow() + timedelta(days=10),
            status=StoryStatus.EXPORTED.value,
            tags=["frontend", "ui", "form"],
            dependencies=[],  # Will be set after first story is created
            story_metadata={
                "original_inquiry": "ユーザー登録機能を追加したいです。メールアドレスとパスワードでの認証が必要です。",
                "generation_log": [
                    "Analyzed inquiry for UI requirements",
                    "Identified dependency on API endpoint",
                    "Applied frontend template"
                ],
                "applied_template": "frontend_form",
                "confidence": 0.88
            }
        ),
        
        # Story for second inquiry (bug fix)
        StoryModel(
            inquiry_id=inquiries[1].id,
            title="パスワードリセットリンク修正",
            description="ログイン画面のパスワードリセットリンクが動作しない問題を調査し修正する。緊急対応が必要。",
            category=StoryCategory.MAINTENANCE.value,
            priority=Priority.URGENT.value,
            estimated_effort=2.0,
            deadline=datetime.utcnow() + timedelta(days=1),
            status=StoryStatus.PENDING_REVIEW.value,
            tags=["bug", "urgent", "authentication"],
            story_metadata={
                "original_inquiry": "バグ報告：ログイン画面でパスワードを忘れた場合のリンクが動作しません。緊急で修正が必要です。",
                "generation_log": [
                    "Detected urgent keywords",
                    "Classified as bug fix",
                    "Applied maintenance template"
                ],
                "applied_template": "bug_fix",
                "confidence": 0.92
            }
        )
    ]
    
    # Set dependency for second story on first story
    if len(stories) >= 2:
        stories[1].dependencies = [str(stories[0].id)]
    
    return stories


def create_sample_templates() -> List[StoryTemplateModel]:
    """Create sample story templates"""
    templates = [
        StoryTemplateModel(
            name="API開発テンプレート",
            pattern=StoryPattern.FEATURE_ADDITION.value,
            fields=[
                {
                    "name": "endpoint_path",
                    "type": "text",
                    "required": True,
                    "defaultValue": "/api/"
                },
                {
                    "name": "http_method",
                    "type": "select",
                    "required": True,
                    "options": ["GET", "POST", "PUT", "DELETE"],
                    "defaultValue": "POST"
                },
                {
                    "name": "authentication_required",
                    "type": "select",
                    "required": True,
                    "options": ["Yes", "No"],
                    "defaultValue": "Yes"
                }
            ],
            checklist=[
                "APIエンドポイントの実装",
                "リクエスト/レスポンスモデルの定義",
                "バリデーションの実装",
                "エラーハンドリングの実装",
                "ユニットテストの作成",
                "API仕様書の更新"
            ],
            default_estimate=6.0,
            is_custom=False
        ),
        StoryTemplateModel(
            name="バグ修正テンプレート",
            pattern=StoryPattern.BUG_FIX.value,
            fields=[
                {
                    "name": "bug_severity",
                    "type": "select",
                    "required": True,
                    "options": ["Critical", "High", "Medium", "Low"],
                    "defaultValue": "Medium"
                },
                {
                    "name": "affected_component",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "reproduction_steps",
                    "type": "text",
                    "required": False
                }
            ],
            checklist=[
                "バグの再現確認",
                "根本原因の調査",
                "修正の実装",
                "テストケースの追加",
                "回帰テストの実行",
                "修正内容の文書化"
            ],
            default_estimate=3.0,
            is_custom=False
        ),
        StoryTemplateModel(
            name="調査タスクテンプレート",
            pattern=StoryPattern.INVESTIGATION.value,
            fields=[
                {
                    "name": "investigation_scope",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "expected_outcome",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "deadline",
                    "type": "date",
                    "required": False
                }
            ],
            checklist=[
                "調査計画の作成",
                "データ収集",
                "分析の実行",
                "結果の文書化",
                "推奨事項の提示",
                "ステークホルダーへの報告"
            ],
            default_estimate=4.0,
            is_custom=False
        )
    ]
    return templates


def seed_data():
    """
    Seed the database with sample data for development
    """
    db: Session = SessionLocal()
    
    try:
        print("🌱 Starting database seeding...")
        
        # Check if data already exists
        existing_inquiries = db.query(InquiryModel).count()
        if existing_inquiries > 0:
            print(f"ℹ️  Database already contains {existing_inquiries} inquiries. Skipping seeding.")
            return
        
        # Create sample data
        print("📝 Creating sample inquiries...")
        inquiries = create_sample_inquiries()
        db.add_all(inquiries)
        db.flush()  # Flush to get IDs
        
        print("📋 Creating sample stories...")
        stories = create_sample_stories(inquiries)
        db.add_all(stories)
        
        print("📄 Creating sample templates...")
        templates = create_sample_templates()
        db.add_all(templates)
        
        # Commit all changes
        db.commit()
        
        print(f"✅ Seeding completed successfully!")
        print(f"   - Created {len(inquiries)} inquiries")
        print(f"   - Created {len(stories)} stories")
        print(f"   - Created {len(templates)} templates")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_data():
    """
    Clear all data from the database (for testing)
    """
    db: Session = SessionLocal()
    
    try:
        print("🗑️  Clearing database data...")
        
        # Delete in reverse order of dependencies
        db.query(StoryModel).delete()
        db.query(InquiryModel).delete()
        db.query(StoryTemplateModel).delete()
        
        db.commit()
        print("✅ Database cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error during clearing: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()