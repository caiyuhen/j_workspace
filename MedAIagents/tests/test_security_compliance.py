"""
安全与合规模块单元测试
Security & Compliance Module Unit Tests
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta

from medai.security.compliance import (
    DataEncryptor,
    DataDeidentifier,
    RBACManager,
    AuditLogger,
    HIPAAComplianceChecker,
    SecurityManager,
)


class TestDataEncryptor:
    """数据加密器测试"""

    @pytest.fixture
    def temp_dir(self):
        td = tempfile.mkdtemp()
        yield td
        shutil.rmtree(td, ignore_errors=True)

    @pytest.fixture
    def encryptor(self, temp_dir):
        key_file = os.path.join(temp_dir, 'test_key')
        return DataEncryptor(key_file=key_file)

    def test_encrypt_decrypt(self, encryptor):
        """测试加密解密基本功能"""
        plaintext = "患者张三，男，65岁"
        encrypted = encryptor.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty(self, encryptor):
        """测试空字符串加密"""
        assert encryptor.encrypt("") == ""
        assert encryptor.decrypt("") == ""

    def test_encrypt_dict(self, encryptor):
        """测试字典字段加密"""
        data = {
            'name': '张三',
            'age': 65,
            'diagnosis': '高血压',
            'public_info': '公开信息'
        }
        encrypted = encryptor.encrypt_dict(data, fields=['name', 'diagnosis'])
        assert encrypted['name'] != '张三'
        assert encrypted['diagnosis'] != '高血压'
        assert encrypted['age'] == 65
        assert encrypted['public_info'] == '公开信息'

    def test_decrypt_dict(self, encryptor):
        """测试字典字段解密"""
        data = {
            'name': encryptor.encrypt('张三'),
            'diagnosis': encryptor.encrypt('高血压'),
            'age': 65,
        }
        decrypted = encryptor.decrypt_dict(data, fields=['name', 'diagnosis'])
        assert decrypted['name'] == '张三'
        assert decrypted['diagnosis'] == '高血压'
        assert decrypted['age'] == 65

    def test_key_persistence(self, temp_dir):
        """测试密钥持久化"""
        key_file = os.path.join(temp_dir, 'persist_key')
        e1 = DataEncryptor(key_file=key_file)
        encrypted = e1.encrypt('test_data')

        e2 = DataEncryptor(key_file=key_file)
        decrypted = e2.decrypt(encrypted)
        assert decrypted == 'test_data'

    def test_password_derived_key(self, temp_dir):
        """测试密码派生密钥"""
        key_file = os.path.join(temp_dir, 'pwd_key')
        e1 = DataEncryptor(key_file=key_file, password='secret123')
        encrypted = e1.encrypt('sensitive')

        e2 = DataEncryptor(key_file=key_file, password='secret123')
        decrypted = e2.decrypt(encrypted)
        assert decrypted == 'sensitive'


class TestDataDeidentifier:
    """数据去标识化测试"""

    @pytest.fixture
    def deidentifier(self):
        return DataDeidentifier()

    def test_remove_sensitive_fields(self, deidentifier):
        """测试敏感字段移除"""
        data = {
            'name': '张三',
            'phone': '13800138000',
            'id_card': '310101199001011234',
            'address': '上海市',
            'diagnosis': '高血压',
        }
        result = deidentifier.deidentify(data)
        assert 'name' not in result
        assert 'phone' not in result
        assert 'id_card' not in result
        assert 'address' not in result
        assert 'diagnosis' in result

    def test_age_anonymization(self, deidentifier):
        """测试年龄匿名化"""
        assert deidentifier._anonymize_field('age', 25) == '18-29岁'
        assert deidentifier._anonymize_field('age', 45) == '40-49岁'
        assert deidentifier._anonymize_field('age', 75) == '≥70岁'
        assert deidentifier._anonymize_field('age', 15) == '<18岁'

    def test_batch_deidentify(self, deidentifier):
        """测试批量去标识化"""
        records = [
            {'name': '张三', 'age': 30, 'diagnosis': 'A'},
            {'name': '李四', 'age': 50, 'diagnosis': 'B'},
        ]
        results = deidentifier.batch_deidentify(records)
        assert len(results) == 2
        assert 'name' not in results[0]
        assert 'name' not in results[1]


class TestRBACManager:
    """RBAC访问控制测试"""

    @pytest.fixture
    def temp_db(self):
        td = tempfile.mkdtemp()
        db_path = os.path.join(td, 'rbac_test.db')
        yield db_path
        shutil.rmtree(td, ignore_errors=True)

    @pytest.fixture
    def rbac(self, temp_db):
        return RBACManager(db_path=temp_db)

    def test_add_user(self, rbac):
        """测试添加用户"""
        assert rbac.add_user('u1', 'doctor_a', 'doctor', '心内科') is True
        assert rbac.get_user_role('u1') == 'doctor'

    def test_add_user_invalid_role(self, rbac):
        """测试添加无效角色用户"""
        assert rbac.add_user('u2', 'user_b', 'invalid_role') is False

    def test_check_permission(self, rbac):
        """测试权限检查"""
        rbac.add_user('u1', 'admin_a', 'admin')
        rbac.add_user('u2', 'doc_b', 'doctor')
        rbac.add_user('u3', 'viewer_c', 'viewer')

        assert rbac.check_permission('u1', 'patient.write') is True
        assert rbac.check_permission('u2', 'emr.read') is True
        assert rbac.check_permission('u2', 'patient.write') is True
        assert rbac.check_permission('u3', 'knowledge.read') is True
        assert rbac.check_permission('u3', 'patient.write') is False
        assert rbac.check_permission('unknown', 'patient.read') is False

    def test_list_users(self, rbac):
        """测试用户列表"""
        rbac.add_user('u1', 'a', 'doctor')
        rbac.add_user('u2', 'b', 'researcher')
        users = rbac.list_users()
        assert len(users) == 2
        assert users[0]['username'] in ['a', 'b']

    def test_get_role_permissions(self, rbac):
        """测试获取角色权限"""
        perms = rbac.get_role_permissions('doctor')
        assert perms is not None
        assert 'patient.read' in perms['permissions']
        assert perms['description'] == '临床医生'

        assert rbac.get_role_permissions('nonexistent') is None


class TestAuditLogger:
    """审计日志测试"""

    @pytest.fixture
    def temp_db(self):
        td = tempfile.mkdtemp()
        db_path = os.path.join(td, 'audit_test.db')
        yield db_path
        shutil.rmtree(td, ignore_errors=True)

    @pytest.fixture
    def logger(self, temp_db):
        return AuditLogger(db_path=temp_db)

    def test_log_and_query(self, logger):
        """测试日志记录和查询"""
        logger.log(
            user_id='u1',
            username='doctor_a',
            action='patient.read',
            resource_type='patient',
            resource_id='p001',
            success=True,
        )

        logs = logger.query_logs(user_id='u1')
        assert len(logs) == 1
        assert logs[0]['action'] == 'patient.read'
        assert logs[0]['success'] == 1

    def test_query_by_action(self, logger):
        """测试按动作查询"""
        logger.log('u1', 'a', 'patient.read', success=True)
        logger.log('u1', 'a', 'patient.write', success=True)
        logger.log('u2', 'b', 'patient.read', success=True)

        logs = logger.query_logs(action='patient.read')
        assert len(logs) == 2

    def test_cleanup_old_logs(self, logger):
        """测试清理过期日志"""
        logger.log('u1', 'a', 'test.action', success=True)
        logger.max_retention_days = 0
        logger.cleanup_old_logs()

        logs = logger.query_logs()
        assert len(logs) == 0


class TestHIPAAComplianceChecker:
    """HIPAA合规检查测试"""

    def test_phi_detection(self):
        """测试PHI检测"""
        checker = HIPAAComplianceChecker()
        data = {'name': '张三', 'phone': '13800138000', 'diagnosis': '高血压'}
        phi = checker.check_phi_presence(data)
        assert len(phi) > 0

    def test_safe_text(self):
        """测试无PHI文本"""
        checker = HIPAAComplianceChecker()
        data = {'study_size': 100, 'mean_age': 65}
        phi = checker.check_phi_presence(data)
        assert len(phi) == 0


class TestSecurityManager:
    """安全管理器集成测试"""

    @pytest.fixture
    def temp_dir(self):
        td = tempfile.mkdtemp()
        yield td
        shutil.rmtree(td, ignore_errors=True)

    def test_full_workflow(self, temp_dir):
        """测试完整安全工作流"""
        import uuid
        sm = SecurityManager()

        # 使用唯一用户名避免数据库冲突
        unique_user = f"doctor_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"

        # 注册用户
        sm.rbac.add_user(user_id, unique_user, 'doctor')

        # 检查权限
        assert sm.check_access(user_id, 'emr.read') is True
        assert sm.check_access(user_id, 'research.create') is False

        # 记录审计
        sm.audit_logger.log(user_id, unique_user, 'emr.read', success=True)
        logs = sm.audit_logger.query_logs(user_id=user_id)
        assert len(logs) == 1

        # 加密数据
        encrypted = sm.encryptor.encrypt('敏感数据')
        decrypted = sm.encryptor.decrypt(encrypted)
        assert decrypted == '敏感数据'

        # 去标识化
        data = {'name': '张三', 'age': 65, 'diagnosis': '高血压'}
        deid = sm.deidentifier.deidentify(data)
        assert 'name' not in deid
