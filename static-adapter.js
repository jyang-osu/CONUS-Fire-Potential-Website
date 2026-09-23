const numericCache=new Map();
async function readBinary(item){
 if(numericCache.has(item.key))return numericCache.get(item.key);
 const r=await fetch(item.binary);if(!r.ok)throw Error('Data file unavailable: '+item.time);
 if(!('DecompressionStream' in window))throw Error('Please use a current Chrome, Edge, Firefox, or Safari browser.');
 const compressed=await r.arrayBuffer(),magic=new Uint8Array(compressed);
 const buffer=magic[0]===31&&magic[1]===139?await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():compressed;
 if(buffer.byteLength!==item.width*item.height*4)throw Error('Invalid numeric grid length');
 const integers=new Int32Array(buffer);const a=Float64Array.from(integers,x=>x===-2147483648?NaN:x/100);
 numericCache.set(item.key,a);if(numericCache.size>24)numericCache.delete(numericCache.keys().next().value);
 return a;
}
async function request(url){
 const u=new URL(url,'https://local.invalid');
 if(u.pathname==='/api/catalog'){
  numericCache.clear();
  const r=await fetch('catalog.json',{cache:'no-store'});if(!r.ok)throw Error('Run Export_Data.cmd to prepare the site data.');
  return await r.json();
 }
 if(u.pathname==='/api/layer'){
  const item=catalog.items.find(x=>x.key===u.searchParams.get('key'));if(!item)throw Error('Map not available.');
  const a=await readBinary(item);
  return {...item,filename:item.png.split('/').at(-1),values:Array.from(a,x=>Number.isFinite(x)?x:null)};
 }
 if(u.pathname==='/api/timeseries'){
  const variable=u.searchParams.get('variable'),row=Number(u.searchParams.get('row')),col=Number(u.searchParams.get('col'));
  const items=catalog.items.filter(x=>x.variable===variable).sort((a,b)=>a.time.localeCompare(b.time));
  if(!items.length)throw Error('No history available.');
  const latest=items.at(-1).time;
  const date=s=>new Date(s.slice(0,4)+'-'+s.slice(4,6)+'-'+s.slice(6,8)+'T'+s.slice(9,11)+':'+s.slice(11,13)+':00Z');
  const encode=d=>d.toISOString().slice(0,10).replaceAll('-','')+'_'+d.toISOString().slice(11,16).replace(':','');
  const lookup=new Map(items.map(x=>[x.time,x]));
  const points=Array.from({length:240},(_,i)=>({time:encode(new Date(date(latest).getTime()-(239-i)*3600000)),value:null,status:'missing'}));
  let next=0;
  async function worker(){while(next<points.length){const i=next++,point=points[i],item=lookup.get(point.time);if(!item)continue;
   try{const a=await readBinary(item),v=a[row*item.width+col];point.value=Number.isFinite(v)?v:null;point.status=point.value===null?'nodata':'valid'}catch(e){point.status='unavailable'}
  }}
  await Promise.all(Array.from({length:6},worker));
  return {variable,units:catalog.variables[variable][1],latest_time:latest,points,valid_hours:points.filter(x=>x.value!==null).length,total_hours:240};
 }
 throw Error('Unsupported request');
}
