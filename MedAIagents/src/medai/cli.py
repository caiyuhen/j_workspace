"""
命令行接口
Command Line Interface for MedAIagents
"""

import click
import sys
from typing import Optional
from loguru import logger

from . import __version__
from .agent import MedicalAgent
from .config import Config


# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


@click.group()
@click.version_option(version=__version__, prog_name="medai")
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--debug', '-d', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, config: Optional[str], debug: bool):
    """
    MedAIagents - 医学专用版AI代理框架
    
    面向医疗临床、科研、电子病历的专业AI助手
    """
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['debug'] = debug
    
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.debug("调试模式已启用")


@cli.command()
@click.option('--model', '-m', default='openai', help='LLM提供商 (openai/anthropic/deepseek)')
@click.option('--no-knowledge', is_flag=True, help='不使用医学知识库')
@click.pass_context
def chat(ctx, model: str, no_knowledge: bool):
    """
    与医学AI助手对话
    
    交互式聊天模式，可以问任何医学相关问题。
    """
    click.echo(click.style(f"🚀 MedAIagents v{__version__}", fg='blue', bold=True))
    click.echo(click.style("=" * 50, fg='blue'))
    click.echo("医学AI助手已启动，输入 'quit' 或 'exit' 退出")
    click.echo("=" * 50)
    
    try:
        agent = MedicalAgent(config_path=ctx.obj.get('config_path'))
        
        # 切换模型
        if model != 'openai':
            try:
                agent.switch_model(model)
                click.echo(f"✓ 已切换到 {model} 模型")
            except Exception as e:
                click.echo(click.style(f"✗ 切换模型失败: {e}", fg='red'))
        
        click.echo()
        
        while True:
            user_input = click.prompt(click.style("您", fg='green'), prompt_suffix=": ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                click.echo(click.style("再见！感谢使用 MedAIagents", fg='blue'))
                break
            
            if not user_input.strip():
                continue
            
            # 处理命令
            if user_input.startswith('/'):
                _handle_command(user_input, agent)
                continue
            
            # 正常对话
            with click.progressbar(length=1, label='思考中...', show_eta=False) as bar:
                response = agent.chat(user_input, use_knowledge=not no_knowledge)
                bar.update(1)
            
            click.echo()
            click.echo(click.style("MedAI: ", fg='blue') + response)
            click.echo()
            
    except Exception as e:
        click.echo(click.style(f"错误: {e}", fg='red'))
        if ctx.obj.get('debug'):
            import traceback
            click.echo(traceback.format_exc())


def _handle_command(command: str, agent: MedicalAgent):
    """处理特殊命令"""
    parts = command[1:].split()
    cmd = parts[0].lower() if parts else ''
    
    if cmd in ['help', 'h']:
        click.echo(click.style("\n可用命令:", fg='cyan', bold=True))
        click.echo("  /help, /h      - 显示帮助信息")
        click.echo("  /stats, /s     - 显示统计信息")
        click.echo("  /history, /hi  - 显示对话历史")
        click.echo("  /sessions, /se - 列出所有会话")
        click.echo("  /diagnose, /d  - 诊断辅助模式")
        click.echo("  /medcheck, /mc - 用药安全检查")
        click.echo("  /search, /se   - 搜索医学知识库")
        click.echo("  /clear, /c     - 清空当前会话")
        click.echo()
    
    elif cmd in ['stats', 's']:
        stats = agent.get_statistics()
        click.echo(click.style("\n统计信息:", fg='cyan', bold=True))
        click.echo(f"  版本: {stats['version']}")
        click.echo(f"  当前会话: {stats['current_session_id']}")
        click.echo(f"  会话消息数: {stats['messages_in_session']}")
        click.echo(f"  总会话数: {stats['total_sessions']}")
        click.echo()
    
    elif cmd in ['history', 'hi']:
        history = agent.get_conversation_history()
        click.echo(click.style("\n对话历史:", fg='cyan', bold=True))
        for i, msg in enumerate(history, 1):
            role = '您' if msg['role'] == 'user' else 'MedAI'
            color = 'green' if msg['role'] == 'user' else 'blue'
            click.echo(f"\n{click.style(role, fg=color)}: {msg['content'][:100]}...")
        click.echo()
    
    elif cmd in ['diagnose', 'd']:
        click.echo(click.style("\n诊断辅助模式", fg='cyan', bold=True))
        symptoms_str = click.prompt("请输入症状（用逗号分隔）")
        symptoms = [s.strip() for s in symptoms_str.split(',') if s.strip()]
        
        lab_results = {}
        if click.confirm("是否有检查结果？"):
            lab_input = click.prompt("请输入检查结果（格式：项目=值，多个用逗号分隔）")
            for item in lab_input.split(','):
                if '=' in item:
                    k, v = item.split('=', 1)
                    lab_results[k.strip()] = v.strip()
        
        with click.progressbar(length=1, label='分析中...', show_eta=False) as bar:
            result = agent.diagnose(symptoms, lab_results)
            bar.update(1)
        
        click.echo("\n" + click.style("诊断结果:", fg='yellow', bold=True))
        if result.get('primary_diagnosis'):
            diag = result['primary_diagnosis']
            click.echo(f"  主要诊断: {diag.get('disease', '未知')}")
            click.echo(f"  ICD-10: {diag.get('icd10', '未知')}")
        
        if result.get('recommended_tests'):
            click.echo("\n" + click.style("建议检查:", fg='yellow', bold=True))
            for test in result['recommended_tests']:
                click.echo(f"  - {test}")
        click.echo()
    
    elif cmd in ['medcheck', 'mc']:
        click.echo(click.style("\n用药安全检查", fg='cyan', bold=True))
        meds_str = click.prompt("请输入药物名称（用逗号分隔）")
        medications = [m.strip() for m in meds_str.split(',') if m.strip()]
        
        allergies = []
        if click.confirm("是否有药物过敏史？"):
            allergy_str = click.prompt("请输入过敏药物")
            allergies = [a.strip() for a in allergy_str.split(',') if a.strip()]
        
        with click.progressbar(length=1, label='检查中...', show_eta=False) as bar:
            result = agent.check_medication_safety(medications, allergies)
            bar.update(1)
        
        click.echo("\n" + click.style("检查结果:", fg='yellow', bold=True))
        click.echo(f"  安全状态: {'✓ 安全' if result.get('is_safe') else '✗ 存在风险'}")
        
        if result.get('warnings'):
            click.echo("\n" + click.style("警告:", fg='red', bold=True))
            for warning in result['warnings']:
                click.echo(f"  - {warning.get('description', '未知警告')}")
        
        if result.get('recommendations'):
            click.echo("\n" + click.style("建议:", fg='yellow', bold=True))
            for rec in result['recommendations']:
                click.echo(f"  - {rec}")
        click.echo()
    
    elif cmd in ['search', 's']:
        query = click.prompt("请输入搜索关键词")
        use_pubmed = click.confirm("是否搜索PubMed文献？")
        
        with click.progressbar(length=1, label='搜索中...', show_eta=False) as bar:
            results = agent.search_knowledge(query, limit=5, use_pubmed=use_pubmed)
            bar.update(1)
        
        click.echo("\n" + click.style("搜索结果:", fg='yellow', bold=True))
        if not results:
            click.echo("  未找到相关结果")
        else:
            for i, item in enumerate(results, 1):
                title = item.get('title', f'结果 {i}')
                content = item.get('content', '')[:200]
                source = item.get('source', '未知')
                click.echo(f"\n{i}. {click.style(title, fg='cyan')}")
                click.echo(f"   来源: {source}")
                click.echo(f"   {content}...")
        click.echo()
    
    else:
        click.echo(click.style(f"未知命令: {cmd}", fg='red'))
        click.echo("输入 /help 查看可用命令")


@cli.command()
@click.argument('note_type', type=click.Choice(['admission', 'progress', 'discharge']))
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.pass_context
def note(ctx, note_type: str, output: Optional[str]):
    """
    生成医学文书
    
    支持的文书类型: admission (入院记录), progress (病程记录), discharge (出院记录)
    """
    click.echo(click.style(f"📝 生成{note_type}文书", fg='blue', bold=True))
    
    try:
        agent = MedicalAgent(config_path=ctx.obj.get('config_path'))
        
        # 收集患者信息
        patient_info = {
            'name': click.prompt("患者姓名", default='患者'),
            'gender': click.prompt("性别", default='男'),
            'age': click.prompt("年龄", type=int, default=0),
        }
        
        # 收集临床数据
        clinical_data = {}
        
        if note_type == 'admission':
            clinical_data['chief_complaint'] = click.prompt("主诉")
            clinical_data['diagnosis'] = click.prompt("初步诊断")
        
        elif note_type == 'progress':
            clinical_data['subjective'] = click.prompt("主诉/病情变化")
            clinical_data['temperature'] = click.prompt("体温 (℃)", type=float, default=36.5)
            clinical_data['pulse'] = click.prompt("脉搏 (次/分)", type=int, default=72)
            clinical_data['respiration'] = click.prompt("呼吸 (次/分)", type=int, default=18)
            clinical_data['blood_pressure'] = click.prompt("血压 (mmHg)", default='120/80')
        
        elif note_type == 'discharge':
            clinical_data['admission_diagnosis'] = click.prompt("入院诊断")
            clinical_data['discharge_diagnosis'] = click.prompt("出院诊断")
            clinical_data['discharge_orders'] = click.prompt("出院医嘱")
        
        with click.progressbar(length=1, label='生成中...', show_eta=False) as bar:
            note_content = agent.generate_medical_note(note_type, patient_info, clinical_data)
            bar.update(1)
        
        click.echo("\n" + click.style("生成的文书:", fg='cyan', bold=True))
        click.echo("=" * 60)
        click.echo(note_content)
        click.echo("=" * 60)
        
        if output or click.confirm("是否保存到文件？"):
            if not output:
                output = f"{note_type}_note.txt"
            with open(output, 'w', encoding='utf-8') as f:
                f.write(note_content)
            click.echo(f"✓ 已保存到: {output}")
        
    except Exception as e:
        click.echo(click.style(f"错误: {e}", fg='red'))
        if ctx.obj.get('debug'):
            import traceback
            click.echo(traceback.format_exc())


@cli.command()
@click.argument('diagnosis')
@click.pass_context
def icd10(ctx, diagnosis: str):
    """
    查询ICD-10编码
    
    根据诊断名称查找对应的ICD-10编码
    """
    click.echo(click.style(f"🔍 查询ICD-10编码: {diagnosis}", fg='blue', bold=True))
    
    try:
        agent = MedicalAgent(config_path=ctx.obj.get('config_path'))
        result = agent.get_icd10_code(diagnosis)
        
        if result['found']:
            click.echo(f"\n{click.style('找到编码:', fg='green', bold=True)}")
            click.echo(f"  诊断: {result['diagnosis']}")
            click.echo(f"  ICD-10: {click.style(result['icd10_code'], fg='cyan', bold=True)}")
        else:
            click.echo(f"\n{click.style('未找到精确匹配', fg='yellow')}")
            if result.get('suggestions'):
                click.echo("可能的相关编码:")
                for sug in result['suggestions'][:5]:
                    click.echo(f"  - {sug.get('diagnosis', '')}: {sug.get('icd10_code', '')}")
        
    except Exception as e:
        click.echo(click.style(f"错误: {e}", fg='red'))


@cli.command()
@click.option('--limit', '-n', default=10, help='显示日志数量')
@click.option('--output', '-o', type=click.Path(), help='导出到文件')
@click.pass_context
def audit(ctx, limit: int, output: Optional[str]):
    """
    查看审计日志
    """
    click.echo(click.style(f"📋 审计日志 (最近 {limit} 条)", fg='blue', bold=True))
    
    try:
        agent = MedicalAgent(config_path=ctx.obj.get('config_path'))
        logs = agent.get_audit_logs(limit=limit)
        
        if not logs:
            click.echo("暂无审计日志")
            return
        
        for log in logs:
            timestamp = log.get('timestamp', '')[:19]
            action = log.get('action', '未知')
            username = log.get('username', '未知')
            success = '✓' if log.get('success') else '✗'
            
            click.echo(f"[{timestamp}] {success} {username} - {action}")
        
        if output or click.confirm("是否导出日志？"):
            import json
            if not output:
                output = 'audit_logs.json'
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            click.echo(f"✓ 已导出到: {output}")
        
    except Exception as e:
        click.echo(click.style(f"错误: {e}", fg='red'))


@cli.command()
@click.option('--port', '-p', type=int, default=8228, help='服务端口 (默认: 8228)')
@click.option('--host', '-h', type=str, default='127.0.0.1', help='绑定地址 (默认: 127.0.0.1)')
@click.option('--headless', is_flag=True, help='无头模式 (仅启动后端服务)')
def server(port: int, host: str, headless: bool):
    """
    启动 Web 服务
    
    启动 MedAIagents 的 Web 服务，支持桌面应用或仅后端 API 服务。
    """
    if headless:
        click.echo(click.style(f"\n🚀 MedAIagents v{__version__}", fg='blue', bold=True))
        click.echo(click.style("=" * 50, fg='blue'))
        click.echo(f"\n🌐 后端服务地址: http://{host}:{port}")
        click.echo(f"📖 API 文档地址: http://{host}:{port}/docs")
        click.echo("\n按 Ctrl+C 停止服务\n")
        
        try:
            import uvicorn
            from medai.desktop.server import app
            
            uvicorn.run(app, host=host, port=port, log_level="info")
        except KeyboardInterrupt:
            click.echo("\n👋 服务已停止")
        except Exception as e:
            click.echo(click.style(f"❌ 启动失败: {e}", fg='red'))
    else:
        # 桌面应用模式
        try:
            from medai.desktop.app import run_desktop_app
            run_desktop_app()
        except Exception as e:
            click.echo(click.style(f"❌ 启动失败: {e}", fg='red'))


@cli.command()
def info():
    """显示系统信息"""
    click.echo(click.style(f"\n🚀 MedAIagents v{__version__}", fg='blue', bold=True))
    click.echo(click.style("=" * 50, fg='blue'))
    click.echo()
    click.echo("核心功能模块:")
    click.echo("  ✓ 临床决策支持 (CDSS)")
    click.echo("  ✓ 医学知识库检索")
    click.echo("  ✓ 电子病历 (EMR) 自动化")
    click.echo("  ✓ 用药安全检查")
    click.echo("  ✓ 多模型 LLM 路由")
    click.echo("  ✓ 会话记忆系统")
    click.echo("  ✓ 安全与合规 (HIPAA/RBAC)")
    click.echo("  ✓ 桌面应用支持")
    click.echo()
    click.echo("支持的LLM提供商:")
    click.echo("  ✓ OpenAI (GPT-4, GPT-3.5)")
    click.echo("  ✓ Anthropic (Claude)")
    click.echo("  ✓ DeepSeek")
    click.echo()
    click.echo("使用方式:")
    click.echo("  medai chat      - 命令行对话")
    click.echo("  medai-desktop   - 桌面应用")
    click.echo("  medai server    - Web 服务")
    click.echo()
    click.echo("官方文档: https://docs.medaiagents.com")
    click.echo()


if __name__ == '__main__':
    cli()
