# Ubuntu 部署常见问题

## 问题1: uvicorn 命令找不到

### 错误信息
```
Command 'uvicorn' not found
```

### 原因
没有激活 Python 虚拟环境，或者虚拟环境中没有安装 uvicorn。

### 解决方法

#### 方法1: 激活虚拟环境后运行（推荐）

```bash
# 1. 进入后端目录
cd ~/agent/translator_online/Translator_online/web/backend

# 2. 检查虚拟环境是否存在
ls -la venv

# 3. 如果虚拟环境不存在，创建它
python3 -m venv venv

# 4. 激活虚拟环境
source venv/bin/activate

# 5. 安装依赖（如果还没安装）
pip install --upgrade pip
pip install -r requirements.txt

# 6. 验证 uvicorn 是否安装
which uvicorn
uvicorn --version

# 7. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方法2: 使用 Python 模块方式运行

如果虚拟环境已激活但 uvicorn 命令仍找不到：

```bash
# 激活虚拟环境
source venv/bin/activate

# 使用 python -m 方式运行
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方法3: 使用完整路径

```bash
# 使用虚拟环境中的 uvicorn 完整路径
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 完整安装步骤

如果这是第一次部署，请按以下步骤操作：

```bash
# 1. 进入后端目录
cd ~/agent/translator_online/Translator_online/web/backend

# 2. 创建虚拟环境（如果不存在）
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级 pip
pip install --upgrade pip

# 5. 安装后端依赖
pip install -r requirements.txt

# 6. 返回项目根目录安装核心依赖（如果需要）
cd ../..
pip install -r requirements.txt

# 7. 返回后端目录
cd web/backend

# 8. 确保虚拟环境已激活（提示符前应该有 (venv)）
# 如果没看到 (venv)，重新激活
source venv/bin/activate

# 9. 验证安装
pip list | grep uvicorn

# 10. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 问题2: Python 版本不兼容

### 错误信息
```
Python version X.X is not supported
```

### 解决方法

```bash
# 检查 Python 版本
python3 --version

# 如果版本低于 3.8，安装 Python 3.10
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# 使用 Python 3.10 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate
```

## 问题3: 端口被占用

### 错误信息
```
Address already in use
```

### 解决方法

```bash
# 检查端口占用
sudo netstat -tulpn | grep :8000
# 或
sudo lsof -i :8000

# 杀死占用端口的进程
sudo kill -9 <PID>

# 或使用其他端口
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 问题4: 权限问题

### 错误信息
```
Permission denied
```

### 解决方法

```bash
# 确保数据目录有写权限
chmod -R 755 web/backend/data
chmod -R 755 logs

# 如果使用 root 用户，建议创建普通用户
sudo adduser translator
sudo su - translator
```

## 问题5: 模块导入错误

### 错误信息
```
ModuleNotFoundError: No module named 'app'
```

### 解决方法

```bash
# 确保在正确的目录运行
cd ~/agent/translator_online/Translator_online/web/backend

# 检查当前目录
pwd

# 确保 app 目录存在
ls -la app/

# 使用正确的命令
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 快速检查清单

在启动服务前，请确认：

- [ ] 已进入 `web/backend` 目录
- [ ] 虚拟环境已创建（`venv` 目录存在）
- [ ] 虚拟环境已激活（命令行提示符前有 `(venv)`）
- [ ] 已安装所有依赖（`pip install -r requirements.txt`）
- [ ] `.env` 文件已配置 API 密钥
- [ ] 数据目录有写权限

## 验证安装

```bash
# 1. 检查虚拟环境
source venv/bin/activate
which python
which pip

# 2. 检查关键包
pip list | grep -E "uvicorn|fastapi|pydantic"

# 3. 测试导入
python -c "import app.main; print('OK')"

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 生产环境启动（不使用 --reload）

```bash
# 激活虚拟环境
source venv/bin/activate

# 生产模式启动（无自动重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用 gunicorn（推荐生产环境）
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

