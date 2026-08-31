#!/usr/bin/env python3
import os, sys, struct, zipfile, shutil, hashlib, subprocess, tempfile, io, zlib
from pathlib import Path

# Paths are intentionally configurable so the copyrighted upstream APK and private signing
# material never need to live in Git.
REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('FX_BASE_APK', REPO_ROOT / 'upstream' / 'FX-9.1.0.8.apk')).expanduser().resolve()
OUT_ROOT = Path(os.environ.get('FX_OUTPUT_DIR', REPO_ROOT / 'build')).expanduser().resolve()
WORK = OUT_ROOT / 'intermediates'
OUT_UNSIGNED = WORK/'FX-Extended_9.1.0.8_THEME_TEST_unsigned.apk'
OUT_V1 = WORK/'FX-Extended_9.1.0.8_THEME_TEST_v1.apk'
OUT_ALIGNED = WORK/'FX-Extended_9.1.0.8_THEME_TEST_v1_aligned.apk'
OUT_FINAL = OUT_ROOT/'FX-Extended_9.1.0.8_DarkGlass_AMOLED_PixelBlue_TEST.apk'
KEYSTORE = Path(os.environ.get('FX_KEYSTORE', OUT_ROOT / 'signing' / 'FX-Extended-test-signing.p12')).expanduser().resolve()
KEYPASS_FILE = Path(os.environ.get('FX_KEYPASS_FILE', OUT_ROOT / 'signing' / 'FX-Extended-test-signing-password.txt')).expanduser().resolve()
NEW_PACKAGE = 'com.mekromn.fxextended'
NEW_LABEL = 'FX Extended'
NEW_XML = [
    ('theme_fxext_dark_glass', 'res/fx_dark_glass.xml', 0x7f130043),
    ('theme_fxext_amoled_black_transparent', 'res/fx_amoled_black_transparent.xml', 0x7f130044),
]
PIXEL_BLUE = 0xFF4285F4

# ---- basic binary helpers ----
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def p16(x): return struct.pack('<H',x)
def p32(x): return struct.pack('<I',x)
def p64(x): return struct.pack('<Q',x)
def chunk_hdr(b,o): return struct.unpack_from('<HHI',b,o)
def align4(n): return (n+3)&~3

def read_len8(b,o):
    x=b[o]; o+=1
    if x & 0x80:
        x=((x&0x7f)<<8)|b[o]; o+=1
    return x,o

def enc_len8(x):
    if x < 0x80: return bytes([x])
    if x < 0x8000: return bytes([0x80 | (x>>8), x&0xff])
    raise ValueError('utf8 length too long')

def read_len16(b,o):
    x=u16(b,o); o+=2
    if x & 0x8000:
        y=u16(b,o); o+=2
        x=((x&0x7fff)<<16)|y
    return x,o

def enc_len16(x):
    if x < 0x8000: return p16(x)
    if x < 0x80000000: return p16(0x8000 | (x>>16)) + p16(x&0xffff)
    raise ValueError('utf16 length too long')

def parse_string_pool(chunk: bytes):
    typ,hs,sz = chunk_hdr(chunk,0)
    assert typ == 0x0001
    sc,stc,flags,ss,sts = struct.unpack_from('<IIIII',chunk,8)
    utf8=bool(flags&0x100)
    soff=[u32(chunk,hs+4*i) for i in range(sc)]
    styleoff=[u32(chunk,hs+4*sc+4*i) for i in range(stc)]
    strings=[]
    for ro in soff:
        q=ss+ro
        if utf8:
            _,q=read_len8(chunk,q); bl,q=read_len8(chunk,q)
            strings.append(chunk[q:q+bl].decode('utf-8','replace'))
        else:
            ln,q=read_len16(chunk,q)
            strings.append(chunk[q:q+2*ln].decode('utf-16le','replace'))
    return dict(hs=hs,size=sz,count=sc,style_count=stc,flags=flags,strings_start=ss,styles_start=sts,
                offsets=soff,style_offsets=styleoff,strings=strings,utf8=utf8)

