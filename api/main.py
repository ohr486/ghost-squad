"""Ghost Squad API - Main application."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import importer, inquiry, story
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.importer_config_loader import ImporterConfigLoader
from services.importer.plugin_registry import PluginRegistryService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理."""
    # 起動時: インポーター設定をロード
    config_path = Path("config/importer_config.yaml")
    if config_path.exists():
        try:
            plugin_registry = PluginRegistryService()
            ai_provider_registry = AIProviderRegistryService()

            loader = ImporterConfigLoader(
                plugin_registry=plugin_registry,
                ai_provider_registry=ai_provider_registry,
            )
            loader.load_from_file(config_path)

            # ルーターにレジストリを設定
            importer.set_plugin_registry(plugin_registry)
            importer.set_ai_provider_registry(ai_provider_registry)

            logger.info("インポーター設定をロードしました")
        except Exception as e:
            logger.error(f"インポーター設定のロードに失敗しました: {e}")
    else:
        logger.warning(f"設定ファイルが見つかりません: {config_path}")

    yield
    # 終了時のクリーンアップ（必要に応じて追加）


app = FastAPI(
    title="Ghost Squad API",
    description="AI-Driven Task Management Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(inquiry.router)
app.include_router(story.router)
app.include_router(importer.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Ghost Squad API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
