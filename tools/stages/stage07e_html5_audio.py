#!/usr/bin/env python3
from pathlib import Path
import argparse
SHIM='''(function(g){"use strict";var sounds={};function wrap(o){var a=new Audio();a.preload="metadata";a.src=o.url||"";a.volume=Math.max(0,Math.min(1,(o.volume==null?100:o.volume)/100));if(o.onfinish){a.addEventListener("ended",function(){o.onfinish.call(s);});}var s={id:o.id||("sound"+Date.now()),_audio:a,get paused(){return a.paused;},get duration(){return isFinite(a.duration)?a.duration*1000:0;},get position(){return isFinite(a.currentTime)?a.currentTime*1000:0;},play:function(){var p=a.play();if(p&&p.catch){p.catch(function(){});}return s;},pause:function(){a.pause();return s;},resume:function(){return s.play();},setPosition:function(ms){try{a.currentTime=Math.max(0,ms/1000);}catch(e){}return s;},setVolume:function(v){a.volume=Math.max(0,Math.min(1,v/100));return s;},destruct:function(){a.pause();a.removeAttribute("src");try{a.load();}catch(e){}return null;}};sounds[s.id]=s;return s;}g.soundManager={setup:function(){return this;},createSound:function(o){if(!o||!o.url){return false;}if(o.id&&sounds[o.id]){this.destroySound(o.id);}return wrap(o);},destroySound:function(id){var s=sounds[id];if(!s){return false;}s.destruct();delete sounds[id];return true;}};})(window);\n'''
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); p=a.decoded/'assets/web/lib/soundmanager/soundmanager2.js'
    if not p.exists(): raise RuntimeError('SoundManager library missing')
    old=p.read_text(errors='ignore')
    for tok in ('ShockwaveFlash','download.macromedia.com','preferFlash'):
        if tok not in old: raise RuntimeError(f'expected Flash implementation marker missing: {tok}')
    p.write_text(SHIM)
    cfg=a.decoded/'assets/web/lib/soundmanager/config.js'
    if cfg.exists(): cfg.write_text('soundManager.setup({});\n')
    text=p.read_text()
    for tok in ('Flash','Shockwave','macromedia','swf','pluginspage','codebase'):
        if tok.lower() in text.lower(): raise RuntimeError(f'Flash residue remains in HTML5 shim: {tok}')
    for api in ('createSound','destroySound','setPosition','setVolume','resume','pause','play'):
        if api not in text: raise RuntimeError(f'compatibility API missing: {api}')
    print('stage07e replaced legacy SoundManager/Flash stack with HTML5 Audio-only compatibility shim')
if __name__=='__main__': main()
