#!/usr/bin/env python3
"""
一键部署脚本 - 菜谱管理系统
用于快速部署到Render平台
"""

import subprocess
import os
import sys

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description}失败")
            if result.stderr.strip():
                print(f"   错误: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}异常: {e}")
        return False

def check_git_status():
    """检查Git状态"""
    print("\n📋 检查Git状态...")
    
    # 检查是否在Git仓库中
    if not os.path.exists('.git'):
        print("❌ 当前目录不是Git仓库")
        print("💡 请先运行: git init")
        return False
    
    # 检查是否有远程仓库
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️  未配置远程仓库")
        print("💡 请先添加远程仓库: git remote add origin <你的仓库URL>")
        return False
    
    print("✅ Git仓库状态正常")
    return True

def deploy_to_render():
    """部署到Render的主流程"""
    print("🚀 开始部署菜谱管理系统到Render...")
    print("=" * 50)
    
    # 检查Git状态
    if not check_git_status():
        return False
    
    # 添加所有文件
    if not run_command("git add .", "添加所有文件到Git"):
        return False
    
    # 提交更改
    commit_message = "修复用户状态管理bug，添加session支持和Render部署配置"
    if not run_command(f'git commit -m "{commit_message}"', "提交代码更改"):
        # 如果没有更改要提交，这是正常的
        print("💡 可能没有新的更改需要提交")
    
    # 推送到远程仓库
    if not run_command("git push origin main", "推送代码到远程仓库"):
        # 尝试master分支
        if not run_command("git push origin master", "推送代码到远程仓库(master分支)"):
            print("❌ 推送失败，请检查远程仓库配置")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 代码已成功推送！")
    print("\n📋 接下来的步骤:")
    print("1. 访问 https://render.com")
    print("2. 登录你的账号")
    print("3. 点击 'New +' → 'Web Service'")
    print("4. 连接你的GitHub仓库")
    print("5. 选择这个项目")
    print("6. Render会自动检测render.yaml配置文件")
    print("7. 点击'Deploy'开始部署")
    
    print("\n🔧 配置要点:")
    print("- 运行环境: Python")
    print("- 构建命令: pip install -r requirements.txt")
    print("- 启动命令: gunicorn --bind 0.0.0.0:$PORT app:app")
    print("- 健康检查: /login")
    
    print("\n✨ 修复内容:")
    print("✅ 用户状态管理bug已修复")
    print("✅ 添加Flask session支持")
    print("✅ 用户登录状态持久化")
    print("✅ 支持安全登出功能")
    print("✅ 简化URL结构")
    
    return True

def main():
    """主函数"""
    print("🍽️  菜谱管理系统 - 一键部署工具")
    print("📁 当前目录:", os.getcwd())
    
    # 检查必要文件
    required_files = ['app.py', 'requirements.txt', 'render.yaml']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("✅ 所有必要文件都存在")
    
    # 开始部署流程
    if deploy_to_render():
        print("\n🎊 部署准备完成！请按照上述步骤在Render控制台完成部署。")
    else:
        print("\n😞 部署准备失败，请检查错误信息并重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 