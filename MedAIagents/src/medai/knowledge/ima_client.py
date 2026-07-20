"""
腾讯 IMA 知识库 OpenAPI 客户端
Tencent IMA Knowledge Base OpenAPI Client

接口文档参考: https://ima.qq.com/agent-interface
认证方式: ClientID + APIKey (Header)
Base URL: https://ima.qq.com
"""

import httpx
from typing import Dict, List, Any, Optional
from loguru import logger


class IMAClient:
    """IMA 知识库 OpenAPI 客户端"""
    
    BASE_URL = "https://ima.qq.com"
    
    def __init__(self, client_id: str = "", api_key: str = ""):
        self.client_id = client_id
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)
    
    def _headers(self) -> Dict[str, str]:
        return {
            "ima-openapi-clientid": self.client_id,
            "ima-openapi-apikey": self.api_key,
            "Content-Type": "application/json",
        }
    
    def is_configured(self) -> bool:
        return bool(self.client_id and self.api_key)
    
    async def _post(self, endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用 IMA POST 接口"""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            resp = await self._client.post(url, headers=self._headers(), json=body)
            data = resp.json()
            if data.get("code") != 0:
                return {
                    "success": False,
                    "error": f"IMA API error: code={data.get('code')}, msg={data.get('msg', 'unknown')}"
                }
            return {"success": True, "data": data.get("data", {})}
        except httpx.TimeoutException:
            return {"success": False, "error": "IMA API 请求超时（30秒）"}
        except Exception as e:
            logger.error(f"IMA API request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_knowledge_base(
        self,
        query: str = "",
        cursor: str = "",
        limit: int = 20
    ) -> Dict[str, Any]:
        """搜索/列出知识库
        
        Args:
            query: 搜索关键词，空字符串则列出所有
            cursor: 分页游标
            limit: 返回数量上限
        
        Returns:
            {success, knowledge_bases: [{kb_id, kb_name, description, content_count, member_count}]}
        """
        result = await self._post("openapi/wiki/v1/search_knowledge_base", {
            "query": query,
            "cursor": cursor,
            "limit": limit,
        })
        if not result["success"]:
            return result
        
        info_list = result["data"].get("info_list", [])
        knowledge_bases = []
        for kb in info_list:
            knowledge_bases.append({
                "kb_id": kb.get("kb_id", ""),
                "kb_name": kb.get("kb_name", ""),
                "description": kb.get("description", ""),
                "content_count": kb.get("content_count", 0),
                "member_count": kb.get("member_count", 0),
                "creator": kb.get("creator", ""),
                "base_type": kb.get("base_type", ""),
                "role_type": kb.get("role_type", ""),
            })
        return {
            "success": True,
            "knowledge_bases": knowledge_bases,
            "is_end": result["data"].get("is_end", True),
            "cursor": result["data"].get("cursor", ""),
        }
    
    async def get_knowledge_list(
        self,
        knowledge_base_id: str,
        folder_id: str = "",
        cursor: str = "",
        limit: int = 50
    ) -> Dict[str, Any]:
        """浏览知识库中的文件和文件夹列表
        
        Args:
            knowledge_base_id: 知识库ID
            folder_id: 文件夹ID，空字符串则列出根目录
            cursor: 分页游标
            limit: 返回数量上限
        """
        body = {
            "cursor": cursor,
            "limit": limit,
            "knowledge_base_id": knowledge_base_id,
        }
        if folder_id:
            body["folder_id"] = folder_id
        
        result = await self._post("openapi/wiki/v1/get_knowledge_list", body)
        if not result["success"]:
            return result
        
        type_map = {
            1: "PDF", 2: "网页", 3: "Word", 4: "PPT", 5: "Excel",
            6: "公众号文章", 7: "Markdown", 9: "图片", 11: "笔记", 99: "文件夹"
        }
        
        knowledge_list = result["data"].get("knowledge_list", [])
        items = []
        for item in knowledge_list:
            media_type = item.get("media_type", 0)
            items.append({
                "media_id": item.get("media_id", ""),
                "title": item.get("title", ""),
                "type": type_map.get(media_type, f"类型{media_type}"),
                "media_type": media_type,
                "tags": item.get("tags", []),
                "parent_folder_id": item.get("parent_folder_id", "根目录"),
            })
        
        current_path = result["data"].get("current_path", [])
        return {
            "success": True,
            "items": items,
            "current_path": [{"id": p.get("id", ""), "name": p.get("name", "")} for p in current_path],
            "is_end": result["data"].get("is_end", True),
            "cursor": result["data"].get("cursor", ""),
        }
    
    async def search_knowledge(
        self,
        query: str,
        knowledge_base_id: str
    ) -> Dict[str, Any]:
        """在指定知识库中搜索文件或文件夹
        
        Args:
            query: 搜索关键词
            knowledge_base_id: 目标知识库ID
        """
        result = await self._post("openapi/wiki/v1/search_knowledge", {
            "query": query,
            "knowledge_base_id": knowledge_base_id,
        })
        if not result["success"]:
            return result
        
        type_map = {
            1: "PDF", 2: "网页", 3: "Word", 4: "PPT", 5: "Excel",
            6: "公众号文章", 7: "Markdown", 9: "图片", 11: "笔记", 99: "文件夹"
        }
        
        info_list = result["data"].get("info_list", [])
        items = []
        for item in info_list:
            media_type = item.get("media_type", 0)
            items.append({
                "media_id": item.get("media_id", ""),
                "title": item.get("title", ""),
                "type": type_map.get(media_type, f"类型{media_type}"),
                "parent_folder_id": item.get("parent_folder_id", "根目录"),
            })
        
        return {"success": True, "items": items, "query": query}
    
    async def close(self):
        await self._client.aclose()
