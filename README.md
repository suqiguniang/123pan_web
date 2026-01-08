# 123pan Web版

## 📌 About
**123pan Web版** 是一个基于 Python 和 Web 技术的 123云盘非官方 Web 客户端，提供现代化的 Web 界面来管理您的 123云盘文件。该项目将原有的桌面 GUI 应用扩展为 Web 服务，支持多用户访问，无需安装客户端即可通过浏览器管理云盘文件。

## 🌟 主要特性
- **Web 界面**：响应式设计，支持桌面和移动设备访问
- **完整功能**：文件浏览、上传下载、分享链接、文件夹管理
- **会话管理**：支持多用户登录，会话自动管理
- **静态文件服务**：内置 Web 服务器，无需额外配置
- **RESTful API**：提供标准化的 API 接口
- **兼容性**：基于原 `Pan123` 库，保留所有核心功能

## 🏗️ 项目结构
```
123pan-web/
├── main/
│   ├── pan.py              # 核心云盘库 (原桌面版)
│   └── web/                # Web 静态文件
│       ├── index.html      # 主界面
│       ├── login.html      # 登录页面
│       └── style.css       # 样式文件
├── 123pan_web.py           # Web 服务器主文件
├── config.json             # 配置文件 (自动生成)
└── README.md               # 说明文档
```

## 🚀 快速开始

### 安装依赖
```bash
pip install PyQt5 requests
```

### 运行服务
```bash
python 123pan_web.py
```

### 访问应用
1. 打开浏览器访问：`http://localhost:8080`
2. 使用您的 123云盘账号登录
3. 开始管理您的云盘文件

## 📁 核心功能

### 文件管理
- 📁 浏览文件和文件夹
- 📤 文件上传 (支持多文件)
- 📥 文件下载 (直接下载或生成链接)
- 📝 新建文件夹
- 🗑️ 删除文件

### 分享功能
- 🔗 生成分享链接
- 🔐 可设置提取码
- ⏰ 长期有效链接

### 其他特性
- 🔄 实时刷新文件列表
- ↩️ 路径导航面包屑
- 🔒 安全的会话管理
- 📱 响应式设计

## 🔧 技术栈

### 后端
- **Python 3** - 主要编程语言
- **WSGI** - Web 服务器网关接口
- **JSON** - 配置和数据交换格式
- **uuid** - 会话 ID 生成

### 前端
- **HTML5/CSS3** - 页面结构和样式
- **JavaScript (ES6)** - 交互逻辑
- **Font Awesome** - 图标库
- **响应式设计** - 移动端适配

### 通信
- **RESTful API** - 前后端分离架构
- **Cookie 会话** - 用户状态管理
- **JSON 数据格式** - 标准数据交换

## 🔐 安全特性
- 会话超时自动销毁 (30分钟)
- Cookie HttpOnly 标记
- 密码不直接存储在 Cookie 中
- 配置文件加密存储

## 📊 API 接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/list` | POST | 获取文件列表 |
| `/api/mkdir` | POST | 创建文件夹 |
| `/api/cd` | POST | 切换目录 |
| `/api/download` | POST | 获取下载链接 |
| `/api/share` | POST | 创建分享链接 |
| `/api/delete` | POST | 删除文件 |
| `/login` | POST | 用户登录 |
| `/logout` | GET | 用户登出 |

## ⚙️ 配置说明

### 配置文件位置
- **Windows**: `%APPDATA%\Qxyz17\123pan\config.json`
- **Linux/macOS**: `~/.config/Qxyz17/123pan/config.json`

### 配置内容
```json
{
    "userName": "用户名",
    "passWord": "密码",
    "authorization": "Bearer token",
    "deviceType": "设备类型",
    "osVersion": "系统版本",
    "settings": {
        "defaultDownloadPath": "默认下载路径",
        "askDownloadLocation": true
    }
}
```

## 🧩 扩展功能

### 计划中的特性
- [ ] <del>文件搜索功能</del>
- [ ] 批量操作支持
- [ ] 文件预览 (图片/文档)
- [ ] 回收站管理
- [ ] 上传进度实时显示
- [ ] <del>断点续传</del>

### 集成可能性
- Docker 容器化
- Nginx 反向代理
- HTTPS 支持
- OAuth2 认证

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 代码规范
- 遵循 Python PEP8 规范
- 使用有意义的变量名
- 添加必要的注释
- 保持向后兼容性

## 📄 许可证

本项目基于 MIT 许可证开源，详情请查看 LICENSE 文件。

## ⚠️ 免责声明

本项目为**非官方**第三方应用，与 123云盘官方无关。使用本软件时，请遵守：
1. 123云盘的服务条款
2. 相关法律法规
3. 合理使用原则

开发者不对因使用本软件造成的任何损失负责。

## 📞 支持与反馈

如果您遇到问题或有建议：
1. 查看 Issues 中是否有类似问题
2. 创建新的 Issue 详细描述问题
3. 提供错误日志和复现步骤

## 🌐 相关链接
- [123云盘官方网站](https://www.123pan.com)
- [原版桌面应用](https://github.com/Qxyz17/123pan)
- [Python 官方网站](https://www.python.org)

---

**感谢使用 123云盘 Web版！** 🎉

如果这个项目对您有帮助，请考虑给它一个 ⭐ Star 支持！
