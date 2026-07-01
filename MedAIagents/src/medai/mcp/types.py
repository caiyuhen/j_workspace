"""
MCP (Model Context Protocol) Pydantic 类型定义

定义了 MCP 协议中常用的数据模型，包括工具、资源、提示词、请求和响应等。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MCPTool(BaseModel):
    """MCP 工具定义"""

    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict, description="工具输入参数的 JSON Schema"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "search_patient",
                "description": "根据患者 ID 搜索患者信息",
                "input_schema": {
                    "type": "object",
                    "properties": {"patient_id": {"type": "string"}},
                    "required": ["patient_id"],
                },
            }
        }
    )


class MCPResource(BaseModel):
    """MCP 资源定义"""

    uri: str = Field(..., description="资源 URI")
    name: str = Field(..., description="资源名称")
    mime_type: Optional[str] = Field(default=None, description="资源的 MIME 类型")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uri": "file:///data/patients/12345.json",
                "name": "患者12345病历",
                "mime_type": "application/json",
            }
        }
    )


class MCPPromptArgument(BaseModel):
    """MCP 提示词参数定义"""

    name: str = Field(..., description="参数名称")
    description: Optional[str] = Field(default=None, description="参数描述")
    required: bool = Field(default=False, description="是否必填")


class MCPPrompt(BaseModel):
    """MCP 提示词定义"""

    name: str = Field(..., description="提示词名称")
    description: str = Field(..., description="提示词描述")
    arguments: Optional[List[MCPPromptArgument]] = Field(
        default=None, description="提示词参数列表"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "summarize_medical_record",
                "description": "总结病历信息",
                "arguments": [
                    {"name": "record_text", "description": "病历文本", "required": True}
                ],
            }
        }
    )


class MCPCallToolRequest(BaseModel):
    """调用 MCP 工具的请求"""

    name: str = Field(..., description="要调用的工具名称")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="工具调用参数"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "search_patient", "arguments": {"patient_id": "P12345"}}
        }
    )


class MCPCallToolResult(BaseModel):
    """调用 MCP 工具的结果"""

    content: List[Dict[str, Any]] = Field(
        default_factory=list, description="工具返回的内容列表"
    )
    is_error: bool = Field(default=False, description="是否发生错误")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": [{"type": "text", "text": "患者信息: ..."}],
                "is_error": False,
            }
        }
    )


class MCPClientInfo(BaseModel):
    """MCP 客户端信息"""

    name: str = Field(..., description="客户端名称")
    version: str = Field(..., description="客户端版本")


class MCPServerInfo(BaseModel):
    """MCP 服务器信息"""

    name: str = Field(..., description="服务器名称")
    version: str = Field(..., description="服务器版本")


class MCPCapabilities(BaseModel):
    """MCP 能力声明"""

    tools: Optional[Dict[str, Any]] = Field(default=None, description="工具支持")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="资源支持")
    prompts: Optional[Dict[str, Any]] = Field(default=None, description="提示词支持")


class MCPInitializeRequest(BaseModel):
    """MCP 初始化请求"""

    protocol_version: str = Field(
        default="2024-11-05", alias="protocolVersion", description="协议版本"
    )
    capabilities: MCPCapabilities = Field(
        default_factory=MCPCapabilities, description="客户端能力声明"
    )
    client_info: MCPClientInfo = Field(
        ..., alias="clientInfo", description="客户端信息"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "MedAIagents", "version": "1.0.0"},
            }
        },
    )


class MCPInitializeResult(BaseModel):
    """MCP 初始化响应"""

    protocol_version: str = Field(
        ..., alias="protocolVersion", description="协议版本"
    )
    capabilities: MCPCapabilities = Field(
        ..., description="服务器能力声明"
    )
    server_info: MCPServerInfo = Field(
        ..., alias="serverInfo", description="服务器信息"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "medical-server", "version": "0.1.0"},
            }
        },
    )
