import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embedding_service
from app.ai.client import ai_client

logger = logging.getLogger("ai.search")


class SemanticSearch:
    """Semantic search across all indexed entities using pgvector."""

    async def search(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        entity_types: Optional[list[str]] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> dict:
        results = []

        if entity_types:
            for entity_type in entity_types:
                matches = await embedding_service.search_similar(
                    db=db,
                    tenant_id=tenant_id,
                    query=query,
                    entity_type=entity_type,
                    limit=limit,
                    threshold=threshold,
                )
                results.extend(matches)
        else:
            results = await embedding_service.search_similar(
                db=db,
                tenant_id=tenant_id,
                query=query,
                limit=limit,
                threshold=threshold,
            )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        return {
            "query": query,
            "results": results,
            "total": len(results),
        }

    async def search_with_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        entity_types: Optional[list[str]] = None,
        limit: int = 10,
    ) -> dict:
        search_results = await self.search(
            db=db,
            tenant_id=tenant_id,
            query=query,
            entity_types=entity_types,
            limit=limit,
        )

        if not search_results["results"]:
            return {
                **search_results,
                "summary": "No relevant results found.",
            }

        context = "\n".join(
            f"- [{r['entity_type']}:{r['entity_id']}] {r['content'][:200]}"
            for r in search_results["results"][:5]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful search assistant. Summarize the search results "
                    "in relation to the user's query. Be concise and actionable."
                ),
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\nResults:\n{context}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, max_tokens=300)
        summary = ai_client.extract_content(response)

        return {
            **search_results,
            "summary": summary,
        }

    async def index_product(
        self,
        db: AsyncSession,
        tenant_id: str,
        product: dict,
    ):
        content = (
            f"Product: {product['name']}. SKU: {product.get('sku', 'N/A')}. "
            f"Category: {product.get('category', 'N/A')}. "
            f"Price: {product.get('price', 'N/A')}. "
            f"Description: {product.get('description', 'No description')}"
        )
        await embedding_service.upsert_embedding(
            db=db,
            tenant_id=tenant_id,
            entity_type="product",
            entity_id=str(product["id"]),
            content=content,
            metadata={"name": product["name"], "sku": product.get("sku")},
        )

    async def index_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer: dict,
    ):
        content = (
            f"Customer: {customer['name']}. Email: {customer.get('email', 'N/A')}. "
            f"Phone: {customer.get('phone', 'N/A')}. Type: {customer.get('type', 'N/A')}. "
            f"Notes: {customer.get('notes', 'None')}"
        )
        await embedding_service.upsert_embedding(
            db=db,
            tenant_id=tenant_id,
            entity_type="customer",
            entity_id=str(customer["id"]),
            content=content,
            metadata={"name": customer["name"], "email": customer.get("email")},
        )

    async def index_invoice(
        self,
        db: AsyncSession,
        tenant_id: str,
        invoice: dict,
    ):
        items_text = ", ".join(
            f"{item['product_name']} x{item['quantity']}"
            for item in invoice.get("items", [])
        )
        content = (
            f"Invoice {invoice['invoice_number']}. Customer: {invoice.get('customer_name', 'N/A')}. "
            f"Total: {invoice.get('total', 0)}. Date: {invoice.get('date', 'N/A')}. "
            f"Items: {items_text or 'N/A'}"
        )
        await embedding_service.upsert_embedding(
            db=db,
            tenant_id=tenant_id,
            entity_type="invoice",
            entity_id=str(invoice["id"]),
            content=content,
            metadata={"invoice_number": invoice["invoice_number"], "total": str(invoice.get("total"))},
        )

    async def reindex_all(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        items: list[dict],
        batch_size: int = 50,
    ) -> int:
        total = 0
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            prepared = []
            for item in batch:
                if entity_type == "product":
                    content = f"Product: {item['name']}. SKU: {item.get('sku', '')}. Category: {item.get('category', '')}."
                elif entity_type == "customer":
                    content = f"Customer: {item['name']}. Email: {item.get('email', '')}. Type: {item.get('type', '')}."
                else:
                    content = str(item)
                prepared.append({"entity_id": str(item["id"]), "content": content, "metadata": item})

            count = await embedding_service.bulk_upsert(db, tenant_id, entity_type, prepared)
            total += count

        return total
