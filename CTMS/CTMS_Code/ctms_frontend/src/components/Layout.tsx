import React from 'react';
import { Box, AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Button } from '@mui/material';
import { 
  Dashboard as DashboardIcon, Assignment, Group, LocalHospital, 
  Description, Logout, Warning, Visibility, Person, Medication, Science, History
} from '@mui/icons-material';
import { useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const drawerWidth = 240;

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const menuItems = [
    { text: '仪表盘', icon: <DashboardIcon />, path: '/' },
    { text: '项目管理', icon: <Assignment />, path: '/trials' },
    { text: '受试者管理', icon: <Group />, path: '/subjects' },
    { text: '中心管理', icon: <LocalHospital />, path: '/sites' },
    { text: 'AE/SAE 管理', icon: <Warning />, path: '/safety' },
    { text: '监查管理', icon: <Visibility />, path: '/monitoring' },
    { text: '药物管理', icon: <Medication />, path: '/drugs' },
    { text: '样本管理', icon: <Science />, path: '/specimens' },
    { text: '文档管理', icon: <Description />, path: '/documents' },
    { text: '用户管理', icon: <Person />, path: '/users' },
    { text: '审计追踪', icon: <History />, path: '/audit-trail' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            CTMS - {user?.role}
          </Typography>
          <Button color="inherit" onClick={handleLogout} startIcon={<Logout />}>
            退出登录
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton onClick={() => navigate(item.path)}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
