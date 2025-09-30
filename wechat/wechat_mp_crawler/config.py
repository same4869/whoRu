"""
微信公众号爬虫配置文件
"""

# 配置信息
CONFIG = {
    # 微信公众号API URL
    "url": "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&fakeid=MzA3Mzc3NzAyMA%3D%3D&query=&begin=0&count=4&type=9&need_author_name=1&fingerprint=7fa460cc35828e21181125fa128dfe24&token=471377576&lang=zh_CN&f=json&ajax=1",
    
    # 微信公众号管理后台Cookie
    "cookie": "appmsglist_action_3074209717=card; ptcz=c7407f6d63631fc9cdfba90d1ea9dbd7f9b0b7e9a1376919f8026b7fb87a786c; _qimei_q36=; ua_id=MD6qFCL0L2Pab0raAAAAAHVsbrj9QB3wYrJnEp0fDpM=; wxuin=28451059600290; mm_lang=zh_CN; pgv_pvid=503032172; ts_uid=854831996; RK=kQl119e/cw; _ga=GA1.2.1513529362.1741230636; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22195696ef8e6164-01c2afb93476d5a-26011a51-2073600-195696ef8e777b%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk1Njk2ZWY4ZTYxNjQtMDFjMmFmYjkzNDc2ZDVhLTI2MDExYTUxLTIwNzM2MDAtMTk1Njk2ZWY4ZTc3N2IifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22195696ef8e6164-01c2afb93476d5a-26011a51-2073600-195696ef8e777b%22%7D; mp_e6c1df805ebbda71bc8328f82d8e25e5_mixpanel=%7B%22distinct_id%22%3A%20%22999d6d247e5dc6ef7539593680f28b4a%22%2C%22%24device_id%22%3A%20%22194da5a4c33157-057df52cc294ff-26011b51-1fa400-194da5a4c33157%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%20%22999d6d247e5dc6ef7539593680f28b4a%22%2C%22%24search_engine%22%3A%20%22google%22%7D; _qimei_fingerprint=02b428df3da11053dadab53826a4ff4a; _qimei_uuid42=1971e0e360e1000189bf969f8a40840e900a38d0a1; _qimei_i_3=6dfc5a84915f03dec9c6ac66598d75b3a5e8adf4400a04d0bd8c2e5c2f9a273e35663f943989e29eaef3; _qimei_h38=; _qimei_i_1=5ce073fcec26; yyb_muid=39D28B687176638126DF9807700E6270; _gcl_au=1.1.1565952686.1758676194; rewardsn=; wxtokenkey=777; _clck=3074209717|1|fzq|0; uuid=6f4fac1c477a2e11288b338e450dbe60; rand_info=CAESIGtsyleHgfGvepWVXl7WLmO+vmz0o/JLe1hYmpXjT2mM; slave_bizuin=3074209717; data_bizuin=3074209717; bizuin=3074209717; data_ticket=S42No9bu6mBsaXNyYonjhz9WuuYRWipsjE8PJVYjL/SNPYooTUlg+qnjGRTkbXDK; slave_sid=RzZUbzhaT2t6N0VkTmhrN0tqOGVOMUJTdWdrYmR6WmpMbkFUa3VDTTZVNEZpaE82d2RrTWhkZXFpdmVLS29Yc3BQSDFMcTladW5mVF9lRDJmb0hOdTI3SFFXUUpVUFJoM19jR2VxTHlld1B2NXVadE9DMnU2cTZaQkVNWE9XeU9uOWhib3VDWlk0T3k4QmI2; slave_user=gh_3a87c17ec229; xid=d6f7ae14e4d8a81b7427a06e6d331bbc; _clsk=1pitn25|1759136313175|13|1|mp.weixin.qq.com/weheat-agent/payload/record",
    
    # 请求间隔时间范围（秒）
    "rate_limit_delay": (10.0, 30.0),
    
    # 默认输出文件名
    "default_output_file": "wechat_articles.csv",
}


def get_config():
    """获取配置"""
    return CONFIG.copy()