#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京东联盟商品清单拉取(dacu.net 每日自动化)
凭据从环境变量读取:JD_APP_KEY / JD_APP_SECRET(仓库内永远不出现明文)
输出:assets/data/deals-jd.json
"""
import os, sys, json, time, hashlib, urllib.request, urllib.parse, urllib.error

GATEWAY = 'https://api.jd.com/routerjson'
APP_KEY = os.environ.get('JD_APP_KEY', '')
SECRET = os.environ.get('JD_APP_SECRET', '')
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'deals-jd.json')

KEYWORDS = ['零食', '纸巾', '洗衣液', '手机', '耳机', '小家电']
PER_PAGE = 6
MAX_ITEMS = 24


def call(method, param_json):
    """调用京东联盟开放 API(MD5 签名),返回解析后的内层结果"""
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 8 * 3600))
    params = {
        'method': method,
        'app_key': APP_KEY,
        'timestamp': ts,
        'format': 'json',
        'v': '1.0',
        'sign_method': 'md5',
        '360buy_param_json': json.dumps(param_json, ensure_ascii=False, separators=(',', ':')),
    }
    sign_str = SECRET + ''.join(k + str(params[k]) for k in sorted(params)) + SECRET
    params['sign'] = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=data, headers={'User-Agent': 'dacu-site/1.0'})
    with urllib.request.urlopen(req, timeout=25) as r:
        resp = json.loads(r.read().decode('utf-8'))
    if 'error_response' in resp:
        raise RuntimeError(json.dumps(resp['error_response'], ensure_ascii=False))
    inner = resp.get(method.replace('.', '_') + '_responce', {})
    # 内层结果字段名不统一:queryResult / getResult / result,取第一个命中的字符串
    result = None
    for key in ('queryResult', 'getResult', 'result'):
        if isinstance(inner.get(key), str):
            result = inner[key]
            break
    if result is None:
        for _, v in inner.items():
            if isinstance(v, str):
                result = v
                break
    if result is None:
        return inner
    try:
        data = json.loads(result)
    except ValueError:
        return {'raw': result}
    # 联盟内层 JSON 自带 code/message(如 1002001 无此应用信息)
    if isinstance(data, dict) and data.get('code') not in (0, 200, None, '0', '200'):
        raise RuntimeError('JD API: %s' % data.get('message', json.dumps(data, ensure_ascii=False)[:200]))
    return data


def get_site_id():
    """取一个可用推广位 siteId(转链必须)"""
    r = call('jd.union.open.site.query', {'req': {}})
    sites = (r.get('data') or {}).get('list') or (r.get('data') or [])
    for s in sites if isinstance(sites, list) else []:
        sid = s.get('siteId') or s.get('id')
        if sid:
            print('siteId = %s (%s)' % (sid, s.get('siteName', '')))
            return str(sid)
    return None


def convert(material_url, site_id):
    r = call('jd.union.open.promotion.common.get',
             {'promotionCodeReq': {'materialId': material_url, 'siteId': site_id}})
    return (r.get('data') or {}).get('clickURL') or ''


def parse_goods(item):
    sku = item.get('skuId')
    price_info = item.get('priceInfo') or {}
    comm_info = item.get('commissionInfo') or {}
    coupon_info = item.get('couponInfo') or {}
    coupons = coupon_info.get('couponList') or []
    coupon = ''
    if coupons:
        c = coupons[0]
        discount = c.get('discount')
        quota = c.get('quota')
        if discount:
            coupon = ('满%s减%s' % (int(quota), int(discount))) if quota else ('减%s元' % int(discount))
    return {
        'sku': sku,
        'title': (item.get('goodsName') or '').strip(),
        'image': (item.get('imageUrlList') or [''])[0],
        'price': price_info.get('lowestPrice') or price_info.get('price'),
        'commissionShare': comm_info.get('commissionShare') or 0,
        'coupon': coupon,
        'shop': (item.get('shopInfo') or {}).get('shopName', ''),
        'material': item.get('materialUrl') or ('https://item.jd.com/%s.html' % sku if sku else ''),
    }


def main():
    if not APP_KEY or not SECRET:
        print('ERROR: 缺少 JD_APP_KEY / JD_APP_SECRET 环境变量')
        sys.exit(1)

    print('== 1/3 查询推广位 ==')
    site_id = get_site_id()
    if not site_id:
        print('WARN: 未找到推广位 siteId,商品将保留原始链接(无佣金跟踪),请到 union.jd.com 创建推广位后重跑')

    print('== 2/3 拉取商品 ==')
    seen, goods = set(), []
    for kw in KEYWORDS:
        try:
            r = call('jd.union.open.goods.query',
                     {'goodsReqDTO': {'keyword': kw, 'pageIndex': 1, 'pageSize': PER_PAGE,
                                      'commissionShareStart': 3}})
            lst = ((r.get('data') or {}).get('list')) or []
        except Exception as e:
            print('  [%s] 失败: %s' % (kw, e))
            continue
        got = 0
        for it in lst:
            g = parse_goods(it)
            if not g['sku'] or g['sku'] in seen or not g['title']:
                continue
            seen.add(g['sku'])
            goods.append(g)
            got += 1
        print('  [%s] %d 条' % (kw, got))

    goods.sort(key=lambda x: x['commissionShare'], reverse=True)
    goods = goods[:MAX_ITEMS]

    print('== 3/3 转推广链接 ==')
    items = []
    for g in goods:
        url = g['material']
        if site_id and g['material']:
            try:
                url = convert(g['material'], site_id) or url
            except Exception as e:
                print('  转链失败 sku=%s: %s' % (g['sku'], e))
        items.append({'title': g['title'], 'image': g['image'], 'price': g['price'],
                      'coupon': g['coupon'], 'url': url, 'shop': g['shop']})

    if not items:
        print('ERROR: 没有拉到任何商品,不写入 JSON')
        sys.exit(2)

    out = {'updated': time.strftime('%Y-%m-%d'), 'platform': 'jd', 'items': items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('OK 写入 %d 条 -> %s' % (len(items), os.path.normpath(OUT)))


if __name__ == '__main__':
    main()
