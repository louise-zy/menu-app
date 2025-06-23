from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import random
import requests
from openai import OpenAI
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# 数据文件路径
DATA_FILE = 'recipes.json'

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')  # 从环境变量获取

# 初始化OpenAI客户端
try:
    if DEEPSEEK_API_KEY:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        print("DeepSeek客户端初始化成功")
    else:
        print("⚠️ 警告：未设置DEEPSEEK_API_KEY环境变量，AI分析功能将不可用")
        client = None
except Exception as e:
    print(f"DeepSeek客户端初始化失败: {e}")
    client = None

def load_all_user_data():
    """加载所有用户数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容旧数据格式
                if isinstance(data, list):
                    # 旧格式：直接是菜谱列表，迁移到default用户
                    return {"default": data}
                return data
        except:
            return {}
    return {}

def save_all_user_data(all_data):
    """保存所有用户数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

def load_recipes(user_id="default"):
    """加载指定用户的菜谱数据"""
    all_data = load_all_user_data()
    return all_data.get(user_id, [])

def save_recipes(recipes, user_id="default"):
    """保存指定用户的菜谱数据"""
    all_data = load_all_user_data()
    all_data[user_id] = recipes
    save_all_user_data(all_data)

def get_user_list():
    """获取所有用户列表"""
    all_data = load_all_user_data()
    return list(all_data.keys())

def create_user(user_id):
    """创建新用户"""
    if not user_id or user_id.strip() == "":
        return False, "用户名不能为空"
    
    user_id = user_id.strip()
    
    # 检查用户名是否已存在
    all_data = load_all_user_data()
    if user_id in all_data:
        return False, "用户名已存在"
    
    # 创建新用户
    all_data[user_id] = []
    save_all_user_data(all_data)
    return True, "用户创建成功"

