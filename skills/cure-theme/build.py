import pathlib, sys
D = pathlib.Path(__file__).parent
base_css = (D/'base.css').read_text(); base_js = (D/'base.js').read_text()
PREV = """function(el,cls){for(var p=el;p;p=p.previousElementSibling){if(p!==el&&p.classList&&p.classList.contains(cls))return (p.textContent||'').replace(/\\s+/g,' ').trim()}if(el.parentElement&&el.parentElement.id!=='nav'&&el.parentElement.previousElementSibling){var q=el.parentElement.previousElementSibling;if(q.classList.contains(cls))return (q.textContent||'').replace(/\\s+/g,' ').trim()}return ''}"""
CFG = {
 'desk': dict(module='CFO Modeling Desk', tag='Finance', items='.nav-item', active='.nav-item.active', scroller='',
              group="function(el){if(!el)return '';return ("+PREV+")(el,'nav-group')}"),
 'hr':   dict(module='HR Command Center', tag='Human Resources', items='.nv-sub button, .nv-g.flat>.nv-h',
              active='.nv-sub button[aria-current="page"], .nv-g.act.flat>.nv-h', scroller='.main',
              group="function(el){if(!el)return '';var g=el.closest('.nv-g');if(!g||g.classList.contains('flat'))return '';var h=g.querySelector('.nv-h .lb');if(!h)return '';var b=h.querySelector('.bi>span');return ((b||h).textContent||'').replace(/\\s+/g,' ').trim()}"),
 'inv':  dict(module='Inventory Analysis & Audit', tag='Inventory', items='.tab-btn', active='.tab-btn[aria-selected="true"]', scroller='',
              group="function(el){if(!el)return '';return ("+PREV+")(el,'sidebar-label')}"),
}
import json
for k, c in CFG.items():
    app_css = (D/f'app_{k}.css').read_text()
    cfg = "window.CURE_CFG={module:%s,tag:%s,items:%s,active:%s,scroller:%s,group:%s};" % (
        json.dumps(c['module']), json.dumps(c['tag']), json.dumps(c['items']), json.dumps(c['active']), json.dumps(c['scroller']), c['group'])
    snip = ("<!--CURE-SKIN:start v1 -->\n<style id=\"cure-skin\">\n" + base_css + "\n" + app_css + "\n</style>\n"
            "<script id=\"cure-skin-js\">\n" + cfg + "\n" + base_js + "\n</script>\n<!--CURE-SKIN:end -->\n")
    (D/f'snippet_{k}.html').write_text(snip)
    print(k, len(snip))
