import React from 'react';
import { Card, Divider } from 'antd';
import LoginForm from '../components/LoginForm';
import styles from '../styles/LoginPage.module.css';

const LoginPage: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.background}>
        <div className={styles.overlay} />
      </div>
      
      <div className={styles.content}>
        <Card className={styles.loginCard} bordered={false}>
          <div className={styles.header}>
            <h1 className={styles.title}>CTMS + EDC</h1>
            <p className={styles.subtitle}>临床试验管理与数据采集平台</p>
          </div>
          
          <Divider />
          
          <LoginForm />
          
          <Divider />
          
          <div className={styles.footer}>
            <p>© 2026 Clinical Trial Management System. All rights reserved.</p>
            <p className={styles.version}>Version 4.0</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