def get_all_ingredients(user_id="default"):
    """获取指定用户所有菜谱中的食材列表，按拼音首字母分组"""
    recipes = load_recipes(user_id)
    all_ingredients = set()
    
    for recipe in recipes:
        for ingredient in recipe['ingredients']:
            # 简单处理食材名称，去掉数量等信息
            ingredient_name = ingredient.strip()
            
            # 尝试提取主要食材名称（去掉数量、单位等）
            # 例如："五花肉 500g" -> "五花肉"
            for keyword in ['猪肉', '牛肉', '羊肉', '鸡肉', '鸭肉', '鱼肉', '虾', '蟹', '五花肉', '里脊肉', '排骨',
                          '白菜', '萝卜', '土豆', '茄子', '西红柿', '黄瓜', '丝瓜', '冬瓜', '南瓜', '胡萝卜',
                          '豆腐', '豆角', '青椒', '红椒', '洋葱', '大蒜', '生姜', '葱', '香菜', '菠菜', '韭菜',
                          '米饭', '面条', '饺子', '包子', '馒头', '鸡蛋', '牛奶', '芝麻', '花生', '核桃']:
                if keyword in ingredient_name:
                    all_ingredients.add(keyword)
                    break
            else:
                # 如果没有匹配到关键词，就使用原始名称（去掉数量）
                import re
                # 去掉常见的数量单位
                clean_name = re.sub(r'\d+[克斤两袋个只条颗粒勺汤匙茶匙毫升升杯碗盘].*', '', ingredient_name).strip()
                if clean_name and len(clean_name) > 1:
                    all_ingredients.add(clean_name)
    
    # 按拼音首字母分组
    grouped_ingredients = {}
    
    # 拼音首字母映射（常用食材）
    pinyin_map = {
        # A组
        
        # B组
        '白菜': 'B', '包子': 'B', '菠菜': 'B', '白萝卜': 'B', '白米': 'B', '白糖': 'B', '蚌肉': 'B',
        
        # C组
        '葱': 'C', '蛏子': 'C', '菜花': 'C', '菜心': 'C', '草鱼': 'C', '草莓': 'C', '醋': 'C',
        
        # D组
        '豆腐': 'D', '豆角': 'D', '大蒜': 'D', '冬瓜': 'D', '大米': 'D', '蛋': 'D', '冬笋': 'D',
        
        # E组
        
        # F组
        '番茄': 'F', '肥肉': 'F', '粉丝': 'F', '蜂蜜': 'F',
        
        # G组
        '龚菜': 'G', '狗肉': 'G', '桂花': 'G', '干菜': 'G',
        
        # H组
        '胡萝卜': 'H', '花生': 'H', '红椒': 'H', '核桃': 'H', '黄瓜': 'H', '海带': 'H', '韭黄': 'H',
        
        # J组
        '鸡蛋': 'J', '鸡肉': 'J', '韭菜': 'J', '饺子': 'J', '金针菇': 'J', '尖椒': 'J', '酒': 'J',
        
        # K组
        '口蘑': 'K', '苦瓜': 'K', '烤鸭': 'K',
        
        # L组
        '萝卜': 'L', '里脊肉': 'L', '莲藕': 'L', '辣椒': 'L', '绿豆': 'L', '鲤鱼': 'L',
        
        # M组
        '面条': 'M', '米饭': 'M', '馒头': 'M', '蘑菇': 'M', '木耳': 'M', '毛豆': 'M',
        
        # N组
        '牛肉': 'N', '南瓜': 'N', '牛奶': 'N', '糯米': 'N', '柠檬': 'N',
        
        # P组
        '排骨': 'P', '苹果': 'P', '啤酒': 'P',
        
        # Q组
        '茄子': 'Q', '青椒': 'Q', '青菜': 'Q', '芹菜': 'Q', '青豆': 'Q',
        
        # R组
        '肉': 'R', '热狗': 'R',
        
        # S组
        '生姜': 'S', '丝瓜': 'S', '蒜': 'S', '笋': 'S', '酸菜': 'S', '山药': 'S',
        
        # T组
        '土豆': 'T', '糖': 'T', '豚肉': 'T', '桃': 'T',
        
        # W组
        '五花肉': 'W', '豌豆': 'W', '乌鸡': 'W', '梧桐': 'W',
        
        # X组
        '西红柿': 'X', '香菜': 'X', '蟹': 'X', '虾': 'X', '香菇': 'X', '小白菜': 'X',
        
        # Y组
        '洋葱': 'Y', '鸭肉': 'Y', '羊肉': 'Y', '鱼肉': 'Y', '油菜': 'Y', '玉米': 'Y',
        
        # Z组
        '猪肉': 'Z', '竹笋': 'Z', '芝麻': 'Z', '紫菜': 'Z', '枣': 'Z'
    }
    
    for ingredient in sorted(all_ingredients):
        # 获取拼音首字母
        first_letter = pinyin_map.get(ingredient, None)
        
        # 如果不在映射中，尝试从食材名称中找到映射的关键词
        if first_letter is None:
            for mapped_ingredient, letter in pinyin_map.items():
                if mapped_ingredient in ingredient:
                    first_letter = letter
                    break
        
        # 如果仍然没有找到，使用默认分组
        if first_letter is None:
            char_code = ord(ingredient[0])
            if 0x4e00 <= char_code <= 0x9fff:  # 中文字符范围
                # 使用更精确的Unicode分组
                if char_code <= 0x4f9d: first_letter = 'A-D'
                elif char_code <= 0x535a: first_letter = 'E-H'
                elif char_code <= 0x5965: first_letter = 'I-L'
                elif char_code <= 0x5d14: first_letter = 'M-P'
                elif char_code <= 0x658c: first_letter = 'Q-S'
                elif char_code <= 0x6c14: first_letter = 'T-W'
                else: first_letter = 'X-Z'
            else:
                # 英文或其他字符
                first_letter = ingredient[0].upper() if ingredient[0].isalpha() else 'OTHER'
        
        if first_letter not in grouped_ingredients:
            grouped_ingredients[first_letter] = []
        grouped_ingredients[first_letter].append(ingredient)
    
    # 对每组内的食材排序
    for letter in grouped_ingredients:
        grouped_ingredients[letter].sort()
    
    return grouped_ingredients

