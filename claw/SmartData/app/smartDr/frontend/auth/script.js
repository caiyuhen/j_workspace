// 登录表单处理
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('loginMessage');
    
    // 清除之前的提示信息
    messageDiv.className = 'message';
    messageDiv.textContent = '';
    
    // 简单验证
    if (!username || !password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }
    
    try {
        // 发送登录请求到认证服务
        const response = await fetch('http://localhost:3001/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('登录成功！', 'success');
            // 保存token到本地存储
            localStorage.setItem('authToken', result.token);
            
            // 根据用户角色重定向到相应系统
            // 这里是简化示例，实际应用中应该从服务器获取用户角色信息
            window.location.href = '/dashboard';
        } else {
            showMessage(result.message || '登录失败', 'error');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showMessage('服务器连接失败，请稍后重试', 'error');
    }
});

// 显示消息的辅助函数
function showMessage(message, type) {
    const messageDiv = document.getElementById('loginMessage');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
}

// 页面加载完成后检查本地存储中的token
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('authToken');
    if (token) {
        // 可以在这里添加token验证逻辑
        console.log('已发现有效的认证令牌');
    }
});