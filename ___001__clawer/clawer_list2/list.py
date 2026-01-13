import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from urllib.parse import urljoin

def crawl_tcm_herbs():
    """
    爬取中药大全网站，提取中药名称和链接
    """
    url = "https://zhongyibaike.com/wiki/%E4%B8%AD%E8%8D%AF%E5%A4%A7%E5%85%A8"
    
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    try:
        # 发送请求
        print("正在获取网页内容...")
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'  # 设置编码
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 存储中药名称和链接
        herbs = []
        base_url = "https://zhongyibaike.com"
        
        # 排除的文本（导航链接、分类标题等）
        excluded_texts = {
            '中医百科', '中药大全', 'Search', 'Login', '关于我们', '版权声明', '服务条款',
            '中医理论', '中医保健', '中医食疗', '中医方剂', '疾病大全', '中医书籍',
            '解表药', '泻下药', '和解药', '清热药', '温里药', '补益药', '固涩药',
            '安神药', '开窍药', '理气药', '理血药', '治风药', '治燥药', '祛湿药',
            '祛痰药', '消食药', '驱虫药', '涌吐药', '痈疡药',
            '发散风寒药', '发散风热药', '清热泻火药', '清热燥湿药', '清热解毒药',
            '清热凉血药', '清虚热药', '攻下药', '润下药', '峻下逐水药',
            '温化寒痰药', '清化热痰药', '止咳平喘药', '化湿药', '利水渗湿药',
            '温里药', '理气药', '消食药', '驱虫药', '止血药', '活血化瘀药',
            '补气药', '补阳药', '补血药', '补阴药', '固表止汗药', '涩肠止泻药',
            '涩精缩尿止带药', '涌吐药', '攻毒杀虫止痒药', '拔毒化腐生肌药', '下乳药'
        }
        
        # 优先查找主内容区域（article标签）
        main_article = soup.find('article', class_=lambda x: x and 'article' in str(x).lower())
        if not main_article:
            # 如果没有article，查找content区域
            main_article = soup.find('div', id='content') or soup.find('div', class_='content')
        
        if main_article:
            print("找到主内容区域，开始提取中药链接...")
            # 在主内容区域内查找所有/wiki/链接
            links = main_article.find_all('a', href=lambda x: x and '/wiki/' in x)
            print(f"在主内容区域找到 {len(links)} 个/wiki/链接")
            
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                # 过滤条件：
                # 1. 文本不为空
                # 2. 是wiki链接
                # 3. 不在排除列表中
                # 4. 文本长度合理（中药名称通常不会太长，也不会太短）
                if (text and 
                    '/wiki/' in href and 
                    text not in excluded_texts and
                    1 <= len(text) <= 20 and  # 中药名称长度通常在1-20个字符
                    not text.startswith('http') and  # 排除URL文本
                    '#' not in href):  # 排除锚点链接
                    
                    # 构建完整URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(base_url, href)
                    
                    # 避免重复
                    if (text, full_url) not in herbs:
                        herbs.append((text, full_url))
        else:
            print("未找到主内容区域，使用备用方法...")
            # 备用方法：查找所有列表项中的链接
            list_items = soup.find_all('li')
            for li in list_items:
                link = li.find('a', href=True)
                if link:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if (text and 
                        '/wiki/' in href and 
                        text not in excluded_texts and
                        1 <= len(text) <= 20 and
                        '#' not in href):
                        
                        if href.startswith('http'):
                            full_url = href
                        else:
                            full_url = urljoin(base_url, href)
                        
                        if (text, full_url) not in herbs:
                            herbs.append((text, full_url))
        
        if herbs:
            # 去重（保持原始顺序，不排序）
            seen = set()
            unique_herbs = []
            for herb in herbs:
                if herb not in seen:
                    seen.add(herb)
                    unique_herbs.append(herb)
            
            herbs = unique_herbs
            
            # 创建DataFrame
            df = pd.DataFrame(herbs, columns=['中药名称', '链接'])
            
            # 保存到Excel
            output_file = os.path.join(os.path.dirname(__file__), '中药大全列表.xlsx')
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            print(f"\n成功爬取 {len(herbs)} 个中药")
            print(f"结果已保存到: {output_file}")
            
            # 显示前几条数据
            print("\n前20条数据预览:")
            print(df.head(20).to_string(index=False))
            
            # 验证是否包含常见中药
            common_herbs = ['麻黄', '桂枝', '葛根', '柴胡', '黄芩', '黄连', '人参', '当归']
            print("\n验证常见中药:")
            for ch in common_herbs:
                found = df[df['中药名称'] == ch]
                if len(found) > 0:
                    print(f"  [找到] {ch}")
                else:
                    print(f"  [未找到] {ch}")
        else:
            print("未找到任何中药数据")
            print("提示：可能需要检查网页结构或网络连接")
            
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    crawl_tcm_herbs()
