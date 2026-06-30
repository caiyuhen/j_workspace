"""
安全与合规模块
Security & Compliance Module
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from loguru import logger

from ..config import Config


class DataEncryptor:
    """数据加密器"""
    
    def __init__(self, key_file: str = None, password: str = None):
        """初始化加密器
        
        Args:
            key_file: 密钥文件路径
            password: 密码（用于生成密钥）
        """
        self.key_file = key_file or './data/encryption_key'
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        # 加载或生成密钥
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            if password:
                # 从密码生成密钥
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=480000,
                )
                self.key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            else:
                # 生成新密钥
                self.key = Fernet.generate_key()
            
            # 保存密钥
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        if not data:
            return data
        encrypted = self.cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def encrypt_dict(self, data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
        """加密字典中的指定字段"""
        result = data.copy()
        if fields:
            for field in fields:
                if field in result and isinstance(result[field], str):
                    result[field] = self.encrypt(result[field])
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
        """解密字典中的指定字段"""
        result = data.copy()
        if fields:
            for field in fields:
                if field in result and isinstance(result[field], str):
                    result[field] = self.decrypt(result[field])
        return result


class DataDeidentifier:
    """数据去标识化处理器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # 需要移除的敏感字段
        self.sensitive_fields = [
            'name', 'patient_name', 'full_name',
            'id_card', 'id_number', 'identity',
            'phone', 'telephone', 'mobile',
            'email', 'email_address',
            'address', 'home_address', 'residence',
            'birth_date', 'date_of_birth',
            'hospital_number', 'medical_record_number'
        ]
        
        # 字段匿名化映射
        self.anonymization_map = {
            'name': '患者',
            'gender': '性别',
            'age': '年龄',
            'diagnosis': '诊断'
        }
    
    def deidentify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """对数据进行去标识化处理"""
        result = data.copy()
        
        # 移除敏感字段
        for field in self.sensitive_fields:
            if field in result:
                del result[field]
        
        # 对保留字段进行匿名化处理
        for field, alias in self.anonymization_map.items():
            if field in result:
                result[field] = self._anonymize_field(field, result[field])
        
        return result
    
    def _anonymize_field(self, field: str, value: Any) -> Any:
        """匿名化单个字段"""
        if field == 'age' and isinstance(value, (int, str)):
            # 年龄按年龄段分组
            try:
                age = int(value)
                if age < 18:
                    return '<18岁'
                elif age < 30:
                    return '18-29岁'
                elif age < 40:
                    return '30-39岁'
                elif age < 50:
                    return '40-49岁'
                elif age < 60:
                    return '50-59岁'
                elif age < 70:
                    return '60-69岁'
                else:
                    return '≥70岁'
            except:
                return value
        
        return value
    
    def batch_deidentify(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量去标识化"""
        return [self.deidentify(record) for record in records]


class RBACManager:
    """基于角色的访问控制管理器"""
    
    def __init__(self, db_path: str = './data/rbac.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self._init_tables()
        
        # 预定义角色及其权限
        self.role_permissions = {
            'admin': {
                'permissions': ['*'],
                'description': '系统管理员'
            },
            'doctor': {
                'permissions': [
                    'patient.read', 'patient.write',
                    'emr.read', 'emr.write',
                    'order.create', 'order.read',
                    'diagnosis.create', 'diagnosis.read',
                    'knowledge.read'
                ],
                'description': '临床医生'
            },
            'researcher': {
                'permissions': [
                    'patient.read.deidentified',
                    'emr.read.deidentified',
                    'research.create',
                    'statistics.read',
                    'knowledge.read'
                ],
                'description': '科研人员'
            },
            'viewer': {
                'permissions': [
                    'patient.read.basic',
                    'knowledge.read'
                ],
                'description': '查看者'
            }
        }
    
    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                created_at TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # 角色权限表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role TEXT PRIMARY KEY,
                permissions TEXT,
                description TEXT
            )
        ''')
        
        # 审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                user_id TEXT,
                action TEXT,
                resource TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                success BOOLEAN
            )
        ''')
        
        self.conn.commit()
        
        # 初始化角色权限
        self._init_role_permissions()
    
    def _init_role_permissions(self):
        """初始化角色权限"""
        cursor = self.conn.cursor()
        
        for role, data in self.role_permissions.items():
            cursor.execute(
                '''INSERT OR REPLACE INTO role_permissions 
                   (role, permissions, description) VALUES (?, ?, ?)''',
                (role, json.dumps(data['permissions']), data['description'])
            )
        
        self.conn.commit()
    
    def add_user(self, user_id: str, username: str, role: str, department: str = None) -> bool:
        """添加用户"""
        if role not in self.role_permissions:
            logger.warning(f"Invalid role: {role}")
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''INSERT INTO users (user_id, username, role, department, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, username, role, department, datetime.now().isoformat())
            )
            self.conn.commit()
            logger.info(f"Added user: {username} with role: {role}")
            return True
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return False
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """获取用户角色"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有权限"""
        role = self.get_user_role(user_id)
        if not role:
            return False
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT permissions FROM role_permissions WHERE role = ?', (role,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        permissions = json.loads(result[0])
        
        # 通配符权限
        if '*' in permissions:
            return True
        
        # 精确匹配
        if permission in permissions:
            return True
        
        # 通配符前缀匹配（如 'patient.*'）
        for perm in permissions:
            if perm.endswith('.*'):
                prefix = perm[:-2]
                if permission.startswith(prefix):
                    return True
        
        return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, role, department, created_at FROM users')
        rows = cursor.fetchall()
        
        return [
            {
                'user_id': row[0],
                'username': row[1],
                'role': row[2],
                'department': row[3],
                'created_at': row[4]
            }
            for row in rows
        ]
    
    def get_role_permissions(self, role: str) -> Dict[str, Any]:
        """获取角色权限"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT permissions, description FROM role_permissions WHERE role = ?', (role,))
        result = cursor.fetchone()
        
        if result:
            return {
                'role': role,
                'permissions': json.loads(result[0]),
                'description': result[1]
            }
        return None


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, db_path: str = './data/audit.db', max_retention_days: int = 365):
        self.db_path = db_path
        self.max_retention_days = max_retention_days
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()
    
    def _init_table(self):
        """初始化日志表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                user_id TEXT,
                username TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action ON audit_logs(action)')
        
        self.conn.commit()
    
    def log(
        self,
        user_id: str,
        username: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True
    ):
        """记录审计日志"""
        cursor = self.conn.cursor()
        
        cursor.execute(
            '''INSERT INTO audit_logs 
               (timestamp, user_id, username, action, resource_type, resource_id, 
                details, ip_address, user_agent, success)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                datetime.now().isoformat(),
                user_id,
                username,
                action,
                resource_type,
                resource_id,
                json.dumps(details) if details else None,
                ip_address,
                user_agent,
                success
            )
        )
        
        self.conn.commit()
        logger.debug(f"Audit log: {username} - {action} - {'Success' if success else 'Failed'}")
    
    def query_logs(
        self,
        user_id: str = None,
        action: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询审计日志"""
        query = 'SELECT * FROM audit_logs WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action:
            query += ' AND action = ?'
            params.append(action)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = ['id', 'timestamp', 'user_id', 'username', 'action', 
                   'resource_type', 'resource_id', 'details', 
                   'ip_address', 'user_agent', 'success']
        
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            if record['details']:
                record['details'] = json.loads(record['details'])
            results.append(record)
        
        return results
    
    def cleanup_old_logs(self):
        """清理过期日志"""
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=self.max_retention_days)).isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM audit_logs WHERE timestamp < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")


class HIPAAComplianceChecker:
    """HIPAA合规性检查器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # HIPAA识别的PHI（受保护健康信息）字段
        self.phi_fields = [
            'name', 'patient_name',
            'address', 'geography',
            'dates', 'dates_relating_to_individual',
            'phone_number',
            'fax_number',
            'email_address',
            'social_security_number',
            'medical_record_number',
            'health_plan_beneficiary_number',
            'account_number',
            'certificate_license_number',
            'vehicle_identifiers',
            'device_identifiers',
            'web_urls',
            'ip_addresses',
            'biometric_identifiers',
            'full_face_photos',
            'any_unique_identifying_number'
        ]
    
    def check_phi_presence(self, data: Dict[str, Any]) -> List[str]:
        """检查数据中是否存在PHI字段"""
        found_phi = []
        for key in data.keys():
            key_lower = key.lower()
            for phi_field in self.phi_fields:
                if phi_field in key_lower or key_lower in phi_field:
                    found_phi.append(key)
                    break
        return found_phi
    
    def generate_compliance_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成合规性报告"""
        phi_fields = self.check_phi_presence(data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'compliance_status': 'PASS' if not phi_fields else 'FAIL',
            'phi_fields_found': phi_fields,
            'phi_count': len(phi_fields),
            'recommendations': [
                '对所有PHI字段进行加密存储',
                '实施严格的访问控制',
                '建立数据访问审计日志',
                '定期进行安全风险评估'
            ] if phi_fields else []
        }


class SecurityManager:
    """安全管理器 - 整合所有安全功能"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        self.encryptor = DataEncryptor()
        self.deidentifier = DataDeidentifier(config)
        self.rbac = RBACManager()
        self.audit_logger = AuditLogger()
        self.compliance_checker = HIPAAComplianceChecker(config)
        
        logger.info("Security Manager initialized")
    
    def secure_data(
        self,
        data: Dict[str, Any],
        encrypt_fields: List[str] = None,
        deidentify: bool = False
    ) -> Dict[str, Any]:
        """安全化处理数据"""
        result = data.copy()
        
        # 加密指定字段
        if encrypt_fields:
            result = self.encryptor.encrypt_dict(result, encrypt_fields)
        
        # 去标识化
        if deidentify:
            result = self.deidentifier.deidentify(result)
        
        return result
    
    def check_access(self, user_id: str, permission: str) -> bool:
        """检查访问权限"""
        return self.rbac.check_permission(user_id, permission)
    
    def log_access(
        self,
        user_id: str,
        username: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        success: bool = True
    ):
        """记录访问日志"""
        self.audit_logger.log(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=success
        )
    
    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查合规性"""
        return self.compliance_checker.generate_compliance_report(data)
