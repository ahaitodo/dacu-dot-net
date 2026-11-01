#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京东联盟商品清单拉取(dacu.net 每日自动化)
凭据从环境变量读取(仓库内永远不出现明文):
  JD_APP_KEY / JD_APP_SECRET   主凭据
  JD_APP_KEY2 / JD_APP_SECRET2 备用凭据(主凭据无权限时自动回退)
输出:assets/data/deals-jd.json
"""
import os, sys, json, time, hashlib, urllib.request, urllib.parse

GATEWAY = 'https://api.jd.com/routerjson'
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'deals-jd.json')

KEYWORDS = ['零食', '纸巾', '洗衣液', '手机', '耳机', '小家电']
PER_PAGE = 6
MAX_ITEMS = 24


def call(ak, sec, method, param_json):
    """调用京东联盟开放 API(MD5 签名),返回解析后的内层结果"""
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 8 * 3600))
    params = {
        'method': method,
        'app_key': ak,
        'timestamp': ts,
        'format': 'json',
        'v': '1.0',
        'sign_method': 'md5',
        '360buy_param_json': json.dumps(param_json, ensure_ascii=False, separators=(',', ':')),
    }
    sign_str = sec + ''.join(k + str(params[k]) for k in sorted(params)) + sec
    params['sign'] = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=data, headers={'User-Agent': 'dacu-site/1.0'})
    with urllib.request.urlopen(req, timeout=25) as r:
        resp = json.loads(r.read().decode('utf-8'))
    if 'error_response' in resp:
        raise RuntimeError(json.dumps(resp['error_response'], ensure_ascii=False))
    inner = resp.get(method.replace('.', '_') + '_responce', {})
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
    # 联盟内层 JSON 自带 code/message(如 1002001 无此应用 / 403 无访问权限 / 2000 配额)
    if isinstance(data, dict) and data.get('code') not in (0, 200, None, '0', '200'):
        raise RuntimeError('JD API: %s' % data.get('message', json.dumps(data, ensure_ascii=False)[:200]))
    return data


def is_quota_error(msg):
    return '调用上限' in msg or 'Limited' in msg


def fetch_all(ak, sec):
    """用一组凭据完成:查推广位 → 拉商品。返回 (site_id, goods)"""
    site_id = None
    try:
        r = call(ak, sec, 'jd.union.open.position.query',
                 {'req': {'page': {'pageIndex': 1, 'pageSize': 20}}})
        data = r.get('data') or {}
        sites = data.get('list') if isinstance(data, dict) else data
        for s in sites if isinstance(sites, list) else []:
            sid = s.get('siteId') or s.get('id')
            if sid:
                site_id = str(sid)
                print('推广位 siteId = %s (%s)' % (sid, s.get('siteName', '')))
                break
        if not site_id:
            print('WARN: 账号下暂无推广位,请到 union.jd.com 推广管理新建(1 分钟)')
    except Exception as e:
        msg = str(e)
        if is_quota_error(msg):
            raise
        print('推广位查询失败(继续用商品接口): %s' % msg[:150])

    seen, goods = set(), []
    for kw in KEYWORDS:
        r = call(ak, sec, 'jd.union.open.goods.query',
                 {'goodsReqDTO': {'keyword': kw, 'pageIndex': 1, 'pageSize': PER_PAGE,
                                  'commissionShareStart': 3}})
        lst = ((r.get('data') or {}).get('list')) or []
        got = 0
        for it in lst:
            sku = it.get('skuId')
            if not sku or sku in seen:
                continue
            seen.add(sku)
            price_info = it.get('priceInfo') or {}
            comm_info = it.get('commissionInfo') or {}
            coupons = (it.get('couponInfo') or {}).get('couponList') or []
            coupon = ''
            if coupons:
                c = coupons[0]
                if c.get('discount'):
                    coupon = ('满%s减%s' % (int(c['quota']), int(c['discount']))) if c.get('quota') \
                        else ('减%s元' % int(c['discount']))
            goods.append({
                'sku': sku,
                'title': (it.get('goodsName') or '').strip(),
                'image': (it.get('imageUrlList') or [''])[0],
                'price': price_info.get('lowestPrice') or price_info.get('price'),
                'commissionShare': comm_info.get('commissionShare') or 0,
                'coupon': coupon,
                'material': it.get('materialUrl') or ('https://item.jd.com/%s.html' % sku),
            })
            got += 1
        print('  [%s] %d 条' % (kw, got))
    return site_id, goods


def convert_all(ak, sec, site_id, goods):
    """批量转推广链接;无 siteId 时尝试不带 siteId 调用"""
    items = []
    for g in goods:
        url = g['material']
        req = {'materialId': g['material']}
        if site_id:
            req['siteId'] = site_id
        try:
            r = call(ak, sec, 'jd.union.open.promotion.common.get', {'promotionCodeReq': req})
            url = (r.get('data') or {}).get('clickURL') or url
        except Exception as e:
            msg = str(e)
            if is_quota_error(msg):
                raise RuntimeError(msg)
            if '无访问权限' in msg or '权限' in msg:
                raise RuntimeError('转链接口无权限,请给应用申请「京东联盟」API 权限包: %s' % msg[:150])
            print('  转链失败 sku=%s: %s' % (g['sku'], msg[:120]))
        items.append({'title': g['title'], 'image': g['image'], 'price': g['price'],
                      'coupon': g['coupon'], 'url': url})
    return items


def main():
    pairs = []
    if os.environ.get('JD_APP_KEY') and os.environ.get('JD_APP_SECRET'):
        pairs.append((os.environ['JD_APP_KEY'], os.environ['JD_APP_SECRET']))
    if os.environ.get('JD_APP_KEY2') and os.environ.get('JD_APP_SECRET2'):
        pairs.append((os.environ['JD_APP_KEY2'], os.environ['JD_APP_SECRET2']))
    if not pairs:
        print('ERROR: 缺少 JD_APP_KEY / JD_APP_SECRET 环境变量')
        sys.exit(1)

    site_id, goods, last_err = None, [], None
    for i, (ak, sec) in enumerate(pairs):
        print('== 尝试凭据组 %d/%d ==' % (i + 1, len(pairs)))
        try:
            site_id, goods = fetch_all(ak, sec)
            use_ak, use_sec = ak, sec
            break
        except RuntimeError as e:
            msg = str(e)
            last_err = msg
            print('凭据组 %d 失败: %s' % (i + 1, msg[:200]))
            if is_quota_error(msg):
                print('今日配额已用完(京东 0 点重置),明天自动恢复')
                sys.exit(2)
            continue
    else:
        print('ERROR: 所有凭据组均失败: %s' % last_err)
        sys.exit(1)

    if not goods:
        print('ERROR: 没有拉到任何商品,不写入 JSON')
        sys.exit(2)

    goods.sort(key=lambda x: x['commissionShare'], reverse=True)
    goods = goods[:MAX_ITEMS]

    print('== 转推广链接 ==')
    try:
        items = convert_all(use_ak, use_sec, site_id, goods)
    except RuntimeError as e:
        msg = str(e)
        if is_quota_error(msg):
            print('转链时配额耗尽(0 点重置)')
            sys.exit(2)
        print('ERROR: %s' % msg)
        sys.exit(3)

    out = {'updated': time.strftime('%Y-%m-%d'), 'platform': 'jd', 'items': items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('OK 写入 %d 条 -> %s' % (len(items), os.path.normpath(OUT)))


if __name__ == '__main__':
    main()
