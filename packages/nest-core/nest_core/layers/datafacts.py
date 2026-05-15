# SPDX-License-Identifier: Apache-2.0
"""DataFacts layer interface: dataset metadata, freshness, integrity, access.

Example::

    class MyDataFacts(DataFacts):
        async def publish(self, dataset):
            url = DataFactsUrl(f"df://{dataset.name}")
            self._store[url] = dataset
            return url
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AccessGrant, AgentId, DataFactsUrl, DatasetMetadata


@runtime_checkable
class DataFacts(Protocol):
    """Dataset metadata exchange protocol.

    Example::

        df: DataFacts = DataFactsV1()
        url = await df.publish(meta)
    """

    async def publish(self, dataset: DatasetMetadata) -> DataFactsUrl:
        """Publish dataset metadata and return its URL.

        Example::

            url = await df.publish(DatasetMetadata(name="weather", owner=AgentId("a1")))
        """
        ...

    async def fetch(self, url: DataFactsUrl) -> DatasetMetadata:
        """Fetch metadata for a published dataset.

        Example::

            meta = await df.fetch(DataFactsUrl("df://weather"))
        """
        ...

    async def request_access(self, url: DataFactsUrl, requester: AgentId) -> AccessGrant:
        """Request access to a dataset.

        Example::

            grant = await df.request_access(url, AgentId("a2"))
        """
        ...

    async def verify_freshness(self, url: DataFactsUrl) -> bool:
        """Check if a dataset's metadata is still fresh.

        Example::

            fresh = await df.verify_freshness(url)
        """
        ...
