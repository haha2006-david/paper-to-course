"""Validate embedded LaTeX with the same offline KaTeX shipped in the reader."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess


def expressions(value, path='lesson'):
    if isinstance(value, str):
        for match in re.finditer(r'\\\[(.*?)\\\]|\\\((.*?)\\\)', value, re.S):
            yield {'path':path, 'tex':match.group(1) if match.group(1) is not None else match.group(2),
                   'display':match.group(1) is not None}
    elif isinstance(value, dict):
        for key, item in value.items():
            if key != 'image': yield from expressions(item, path+'.'+key)
    elif isinstance(value, list):
        for index, item in enumerate(value): yield from expressions(item, f'{path}[{index}]')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lesson',type=Path)
    args=parser.parse_args()
    node=shutil.which('node')
    if not node: parser.exit(2,'Node unavailable: formula validation not executed.\n')
    data=json.loads(args.lesson.read_text(encoding='utf-8-sig'))
    records=list(expressions(data))
    katex=Path(__file__).resolve().parents[1]/'assets/math/katex.min.js'
    code="""const fs=require('fs'),katex=require(process.argv[1]);let errors=0;
    for(const item of JSON.parse(fs.readFileSync(0,'utf8'))){try{
        katex.renderToString(item.tex,{displayMode:item.display,throwOnError:true,trust:false,maxExpand:1000,maxSize:10,strict:'error'});
    }catch(e){errors++;process.stderr.write(item.path+': '+e.message+'\\n');}}
    process.exitCode=errors?1:0;"""
    result=subprocess.run([node,'-e',code,str(katex)],input=json.dumps(records),text=True,timeout=30,
                          encoding='utf-8',capture_output=True)
    if result.stderr: print(result.stderr,end='')
    if result.returncode: raise SystemExit(result.returncode)
    print(f'{len(records)} LaTeX expressions validated with bundled KaTeX.')


if __name__=='__main__':main()