def append_string_pool(chunk: bytes, new_strings):
    info=parse_string_pool(chunk)
    existing={s:i for i,s in enumerate(info['strings'])}
    add=[]; mapping={}
    for s in new_strings:
        if s in existing:
            mapping[s]=existing[s]
        elif s in mapping:
            pass
        else:
            mapping[s]=info['count']+len(add); add.append(s)
    if not add: return chunk, mapping
    hs=info['hs']; stc=info['style_count']; old_sc=info['count']
    old_ss=info['strings_start']; old_sts=info['styles_start']
    old_string_end = old_sts if old_sts else len(chunk)
    old_string_data = chunk[old_ss:old_string_end]
    style_data = chunk[old_sts:] if old_sts else b''
    appended=bytearray(); new_offsets=list(info['offsets'])
    for s in add:
        new_offsets.append(len(old_string_data)+len(appended))
        if info['utf8']:
            raw=s.encode('utf-8'); u16len=len(s.encode('utf-16le'))//2
            appended += enc_len8(u16len)+enc_len8(len(raw))+raw+b'\x00'
        else:
            raw=s.encode('utf-16le'); u16len=len(raw)//2
            appended += enc_len16(u16len)+raw+b'\x00\x00'
    data = bytearray(old_string_data) + appended
    while len(data)%4: data += b'\x00'
    new_sc=old_sc+len(add)
    new_ss=hs+4*new_sc+4*stc
    new_sts=(new_ss+len(data)) if old_sts else 0
    new_size=new_ss+len(data)+len(style_data)
    out=bytearray()
    out += struct.pack('<HHI',0x0001,hs,new_size)
    out += struct.pack('<IIIII',new_sc,stc,info['flags'],new_ss,new_sts)
    out += b''.join(p32(x) for x in new_offsets)
    out += b''.join(p32(x) for x in info['style_offsets'])
    assert len(out)==new_ss
    out += data
    out += style_data
    assert len(out)==new_size
    return bytes(out), mapping

def axml_strings(axml: bytes):
    typ,hs,sz=chunk_hdr(axml,0); assert typ==0x0003
    o=hs
    while o<len(axml):
        t,h,s=chunk_hdr(axml,o)
        if t==1:
            info=parse_string_pool(axml[o:o+s]); return o,s,info
        o+=s
    raise ValueError('no string pool')

def rebuild_axml_with_pool(axml: bytes, added_strings):
    typ,hs,sz=chunk_hdr(axml,0); sp_off,sp_sz,info=axml_strings(axml)
    new_sp,mapping=append_string_pool(axml[sp_off:sp_off+sp_sz],added_strings)
    out=bytearray(axml[:sp_off])+new_sp+axml[sp_off+sp_sz:]
    struct.pack_into('<I',out,4,len(out))
    return bytes(out), mapping

def get_axml_string_list(axml):
    _,_,info=axml_strings(axml); return info['strings']

