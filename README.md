# Dacu 大促 dacu.net

优惠导航静态站（GitHub Pages 托管，自定义域名 dacu.net），无需后台，页面内容手工维护。

**定位**：低调、认真推荐的优惠导航 —— 电商官方入口 + 云服务长期优惠 + 大促倒计时。设计体系与 [duanluo.cn](https://duanluo.cn) 一致（明色默认 + 深色切换）。

## 页面结构

| 文件 | 说明 |
|------|------|
| `index.html` | 首页：电商入口卡片（拼多多/淘宝/京东）+ **云服务卡块（腾讯云/阿里云 CPS）** + 大促日历 + 微信订阅 + FAQ |
| `guoqing.html` | 中秋国庆大促页（实时倒计时，三阶段自动切换） |
| `shuang11.html` | 双 11 大促页 |
| `shuang12.html` | 双 12 大促页 |
| `assets/style.css` | 全站样式（品牌色/主题色都在 `:root` 变量里） |
| `assets/site.js` | 全站脚本（主题切换、倒计时、日历状态、微信号复制） |
| `assets/og-cover.png` | 社交分享封面图 |
| `data/friend-links.json` | **友链数据源**（改这里，不用逐页改 HTML） |
| `tools/update_links.py` | 把友链数据源同步到 4 个页面的页脚 |
| `robots.txt` / `sitemap.xml` | 搜索引擎收录配套 |

## 日常维护

### 1. 修改推广链接（电商 / 云服务 CPS）

- **电商**（拼多多 / 淘宝 / 京东）：在 `index.html` 和各促销页的 `plinks` 行里，链接已就位，换链接时全局搜索替换即可。
- **腾讯云 / 阿里云 CPS**：在 `index.html` 与三个大促页中搜索 `★ 腾讯云 CPS`、`★ 阿里云 CPS` 注释，
  把对应 `<a class="btn" href="...">` 的 `href` 换成你在云厂商联盟后台拿到的专属推广链接。
  （当前占位的是官网首页地址，点击不产生佣金，记得替换。）

### 2. 新增大促页（例如双旦、618）

1. 复制一个现有大促页（如 `shuang11.html`）改名；
2. 改 `head` 里的 title / description / canonical / JSON-LD 日期；
3. 改 `#stage` 上的 `data-start` / `data-end` 和 `data-*-badge` 等文案（倒计时逻辑自动生效）；
4. 在 4 个页面的导航（`nav.pill`）和首页「大促日历」中加入新页面链接；
5. 更新 `sitemap.xml`。

### 3. 添加 / 修改友情链接（页脚）

友链区块已预置在全站 4 个页面的页脚（`<!-- FRIEND-LINKS:START -->` 与 `<!-- FRIEND-LINKS:END -->` 之间，**不要删除标记**）。

1. 编辑 `data/friend-links.json`：

```json
{
  "contact_html": "",
  "links": [
    { "name": "对方站点名称", "url": "https://对方网址.com/" }
  ]
}
```

2. 在站点根目录运行（需要本机装有 Python 3）：

```
python tools/update_links.py
```

3. `git add -A && git commit -m "更新友情链接" && git push origin main`，1~2 分钟后全站页脚生效。

> `contact_html` 可选，留空则页脚只显示友链列表；`python tools/update_links.py --check` 可检查页面与数据源是否一致。

### 4. 部署

`main` 分支即站点源（GitHub Pages，`.nojekyll` 已就位，CNAME 指向 dacu.net）。
`git push origin main` 即为上线，1~2 分钟后生效。

### 5. 回滚

- 升级前原始版本标签：`pre-upgrade-2026-10-15`
- 本机备份副本目录：`dacu_backup_2026-10-15`（含全部原文件）

## 说明

- 微信联系方式：9262895（出现在首页、各促销页的订阅区块和页脚）。
- 页脚已声明「部分链接为推广链接」，合规友好。
