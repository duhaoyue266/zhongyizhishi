import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re
from urllib.parse import urljoin
from tqdm import tqdm

def sanitize_filename(filename):
    """
    清理文件名，移除Windows不允许的字符
    """
    # Windows不允许的字符: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    # 移除首尾空格和点
    filename = filename.strip(' .')
    # 限制文件名长度（Windows最大255字符，但为了安全限制为200）
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def format_text_content(text):
    """
    格式化文本内容，合并不必要的换行
    """
    # 先按换行分割
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return ""
    
    formatted_lines = []
    i = 0
    
    # 定义标题关键词
    title_keywords = ['的药方', '的功效', '出处', '组成', '解释', '主治', '用法', '功效', '方解', '注意事项', '禁忌', '附方']
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 判断是否是标题
        is_title = False
        for keyword in title_keywords:
            if line == keyword or line.endswith(keyword):
                is_title = True
                break
        
        # 如果是标题，单独一行，前后加空行
        if is_title or (len(line) <= 15 and not any(c in line for c in '，。；：')):
            # 检查是否是纯标题（不包含标点）
            if is_title or (len(line) <= 10 and not re.search(r'[，。；：、]', line)):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
                i += 1
                continue
        
        # 合并短行和标点符号行
        merged_parts = []
        current_part = line
        
        i += 1
        # 继续合并后续的短行
        while i < len(lines):
            next_line = lines[i].strip()
            
            if not next_line:
                break
            
            # 检查下一行是否是标题
            next_is_title = False
            for keyword in title_keywords:
                if next_line == keyword or next_line.endswith(keyword):
                    next_is_title = True
                    break
            
            if next_is_title or (len(next_line) <= 10 and not re.search(r'[，。；：、]', next_line)):
                # 如果下一行可能是新标题，停止合并
                if next_is_title:
                    break
            
            # 如果下一行是单独的标点符号
            if next_line in ['、', '，', '。', '；', '：', ',', '.', ';', ':', '）', ')', '（', '(']:
                current_part += next_line
                i += 1
                continue
            
            # 如果下一行很短（1-5个字符），尝试合并
            if len(next_line) <= 5:
                # 检查是否是数字+单位
                if re.match(r'^\d+[克枚毫升升个]', next_line):
                    current_part += ' ' + next_line
                # 检查是否是单独的标点
                elif next_line in ['、', '，', '。', '；', '：']:
                    current_part += next_line
                # 其他短行，直接合并（可能是被拆分的词）
                else:
                    current_part += next_line
                i += 1
                continue
            
            # 如果当前部分已经比较长，可能是段落结束
            if len(current_part) > 80:
                merged_parts.append(current_part)
                current_part = next_line
                i += 1
                # 如果下一行也很长，可能是新段落
                if len(next_line) > 50:
                    break
                continue
            
            # 合并：如果当前部分以标点结尾，直接连接下一行
            if current_part and current_part[-1] in ['、', '，', '。', '；', '：', ',', '.', ';', ':', '）', ')']:
                current_part += next_line
            # 如果当前部分以中文/数字结尾，下一行以中文/数字开头，加空格
            elif (current_part and next_line and
                  (('\u4e00' <= current_part[-1] <= '\u9fff') or current_part[-1].isdigit()) and
                  (('\u4e00' <= next_line[0] <= '\u9fff') or next_line[0].isdigit())):
                current_part += ' ' + next_line
            else:
                current_part += next_line
            
            i += 1
            
            # 如果合并后太长，停止
            if len(current_part) > 150:
                break
        
        if current_part:
            merged_parts.append(current_part)
        
        # 添加合并后的内容
        for part in merged_parts:
            formatted_lines.append(part)
        
        # 在段落之间添加空行
        if i < len(lines):
            formatted_lines.append('')
    
    # 清理多余的空行（连续超过2个空行）
    result = []
    empty_count = 0
    for line in formatted_lines:
        if line == '':
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            empty_count = 0
            result.append(line)
    
    return '\n'.join(result)