# ---- manifest patch ----
def patch_manifest(axml: bytes):
    dyn_perm = NEW_PACKAGE + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    auth_map = {
        'nextapp.fx.TemporaryFileProvider': NEW_PACKAGE + '.TemporaryFileProvider',
        'nextapp.fx.FileProvider': NEW_PACKAGE + '.FileProvider',
        'nextapp.fx.androidx-startup': NEW_PACKAGE + '.androidx-startup',
    }
    task_values=[]
    strings=get_axml_string_list(axml)
    for s in strings:
        if s.startswith('nextapp.fx.') and ('TextEditor' in s or 'MediaPlayerActivity' in s or 'ImageViewerActivity' in s or 'ExecActivity' in s or 'DexClassViewerActivity' in s):
            task_values.append(s)
    added=[NEW_PACKAGE,dyn_perm,*auth_map.values(),*[NEW_PACKAGE+s[len('nextapp.fx'):] for s in task_values]]
    axml,mapping=rebuild_axml_with_pool(axml,added)
    strings=get_axml_string_list(axml)
    str_to_idx={s:i for i,s in enumerate(strings)}
    typ,root_h,_=chunk_hdr(axml,0); o=root_h
    out=bytearray(axml[:root_h]); stack=[]
    while o < len(axml):
        t,h,s=chunk_hdr(axml,o); ch=bytearray(axml[o:o+s])
        if t==0x0102:
            ext=16; name_idx=u32(ch,ext+4); tag=strings[name_idx]
            ast,asz,ac,ididx,cidx,sidx=struct.unpack_from('<HHHHHH',ch,ext+8)
            aoff=ext+ast; attrs=[]
            for i in range(ac):
                x=aoff+i*asz; ns=u32(ch,x); an=u32(ch,x+4); raw=u32(ch,x+8); dt=ch[x+15]; data=u32(ch,x+16)
                n=strings[an]
                val = strings[raw] if raw!=0xffffffff and raw<len(strings) else (strings[data] if dt==3 and data<len(strings) else None)
                attrs.append((i,x,n,val,dt,data))
            remove=[]
            if tag=='manifest':
                for i,x,n,val,dt,data in attrs:
                    if n=='sharedUserId': remove.append(i)
                    elif n=='package':
                        idx=str_to_idx[NEW_PACKAGE]; struct.pack_into('<I',ch,x+8,idx); ch[x+15]=3; struct.pack_into('<I',ch,x+16,idx)
            for i,x,n,val,dt,data in attrs:
                if n=='name' and val=='nextapp.fx.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION':
                    idx=str_to_idx[dyn_perm]; struct.pack_into('<I',ch,x+8,idx); ch[x+15]=3; struct.pack_into('<I',ch,x+16,idx)
                elif n=='authorities' and val in auth_map:
                    nv=auth_map[val]; idx=str_to_idx[nv]; struct.pack_into('<I',ch,x+8,idx); ch[x+15]=3; struct.pack_into('<I',ch,x+16,idx)
                elif n=='taskAffinity' and val in task_values:
                    nv=NEW_PACKAGE+val[len('nextapp.fx'):]; idx=str_to_idx[nv]; struct.pack_into('<I',ch,x+8,idx); ch[x+15]=3; struct.pack_into('<I',ch,x+16,idx)
            if remove:
                keep=[i for i in range(ac) if i not in remove]
                attr_bytes=b''.join(bytes(ch[aoff+i*asz:aoff+(i+1)*asz]) for i in keep)
                new=bytearray(ch[:aoff])+attr_bytes+ch[aoff+ac*asz:]
                struct.pack_into('<H',new,ext+12,len(keep))
                struct.pack_into('<I',new,4,len(new))
                ch=new
            stack.append(tag)
        elif t==0x0103:
            if stack: stack.pop()
        out += ch; o += s
    struct.pack_into('<I',out,4,len(out))
    return bytes(out)

# ---- theme palette patch ----
def patch_palette(axml: bytes, palette: dict):
    strings=get_axml_string_list(axml)
    typ,root_h,_=chunk_hdr(axml,0); out=bytearray(axml); o=root_h
    while o < len(out):
        t,h,s=chunk_hdr(out,o)
        if t==0x0102:
            ext=o+16; name_idx=u32(out,ext+4); tag=strings[name_idx]
            ast,asz,ac,*_=struct.unpack_from('<HHHHHH',out,ext+8); aoff=ext+ast
            vals={}
            for i in range(ac):
                x=aoff+i*asz; an=u32(out,x+4); raw=u32(out,x+8); dt=out[x+15]; data=u32(out,x+16); n=strings[an]
                val=strings[raw] if raw!=0xffffffff and raw<len(strings) else (strings[data] if dt==3 and data<len(strings) else None)
                vals[n]=(x,val)
            if tag=='color' and 'name' in vals and 'value' in vals:
                cname=vals['name'][1]
                if cname in palette:
                    x=vals['value'][0]; struct.pack_into('<I',out,x+8,0xffffffff); out[x+15]=0x1c; struct.pack_into('<I',out,x+16,palette[cname]&0xffffffff)
        o += s
    return bytes(out)

