"""
LLM 工具调用测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from medai.llm.routing import OpenAIProvider, LLMRouter
from medai.llm.tool_parser import ToolCallParser


@pytest.fixture
def openai_provider():
    config = {
        'api_key': 'test-key',
        'base_url': 'https://api.openai.com/v1',
        'default_model': 'gpt-4',
    }
    provider = OpenAIProvider(config)
    provider.client = MagicMock()
    return provider


@pytest.fixture
def mock_tool_response():
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = None
    func_mock = MagicMock()
    func_mock.name = 'get_weather'
    func_mock.arguments = '{"location":"Beijing"}'
    response.choices[0].message.tool_calls = [
        MagicMock(
            id='call_123',
            type='function',
            function=func_mock
        )
    ]
    return response


@pytest.mark.asyncio
async def test_openai_chat_completion_passes_tools(openai_provider, mock_tool_response):
    """测试 tools 参数被正确传递给 OpenAI API"""
    openai_provider.client.chat.completions.create = AsyncMock(return_value=mock_tool_response)

    messages = [{'role': 'user', 'content': 'What is the weather?'}]
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'get_weather',
                'description': 'Get weather info',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {'type': 'string'}
                    }
                }
            }
        }
    ]

    result = await openai_provider.chat_completion(messages, tools=tools, tool_choice='auto')

    openai_provider.client.chat.completions.create.assert_awaited_once()
    call_kwargs = openai_provider.client.chat.completions.create.call_args.kwargs
    assert call_kwargs['tools'] == tools
    assert call_kwargs['tool_choice'] == 'auto'
    assert result == mock_tool_response


@pytest.mark.asyncio
async def test_openai_chat_completion_without_tools(openai_provider):
    """测试不带 tools 时正常返回字符串内容"""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = 'Hello, world!'
    openai_provider.client.chat.completions.create = AsyncMock(return_value=response)

    messages = [{'role': 'user', 'content': 'Hi'}]
    result = await openai_provider.chat_completion(messages)

    assert result == 'Hello, world!'
    call_kwargs = openai_provider.client.chat.completions.create.call_args.kwargs
    assert 'tools' not in call_kwargs
    assert 'tool_choice' not in call_kwargs


def test_parse_tool_calls(openai_provider, mock_tool_response):
    """测试从响应中解析 tool_calls"""
    tool_calls = openai_provider.parse_tool_calls(mock_tool_response)
    assert len(tool_calls) == 1
    assert tool_calls[0]['id'] == 'call_123'
    assert tool_calls[0]['type'] == 'function'
    assert tool_calls[0]['function']['name'] == 'get_weather'
    assert tool_calls[0]['function']['arguments'] == '{"location":"Beijing"}'


def test_parse_tool_calls_empty(openai_provider):
    """测试无 tool_calls 时返回空列表"""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.tool_calls = None
    assert openai_provider.parse_tool_calls(response) == []


def test_parse_tool_calls_no_choices(openai_provider):
    """测试 choices 为空时返回空列表"""
    response = MagicMock()
    response.choices = []
    assert openai_provider.parse_tool_calls(response) == []


def test_tool_call_parser_normalize_dict():
    """测试 normalize_tool_call 处理字典"""
    tc = {
        'id': 'call_1',
        'type': 'function',
        'function': {
            'name': 'foo',
            'arguments': '{"a":1}'
        }
    }
    normalized = ToolCallParser.normalize_tool_call(tc)
    assert normalized['id'] == 'call_1'
    assert normalized['type'] == 'function'
    assert normalized['function']['name'] == 'foo'
    assert normalized['function']['arguments'] == '{"a":1}'


def test_tool_call_parser_normalize_object():
    """测试 normalize_tool_call 处理对象"""
    tc = MagicMock()
    tc.id = 'call_2'
    tc.type = 'function'
    tc.function = MagicMock()
    tc.function.name = 'bar'
    tc.function.arguments = '{"b":2}'

    normalized = ToolCallParser.normalize_tool_call(tc)
    assert normalized['id'] == 'call_2'
    assert normalized['type'] == 'function'
    assert normalized['function']['name'] == 'bar'
    assert normalized['function']['arguments'] == '{"b":2}'


@pytest.mark.asyncio
async def test_llm_router_chat_with_tools():
    """测试 LLMRouter.chat_with_tools 方法"""
    router = LLMRouter.__new__(LLMRouter)
    router.config = MagicMock()
    router.config.get = MagicMock(return_value='openai')
    router._providers = {}

    mock_provider = MagicMock(spec=OpenAIProvider)
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = 'Using tool'
    mock_response.choices[0].message.tool_calls = [
        MagicMock(
            id='call_1',
            type='function',
            function=MagicMock(name='search', arguments='{"q":"test"}')
        )
    ]
    mock_provider.chat_completion = AsyncMock(return_value=mock_response)
    mock_provider.parse_tool_calls = MagicMock(return_value=[
        {'id': 'call_1', 'type': 'function', 'function': {'name': 'search', 'arguments': '{"q":"test"}'}}
    ])

    router._providers['openai'] = mock_provider

    messages = [{'role': 'user', 'content': 'Search something'}]
    tools = [{'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}]

    content, tool_calls = await router.chat_with_tools(messages, tools)
    assert content == 'Using tool'
    assert len(tool_calls) == 1
    assert tool_calls[0]['function']['name'] == 'search'
