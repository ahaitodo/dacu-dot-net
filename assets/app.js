/* dacu.net 全站脚本:微信号复制、页脚年份、大促倒计时(未开始/进行中/已结束 三阶段) */
(function(){
  'use strict';
  var WXID='9262895';

  /* 页脚年份 */
  var y=document.getElementById('y');
  if(y) y.textContent=new Date().getFullYear();

  /* 复制微信号 */
  var copyBtn=document.getElementById('copyBtn');
  if(copyBtn){
    var msg=document.getElementById('wxmsg');
    var ok=function(){
      msg.style.color='#2ecc71';
      msg.textContent='✓ 已复制微信号 '+WXID+' · 请在微信中搜索添加';
      copyBtn.textContent='已复制';
      setTimeout(function(){copyBtn.textContent='复制';msg.textContent='';},3000);
    };
    var fallback=function(){
      try{
        var ta=document.createElement('textarea');
        ta.value=WXID;ta.style.position='fixed';ta.style.opacity='0';
        document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);
        ok();
      }catch(e){
        msg.style.color='#ff4d2e';msg.textContent='复制失败,请手动复制: '+WXID;
      }
    };
    copyBtn.addEventListener('click',function(){
      if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(WXID).then(ok).catch(fallback);}
      else{fallback();}
    });
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
    stage.style.animation='none';
    void stage.offsetWidth;
    stage.style.animation='';
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

  /* 大促日历状态:即将开始 / 进行中 / 已收官(有 data-start 的卡片才参与) */
  var calLinks=document.querySelectorAll('.cal a[data-start]');
  if(calLinks.length){
    function calStatus(a){
      var s=new Date(a.dataset.start),e=new Date(a.dataset.end);
      if(isNaN(s.getTime())||isNaN(e.getTime())) return;
      var now=new Date(),st=a.querySelector('.status');
      if(!st) return;
      if(now<s){st.textContent='即将开始';st.classList.remove('now');}
      else if(now<e){st.textContent='进行中';st.classList.add('now');}
      else{st.textContent='已收官';st.classList.remove('now');}
    }
    Array.prototype.forEach.call(calLinks,calStatus);
    setInterval(function(){Array.prototype.forEach.call(calLinks,calStatus);},60000);
  }
})();