DARK_GLASS = {
 'actionBarBackground':0xCC111820,
 'actionBarBackgroundOpaque':0xFF111820,
 'drawerHeaderBackground':0xD9141A22,
 'menuBackground':0xE6161C24,
 'windowBackground':0xA611171E,
 'contentBackground':0xD9141A22,
 'headerBackground':0xE61A2230,
 'headerBackgroundInactive':0xB3151A20,
 'specialTextColor':PIXEL_BLUE,
 'defaultTrimBase':0xFF202A36,
 'defaultTrimAccent':PIXEL_BLUE,
 'progressComplete':PIXEL_BLUE,
 'progressRemaining':0x663A4656,
 'boxBackground':0xB31B2430,
 'boxPressedBackground':0x664285F4,
 'boxEffectOnlyPressedBackground':0x664285F4,
 'boxFlatPressedBackground':0x554285F4,
 'selectionBackground':0x554285F4,
 'selectionPressedBackground':0x774285F4,
 'editorBackground':0xF20D1117,
}
AMOLED_GLASS = {
 'actionBarBackground':0xCC000000,
 'actionBarBackgroundOpaque':0xFF000000,
 'drawerHeaderBackground':0xCC000000,
 'menuBackground':0xE6000000,
 'windowBackground':0x99000000,
 'contentBackground':0xFF000000,
 'headerBackground':0xE6000000,
 'headerBackgroundInactive':0xB3000000,
 'specialTextColor':PIXEL_BLUE,
 'defaultTrimBase':0xFF000000,
 'defaultTrimAccent':PIXEL_BLUE,
 'progressComplete':PIXEL_BLUE,
 'progressRemaining':0x66333333,
 'boxBackground':0xB3000000,
 'boxPressedBackground':0x664285F4,
 'boxEffectOnlyPressedBackground':0x664285F4,
 'boxFlatPressedBackground':0x554285F4,
 'selectionBackground':0x554285F4,
 'selectionPressedBackground':0x774285F4,
 'editorBackground':0xFF000000,
}

# ---- module registry patch ----
def patch_theme_registry(axml: bytes):
    new_ids=['fx_dark_glass','fx_amoled_black_transparent']
    axml,_=rebuild_axml_with_pool(axml,new_ids)
    strings=get_axml_string_list(axml); idx={s:i for i,s in enumerate(strings)}
    typ,rh,_=chunk_hdr(axml,0)
    o=rh; stack=[]; trans_depth=None; template_start=None; template_end=None; insert_at=None
    while o<len(axml):
        t,h,s=chunk_hdr(axml,o)
        if t==0x0102:
            ext=o+16; tag=strings[u32(axml,ext+4)]; ast,asz,ac,*_=struct.unpack_from('<HHHHHH',axml,ext+8); aoff=ext+ast
            attrs={}
            for i in range(ac):
                x=aoff+i*asz; n=strings[u32(axml,x+4)]; raw=u32(axml,x+8); dt=axml[x+15]; data=u32(axml,x+16)
                val=strings[raw] if raw!=0xffffffff and raw<len(strings) else (strings[data] if dt==3 and data<len(strings) else None)
                attrs[n]=val
            stack.append((tag,attrs))
            if tag=='theme-set' and attrs.get('id')=='translucent': trans_depth=len(stack)
            if trans_depth and tag=='theme' and attrs.get('id')=='translucent_dark': template_start=bytes(axml[o:o+s])
        elif t==0x0103:
            tag=strings[u32(axml,o+20)]
            if trans_depth and tag=='theme' and stack and stack[-1][0]=='theme' and stack[-1][1].get('id')=='translucent_dark': template_end=bytes(axml[o:o+s])
            if trans_depth and tag=='theme-set' and len(stack)==trans_depth:
                insert_at=o; break
            if stack: stack.pop()
        o+=s
    if not all([template_start,template_end,insert_at is not None]): raise RuntimeError('theme registry template not found')
    def make_theme(idstr,resid,preview):
        ch=bytearray(template_start); ext=16; ast,asz,ac,*_=struct.unpack_from('<HHHHHH',ch,ext+8); aoff=ext+ast
        for i in range(ac):
            x=aoff+i*asz; n=strings[u32(ch,x+4)]
            if n=='id':
                si=idx[idstr]; struct.pack_into('<I',ch,x+8,si); ch[x+15]=3; struct.pack_into('<I',ch,x+16,si)
            elif n=='resource':
                struct.pack_into('<I',ch,x+8,0xffffffff); ch[x+15]=1; struct.pack_into('<I',ch,x+16,resid)
            elif n=='color':
                struct.pack_into('<I',ch,x+8,0xffffffff); ch[x+15]=0x1c; struct.pack_into('<I',ch,x+16,preview)
        return bytes(ch)+template_end
    insertion=make_theme('fx_dark_glass',0x7f130043,0xFF111820)+make_theme('fx_amoled_black_transparent',0x7f130044,0xFF000000)
    out=bytearray(axml[:insert_at])+insertion+axml[insert_at:]
    struct.pack_into('<I',out,4,len(out))
    return bytes(out)

