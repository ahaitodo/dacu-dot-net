/* ============================================================
   Dacu 大促 dacu.net — 全站共享脚本
   包含：明/暗主题切换、页脚年份、
         大促倒计时（未开始/进行中/已结束 三阶段）、大促日历状态
   ============================================================ */

/* ---------- 明/暗主题切换 ---------- */
function toggleTheme(){
  document.documentElement.classList.toggle('dark');
  var dark = document.documentElement.classList.contains('dark');
  var btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = dark ? '☀️' : '🌙';
  localStorage.setItem('theme', dark ? 'dark' : 'light');
}

(function initTheme(){
  if (localStorage.getItem('theme') === 'dark') {
    document.documentElement.classList.add('dark');
    document.addEventListener('DOMContentLoaded', function(){
      var btn = document.getElementById('themeToggle');
      if (btn) btn.textContent = '☀️';
    });
  }
})();

(function(){
  'use strict';

  /* 页脚年份 */
  var y=document.getElementById('y');
  if(y) y.textContent=new Date().getFullYear();

  /* 商品清单(data-src 指向 JSON,无数据则整块隐藏) */
  var deals=document.getElementById('deals');
  if(deals&&deals.dataset.src){
    fetch(deals.dataset.src,{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(d){
      if(!d||!d.items||!d.items.length){deals.hidden=true;return}
      function esc(s){return String(s==null?'':s).replace(/[<>&"]/g,function(c){return{'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]})}
      var h='';
      for(var i=0;i<d.items.length;i++){
        var it=d.items[i];
        h+='<article class="card deal">'
          +(it.image?'<img class="deal-img" loading="lazy" src="'+esc(it.image)+'" alt="">':'')
          +'<h3>'+esc(it.title)+'</h3>'
          +'<div class="deal-meta">'
          +(it.coupon?'<span class="deal-coupon">券 '+esc(it.coupon)+'</span>':'<span></span>')
          +(it.price?'<span class="deal-price">¥'+esc(it.price)+'</span>':'')
          +'</div>'
          +'<a class="btn" href="'+esc(it.url)+'" target="_blank" rel="sponsored nofollow noopener">去抢购</a>'
          +'</article>';
      }
      deals.innerHTML=h;deals.hidden=false;
      var up=document.getElementById('dealsUpdated');if(up)up.textContent='清单更新于 '+d.updated;
    }).catch(function(){deals.hidden=true});
  }

  /* 主推横幅:按日期自动切换大促(每年自动,无需维护) */
  var banner=document.getElementById('promoBanner');
  if(banner){
    var nowB=new Date(),yy=nowB.getFullYear();
    var CAMPS=[
      {w0:[9,20], w1:[10,8],  s:[10,1],  e:[10,8],  href:'guoqing.html',  name:'中秋国庆大促'},
      {w0:[11,1], w1:[11,12], s:[11,11], e:[11,12], href:'shuang11.html', name:'双 11 主会场'},
      {w0:[12,1], w1:[12,13], s:[12,12], e:[12,13], href:'shuang12.html', name:'双 12 主会场'},
      {w0:[12,25],w1:[1,2],   s:[12,31], e:[1,2],   href:'nianzhong.html', name:'年终大促'}
    ];
    for(var bi=0;bi<CAMPS.length;bi++){
      var cp=CAMPS[bi];
      var weY=cp.w1[0]<cp.w0[0]?yy+1:yy, sY=cp.s[0]<cp.w0[0]?yy+1:yy;
      var ws=new Date(yy,cp.w0[0]-1,cp.w0[1]),we=new Date(weY,cp.w1[0]-1,cp.w1[1],23,59,59);
      if(nowB<ws||nowB>we) continue;
      var ps=new Date(sY,cp.s[0]-1,cp.s[1]);
      var days=Math.max(0,Math.ceil((ps-nowB)/864e5));
      banner.href=cp.href;
      banner.innerHTML='<span class="pb-dot"></span><b>'+cp.name+'</b><span>'
        +(nowB>=ps?'正在爆发 · 立即去抢 →':'现货热卖 · 距爆发日 '+days+' 天 →')
        +'</span>';
      banner.hidden=false;
      break;
    }
  }

  /* 大促日历状态:即将开始 / 进行中 / 已收官(有 data-start 的卡片才参与)
     注意:必须放在倒计时之前——没有 #stage 的页面(如首页)也要更新日历 */
  var calLinks=document.querySelectorAll('.cal a[data-start]');
  if(calLinks.length){
    var calStatus=function(a){
      var s=new Date(a.dataset.start),e=new Date(a.dataset.end);
      if(isNaN(s.getTime())||isNaN(e.getTime())) return;
      var now=new Date(),st=a.querySelector('.status');
      if(!st) return;
      if(now<s){st.textContent='即将开始';st.classList.remove('now');}
      else if(now<e){st.textContent='进行中';st.classList.add('now');}
      else{st.textContent='已收官';st.classList.remove('now');}
    };
    Array.prototype.forEach.call(calLinks,calStatus);
    setInterval(function(){Array.prototype.forEach.call(calLinks,calStatus);},60000);
  }

  /* 倒计时舞台(仅大促页有) */
  var stage=document.getElementById('stage');
  if(!stage) return;

  var startAt=new Date(stage.dataset.start),
      endAt=new Date(stage.dataset.end);
  if(isNaN(startAt.getTime())||isNaN(endAt.getTime())) return;

  var elBadge=document.getElementById('badge'),
      elBadgeDot=document.getElementById('badgeDot'),
      elL1=document.getElementById('line1'),
      elL2=document.getElementById('line2'),
      elLede=document.getElementById('lede'),
      elD=document.getElementById('d'),elH=document.getElementById('h'),
      elM=document.getElementById('m'),elS=document.getElementById('s');
  var titlePrefix=stage.dataset.titlePrefix||'',
      titleLive=stage.dataset.titleLive||document.title,
      titleEnded=stage.dataset.titleEnded||document.title;

  function pad(n){return String(Math.max(0,Math.floor(n))).padStart(2,'0')}

  function phaseOf(now){
    if(now<startAt) return {st:'soon',T:startAt};
    if(now<endAt)   return {st:'live',T:endAt};
    /* 已结束后自动倒数明年同一天 */
    var ny=new Date(startAt);ny.setFullYear(ny.getFullYear()+1);
    return {st:'ended',T:ny};
  }

  function render(ph){
    elBadge.textContent=stage.dataset[ph.st+'Badge']||'';
    elBadgeDot.classList.toggle('live',ph.st==='live');
    elL1.textContent=stage.dataset[ph.st+'Line1']||'';
    elL2.textContent=stage.dataset[ph.st+'Line2']||'';
    elLede.innerHTML=stage.dataset[ph.st+'Lede']||'';
  }

  var curPhase=null;
  function tick(){
    var now=new Date(),ph=phaseOf(now);
    if(!curPhase||ph.st!==curPhase.st){
      curPhase=ph;render(ph);
    }
    var x=Math.max(0,ph.T.getTime()-now.getTime());
    var da=Math.floor(x/864e5);x-=da*864e5;
    var ho=Math.floor(x/36e5);x-=ho*36e5;
    var mi=Math.floor(x/6e4);x-=mi*6e4;
    var se=Math.floor(x/1e3);
    elD.textContent=pad(da);elH.textContent=pad(ho);
    elM.textContent=pad(mi);elS.textContent=pad(se);
    if(ph.st==='soon'&&titlePrefix){
      document.title=titlePrefix+' · '+da+'天 '+pad(ho)+':'+pad(mi)+':'+pad(se);
    }else if(ph.st==='live'){
      document.title=titleLive;
    }else{
      document.title=titleEnded;
    }
  }

  tick();
  setInterval(tick,1000);
})();