def analyze_recipe_seasons_async(recipe_id, recipe_name, ingredients):
    """异步分析菜谱的适宜季节和养生功效"""
    print(f"🔄 开始异步分析菜谱: {recipe_name} (ID: {recipe_id})")
    
    # 检查客户端是否可用
    if client is None:
        print("DeepSeek客户端不可用，使用备用分析")
        seasons = get_fallback_seasons(recipe_name, ingredients)
        wellness_info = {
            'solar_term': '四季皆宜',
            'seasonal_feature': '四季家常菜',
            'tcm_theory': '根据食材特性进行基础分析',
            'health_tips': '请根据个人体质和季节变化适量食用'
        }
        update_recipe_analysis(recipe_id, seasons, wellness_info)
        return
    
    try:
        # 构建专业中医养生提示词
        ingredients_text = "、".join(ingredients)
        
        prompt = f"""用户将提供一道中式菜肴或完整菜谱。请你执行以下任务：

1. 判断菜肴适合的节气与季节：依据食材的特性、气候变化、四时调养原则，分析这道菜最适合在什么时节或节气食用；

2. 标注时令菜品：判断这道菜是否为时令菜（当季食材制作），如春季时令菜、夏季时令菜等，或者是四季皆宜的家常菜；

3. 结合《黄帝内经》的四时养生理论，说明为什么这个时节适合吃这道菜，例如调和五脏、养阴清热、健脾祛湿等；

输出格式如下：

【菜名】：xxx
【推荐节气】：xxx（属于xxx季节）
【时令特色】：xxx时令菜/四季家常菜（说明这道菜的时令特色）
【黄帝内经解读】："xxx"，出自《黄帝内经》或依据其养生理念。
【养生提示】：xxx

现在请分析：
菜名：{recipe_name}
食材：{ingredients_text}"""

        print(f"准备分析菜谱: {recipe_name}")  # 调试用
        
        # 调用DeepSeek Chat模型（reasoner模型有问题，改用chat模型）
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位精通中医养生和《黄帝内经》的专家，擅长分析菜肴的季节适宜性和养生功效。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.3,
            max_tokens=500
        )
        
        ai_result = response.choices[0].message.content.strip()
        print(f"AI分析结果: {ai_result}")  # 调试用
        
        # 解析AI返回的结果
        seasons, wellness_info = parse_ai_analysis(ai_result)
        print(f"解析得到季节: {seasons}")  # 调试用
        
        # 更新菜谱分析结果
        update_recipe_analysis(recipe_id, seasons, wellness_info)
        print(f"✅ 异步分析完成: {recipe_name}")
        
    except Exception as e:
        print(f"DeepSeek Chat分析出错: {e}")
        # 使用备用分析方式
        seasons = get_fallback_seasons(recipe_name, ingredients)
        wellness_info = {
            'solar_term': '四季皆宜',
            'seasonal_feature': '四季家常菜',
            'tcm_theory': '根据食材特性进行基础分析',
            'health_tips': '请根据个人体质和季节变化适量食用'
        }
        update_recipe_analysis(recipe_id, seasons, wellness_info)
        print(f"⚠️ 使用备用分析: {recipe_name}")

def update_recipe_analysis(recipe_id, seasons, wellness_info):
    """更新菜谱的分析结果"""
    try:
        recipes = load_recipes()
        
        # 查找对应的菜谱
        for recipe in recipes:
            if recipe['id'] == recipe_id:
                recipe['seasons'] = seasons
                recipe['wellness_info'] = wellness_info
                break
        
        # 保存更新后的数据
        save_recipes(recipes)
        print(f"📝 已更新菜谱分析结果: {recipe_id}")
        
    except Exception as e:
        print(f"❌ 更新菜谱分析结果失败: {e}")

