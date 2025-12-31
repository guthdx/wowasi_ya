"""Outline Wiki Integration - Publish documents to Outline Wiki."""

import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr

from wowasi_ya.config import Settings, get_settings
from wowasi_ya.models.document import Document, GeneratedProject


@dataclass
class OutlineCollection:
    """Represents an Outline collection (project folder)."""

    id: str
    name: str
    url: str
    url_id: str


@dataclass
class OutlineDocument:
    """Represents a published Outline document."""

    id: str
    title: str
    url: str
    collection_id: str


@dataclass
class PublishResult:
    """Result of publishing a project to Outline."""

    collection: OutlineCollection
    documents: list[OutlineDocument]
    public_url: str | None = None


class OutlineClient:
    """Client for interacting with Outline Wiki API.

    Wraps the outline-wiki-api package to provide async-friendly methods.
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: SecretStr | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize Outline client.

        Args:
            api_url: Outline API URL (e.g., https://docs.iyeska.net)
            api_key: Outline API key
            settings: Optional settings object (uses defaults if not provided)
        """
        self._settings = settings or get_settings()
        self._api_url = api_url or self._settings.outline_api_url
        self._api_key = api_key or self._settings.outline_api_key

        if not self._api_key:
            raise ValueError("Outline API key is required. Set OUTLINE_API_KEY environment variable.")

        # Lazy-load the outline client
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the outline-wiki-api client."""
        if self._client is None:
            try:
                from outline_wiki_api import OutlineWiki
            except ImportError as e:
                raise ImportError(
                    "outline-wiki-api package not installed. Run: pip install outline-wiki-api"
                ) from e

            # Get the actual key value from SecretStr
            api_key_value = self._api_key.get_secret_value() if self._api_key else None
            self._client = OutlineWiki(url=self._api_url, token=api_key_value)

        return self._client

    async def health_check(self) -> bool:
        """Check if Outline API is accessible."""
        try:
            client = self._get_client()
            # Run sync API call in thread pool
            result = await asyncio.to_thread(lambda: client.auth.info())
            return result.ok
        except Exception:
            return False

    async def create_collection(
        self,
        name: str,
        description: str | None = None,
        permission: str = "read_write",
    ) -> OutlineCollection:
        """Create a new collection in Outline.

        Args:
            name: Collection name (project name)
            description: Collection description
            permission: Permission level (read, read_write)

        Returns:
            Created OutlineCollection
        """
        client = self._get_client()

        result = await asyncio.to_thread(
            lambda: client.collections.create(
                name=name,
                description=description or "",
                permission=permission,
            )
        )

        if not result.ok:
            raise RuntimeError(f"Failed to create collection: {result}")

        data = result.data
        return OutlineCollection(
            id=data.id,
            name=data.name,
            url=f"{self._api_url}/collection/{data.url_id}",
            url_id=data.url_id,
        )

    async def create_document(
        self,
        title: str,
        content: str,
        collection_id: str,
        publish: bool = True,
    ) -> OutlineDocument:
        """Create a document in a collection.

        Args:
            title: Document title
            content: Markdown content
            collection_id: Parent collection ID
            publish: Whether to publish immediately

        Returns:
            Created OutlineDocument
        """
        client = self._get_client()

        result = await asyncio.to_thread(
            lambda: client.documents.create(
                title=title,
                text=content,
                collection_id=collection_id,
                publish=publish,
            )
        )

        if not result.ok:
            raise RuntimeError(f"Failed to create document: {result}")

        data = result.data
        return OutlineDocument(
            id=data.id,
            title=data.title,
            url=f"{self._api_url}{data.url}",
            collection_id=collection_id,
        )

    async def enable_sharing(self, collection_id: str) -> str | None:
        """Enable public sharing for a collection.

        Args:
            collection_id: Collection ID to share

        Returns:
            Public share URL or None if failed
        """
        client = self._get_client()

        try:
            result = await asyncio.to_thread(
                lambda: client.collections.update(
                    id=collection_id,
                    sharing=True,
                )
            )

            if result.ok and result.data:
                # Get the share URL
                url_id = result.data.url_id
                return f"{self._api_url}/s/{url_id}"
        except Exception:
            pass

        return None

    async def list_collections(self) -> list[OutlineCollection]:
        """List all collections accessible to the API key."""
        client = self._get_client()

        result = await asyncio.to_thread(lambda: client.collections.list())

        if not result.ok:
            return []

        return [
            OutlineCollection(
                id=c.id,
                name=c.name,
                url=f"{self._api_url}/collection/{c.url_id}",
                url_id=c.url_id,
            )
            for c in result.data
        ]


class OutlinePublisher:
    """Publishes generated projects to Outline Wiki."""

    def __init__(
        self,
        client: OutlineClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize publisher.

        Args:
            client: Outline client (created if not provided)
            settings: Application settings
        """
        self._settings = settings or get_settings()
        self._client = client or OutlineClient(settings=self._settings)

    async def publish(
        self,
        project: GeneratedProject,
        enable_sharing: bool = False,
    ) -> PublishResult:
        """Publish a generated project to Outline.

        Creates a collection for the project and uploads all documents.

        Args:
            project: Generated project with documents
            enable_sharing: Enable public link sharing

        Returns:
            PublishResult with collection and document details
        """
        # Create collection for project
        collection = await self._client.create_collection(
            name=f"Project: {project.project_name}",
            description=f"Generated documentation for {project.project_name}. "
            f"{len(project.documents)} documents, {project.total_word_count:,} words.",
        )

        # Create documents in collection
        published_docs: list[OutlineDocument] = []
        for doc in project.documents:
            outline_doc = await self._client.create_document(
                title=doc.title,
                content=doc.content,
                collection_id=collection.id,
                publish=True,
            )
            published_docs.append(outline_doc)

        # Enable sharing if requested
        public_url = None
        if enable_sharing:
            public_url = await self._client.enable_sharing(collection.id)

        return PublishResult(
            collection=collection,
            documents=published_docs,
            public_url=public_url,
        )

    async def publish_document(
        self,
        document: Document,
        collection_id: str,
    ) -> OutlineDocument:
        """Publish a single document to an existing collection.

        Args:
            document: Document to publish
            collection_id: Target collection ID

        Returns:
            Published OutlineDocument
        """
        return await self._client.create_document(
            title=document.title,
            content=document.content,
            collection_id=collection_id,
            publish=True,
        )


# Convenience function for quick publishing
async def publish_to_outline(
    project: GeneratedProject,
    enable_sharing: bool = False,
    settings: Settings | None = None,
) -> PublishResult:
    """Publish a generated project to Outline Wiki.

    Args:
        project: Generated project with documents
        enable_sharing: Enable public sharing link
        settings: Optional settings

    Returns:
        PublishResult with URLs
    """
    publisher = OutlinePublisher(settings=settings)
    return await publisher.publish(project, enable_sharing=enable_sharing)
