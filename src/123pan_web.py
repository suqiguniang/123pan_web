import os
import sys
import json
import uuid
import hashlib
import threading
from datetime import datetime
from http.cookies import SimpleCookie

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main.pan import Pan123, ConfigManager

from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

# ========== 辅助函数和类 ==========

# 会话管理
sessions = {}
session_lock = threading.Lock()

class WebPan123:
    """Web封装的123云盘接口"""
    
    def __init__(self):
        self.config_manager = ConfigManager
    
    def login(self, username, password):
        """登录并返回Pan123实例"""
        try:
            print(f"尝试登录，用户名: {username}")
            pan = Pan123(readfile=False, user_name=username, pass_word=password, input_pwd=False)
            print("Pan123实例创建成功")
            
            # 尝试登录
            if not getattr(pan, "authorization", None):
                print("未检测到授权，尝试登录...")
                code = pan.login()
                print(f"登录返回码: {code}")
                if code != 200 and code != 0:
                    return None, f"登录失败，返回码: {code}"
            else:
                print("使用已有授权")
            
            # 获取根目录
            print("尝试获取目录信息...")
            res_code, _ = pan.get_dir(save=False)
            print(f"获取目录返回码: {res_code}")
            if res_code != 0:
                return None, "无法获取目录信息"
                
            print("登录成功!")
            return pan, None
        except Exception as e:
            print(f"登录过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    def load_from_session(self, session_id):
        """从会话加载Pan123实例"""
        with session_lock:
            session = sessions.get(session_id)
            if not session:
                print(f"会话 {session_id} 不存在")
                return None, "会话已过期"
            
            print(f"找到会话 {session_id}")
            
            # 检查会话是否过期（30分钟）
            if (datetime.now() - session['last_active']).total_seconds() > 1800:
                print(f"会话 {session_id} 已过期")
                del sessions[session_id]
                return None, "会话已过期"
            
            # 更新最后活动时间
            session['last_active'] = datetime.now()
            
            # 尝试从配置创建Pan123实例
            try:
                print("尝试从配置创建Pan123实例...")
                pan = Pan123(readfile=True, input_pwd=False)
                
                # 验证会话有效性
                print("验证会话有效性...")
                res_code, _ = pan.get_dir(save=False)
                print(f"验证返回码: {res_code}")
                if res_code != 0:
                    return None, "会话无效"
                    
                print("会话验证成功")
                return pan, None
            except Exception as e:
                print(f"从会话加载失败: {str(e)}")
                return None, str(e)

def create_session(pan):
    """创建会话"""
    session_id = str(uuid.uuid4())
    with session_lock:
        sessions[session_id] = {
            'pan_config': {
                'user_name': pan.user_name,
                'passWord': pan.password,
                'authorization': pan.authorization,
                'deviceType': pan.devicetype,
                'osVersion': pan.osversion
            },
            'config': ConfigManager.load_config(),
            'last_active': datetime.now()
        }
        print(f"创建新会话: {session_id}")
    return session_id

def get_session_id(environ):
    """从请求中获取会话ID"""
    cookie_header = environ.get('HTTP_COOKIE', '')
    if cookie_header:
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
            if 'session_id' in cookie:
                session_id = cookie['session_id'].value
                return session_id
        except Exception as e:
            print(f"解析Cookie失败: {e}")
    return None

def parse_request_body(environ):
    """解析请求体"""
    try:
        content_length = environ.get('CONTENT_LENGTH', '0')
        if content_length:
            content_length = int(content_length)
            if content_length > 0:
                body = environ['wsgi.input'].read(content_length)
                
                content_type = environ.get('CONTENT_TYPE', '')
                if 'application/json' in content_type:
                    data = json.loads(body.decode('utf-8'))
                elif 'application/x-www-form-urlencoded' in content_type:
                    data = parse_qs(body.decode('utf-8'))
                    # 将列表转换为单个值
                    data = {k: v[0] for k, v in data.items()}
                else:
                    # 尝试自动检测
                    try:
                        data = json.loads(body.decode('utf-8'))
                    except:
                        data = parse_qs(body.decode('utf-8'))
                        data = {k: v[0] for k, v in data.items()}
                
                return data
    except Exception as e:
        print(f"解析请求体失败: {e}")
    return {}

def serve_static_file(environ, start_response, filepath):
    """提供静态文件"""
    web_dir = os.path.join(os.path.dirname(__file__), 'main', 'web')
    full_path = os.path.join(web_dir, filepath)
    
    print(f"请求静态文件: {filepath}")
    print(f"完整路径: {full_path}")
    
    if not os.path.exists(full_path):
        print(f"文件不存在: {full_path}")
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [f'File not found: {filepath}'.encode('utf-8')]
    
    # 根据文件扩展名设置Content-Type
    content_types = {
        '.html': 'text/html; charset=utf-8',
        '.htm': 'text/html; charset=utf-8',
        '.css': 'text/css',
        '.js': 'application/javascript; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.ico': 'image/x-icon',
        '.svg': 'image/svg+xml',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
        '.json': 'application/json; charset=utf-8',
        '.txt': 'text/plain; charset=utf-8'
    }
    
    ext = os.path.splitext(full_path)[1].lower()
    content_type = content_types.get(ext, 'application/octet-stream')
    
    try:
        with open(full_path, 'rb') as f:
            content = f.read()
        
        file_size = len(content)
        print(f"成功读取文件，大小: {file_size} 字节")
        
        headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(file_size))
        ]
        
        # 如果是HTML文件，添加缓存控制
        if '.html' in ext:
            headers.append(('Cache-Control', 'no-cache, no-store, must-revalidate'))
            headers.append(('Pragma', 'no-cache'))
            headers.append(('Expires', '0'))
        
        start_response('200 OK', headers)
        return [content]
    except Exception as e:
        print(f"读取文件失败: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [str(e).encode('utf-8')]

# ========== 路由处理函数 ==========

def handle_login(environ, start_response):
    """处理登录请求"""
    print("\n=== 处理登录请求 ===")
    
    if environ['REQUEST_METHOD'] != 'POST':
        start_response('405 Method Not Allowed', [('Content-Type', 'text/plain')])
        return [b'Method Not Allowed']
    
    data = parse_request_body(environ)
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    print(f"收到的用户名: {username}")
    print(f"收到的密码长度: {len(password) if password else 0}")
    
    if not username or not password:
        start_response('400 Bad Request', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': '用户名和密码不能为空'}).encode('utf-8')]
    
    web_pan = WebPan123()
    pan, error = web_pan.login(username, password)
    
    if error:
        print(f"登录失败: {error}")
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': error}).encode('utf-8')]
    
    # 保存配置
    try:
        pan.save_file()
        print("配置保存成功")
    except Exception as e:
        print(f"保存配置失败: {e}")
    
    # 创建会话
    session_id = create_session(pan)
    
    # 设置Cookie并重定向
    headers = [
        ('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly; Max-Age=1800'),
        ('Location', '/index.html'),
        ('Content-Type', 'text/plain')
    ]
    start_response('302 Found', headers)
    print(f"登录成功，重定向到 /index.html，会话ID: {session_id}")
    return [b'Redirecting...']

def handle_logout(environ, start_response):
    """处理登出请求"""
    session_id = get_session_id(environ)
    if session_id:
        with session_lock:
            if session_id in sessions:
                del sessions[session_id]
                print(f"会话 {session_id} 已删除")
    
    # 清除Cookie
    headers = [
        ('Set-Cookie', 'session_id=; Path=/; HttpOnly; Expires=Thu, 01 Jan 1970 00:00:00 GMT'),
        ('Location', '/'),
        ('Content-Type', 'text/plain')
    ]
    start_response('302 Found', headers)
    return [b'Logout successful']

def handle_api_list(pan, data, start_response):
    """处理文件列表API"""
    try:
        parent_id = data.get('parent_id', pan.parent_file_id)
        print(f"获取文件列表，父ID: {parent_id}")
        print(f"当前parent_file_list: {pan.parent_file_list}")
        
        # 检查是否需要切换目录
        if parent_id != pan.parent_file_id:
            pan.parent_file_id = parent_id
            pan.list = []  # 清空列表
            pan.all_file = False  # 重置标志
            pan.file_page = 0  # 重置页码
            
        # 获取目录数据
        if not pan.list:  # 如果列表为空，获取数据
            res_code, items = pan.get_dir(save=True)
            print(f"重新获取目录返回码: {res_code}, 项目数: {len(items) if items else 0}")
        else:
            res_code = 0
            items = pan.list
            print(f"使用现有列表，项目数: {len(items)}")
        
        print(f"pan.list长度: {len(pan.list) if hasattr(pan, 'list') else '没有list属性'}")
        
        if res_code != 0:
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '获取目录失败'}).encode('utf-8')]
        
        # 格式化文件列表
        file_list = []
        for item in items:  # 使用items
            print(f"处理项目: {item['FileName']} (ID: {item['FileId']}, Type: {item['Type']})")
            file_list.append({
                'id': item['FileId'],
                'name': item['FileName'],
                'type': 'folder' if item['Type'] == 1 else 'file',
                'size': item['Size'],
                'modified': item.get('UpdatedAt', ''),
                'path': item.get('AbsPath', '')
            })
        
        response_data = {
            'success': True,
            'files': file_list,
            'current_path': parent_id,
            'parent_id': pan.parent_file_list[-2] if len(pan.parent_file_list) > 1 else 0
        }
        
        print(f"返回 {len(file_list)} 个文件")
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    except Exception as e:
        print(f"处理文件列表API失败: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': str(e)}).encode('utf-8')]

def handle_api_mkdir(pan, data, start_response):
    """处理创建文件夹API"""
    try:
        dirname = data.get('dirname', '').strip()
        print(f"创建文件夹: {dirname}")
        if not dirname:
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '文件夹名不能为空'}).encode('utf-8')]
        
        folder_id = pan.mkdir(dirname, remakedir=False)
        if folder_id:
            print(f"文件夹创建成功，ID: {folder_id}")
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'success': True, 'folder_id': folder_id}).encode('utf-8')]
        else:
            print("文件夹创建失败")
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '创建失败'}).encode('utf-8')]
            
    except Exception as e:
        print(f"处理创建文件夹API失败: {e}")
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': str(e)}).encode('utf-8')]

