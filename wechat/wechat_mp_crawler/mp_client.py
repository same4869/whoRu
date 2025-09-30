"""
微信公众号文章爬取客户端
"""

import requests
import time
import csv
import json
import logging
import random
import os
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class WeChatMPClient:
    def __init__(self, cookie: str, rate_limit_delay: Tuple[float, float] = (10.0, 30.0)):
        """
        初始化微信公众号客户端
        
        Args:
            cookie: 微信公众号管理后台的cookie
            rate_limit_delay: 请求间隔时间范围（秒），格式为(最小值, 最大值)
        """
        self.cookie = cookie
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cookie': cookie,
            'Referer': 'https://mp.weixin.qq.com',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_random_delay(self) -> float:
        """获取随机延时时间"""
        min_delay, max_delay = self.rate_limit_delay
        return random.uniform(min_delay, max_delay)
    
    def parse_url_params(self, url: str) -> Dict[str, str]:
        """解析URL参数"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {k: v[0] if isinstance(v, list) and v else v for k, v in params.items()}
    
    def build_url(self, base_url: str, params: Dict[str, str]) -> str:
        """构建URL"""
        parsed = urlparse(base_url)
        query = urlencode(params)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))
    
    def get_articles_page(self, url: str, begin: int = 0, count: int = 5) -> Optional[Dict]:
        """
        获取单页文章列表（带无限重试）
        """
        retry_count = 0
        max_retries = 10000
        
        while retry_count <= max_retries:
            try:
                params = self.parse_url_params(url)
                params['begin'] = str(begin)
                params['count'] = str(min(count, 5))
                
                request_url = self.build_url(url, params)
                
                if retry_count == 0:
                    self.logger.info(f"获取文章: begin={begin}, count={count}")
                else:
                    self.logger.info(f"重试第 {retry_count} 次: begin={begin}, count={count}")
                
                response = self.session.get(request_url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # 检查响应状态
                if 'base_resp' in data:
                    ret_code = data['base_resp'].get('ret', 0)
                    if ret_code != 0:
                        err_msg = data['base_resp'].get('err_msg', '未知错误')
                        self.logger.error(f"API返回错误: {ret_code} - {err_msg}")
                        
                        # 频率控制错误等待10分钟
                        if ret_code == 200013 or 'freq control' in err_msg.lower():
                            self.logger.warning(f"遇到频率控制，等待10分钟后重试... (第{retry_count+1}次)")
                            time.sleep(600)
                        else:
                            # 其他错误递增等待
                            wait_time = min(60 * min(retry_count + 1, 10), 600)
                            self.logger.warning(f"API错误，等待 {wait_time} 秒后重试... (第{retry_count+1}次)")
                            time.sleep(wait_time)
                        
                        retry_count += 1
                        continue
                
                # 请求成功
                if retry_count > 0:
                    self.logger.info(f"重试成功！")
                return data
                
            except requests.RequestException as e:
                wait_time = min(30 * min(retry_count + 1, 10), 300)
                self.logger.warning(f"网络错误，等待 {wait_time} 秒后重试... (第{retry_count+1}次): {e}")
                time.sleep(wait_time)
                retry_count += 1
                continue
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON解析失败，等待60秒后重试... (第{retry_count+1}次): {e}")
                time.sleep(60)
                retry_count += 1
                continue
            except Exception as e:
                self.logger.warning(f"未知错误，等待120秒后重试... (第{retry_count+1}次): {e}")
                time.sleep(120)
                retry_count += 1
                continue
        
        self.logger.error(f"已重试 {max_retries} 次，仍然失败")
        return None
    
    def init_csv_file(self, filename: str):
        """初始化CSV文件"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['title', 'link', 'create_time', 'update_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            self.logger.info(f"已初始化CSV文件: {filename}")
        except Exception as e:
            self.logger.error(f"初始化CSV文件失败: {e}")
            raise
    
    def append_to_csv(self, articles, filename: str):
        """追加数据到CSV文件"""
        if not articles:
            return
        
        try:
            if not os.path.exists(filename):
                self.init_csv_file(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['title', 'link', 'create_time', 'update_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                for article in articles:
                    writer.writerow({
                        'title': article.get('title', ''),
                        'link': article.get('link', ''),
                        'create_time': article.get('create_time', ''),
                        'update_time': article.get('update_time', '')
                    })
            
            self.logger.info(f"已追加 {len(articles)} 篇文章到 {filename}")
        except Exception as e:
            self.logger.error(f"追加CSV文件失败: {e}")
    
    def crawl_and_save(self, url: str, output_file: str = "wechat_articles.csv", max_requests: Optional[int] = None) -> int:
        """
        爬取文章并实时保存到CSV
        """
        begin = 0
        count = 5
        request_count = 0
        total_articles = 0
        
        self.init_csv_file(output_file)
        self.logger.info("开始获取文章列表...")
        
        while True:
            # 检查请求限制
            if max_requests and request_count >= max_requests:
                self.logger.info(f"达到最大请求次数限制: {max_requests}")
                break
            
            # 获取数据
            data = self.get_articles_page(url, begin, count)
            if not data:
                self.logger.error("获取数据失败，停止请求")
                break
            
            app_msg_list = data.get('app_msg_list', [])
            if not app_msg_list:
                self.logger.info("没有更多文章，获取完成")
                break
            
            # 实时保存
            self.append_to_csv(app_msg_list, output_file)
            total_articles += len(app_msg_list)
            self.logger.info(f"已获取并保存 {len(app_msg_list)} 篇文章，总共 {total_articles} 篇")
            
            # 更新分页参数
            begin += count
            request_count += 1
            
            # 检查是否到末尾
            if len(app_msg_list) < count:
                self.logger.info("已获取所有文章")
                break
            
            # 随机延时
            delay = self.get_random_delay()
            self.logger.info(f"等待 {delay:.1f} 秒...")
            time.sleep(delay)
        
        self.logger.info(f"获取完成，总共 {total_articles} 篇文章已保存到 {output_file}")
        return total_articles