const express = require('express');
const router = express.Router();
const { login, register, validateToken } = require('../controllers/authController');

// 用户登录
router.post('/login', login);

// 用户注册
router.post('/register', register);

// 验证令牌
router.get('/validate', validateToken);

module.exports = router;