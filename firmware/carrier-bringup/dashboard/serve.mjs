import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
const files = {'/':['index.html','text/html; charset=utf-8'], '/index.html':['index.html','text/html; charset=utf-8'],
  '/style.css':['style.css','text/css; charset=utf-8'], '/app.mjs':['app.mjs','text/javascript; charset=utf-8'],
  '/protocol.mjs':['protocol.mjs','text/javascript; charset=utf-8']};
const port=Number(process.env.PORT || 8766);
createServer(async (req,res)=>{
  const route=files[new URL(req.url,'http://localhost').pathname];
  if (!route || !['GET','HEAD'].includes(req.method)) {res.writeHead(404);res.end();return;}
  try {
    const data=await readFile(new URL(route[0],import.meta.url));
    res.writeHead(200,{'Content-Type':route[1], 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
      'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'none'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'"});
    res.end(req.method==='HEAD'?undefined:data);
  } catch {res.writeHead(500);res.end('Unable to read dashboard asset.');}
}).listen(port,'127.0.0.1',()=>console.log(`Sensor dashboard: http://127.0.0.1:${port}`));
