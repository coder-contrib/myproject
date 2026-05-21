import logging
from dataclasses import dataclass, field
from typing import Optional
from string import Template

logger = logging.getLogger("ai.templates")


@dataclass
class PromptTemplate:
    name: str
    description: str
    system_template: str
    user_template: Optional[str] = None
    category: str = "general"
    version: int = 1
    variables: list[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        try:
            return self.system_template.format(**kwargs)
        except KeyError as e:
            logger.warning("Missing template variable %s in '%s'", e, self.name)
            return self.system_template

    def render_user(self, **kwargs) -> str:
        if not self.user_template:
            return ""
        try:
            return self.user_template.format(**kwargs)
        except KeyError:
            return self.user_template


class PromptTemplateRegistry:
    """Central registry for all AI prompt templates."""

    def __init__(self):
        self._templates: dict[str, PromptTemplate] = {}
        self._register_defaults()

    def register(self, template: PromptTemplate):
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise KeyError(f"Prompt template '{name}' not found")
        return self._templates[name]

    def list_templates(self, category: Optional[str] = None) -> list[dict]:
        templates = self._templates.values()
        if category:
            templates = [t for t in templates if t.category == category]
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "version": t.version,
                "variables": t.variables,
            }
            for t in templates
        ]

    def update(self, name: str, system_template: Optional[str] = None, user_template: Optional[str] = None):
        t = self.get(name)
        if system_template:
            t.system_template = system_template
            t.version += 1
        if user_template:
            t.user_template = user_template

    def _register_defaults(self):
        self.register(PromptTemplate(
            name="query_assistant",
            description="Natural language to SQL query generation",
            category="query",
            variables=["schema", "tenant_id", "context"],
            system_template=(
                "You are an expert SQL analyst for an ERP system. Convert natural language questions "
                "into safe, read-only PostgreSQL queries.\n\n"
                "Database schema:\n{schema}\n\n"
                "Rules:\n"
                "- ONLY generate SELECT statements\n"
                "- Always filter by tenant_id = '{tenant_id}'\n"
                "- Use appropriate JOINs, aggregations, and date functions\n"
                "- Limit results to 100 rows max\n"
                "- Return JSON with: sql (string or null), explanation (string), confidence (0-1), "
                "answer (string if no SQL needed)\n\n"
                "Additional context: {context}"
            ),
        ))

        self.register(PromptTemplate(
            name="analytics_trends",
            description="Time series trend analysis",
            category="analytics",
            variables=["metric", "period", "data"],
            system_template=(
                "You are a business analytics AI specialized in trend detection. "
                "Analyze the {metric} data over {period} and identify patterns.\n\n"
                "Return JSON with: trends, summary, insights, recommendations.\n\n"
                "Data: {data}"
            ),
        ))

        self.register(PromptTemplate(
            name="report_executive",
            description="Executive summary report generation",
            category="reports",
            variables=["period", "metrics"],
            system_template=(
                "You are a senior business analyst. Generate a professional executive summary.\n\n"
                "Period: {period}\n"
                "Metrics: {metrics}\n\n"
                "Return JSON with: title, highlights, concerns, kpis, narrative, recommendations."
            ),
        ))

        self.register(PromptTemplate(
            name="search_summary",
            description="Summarize semantic search results",
            category="search",
            variables=["query", "results"],
            system_template=(
                "You are a helpful search assistant for an ERP system. "
                "Summarize the most relevant findings from the search results.\n\n"
                "User query: {query}\n"
                "Results: {results}\n\n"
                "Provide a concise, actionable summary."
            ),
        ))

        self.register(PromptTemplate(
            name="anomaly_detection",
            description="Detect anomalies in business data",
            category="analytics",
            variables=["entity_type", "data"],
            system_template=(
                "You are an anomaly detection specialist for business data. "
                "Analyze {entity_type} data for unusual patterns or outliers.\n\n"
                "Data: {data}\n\n"
                "Return JSON with: anomalies (array with item, reason, severity), summary, risk_score."
            ),
        ))

        self.register(PromptTemplate(
            name="product_description",
            description="Generate product descriptions",
            category="content",
            variables=["product_name", "category", "features"],
            system_template=(
                "You are a product copywriter. Write a compelling, professional product description.\n\n"
                "Product: {product_name}\n"
                "Category: {category}\n"
                "Features: {features}\n\n"
                "Return a 2-3 sentence description suitable for an e-commerce catalog."
            ),
        ))

        self.register(PromptTemplate(
            name="customer_insight",
            description="Generate customer behavioral insights",
            category="analytics",
            variables=["customer_data", "purchase_history"],
            system_template=(
                "You are a customer analytics expert. Analyze the customer's behavior and provide insights.\n\n"
                "Customer data: {customer_data}\n"
                "Purchase history: {purchase_history}\n\n"
                "Return JSON with: segment, lifetime_value_estimate, churn_risk (low/medium/high), "
                "engagement_score (0-100), recommendations (array of strings)."
            ),
        ))

        self.register(PromptTemplate(
            name="inventory_optimization",
            description="Optimize inventory reorder suggestions",
            category="operations",
            variables=["stock_data", "sales_velocity"],
            system_template=(
                "You are a supply chain optimization AI. Analyze stock levels and sales velocity "
                "to recommend optimal reorder points.\n\n"
                "Current stock: {stock_data}\n"
                "Sales velocity: {sales_velocity}\n\n"
                "Return JSON with: reorder_items (array of {{product, current_qty, suggested_qty, urgency}}), "
                "total_investment_needed, summary."
            ),
        ))


prompt_registry = PromptTemplateRegistry()
