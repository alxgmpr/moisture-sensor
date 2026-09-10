"""Destroy only this render's rental after 90 minutes, independent of the chat."""
import json,subprocess,time
from pathlib import Path
p=Path(__file__).resolve().parent
lease=json.loads((p/'vast-lease.json').read_text())
while time.time()<lease['deadline_unix']:
    if (p/'vast-destroyed.json').exists():raise SystemExit(0)
    time.sleep(max(0,min(30,lease['deadline_unix']-time.time())))
for _ in range(20):
    r=subprocess.run(['/Users/alex/.local/bin/vastai','--raw','destroy','instance',str(lease['instance_id']),'--yes'],capture_output=True,text=True)
    (p/'vast-deadline-result.txt').write_text(r.stdout+r.stderr)
    check=subprocess.run(['/Users/alex/.local/bin/vastai','--raw','show','instances'],capture_output=True,text=True)
    try:
        instances=json.loads(check.stdout)
        if isinstance(instances,list) and all(v['id']!=lease['instance_id'] for v in instances):
            (p/'vast-destroyed.json').write_text(json.dumps({'instance_id':lease['instance_id'],'destroyed':True,'confirmed_unix':time.time(),'absent_from_instance_list':True}))
            break
    except (ValueError,KeyError):
        pass
    time.sleep(15)