# ---- resources.arsc patch ----
def patch_type_spec(ch: bytes, add_count=2):
    out=bytearray(ch); ec=u32(out,12); out += b'\x00\x00\x00\x00'*add_count
    struct.pack_into('<I',out,12,ec+add_count); struct.pack_into('<I',out,4,len(out)); return bytes(out)

def patch_xml_type(ch: bytes, key_indices, global_indices):
    h=chunk_hdr(ch,0)[1]; ec=u32(ch,12); entries_start=u32(ch,16)
    old_offsets=ch[h:h+4*ec]; between=ch[h+4*ec:entries_start]; entries=ch[entries_start:]
    newoffs=[len(entries)+16*i for i in range(len(key_indices))]
    new_entries=bytearray()
    for ki,gi in zip(key_indices,global_indices):
        new_entries += struct.pack('<HHI',8,0,ki)
        new_entries += struct.pack('<HBBI',8,0,3,gi)
    new_entries_start=entries_start+4*len(key_indices)
    out=bytearray(ch[:h])+old_offsets+b''.join(p32(x) for x in newoffs)+between+entries+new_entries
    struct.pack_into('<I',out,12,ec+len(key_indices)); struct.pack_into('<I',out,16,new_entries_start); struct.pack_into('<I',out,4,len(out))
    return bytes(out)

def patch_string_type_appname(ch: bytes, global_label_idx):
    out=bytearray(ch); h=chunk_hdr(out,0)[1]; ec=u32(out,12); es=u32(out,16); target=0x119
    if target>=ec: return ch
    eo=u32(out,h+4*target)
    if eo==0xffffffff: return ch
    q=es+eo; flags=u16(out,q+2)
    if flags&1: return ch
    v=q+u16(out,q); dt=out[v+3]
    if dt==3: struct.pack_into('<I',out,v+4,global_label_idx)
    return bytes(out)

def patch_arsc(arsc: bytes):
    top_t,top_h,top_s=chunk_hdr(arsc,0); assert top_t==2 and top_h==12
    gt,gh,gs=chunk_hdr(arsc,top_h); assert gt==1
    global_add=[NEW_XML[0][1],NEW_XML[1][1],NEW_LABEL]
    new_g,gmap=append_string_pool(arsc[top_h:top_h+gs],global_add)
    ginfo=parse_string_pool(new_g); gidx={s:i for i,s in enumerate(ginfo['strings'])}
    pkg_off=top_h+gs; pt,ph,ps=chunk_hdr(arsc,pkg_off); assert pt==0x200
    pkg=arsc[pkg_off:pkg_off+ps]
    keyoff=u32(pkg,276); kt,kh,ks=chunk_hdr(pkg,keyoff); assert kt==1
    key_add=[NEW_XML[0][0],NEW_XML[1][0]]
    new_key,kmap=append_string_pool(pkg[keyoff:keyoff+ks],key_add)
    kinfo=parse_string_pool(new_key); kidx={s:i for i,s in enumerate(kinfo['strings'])}
    outpkg=bytearray(pkg[:ph])
    name_raw=NEW_PACKAGE.encode('utf-16le')+b'\x00\x00'; name_raw=name_raw.ljust(256,b'\x00')[:256]
    outpkg[12:12+256]=name_raw
    po=ph
    while po<len(pkg):
        t,h,s=chunk_hdr(pkg,po); ch=pkg[po:po+s]
        if po==keyoff:
            outpkg += new_key
        elif t==0x202 and pkg[po+8]==19:
            outpkg += patch_type_spec(ch,2)
        elif t==0x201 and pkg[po+8]==19:
            outpkg += patch_xml_type(ch,[kidx[key_add[0]],kidx[key_add[1]]],[gidx[global_add[0]],gidx[global_add[1]]])
        elif t==0x201 and pkg[po+8]==16:
            outpkg += patch_string_type_appname(ch,gidx[NEW_LABEL])
        else:
            outpkg += ch
        po += s
    struct.pack_into('<I',outpkg,4,len(outpkg))
    out=bytearray(arsc[:top_h])+new_g+outpkg
    struct.pack_into('<I',out,4,len(out))
    return bytes(out)