def handle_api_cd(pan, data, start_response):
    """处理切换目录API"""
    try:
        folder_id = data.get('folder_id', 0)
        print(f"切换目录到: {folder_id}")
        
        if folder_id == '..':
            if len(pan.parent_file_list) > 1:
                pan.parent_file_list.pop()
                folder_id = pan.parent_file_list[-1]
                print(f"返回上级，新ID: {folder_id}")
            else:
                folder_id = 0
                print("已在根目录")
        
        pan.parent_file_id = folder_id
        if folder_id not in pan.parent_file_list:
            pan.parent_file_list.append(folder_id)
        pan.list = []
        
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({'success': True, 'folder_id': folder_id}).encode('utf-8')]
            
    except Exception as e:
        print(f"处理切换目录API失败: {e}")
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': str(e)}).encode('utf-8')]

def handle_api_download(pan, data, start_response):
    """处理下载API"""
    try:
        file_id = data.get('file_id')
        print(f"处理下载请求，文件ID: {file_id}")
        
        if not file_id:
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '文件ID不能为空'}).encode('utf-8')]
        
        # 查找文件详情
        file_detail = None
        print(f"当前文件列表长度: {len(pan.list) if hasattr(pan, 'list') else 0}")
        
        # 首先尝试从现有列表中查找
        if hasattr(pan, 'list') and pan.list:
            for item in pan.list:
                if str(item['FileId']) == str(file_id):
                    file_detail = item
                    print(f"从现有列表中找到文件: {file_detail['FileName']}")
                    break
        
        # 如果没找到，重新获取目录
        if not file_detail:
            print("未在现有列表中找到文件，重新获取目录...")
            pan.get_dir(save=True)
            for item in pan.list:
                if str(item['FileId']) == str(file_id):
                    file_detail = item
                    print(f"重新获取后找到文件: {file_detail['FileName']}")
                    break
        
        if not file_detail:
            print("文件不存在")
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '文件不存在'}).encode('utf-8')]
        
        # 获取下载链接
        print(f"获取文件下载链接: {file_detail['FileName']}")
        download_url = pan.link_by_fileDetail(file_detail, showlink=False)
        
        if isinstance(download_url, int):
            print(f"获取下载链接失败，返回码: {download_url}")
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '获取下载链接失败'}).encode('utf-8')]
        
        print(f"下载链接获取成功: {download_url[:100]}...")
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': True,
            'download_url': download_url,
            'filename': file_detail['FileName']
        }).encode('utf-8')]
            
    except Exception as e:
        print(f"处理下载API失败: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': str(e)}).encode('utf-8')]

def handle_api_share(pan, data, start_response):
    """处理分享API"""
    try:
        file_id = data.get('file_id')
        password = data.get('password', '')
        
        print(f"处理分享请求，文件ID: {file_id}, 提取码: {password}")
        
        if not file_id:
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '文件ID不能为空'}).encode('utf-8')]
        
        # 查找文件详情
        file_detail = None
        if hasattr(pan, 'list') and pan.list:
            for item in pan.list:
                if str(item['FileId']) == str(file_id):
                    file_detail = item
                    break
        
        if not file_detail:
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': '文件不存在'}).encode('utf-8')]
        
        # 分享逻辑
        data_share = {
            "driveId": 0,
            "expiration": "2099-12-12T08:00:00+08:00",
            "fileIdList": str(file_id),
            "shareName": "123云盘分享",
            "sharePwd": password,
            "event": "shareCreate"
        }
        
        print(f"发送分享请求: {data_share}")
        
        import requests
        share_res = requests.post(
            "https://www.123pan.com/a/api/share/create",
            headers=pan.header_logined,
            data=json.dumps(data_share),
            timeout=30
        )
        
        print(f"分享响应状态码: {share_res.status_code}")
        
        share_res_json = share_res.json()
        print(f"分享响应内容: {share_res_json}")
        
        if share_res_json.get("code", -1) != 0:
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'success': False, 'message': share_res_json.get('message', '分享失败')}).encode('utf-8')]
        
        share_key = share_res_json["data"]["ShareKey"]
        share_url = "https://www.123pan.com/s/" + share_key
        
        print(f"分享成功，链接: {share_url}")
        
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': True,
            'share_url': share_url,
            'password': password
        }).encode('utf-8')]
            
    except Exception as e:
        print(f"处理分享API失败: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'success': False, 'message': str(e)}).encode('utf-8')]

# ========== 主API处理函数 ==========

def handle_api(environ, start_response, path_parts):
    """处理API请求"""
    print(f"\n=== 处理API请求 ===")
    print(f"路径部分: {path_parts}")
    print(f"请求方法: {environ.get('REQUEST_METHOD')}")
    
    # 检查路径部分
    if not path_parts:
        print("API路径为空")
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': 'API路径不能为空'
        }).encode('utf-8')]
    
    action = path_parts[0]
    print(f"API动作: {action}")
    
    # 检查会话
    session_id = get_session_id(environ)
    if not session_id:
        print("未找到会话ID")
        start_response('401 Unauthorized', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': '未登录'
        }).encode('utf-8')]
    
    # 加载Pan123实例
    web_pan = WebPan123()
    pan, error = web_pan.load_from_session(session_id)
    if error:
        print(f"加载会话失败: {error}")
        start_response('401 Unauthorized', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': error
        }).encode('utf-8')]
    
    # 检查请求方法
    if environ['REQUEST_METHOD'] != 'POST':
        print(f"不支持的请求方法: {environ['REQUEST_METHOD']}")
        start_response('405 Method Not Allowed', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': '只支持POST请求'
        }).encode('utf-8')]
    
    # 解析请求体
    try:
        data = parse_request_body(environ)
        print(f"请求数据: {data}")
    except Exception as e:
        print(f"解析请求体失败: {e}")
        start_response('400 Bad Request', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': '请求数据格式错误'
        }).encode('utf-8')]
    
    # 根据action分发处理
    try:
        if action == 'list':
            print("处理文件列表请求")
            return handle_api_list(pan, data, start_response)
            
        elif action == 'mkdir':
            print("处理创建文件夹请求")
            return handle_api_mkdir(pan, data, start_response)
                
        elif action == 'cd':
            print("处理切换目录请求")
            return handle_api_cd(pan, data, start_response)
            
        elif action == 'download':
            print("处理下载请求")
            return handle_api_download(pan, data, start_response)
            
        elif action == 'share':
            print("处理分享请求")
            return handle_api_share(pan, data, start_response)
            
        elif action == 'delete':
            print("处理删除请求")
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({
                'success': True,
                'message': '删除成功'
            }).encode('utf-8')]
            
        else:
            print(f"未知的API动作: {action}")
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({
                'success': False,
                'message': f'API未找到: {action}'
            }).encode('utf-8')]
            
    except Exception as e:
        print(f"API处理异常: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }).encode('utf-8')]

# ========== WSGI主应用函数 ==========

def application(environ, start_response):
    """WSGI应用主函数"""
    print("\n" + "="*50)
    print(f"收到请求: {environ.get('REQUEST_METHOD')} {environ.get('PATH_INFO')}")
    
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    print(f"请求路径: {path}")
    
    # 标准化路径
    if path.endswith('/') and path != '/':
        path = path.rstrip('/')
    
    print(f"标准化路径: {path}")
    
    # 静态文件处理
    if path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.html', '.htm')):
        filename = path.lstrip('/')
        print(f"处理静态文件: {filename}")
        return serve_static_file(environ, start_response, filename)
    
    # API路由
    if path.startswith('/api/'):
        print("匹配到API路由")
        api_path = path[5:]  # 去掉 '/api/'
        path_parts = [p for p in api_path.split('/') if p]
        print(f"API路径部分: {path_parts}")
        return handle_api(environ, start_response, path_parts)
    
    # 其他路由
    elif path == '/' or path == '':
        print("提供登录页面")
        return serve_static_file(environ, start_response, 'login.html')
    
    elif path == '/login':
        print(f"处理登录请求")
        if method == 'POST':
            return handle_login(environ, start_response)
        else:
            headers = [('Location', '/')]
            start_response('302 Found', headers)
            return [b'Redirecting...']
    
    elif path == '/logout':
        print("处理登出请求")
        return handle_logout(environ, start_response)
    
    elif path == '/index.html':
        print("检查index.html访问权限")
        session_id = get_session_id(environ)
        if not session_id:
            print("未登录，重定向")
            headers = [('Location', '/')]
            start_response('302 Found', headers)
            return [b'Redirecting...']
        
        web_pan = WebPan123()
        pan, error = web_pan.load_from_session(session_id)
        if error:
            print(f"会话验证失败: {error}")
            headers = [('Location', '/')]
            start_response('302 Found', headers)
            return [b'Redirecting...']
        
        print("提供主页面")
        return serve_static_file(environ, start_response, 'index.html')
    
    elif path == '/test_index.html':
        print("提供测试页面")
        return serve_static_file(environ, start_response, 'test_index.html')
    
    elif path == '/simple_index.html':
        print("提供简化页面")
        return serve_static_file(environ, start_response, 'simple_index.html')
    
    elif path == '/route_test.html':
        print("提供路由测试页面")
        return serve_static_file(environ, start_response, 'route_test.html')
    
    else:
        print(f"未知路径: {path}，提供登录页面")
        return serve_static_file(environ, start_response, 'login.html')

# ========== 主程序 ==========

def main():
    """桌面应用主函数"""
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    # 检查目录结构
    web_dir = os.path.join(os.path.dirname(__file__), 'main', 'web')
    if not os.path.exists(web_dir):
        print(f"错误: web目录不存在: {web_dir}")
        sys.exit(1)
    
    port = 8080
    host = '0.0.0.0'
    
    print(f"正在启动 123云盘Web版 在 http://{host}:{port}")
    print(f"Web目录: {web_dir}")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    
    try:
        with make_server(host, port, application) as httpd:
            print(f"服务器已启动，访问 http://localhost:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器失败: {e}")
        import traceback
        traceback.print_exc()
