# 使用 Python 3.9 slim 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装 PyQt5 在容器内需要的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

# 复制项目源码到容器（src 目录下的 main 模块、web 静态文件和入口脚本）
COPY src/ /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir PyQt5 requests

# 暴露 8080 端口
EXPOSE 8080

# 启动 Web 服务
CMD ["python", "123pan_web.py"]