def analyze_recipe_seasons(recipe_name, ingredients):
    """使用DeepSeek Chat模型分析菜谱的适宜季节和养生功效（同步版本，用于批量分析）"""
    # 检查客户端是否可用
    if client is None:
        print("DeepSeek客户端不可用，使用备用分析")
        seasons = get_fallback_seasons(recipe_name, ingredients)
        wellness_info = {
            'solar_term': '四季皆宜',
            'seasonal_feature': '四季家常菜',
            'tcm_theory': '根据食材特性进行基础分析',
            'health_tips': '请根据个人体质和季节变化适量食用'
        }
        return seasons, wellness_info
    
    try:
        # 构建专业中医养生提示词
        ingredients_text = "、".join(ingredients)
        
        prompt = f"""用户将提供一道中式菜肴或完整菜谱。请你执行以下任务：

1. 判断菜肴适合的节气与季节：依据食材的特性、气候变化、四时调养原则，分析这道菜最适合在什么时节或节气食用；

2. 标注时令菜品：判断这道菜是否为时令菜（当季食材制作），如春季时令菜、夏季时令菜等，或者是四季皆宜的家常菜；

3. 结合《黄帝内经》的四时养生理论，说明为什么这个时节适合吃这道菜，例如调和五脏、养阴清热、健脾祛湿等；

输出格式如下：

【菜名】：xxx
【推荐节气】：xxx（属于xxx季节）
【时令特色】：xxx时令菜/四季家常菜（说明这道菜的时令特色）
【黄帝内经解读】："xxx"，出自《黄帝内经》或依据其养生理念。
【养生提示】：xxx

现在请分析：
菜名：{recipe_name}
食材：{ingredients_text}"""

        print(f"开始分析菜谱：{recipe_name}")  # 调试用
        
        # 调用DeepSeek Chat模型（reasoner模型有问题，改用chat模型）
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位精通中医养生和《黄帝内经》的专家，擅长分析菜肴的季节适宜性和养生功效。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.3,
            max_tokens=500
        )
        
        ai_analysis = response.choices[0].message.content.strip()
        print(f"AI分析结果: {ai_analysis}")  # 调试用
        
        if not ai_analysis:
            print("AI返回空结果，使用备用方式")
            raise Exception("AI返回空结果")
        
        # 解析AI返回的季节信息和养生分析
        seasons, wellness_info = parse_ai_analysis(ai_analysis)
        print(f"解析得到季节: {seasons}")  # 调试用
        
        return seasons, wellness_info
        
    except Exception as e:
        print(f"DeepSeek Chat分析出错: {e}")
        # 使用备用分析方式
        seasons = get_fallback_seasons(recipe_name, ingredients)
        wellness_info = {
            'solar_term': '四季皆宜',
            'seasonal_feature': '四季家常菜',
            'tcm_theory': '根据食材特性进行基础分析',
            'health_tips': '请根据个人体质和季节变化适量食用'
        }
        print(f"使用备用分析，季节: {seasons}")  # 调试用
        return seasons, wellness_info

def parse_ai_analysis(ai_text):
    """解析AI返回的中医养生分析结果"""
    seasons = []
    wellness_info = {
        'solar_term': '',
        'seasonal_feature': '',
        'tcm_theory': '',
        'health_tips': ''
    }
    
    try:
        # 使用正则表达式更准确地解析多行内容
        import re
        
        # 提取推荐节气
        solar_term_match = re.search(r'【推荐节气】[：:]\s*([^\n【]+)', ai_text, re.DOTALL)
        if solar_term_match:
            solar_term_text = solar_term_match.group(1).strip()
            wellness_info['solar_term'] = solar_term_text
            
            # 从节气文本中提取季节
            if '春' in solar_term_text:
                seasons.append('春季')
            if '夏' in solar_term_text or '长夏' in solar_term_text:
                seasons.append('夏季')
            if '秋' in solar_term_text:
                seasons.append('秋季')
            if '冬' in solar_term_text:
                seasons.append('冬季')
        
        # 提取时令特色
        seasonal_feature_match = re.search(r'【时令特色】[：:]\s*([^\n【]+)', ai_text, re.DOTALL)
        if seasonal_feature_match:
            seasonal_feature_text = seasonal_feature_match.group(1).strip()
            wellness_info['seasonal_feature'] = seasonal_feature_text
        
        # 提取黄帝内经解读（可能跨多行）
        tcm_match = re.search(r'【黄帝内经解读】[：:]\s*([^【]*?)(?=【|$)', ai_text, re.DOTALL)
        if tcm_match:
            tcm_text = tcm_match.group(1).strip()
            # 清理多余的换行和空格
            tcm_text = re.sub(r'\s+', ' ', tcm_text)
            wellness_info['tcm_theory'] = tcm_text
        
        # 提取养生提示（可能跨多行）
        health_match = re.search(r'【养生提示】[：:]\s*([^【]*?)(?=【|$)', ai_text, re.DOTALL)
        if health_match:
            health_text = health_match.group(1).strip()
            # 清理多余的换行和空格
            health_text = re.sub(r'\s+', ' ', health_text)
            wellness_info['health_tips'] = health_text
        
        # 如果没有解析到季节，尝试从整个文本中提取
        if not seasons:
            if '春' in ai_text:
                seasons.append('春季')
            if '夏' in ai_text or '长夏' in ai_text:
                seasons.append('夏季')
            if '秋' in ai_text:
                seasons.append('秋季')
            if '冬' in ai_text:
                seasons.append('冬季')
        
        # 默认值处理
        if not seasons:
            seasons = ['四季']
        
        if not wellness_info['solar_term']:
            wellness_info['solar_term'] = '四季皆宜'
        if not wellness_info['seasonal_feature']:
            wellness_info['seasonal_feature'] = '四季家常菜'
        if not wellness_info['tcm_theory']:
            wellness_info['tcm_theory'] = 'AI分析中医养生理论'
        if not wellness_info['health_tips']:
            wellness_info['health_tips'] = '请根据个人体质适量食用'
            
        print(f"🔍 解析结果 - 季节: {seasons}, 节气: {wellness_info['solar_term']}")  # 调试用
            
    except Exception as e:
        print(f"解析AI分析结果出错: {e}")
        seasons = ['四季']
    
    return seasons, wellness_info

