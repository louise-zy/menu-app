# 部署指南

## 🚀 一键部署到Render

### 方法1：通过Git仓库部署（推荐）

1. **提交代码到Git仓库**
   ```bash
   git add .
   git commit -m "修复用户状态管理bug，添加session支持"
   git push origin main
   ```

2. **在Render控制台创建新服务**
   - 访问 [render.com](https://render.com)
   - 点击 "New +" → "Web Service"
   - 连接你的GitHub仓库
   - 选择这个项目
   - Render会自动检测到 `render.yaml` 配置文件

### 方法2：更新现有部署

如果你已经有Render部署，只需要：

1. **推送代码更新**
   ```bash
   git add .
   git commit -m "修复用户状态管理bug"
   git push origin main
   ```

2. **自动部署**
   - Render会自动检测到代码变更
   - 自动重新构建和部署

### 🔧 配置说明

本项目包含完整的Render配置：

- **配置文件**: `render.yaml`
- **运行环境**: Python
- **Web服务器**: Gunicorn（生产级）
- **自动部署**: 启用
- **健康检查**: `/login` 路径

### 🎯 修复内容

✅ **用户状态管理bug已修复**
- 添加Flask session支持
- 用户登录状态持久化
- 支持安全登出功能
- 简化URL结构

### 🌟 新功能

- **登出功能**: 用户菜单中新增登出选项
- **会话管理**: 刷新页面不再丢失登录状态
- **更简洁的URL**: 移除URL中的用户ID依赖

### 📝 环境变量（可选）

在Render控制台中可以设置：

- `DEEPSEEK_API_KEY`: DeepSeek API密钥（用于AI分析功能）
- `SECRET_KEY`: Flask会话密钥（自动生成）

### ⚡ 部署状态检查

部署完成后，访问你的Render应用URL：
- 应该能看到登录页面
- 测试登录/注册功能
- 确认刷新页面后登录状态保持

### 🔄 滚动更新

每次推送代码更新时，Render会：
1. 自动检测代码变更
2. 重新构建应用
3. 零停机时间部署
4. 保持数据完整性

---

**部署完成！** 🎉

现在你的菜谱应用已经修复了用户状态管理问题，可以正常使用了。 