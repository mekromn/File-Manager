#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).with_name('stage21a_shizuku_system_bridge.py')
t = p.read_text()
old = """    def ver(p):
        return tuple(int(x) if x.isdigit() else x for x in re.split(r'[.-]',p.name))
    return sorted(ds,key=ver)[-1]
"""
new = """    def ver(p):
        # Android SDK directory names mix numeric components and suffix text
        # (for example 36.0.0-rc5 or android-36). Compare only numeric
        # components so every key has one stable type and Python 3 never tries
        # to order int against str.
        nums = tuple(int(x) for x in re.findall(r'\\d+', p.name))
        return nums or (-1,)
    return max(ds,key=ver)
"""
if t.count(old) != 1:
    raise RuntimeError('Stage21 SDK sorter anchor changed: '+str(t.count(old)))
p.write_text(t.replace(old,new,1))
print('stage20z repaired Stage21 Android SDK natural-version directory selection')
