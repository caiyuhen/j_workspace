FROM nginx:alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/

# 复制前端静态文件到 Nginx 默认目录
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