def get_fallback_seasons(recipe_name, ingredients):
    """当API不可用时的备用季节判断逻辑"""
    # 简单的基于关键词的季节判断
    all_text = (recipe_name + " " + " ".join(ingredients)).lower()
    
    # 季节性食材关键词
    spring_keywords = ["春笋", "韭菜", "菠菜", "春菜", "嫩芽", "鲜嫩"]
    summer_keywords = ["西瓜", "冬瓜", "丝瓜", "黄瓜", "凉拌", "冷面", "绿豆", "苦瓜"]
    autumn_keywords = ["萝卜", "莲藕", "板栗", "柿子", "南瓜", "秋葵", "蟹"]
    winter_keywords = ["白菜", "炖", "煲汤", "火锅", "羊肉", "牛肉", "萝卜", "山药"]
    
    seasons = []
    
    # 检查各季节关键词
    if any(keyword in all_text for keyword in spring_keywords):
        seasons.append("春季")
    if any(keyword in all_text for keyword in summer_keywords):
        seasons.append("夏季")
    if any(keyword in all_text for keyword in autumn_keywords):
        seasons.append("秋季")
    if any(keyword in all_text for keyword in winter_keywords):
        seasons.append("冬季")
    
    # 如果没有匹配到或匹配到多个，默认为四季
    return seasons if len(seasons) == 1 else ["四季"]

