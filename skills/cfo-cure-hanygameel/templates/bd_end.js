  /* ------------------------------ render + start ------------------------------ */
  function render(){
    readout();
    const isDept = ST.tab === 'dept'; bar.style.display = isDept ? 'none' : ''; body.style.display = isDept ? 'none' : ''; const dp = document.getElementById('bd-pane-dept'); if(dp) dp.style.display = isDept ? '' : 'none';
    if(isDept) return;
    try{ ({is:tabIS, impact:tabImpact, score:tabScore, cc:tabCC, drv:tabDrv, wi:tabWhatIf})[ST.tab](); }
    catch(e){ console.error(e); body.innerHTML = `<div class="note">${esc(e.message)}</div>`; }
  }
  
  TI.on(() => { syncTI(); if(ST.tab !== 'dept') render(); });
  syncTI(); drawAll();
})();