def extract_text_content(soup):
    """
    从BeautifulSoup对象中提取文本内容，并进行格式化
    """
    # 移除script和style标签
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # 查找主内容区域
    main_content = soup.find('article') or soup.find('div', id='content') or soup.find('div', class_='content') or soup.find('main')
    
    if main_content:
        # 提取文本，保留换行信息
        text = main_content.get_text(separator='\n', strip=True)
    else:
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
    
    # 格式化文本
    formatted_text = format_text_content(text)
    
    return formatted_text

def crawl_formula_details():
    """
    遍历中医方剂列表，爬取每个方剂的详情并保存为txt文件
    """
    # 读取Excel文件
    excel_file = os.path.join(os.path.dirname(__file__), '中医方剂列表.xlsx')
    if not os.path.exists(excel_file):
        print(f"错误：找不到文件 {excel_file}")
        return
    
    print(f"正在读取 {excel_file}...")
    df = pd.read_excel(excel_file)
    print(f"共找到 {len(df)} 个方剂")
    
    # 创建保存目录
    output_dir = os.path.join(os.path.dirname(__file__), '方剂详情')
    os.makedirs(output_dir, exist_ok=True)
    print(f"保存目录: {output_dir}\n")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    success_count = 0
    fail_count = 0
    failed_formulas = []
    
    # 使用tqdm创建进度条
    with tqdm(total=len(df), desc="爬取进度", unit="个") as pbar:
        # 遍历每个方剂
        for index, row in df.iterrows():
            formula_name = str(row['方剂名称']).strip()
            formula_url = str(row['链接']).strip()
            
            # 清理文件名
            safe_filename = sanitize_filename(formula_name)
            txt_file = os.path.join(output_dir, f"{safe_filename}.txt")
            
            # 更新进度条描述
            pbar.set_description(f"正在处理: {formula_name[:20]}")
            
            # 如果文件已存在，跳过
            if os.path.exists(txt_file):
                success_count += 1
                pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "已存在"})
                pbar.update(1)
                continue
            
            try:
                # 发送请求
                response = requests.get(formula_url, headers=headers, timeout=30)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    fail_count += 1
                    failed_formulas.append((formula_name, formula_url, f"状态码: {response.status_code}"))
                    pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "请求失败"})
                    pbar.update(1)
                    continue
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取文本内容
                text_content = extract_text_content(soup)
                
                if not text_content or len(text_content.strip()) < 10:
                    fail_count += 1
                    failed_formulas.append((formula_name, formula_url, "内容为空"))
                    pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "内容为空"})
                    pbar.update(1)
                    continue
                
                # 保存为txt文件
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"方剂名称: {formula_name}\n")
                    f.write(f"链接: {formula_url}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(text_content)
                
                success_count += 1
                pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "成功"})
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                fail_count += 1
                failed_formulas.append((formula_name, formula_url, str(e)))
                pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "请求异常"})
            except Exception as e:
                fail_count += 1
                failed_formulas.append((formula_name, formula_url, str(e)))
                pbar.set_postfix({"成功": success_count, "失败": fail_count, "状态": "处理异常"})
            
            # 更新进度条
            pbar.update(1)
    
    # 输出统计信息
    print("\n" + "=" * 80)
    print(f"爬取完成！")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    
    if failed_formulas:
        print(f"\n失败的方剂列表:")
        for name, url, error in failed_formulas[:10]:  # 只显示前10个
            print(f"  - {name}: {error}")
        if len(failed_formulas) > 10:
            print(f"  ... 还有 {len(failed_formulas) - 10} 个失败项")
        
        # 保存失败列表到文件
        fail_file = os.path.join(output_dir, '失败列表.txt')
        with open(fail_file, 'w', encoding='utf-8') as f:
            f.write("失败的方剂列表\n")
            f.write("=" * 80 + "\n\n")
            for name, url, error in failed_formulas:
                f.write(f"方剂名称: {name}\n")
                f.write(f"链接: {url}\n")
                f.write(f"错误: {error}\n")
                f.write("-" * 80 + "\n")
        print(f"\n失败列表已保存到: {fail_file}")

if __name__ == '__main__':
    crawl_formula_details()
