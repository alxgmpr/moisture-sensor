import subprocess,time
from pathlib import Path
p=Path(__file__).resolve().parent
ssh=['ssh','-p','23694','-i','/Users/alex/.ssh/id_ed25519_llm','-o','ServerAliveInterval=15','-o','ConnectTimeout=15','root@ssh2.vast.ai']
while True:
    r=subprocess.run(ssh+['tail -1 /root/render/render.log; if test -f /root/render/finish.done; then cat /root/render/finish.done; elif test -f /root/render/render.exit; then printf "RENDER_EXIT="; cat /root/render/render.exit; fi'],capture_output=True,text=True,timeout=45)
    print(r.stdout.strip() or 'Cloud status temporarily unavailable',flush=True)
    if 'COMPLETE' in r.stdout or 'RENDER_EXIT=1' in r.stdout:break
    time.sleep(45)
