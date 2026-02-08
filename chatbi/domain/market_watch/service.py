from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import xml.etree.ElementTree as ET

import httpx

from chatbi.domain.market_watch.repository import MarketWatchRepository


class MarketWatchService:
    def __init__(self, repo: MarketWatchRepository | None = None) -> None:
        self.repo = repo or MarketWatchRepository()

    def list_sources(self) -> list[dict[str, Any]]:
        return self.repo.load().get("sources", [])

    def update_sources(self, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        data = self.repo.load()
        data["sources"] = sources
        self.repo.save(data)
        return sources

    @staticmethod
    def _fallback_items() -> dict[str, list[dict[str, Any]]]:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "news": [
                {
                    "title": "多地银行优化消费贷利率定价机制",
                    "link": "",
                    "published_at": now,
                    "source": "Mock Market Feed",
                    "summary": "消费贷获客竞争加剧，利率与客群分层策略同步调整。",
                },
                {
                    "title": "经营贷投放向小微高成长行业倾斜",
                    "link": "",
                    "published_at": now,
                    "source": "Mock Market Feed",
                    "summary": "额度供给更偏向现金流稳定的小微商户。",
                },
            ],
            "policy": [
                {
                    "title": "监管继续强调贷款用途合规与穿透管理",
                    "link": "",
                    "published_at": now,
                    "source": "Mock Policy Feed",
                    "summary": "银行需加强资金流向监测，降低经营贷挪用风险。",
                }
            ],
            "product": [
                {
                    "title": "多家银行上线“经营贷+收单”联动产品",
                    "link": "",
                    "published_at": now,
                    "source": "Mock Product Feed",
                    "summary": "通过交易流水提升额度授信效率并强化风险控制。",
                }
            ],
        }

    @staticmethod
    def _parse_rss(xml_text: str, category: str, source_name: str, limit: int = 8) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        root = ET.fromstring(xml_text)
        for node in root.findall(".//item")[:limit]:
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            pub_date = (node.findtext("pubDate") or "").strip()
            desc = (node.findtext("description") or "").strip()
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published_at": pub_date,
                    "source": source_name,
                    "category": category,
                    "summary": desc[:300],
                }
            )
        return items

    def refresh_snapshot(self, limit: int = 8) -> dict[str, Any]:
        data = self.repo.load()
        sources = [s for s in data.get("sources", []) if s.get("enabled", True)]
        category_map: dict[str, list[dict[str, Any]]] = {"news": [], "policy": [], "product": []}
        fallback_urls = {
            "news": "https://www.bing.com/news/search?q=%E9%93%B6%E8%A1%8C+%E8%B4%B7%E6%AC%BE+%E6%96%B0%E9%97%BB&format=rss",
            "policy": "https://www.bing.com/news/search?q=%E8%B4%B7%E6%AC%BE+%E7%9B%91%E7%AE%A1+%E6%94%BF%E7%AD%96+%E9%93%B6%E8%A1%8C&format=rss",
            "product": "https://www.bing.com/news/search?q=%E9%93%B6%E8%A1%8C+%E4%BF%A1%E8%B4%B7+%E4%BA%A7%E5%93%81+%E5%88%9B%E6%96%B0&format=rss",
        }

        for src in sources:
            category = str(src.get("category") or "news")
            url = str(src.get("url") or "")
            if not url:
                continue
            try:
                resp = httpx.get(
                    url,
                    timeout=15,
                    follow_redirects=True,
                    headers={"User-Agent": "SmartBI-MarketWatch/1.0"},
                )
                resp.raise_for_status()
                parsed = self._parse_rss(resp.text, category=category, source_name=src.get("name", "unknown"), limit=limit)
                category_map.setdefault(category, []).extend(parsed)
            except Exception:
                continue

        # category fallback: if a configured source has no effective results,
        # use robust default search queries to keep page data non-empty.
        for cat, fallback_url in fallback_urls.items():
            if category_map.get(cat):
                continue
            try:
                resp = httpx.get(
                    fallback_url,
                    timeout=15,
                    follow_redirects=True,
                    headers={"User-Agent": "SmartBI-MarketWatch/1.0"},
                )
                resp.raise_for_status()
                parsed = self._parse_rss(
                    resp.text,
                    category=cat,
                    source_name=f"Fallback {cat}",
                    limit=limit,
                )
                category_map.setdefault(cat, []).extend(parsed)
            except Exception:
                continue

        # deduplicate by title+link and truncate
        for cat in ["news", "policy", "product"]:
            unique: list[dict[str, Any]] = []
            seen = set()
            for item in category_map.get(cat, []):
                k = f"{item.get('title')}|{item.get('link')}"
                if k in seen:
                    continue
                seen.add(k)
                unique.append(item)
            category_map[cat] = unique[:limit]

        if not any(category_map.values()):
            category_map = self._fallback_items()

        snapshot = {
            "fetched_at": datetime.utcnow().isoformat(),
            "items": category_map,
        }
        data["snapshot"] = snapshot
        self.repo.save(data)
        return snapshot

    def get_snapshot(self, limit: int = 8, force_refresh: bool = False) -> dict[str, Any]:
        data = self.repo.load()
        snap = data.get("snapshot", {})
        fetched_at = snap.get("fetched_at")
        stale = True
        if fetched_at:
            try:
                ts = datetime.fromisoformat(fetched_at)
                stale = datetime.utcnow() - ts > timedelta(minutes=45)
            except Exception:
                stale = True
        if force_refresh or stale or not snap.get("items"):
            snap = self.refresh_snapshot(limit=limit)
        # enforce limit
        items = snap.get("items", {})
        limited = {
            "news": (items.get("news") or [])[:limit],
            "policy": (items.get("policy") or [])[:limit],
            "product": (items.get("product") or [])[:limit],
        }
        return {
            "fetched_at": snap.get("fetched_at"),
            "items": limited,
        }

    @staticmethod
    def _keyword_count(rows: list[dict[str, Any]], keywords: list[str]) -> int:
        count = 0
        for r in rows:
            text = f"{r.get('title', '')} {r.get('summary', '')}".lower()
            if any(k.lower() in text for k in keywords):
                count += 1
        return count

    def market_analysis(self, limit: int = 8, force_refresh: bool = False) -> dict[str, Any]:
        snap = self.get_snapshot(limit=limit, force_refresh=force_refresh)
        news = snap["items"].get("news", [])
        policy = snap["items"].get("policy", [])
        product = snap["items"].get("product", [])
        all_items = news + policy + product

        risk_heat = self._keyword_count(all_items, ["逾期", "不良", "迁徙", "核销", "违规", "罚"])
        growth_heat = self._keyword_count(all_items, ["增长", "增额", "扩张", "上新", "优惠", "获客"])
        compliance_heat = self._keyword_count(all_items, ["监管", "政策", "通知", "办法", "规范", "合规"])

        if compliance_heat >= max(risk_heat, growth_heat):
            stance = "审慎经营窗口"
        elif growth_heat > risk_heat:
            stance = "增长机会窗口"
        else:
            stance = "风险收敛窗口"

        recommendations = [
            "消费贷：优先观察利率政策与客群准入变化，细化高风险客群限额与定价。",
            "经营贷：监控额度使用率与迁徙率联动，针对低动支高授信客群做激活策略。",
            "策略执行：先在MCP & Skills中形成策略草案并邮件审批，再执行外部触达。",
        ]

        return {
            "fetched_at": snap.get("fetched_at"),
            "market_pulse": {
                "risk_heat": risk_heat,
                "growth_heat": growth_heat,
                "compliance_heat": compliance_heat,
                "stance": stance,
            },
            "coverage": {
                "news_count": len(news),
                "policy_count": len(policy),
                "product_count": len(product),
            },
            "recommendations": recommendations,
        }