def get_current_season():
    """获取当前季节"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "春季"
    elif month in [6, 7, 8]:
        return "夏季"
    elif month in [9, 10, 11]:
        return "秋季"
    else:
        return "冬季"

@app.route('/login')
def login():
    """用户登录/注册页面"""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    """处理用户登录/注册"""
    action = request.form.get('action')
    user_id = request.form.get('user_id', '').strip()
    
    if not user_id:
        flash('请输入用户名！', 'error')
        return redirect(url_for('login'))
    
    if action == 'register':
        success, message = create_user(user_id)
        if success:
            flash(f'用户 {user_id} 创建成功！', 'success')
        else:
            flash(message, 'error')
            return redirect(url_for('login'))
    
    # 检查用户是否存在
    user_list = get_user_list()
    if user_id not in user_list:
        flash('用户不存在，请先注册！', 'error')
        return redirect(url_for('login'))
    
    # 登录成功，重定向到主页
    return redirect(url_for('index', user_id=user_id))

@app.route('/')
@app.route('/user/<user_id>')
def index(user_id=None):
    """首页 - 显示所有菜谱"""
    # 如果没有指定用户ID，重定向到登录页
    if user_id is None:
        return redirect(url_for('login'))
    
    recipes = load_recipes(user_id)
    search_query = request.args.get('search', '')
    season_filter = request.args.get('season', '')
    
    if search_query:
        # 搜索功能
        filtered_recipes = []
        for recipe in recipes:
            if (search_query.lower() in recipe['name'].lower() or 
                search_query.lower() in ' '.join(recipe['ingredients']).lower()):
                filtered_recipes.append(recipe)
        recipes = filtered_recipes
    
    if season_filter:
        # 季节筛选
        filtered_recipes = []
        for recipe in recipes:
            recipe_seasons = recipe.get('seasons', ['四季'])
            if season_filter in recipe_seasons or '四季' in recipe_seasons:
                filtered_recipes.append(recipe)
        recipes = filtered_recipes
    
    # 获取当前季节（用于高亮显示）
    current_season = get_current_season()
    
    return render_template('index.html', 
                         recipes=recipes, 
                         search_query=search_query,
                         season_filter=season_filter,
                         current_season=current_season,
                         user_id=user_id)

@app.route('/user/<user_id>/add', methods=['GET', 'POST'])
def add_recipe(user_id):
    """添加新菜谱"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        steps = request.form.get('steps', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name or not ingredients:
            flash('菜名和材料是必填项！', 'error')
            return render_template('add_recipe.html', user_id=user_id)
        
        # 处理材料（按行分割）
        ingredients_list = [ing.strip() for ing in ingredients.split('\n') if ing.strip()]
        
        # 处理制作步骤（按行分割）
        steps_list = [step.strip() for step in steps.split('\n') if step.strip()]
        
        # 创建新菜谱（先使用默认值，后续异步更新）
        recipe_id = int(datetime.now().timestamp() * 1000)  # 使用时间戳作为ID
        recipe = {
            'id': recipe_id,
            'name': name,
            'ingredients': ingredients_list,
            'steps': steps_list,
            'notes': notes,
            'seasons': ['分析中...'],  # 临时状态
            'wellness_info': {
                'solar_term': '分析中...',
                'seasonal_feature': '四季家常菜',
                'tcm_theory': 'AI正在分析中医养生理论，请稍后查看详情页面...',
                'health_tips': '分析完成后将显示个性化养生建议'
            },
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 立即保存菜谱
        recipes = load_recipes(user_id)
        recipes.append(recipe)
        save_recipes(recipes, user_id)
        
        # 启动后台异步分析
        analysis_thread = threading.Thread(
            target=analyze_recipe_seasons_async,
            args=(recipe_id, name, ingredients_list, user_id),
            daemon=True
        )
        analysis_thread.start()
        
        flash(f'菜谱《{name}》添加成功！🍽️ 中医养生分析正在后台进行中，请稍后查看详情页面获取完整分析结果。', 'success')
        return redirect(url_for('index', user_id=user_id))
    
    return render_template('add_recipe.html', user_id=user_id)

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    """查看单个菜谱详情"""
    recipes = load_recipes()
    recipe = None
    
    for r in recipes:
        if r['id'] == recipe_id:
            recipe = r
            break
    
    if not recipe:
        flash('菜谱不存在！', 'error')
        return redirect(url_for('index'))
    
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/random')
def random_recipe():
    """随机推荐菜谱"""
    recipes = load_recipes()
    
    if not recipes:
        flash('还没有添加任何菜谱！', 'info')
        return redirect(url_for('index'))
    
    random_recipe = random.choice(recipes)
    return redirect(url_for('view_recipe', recipe_id=random_recipe['id']))

@app.route('/seasonal')
def seasonal_recommendation():
    """应季菜谱推荐"""
    recipes = load_recipes()
    current_season = get_current_season()
    
    # 筛选当前季节的菜谱
    seasonal_recipes = []
    for recipe in recipes:
        recipe_seasons = recipe.get('seasons', ['四季'])
        if current_season in recipe_seasons or '四季' in recipe_seasons:
            seasonal_recipes.append(recipe)
    
    if not seasonal_recipes:
        flash(f'还没有适合{current_season}的菜谱！', 'info')
        return redirect(url_for('index'))
    
    # 随机选择一个应季菜谱
    random_seasonal = random.choice(seasonal_recipes)
    flash(f'🌸 为您推荐{current_season}应季菜谱！', 'success')
    return redirect(url_for('view_recipe', recipe_id=random_seasonal['id']))

@app.route('/batch_analyze_seasons', methods=['POST'])
def batch_analyze_seasons():
    """批量分析现有菜谱的季节和养生功效（管理功能）"""
    recipes = load_recipes()
    updated_count = 0
    
    for recipe in recipes:
        if 'seasons' not in recipe or 'wellness_info' not in recipe:
            try:
                # 为没有季节信息的菜谱分析季节和养生功效
                seasons, wellness_info = analyze_recipe_seasons(recipe['name'], recipe['ingredients'])
                recipe['seasons'] = seasons
                recipe['wellness_info'] = wellness_info
                updated_count += 1
            except:
                # 如果AI分析失败，使用备用方式
                seasons = get_fallback_seasons(recipe['name'], recipe['ingredients'])
                wellness_info = {
                    'solar_term': '四季皆宜',
                    'seasonal_feature': '四季家常菜',
                    'tcm_theory': '根据食材特性进行基础分析',
                    'health_tips': '请根据个人体质和季节变化适量食用'
                }
                recipe['seasons'] = seasons
                recipe['wellness_info'] = wellness_info
                updated_count += 1
    
    if updated_count > 0:
        save_recipes(recipes)
        flash(f'成功为 {updated_count} 个菜谱分析了季节和养生信息！🎉', 'success')
    else:
        flash('所有菜谱都已有完整的季节和养生信息！', 'info')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    """删除菜谱"""
    recipes = load_recipes()
    
    for i, recipe in enumerate(recipes):
        if recipe['id'] == recipe_id:
            deleted_name = recipe['name']
            del recipes[i]
            save_recipes(recipes)
            flash(f'菜谱《{deleted_name}》已删除！', 'success')
            break
    else:
        flash('菜谱不存在！', 'error')
    
    return redirect(url_for('index'))

@app.route('/ingredients', methods=['GET', 'POST'])
def ingredients_filter():
    """按食材筛选菜谱"""
    grouped_ingredients = get_all_ingredients()
    filtered_recipes = []
    selected_ingredients = []
    custom_ingredients = []
    
    if request.method == 'POST':
        # 获取选中的食材
        selected_ingredients = request.form.getlist('ingredients')
        
        # 获取手动输入的食材
        custom_input = request.form.get('custom_ingredients', '').strip()
        if custom_input:
            # 按逗号或空格分割自定义食材
            import re
            custom_ingredients = [ing.strip() for ing in re.split(r'[,，\s]+', custom_input) if ing.strip()]
        
        # 合并所有选中的食材
        all_selected = selected_ingredients + custom_ingredients
        
        if all_selected:
            recipes = load_recipes()
            
            # 筛选包含所选食材的菜谱
            for recipe in recipes:
                recipe_ingredients_text = ' '.join(recipe['ingredients']).lower()
                
                # 检查是否包含所选食材
                match_count = 0
                matched_ingredients = []
                for ingredient in all_selected:
                    if ingredient.lower() in recipe_ingredients_text:
                        match_count += 1
                        matched_ingredients.append(ingredient)
                
                # 如果包含至少一个选中的食材就显示
                if match_count > 0:
                    # 添加匹配度信息
                    recipe_copy = recipe.copy()
                    recipe_copy['match_count'] = match_count
                    recipe_copy['match_percentage'] = round((match_count / len(all_selected)) * 100, 1)
                    recipe_copy['matched_ingredients'] = matched_ingredients
                    filtered_recipes.append(recipe_copy)
            
            # 按匹配度排序（匹配度高的在前面）
            filtered_recipes.sort(key=lambda x: x['match_count'], reverse=True)
        
        # 保持选中状态
        selected_ingredients = all_selected
    
    return render_template('ingredients_filter.html', 
                         grouped_ingredients=grouped_ingredients,
                         selected_ingredients=selected_ingredients,
                         custom_ingredients=custom_ingredients,
                         filtered_recipes=filtered_recipes)

@app.route('/api/recipes')
def api_recipes():
    """API接口 - 获取所有菜谱"""
    recipes = load_recipes()
    return jsonify(recipes)

@app.route('/api/ingredients')
def api_ingredients():
    """API接口 - 获取所有食材"""
    ingredients = get_all_ingredients()
    return jsonify(ingredients)

if __name__ == '__main__':
    # 生产环境配置
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 