"""
MedAIagents Web UI -"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request,"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.."""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-202"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
ic"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f""""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator ="""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge ="""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return json"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return jsonify({
            'success': False,
            'error': 'LLM 代理未"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return jsonify({
            'success': False,
            'error': 'LLM 代理未初始化，请先配置 API 密钥',
            'fallback': '系统已在无 L"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return jsonify({
            'success': False,
            'error': 'LLM 代理未初始化，请先配置 API 密钥',
            'fallback': '系统已在无 LLM 模式下运行。您可以使用知识库搜索、诊断辅助等功能。'
"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return jsonify({
            'success': False,
            'error': 'LLM 代理未初始化，请先配置 API 密钥',
            'fallback': '系统已在无 LLM 模式下运行。您可以使用知识库搜索、诊断辅助等功能。'
        })
    
    try:
        response = agent.chat(message, use_knowledge=use_knowledge)
        return jsonify({
"""
MedAIagents Web UI - 医学 AI 代理 Web 界面
使用 Flask + 现代前端设计
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, MedicalKnowledgeBase, ClinicalDecisionSupport
from medai.emr import EMRNoteGenerator, ICD10Coder


# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'medai-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# 全局代理实例
agent = None
kb = None
cdss = None
emr_generator = None
icd_coder = None


def init_agents():
    """初始化代理"""
    global agent, kb, cdss, emr_generator, icd_coder
    try:
        agent = MedicalAgent()
        logger.info("MedicalAgent 初始化成功")
    except Exception as e:
        logger.warning(f"MedicalAgent 初始化失败 (可能缺少 LLM API Key): {e}")
    
    kb = MedicalKnowledgeBase()
    cdss = ClinicalDecisionSupport()
    emr_generator = EMRNoteGenerator()
    icd_coder = ICD10Coder()


@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html', 
                         version='1.0.0',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/chat')
def chat():
    """聊天界面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    use_knowledge = data.get('use_knowledge', True)
    
    if not agent:
        return jsonify({
            'success': False,
            'error': 'LLM 代理未初始化，请先配置 API 密钥',
            'fallback': '系统已在无 LLM 模式下运行。您可以使用知识库搜索、诊断辅助等功能。'
        })
    
    try:
        response = agent.chat(message, use_knowledge=use_knowledge)
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as