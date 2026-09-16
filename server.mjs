import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {join,normalize} from 'node:path';
const root=join(import.meta.dirname,'public');
const port=Number(process.env.PORT||3000);
const key=process.env.PLANT_ID_API_KEY||'';
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml'};
const requests=new Map();
function send(res,status,data){res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store'});res.end(JSON.stringify(data))}
const server=http.createServer(async(req,res)=>{
  if(req.url==='/api/status')return send(res,200,{scanAvailable:!!key});
  if(req.url==='/api/scan'&&req.method==='POST'){
    if(!key)return send(res,503,{error:'SCAN_NOT_CONFIGURED'});
    const ip=req.socket.remoteAddress||'unknown',now=Date.now(),prior=(requests.get(ip)||[]).filter(t=>now-t<3600000);
    if(prior.length>=10)return send(res,429,{error:'RATE_LIMIT'});
    prior.push(now);requests.set(ip,prior);
    let body='';try{for await(const part of req){body+=part;if(body.length>2_100_000)throw Error('TOO_LARGE')};const {image,locale}=JSON.parse(body);
      if(!/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/.test(image||''))return send(res,400,{error:'INVALID_IMAGE'});
      const langs={en:'en',de:'de',ru:'ru',tr:'tr'};const lang=langs[locale]||'en';
      const upstream=await fetch(`https://api.plant.id/v3/identification?details=common_names,description,watering,light&language=${lang}&health=all`,{method:'POST',headers:{'Content-Type':'application/json','Api-Key':key},body:JSON.stringify({images:[image]}),signal:AbortSignal.timeout(25000)});
      if(!upstream.ok)return send(res,502,{error:'PROVIDER_ERROR',status:upstream.status});
      const data=await upstream.json();const suggestions=data.result?.classification?.suggestions||[];
      const best=suggestions[0]||null;const health=data.result?.disease?.suggestions||[];
      const safeSuggestions=suggestions.slice(0,3).map(x=>({name:x.name,probability:x.probability,commonNames:x.details?.common_names||[],description:x.details?.description?.value||'',watering:x.details?.watering||null,light:x.details?.light||null}));
      return send(res,200,{plant:best?{...safeSuggestions[0]}:null,alternatives:safeSuggestions.slice(1),isHealthy:data.result?.is_healthy?.binary??null,health:health.slice(0,3).map(x=>({name:x.name,probability:x.probability})),warning:'AI suggestions are not a confirmed diagnosis.'});
    }catch(err){return send(res,err.message==='TOO_LARGE'?413:400,{error:err.message==='TOO_LARGE'?'TOO_LARGE':'SCAN_FAILED'})}
  }
  const url=new URL(req.url,'http://localhost');let path=normalize(url.pathname).replace(/^\/+/, '');if(!path||path==='.')path='index.html';
  if(path.includes('..')){res.writeHead(403);return res.end()}
  try{const bytes=await readFile(join(root,path));const ext=path.slice(path.lastIndexOf('.'));res.writeHead(200,{'content-type':mime[ext]||'application/octet-stream','x-content-type-options':'nosniff'});res.end(bytes)}catch{res.writeHead(404);res.end('Not found')}
});server.listen(port,()=>console.log(`BitkiDok http://localhost:${port}`));