# ---- zip assembly ----
def is_old_signature(name):
    u=name.upper()
    return u in ('META-INF/MANIFEST.MF','META-INF/CERT.SF','META-INF/CERT.RSA','META-INF/CERT.DSA','META-INF/CERT.EC')

def copy_zipinfo(zi):
    nz=zipfile.ZipInfo(zi.filename,zi.date_time)
    nz.compress_type=zi.compress_type; nz.comment=zi.comment; nz.create_system=zi.create_system; nz.create_version=zi.create_version
    nz.extract_version=zi.extract_version; nz.flag_bits=zi.flag_bits; nz.volume=zi.volume; nz.internal_attr=zi.internal_attr; nz.external_attr=zi.external_attr
    return nz

def make_alignment_extra(fp_pos, filename, align=4):
    base=fp_pos+30+len(filename.encode('utf-8'))
    if base%align==0: return b''
    for dlen in range(0,align):
        total=4+dlen
        if (base+total)%align==0:
            return struct.pack('<HH',0xFFFF,dlen)+b'\x00'*dlen
    raise AssertionError

def build_unsigned(manifest,arsc,registry,dark,amoled):
    WORK.mkdir(parents=True,exist_ok=True)
    replacements={'AndroidManifest.xml':manifest,'resources.arsc':arsc,'res/ox.xml':registry,
                  'res/fx_dark_glass.xml':dark,'res/fx_amoled_black_transparent.xml':amoled}
    with zipfile.ZipFile(BASE,'r') as zin, zipfile.ZipFile(OUT_UNSIGNED,'w',allowZip64=True) as zout:
        existing=set()
        for zi in zin.infolist():
            n=zi.filename
            if is_old_signature(n): continue
            data=replacements.get(n,zin.read(n)); existing.add(n)
            nzi=copy_zipinfo(zi)
            if n=='resources.arsc': nzi.compress_type=zipfile.ZIP_STORED; nzi.extra=make_alignment_extra(zout.fp.tell(),n,4)
            else: nzi.extra=b''
            zout.writestr(nzi,data)
        for n in ('res/fx_dark_glass.xml','res/fx_amoled_black_transparent.xml'):
            if n not in existing:
                zi=zipfile.ZipInfo(n,(1981,1,1,1,1,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o644<<16
                zout.writestr(zi,replacements[n])
    return OUT_UNSIGNED

# ---- v2 signer ----
def lp(x: bytes): return p32(len(x))+x

def find_eocd(data: bytes):
    sig=b'PK\x05\x06'; start=max(0,len(data)-22-65535); i=data.rfind(sig,start)
    if i<0: raise ValueError('EOCD not found')
    comment_len=u16(data,i+20)
    if i+22+comment_len!=len(data): raise ValueError('trailing data or bad EOCD')
    return i

def content_digest_sha256(section1, section3, section4):
    cds=[]
    for sec in (section1,section3,section4):
        for pos in range(0,len(sec),1024*1024):
            ch=sec[pos:pos+1024*1024]
            cds.append(hashlib.sha256(b'\xA5'+p32(len(ch))+ch).digest())
    return hashlib.sha256(b'\x5A'+p32(len(cds))+b''.join(cds)).digest()

def v2_sign(apk_path: Path, out_path: Path, private_key, cert):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    data=apk_path.read_bytes(); eocd_off=find_eocd(data); cd_off=u32(data,eocd_off+16)
    if cd_off>eocd_off: raise ValueError('bad cd offset')
    sec1=data[:cd_off]; sec3=data[cd_off:eocd_off]
    eocd=bytearray(data[eocd_off:]); struct.pack_into('<I',eocd,16,cd_off)
    digest=content_digest_sha256(sec1,sec3,bytes(eocd))
    alg=0x0103
    digest_record=p32(alg)+lp(digest)
    digests=lp(digest_record)
    cert_der=cert.public_bytes(Encoding.DER)
    certs=lp(cert_der)
    attrs=b''
    signed_data=lp(digests)+lp(certs)+lp(attrs)
    signature=private_key.sign(signed_data,padding.PKCS1v15(),hashes.SHA256())
    sig_record=p32(alg)+lp(signature)
    signatures=lp(sig_record)
    pub=private_key.public_key().public_bytes(Encoding.DER,PublicFormat.SubjectPublicKeyInfo)
    signer=lp(signed_data)+lp(signatures)+lp(pub)
    v2_value=lp(lp(signer))
    pair=p64(4+len(v2_value))+p32(0x7109871A)+v2_value
    block_size=len(pair)+24
    sigblock=p64(block_size)+pair+p64(block_size)+b'APK Sig Block 42'
    new_eocd=bytearray(data[eocd_off:]); struct.pack_into('<I',new_eocd,16,cd_off+len(sigblock))
    out=sec1+sigblock+sec3+bytes(new_eocd)
    out_path.write_bytes(out)
    return digest,len(sigblock)

def verify_v2_structure(apk_path: Path, cert):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    d=apk_path.read_bytes(); eo=find_eocd(d); cd=u32(d,eo+16)
    if d[cd-16:cd] != b'APK Sig Block 42': raise AssertionError('no APK signing block magic')
    size2=struct.unpack_from('<Q',d,cd-24)[0]; start=cd-(size2+8); size1=struct.unpack_from('<Q',d,start)[0]
    assert size1==size2
    p=start+8; pairlen=struct.unpack_from('<Q',d,p)[0]; p+=8; pid=u32(d,p); p+=4; assert pid==0x7109871A
    v=d[p:p+pairlen-4]
    def take_lp(buf,off):
        n=u32(buf,off); off+=4; return buf[off:off+n],off+n
    signers,_=take_lp(v,0); signer,_=take_lp(signers,0); sd,q=take_lp(signer,0); sigs,q=take_lp(signer,q); pub,q=take_lp(signer,q)
    sigrec,_=take_lp(sigs,0); alg=u32(sigrec,0); sig,_=take_lp(sigrec,4); assert alg==0x0103
    cert.public_key().verify(sig,sd,padding.PKCS1v15(),hashes.SHA256())
    digs,q=take_lp(sd,0); certseq,q=take_lp(sd,q); attrs,q=take_lp(sd,q)
    drec,_=take_lp(digs,0); dalg=u32(drec,0); stored,_=take_lp(drec,4); assert dalg==alg
    sec1=d[:start]; sec3=d[cd:eo]; e=bytearray(d[eo:]); struct.pack_into('<I',e,16,start)
    actual=content_digest_sha256(sec1,sec3,bytes(e)); assert actual==stored
    return {'block_start':start,'cd_offset':cd,'digest':actual.hex(),'alg':hex(alg),'sig_block_size':cd-start}

def ensure_key():
    KEYSTORE.parent.mkdir(parents=True,exist_ok=True)
    KEYPASS_FILE.parent.mkdir(parents=True,exist_ok=True)
    if KEYSTORE.exists() and KEYPASS_FILE.exists():
        pw=KEYPASS_FILE.read_text().strip(); return pw
    import secrets
    pw=secrets.token_urlsafe(24)
    subprocess.run(['keytool','-genkeypair','-v','-storetype','PKCS12','-keystore',str(KEYSTORE),'-storepass',pw,'-keypass',pw,
                    '-alias','fxextended','-keyalg','RSA','-keysize','2048','-validity','10000',
                    '-dname','CN=FX Extended Test,O=Mekromn FX Extended,C=US'],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    KEYPASS_FILE.write_text(pw+'\n'); os.chmod(KEYPASS_FILE,0o600)
    return pw

def realign_zip(src: Path, dst: Path, align=4):
    with zipfile.ZipFile(src,'r') as zin, zipfile.ZipFile(dst,'w',allowZip64=True) as zout:
        zout.comment=zin.comment
        for zi in zin.infolist():
            data=zin.read(zi.filename)
            nzi=copy_zipinfo(zi)
            nzi.extra=b''
            if nzi.compress_type==zipfile.ZIP_STORED and not zi.filename.endswith('/'):
                nzi.extra=make_alignment_extra(zout.fp.tell(),zi.filename,align)
            zout.writestr(nzi,data)
    return dst

def sign_apk(unsigned: Path):
    pw=ensure_key(); shutil.copy2(unsigned,OUT_V1)
    subprocess.run(['jarsigner','-keystore',str(KEYSTORE),'-storetype','PKCS12','-storepass',pw,'-keypass',pw,
                    '-sigalg','SHA256withRSA','-digestalg','SHA-256',str(OUT_V1),'fxextended'],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    realign_zip(OUT_V1,OUT_ALIGNED,4)
    from cryptography.hazmat.primitives.serialization import pkcs12
    key,cert,chain=pkcs12.load_key_and_certificates(KEYSTORE.read_bytes(),pw.encode())
    digest,bs=v2_sign(OUT_ALIGNED,OUT_FINAL,key,cert)
    return cert,digest,bs

# ---- main ----
def main():
    if not BASE.is_file():
        raise SystemExit(f'Base APK not found: {BASE}\nSet FX_BASE_APK to the exact upstream FX 9.1.0.8 APK.')
    base_hash=hashlib.sha256(BASE.read_bytes()).hexdigest()
    expected='19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6'
    if base_hash != expected:
        raise SystemExit(f'Unexpected base SHA-256: {base_hash}\nExpected: {expected}')
    WORK.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(BASE) as z:
        manifest=z.read('AndroidManifest.xml'); arsc=z.read('resources.arsc'); reg=z.read('res/ox.xml'); base_dark=z.read('res/rI.xml')
    patched_manifest=patch_manifest(manifest)
    patched_arsc=patch_arsc(arsc)
    patched_reg=patch_theme_registry(reg)
    dark=patch_palette(base_dark,DARK_GLASS)
    amoled=patch_palette(base_dark,AMOLED_GLASS)
    for name,data in [('AndroidManifest.xml',patched_manifest),('resources.arsc',patched_arsc),('ox.xml',patched_reg),('fx_dark_glass.xml',dark),('fx_amoled_black_transparent.xml',amoled)]:
        (WORK/name).write_bytes(data)
    build_unsigned(patched_manifest,patched_arsc,patched_reg,dark,amoled)
    cert,digest,bs=sign_apk(OUT_UNSIGNED)
    info=verify_v2_structure(OUT_FINAL,cert)
    pw=KEYPASS_FILE.read_text().strip()
    jv=subprocess.run(['jarsigner','-verify','-strict','-certs',str(OUT_FINAL)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    with zipfile.ZipFile(OUT_FINAL) as z:
        assert z.testzip() is None
        assert z.read('res/fx_dark_glass.xml')==dark
        assert z.read('res/fx_amoled_black_transparent.xml')==amoled
        zi=z.getinfo('resources.arsc'); assert zi.compress_type==zipfile.ZIP_STORED
        raw=OUT_FINAL.read_bytes()
        for ezi in z.infolist():
            if ezi.compress_type != zipfile.ZIP_STORED or ezi.filename.endswith('/'):
                continue
            fnlen,exlen=struct.unpack_from('<HH',raw,ezi.header_offset+26)
            data_off=ezi.header_offset+30+fnlen+exlen
            assert data_off % 4 == 0, (ezi.filename,data_off)
    from cryptography.hazmat.primitives import hashes
    certfp=cert.fingerprint(hashes.SHA256()).hex()
    report={
      'base_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),
      'output_sha256':hashlib.sha256(OUT_FINAL.read_bytes()).hexdigest(),
      'output_size':OUT_FINAL.stat().st_size,
      'package':NEW_PACKAGE,'label':NEW_LABEL,
      'v2':info,'cert_sha256':certfp,'jarsigner_rc':jv.returncode,
      'theme_resource_ids':['0x7f130043','0x7f130044'],
    }
    (WORK/'build_report.txt').write_text('\n'.join(f'{k}: {v}' for k,v in report.items())+'\n')
    print('\n'.join(f'{k}: {v}' for k,v in report.items()))
    print('OUTPUT',OUT_FINAL)

if __name__=='__main__': main()
