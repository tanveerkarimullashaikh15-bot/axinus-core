PAGE = r"""
<div style="font-family:sans-serif;background:#0b1220;color:#e6edf7;padding:12px;border-radius:12px;max-width:520px">
<div style="font-weight:700;font-size:18px;color:#4da3ff">AXINUS Live (Fast Executive UI)</div>
<div id="st" style="margin:6px 0;color:#7fb2ff">Status: ready</div>
<button id="bgo" style="padding:10px 16px;font-size:16px;background:#2563eb;color:#fff;border:none;border-radius:6px">🎙️ Connect</button>
<button id="bstop" style="padding:10px 16px;font-size:16px;background:#374151;color:#fff;border:none;border-radius:6px">⏹ Stop</button>
<div id="ap" style="display:none;margin:8px 0;padding:8px;border:1px solid #f5a623;border-radius:8px;background:#2a2012">
<div id="apm" style="color:#fef3c7;margin-bottom:6px;white-space:pre-wrap"></div>
<button id="apy" style="padding:8px 18px;font-size:16px;background:#10b981;color:#fff;border:none;border-radius:6px">Haan</button>
<button id="apn" style="padding:8px 18px;font-size:16px;background:#ef4444;color:#fff;border:none;border-radius:6px">Na</button>
</div>
<div id="lg" style="height:250px;overflow:auto;background:#111a2e;margin:8px 0;padding:8px;border-radius:8px;font-size:14px"></div>
<div style="display:flex;gap:6px">
<input id="tx" placeholder="Type karke Send dabao..." style="flex:1;padding:8px;background:#1b263b;color:#fff;border:1px solid #2e3e5c;border-radius:6px">
<button id="bsend" style="padding:8px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px">Send</button>
</div>
<input type="file" id="fi" accept="image/*,application/pdf,video/*" style="display:none">
<button id="bup" style="margin-top:8px;padding:10px 16px;font-size:15px;background:#7c3aed;color:#fff;border:none;border-radius:6px;width:100%">📎 Upload File (Photo/PDF/Video)</button>
</div>
<script>
(function(){
const MODEL='gemini-3.8-live';
const URL_='wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained?access_token=';
const SYS=`You are AXINUS, the sharp executive personal AI assistant to Tanveer Shaikh.
Address Tanveer strictly as 'Sir' or 'Boss'. Speak in natural Modern Indian English mixed with simple daily Hinglish (e.g. 'Yes Sir, I am on it', 'Kaam ho gaya hai Sir, please check.').
NEVER use pure or textbook Hindi words. Keep voice responses ultra-short (1-2 lines).
For ANY task (apps, calls, messages, search, notes, coding, files) say 'On it Sir' and call ask_brain at once. NEVER claim a task is done, a message is sent or a call is made until ask_brain returns; then repeat its result in one short line. If ask_brain says Nahi hua/Error, say so honestly. If it asks for yes/no confirmation, ask the user. Greetings: reply directly. If the audio is unclear, background noise, TV or other people talking, or not clearly a command for you, stay completely silent and do nothing - never invent a task.`;

const SETUP={setup:{model:'models/'+MODEL,generationConfig:{responseModalities:['AUDIO']},systemInstruction:{parts:[{text:SYS}]},tools:[{functionDeclarations:[{name:'ask_brain',description:'Execute real tools: YouTube, WhatsApp, Email, Search, Notes, Image, Coding.',parameters:{type:'OBJECT',properties:{request:{type:'STRING',description:'Task detail'}},required:['request']}}]}],inputAudioTranscription:{},outputAudioTranscription:{}}};
let ws=null,mic=null,ctxIn=null,proc=null,ctxOut=null,nextT=0,srcs=[],ready=false;
const cur={in:null,out:null};
const $=id=>document.getElementById(id);
const st=t=>{$('st').textContent='Status: '+t;};

function formatText(t){
t=String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
return t.replace(/https?:\/\/[^\s]+/g,function(u){
if(u.indexOf('https://image.pollinations.ai/')===0)return '<br><img src="'+u+'" style="max-width:100%;border-radius:8px"><br>';
return '<a href="'+u+'" target="_blank" style="color:#60a5fa;text-decoration:underline">▶ Open Link / Media</a>';
});
}
const logLine=(w,t)=>{const d=document.createElement('div');d.innerHTML='<b>'+w+':</b> '+formatText(t);$('lg').appendChild(d);$('lg').scrollTop=1e9;return d;};
const addChunk=(k,t)=>{if(!cur[k])cur[k]=logLine(k==='in'?'Tum':'Axinus','');cur[k].innerHTML+=formatText(t);$('lg').scrollTop=1e9;};

const inv=async(n,a)=>{try{const r=await google.colab.kernel.invokeFunction(n,a||[],{});return(r&&r.data&&r.data['application/json'])?r.data['application/json']:{error:'no data'};}catch(e){return{error:String(e)};}};

const b64=u=>{let s='';for(let i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s);};
const unb64=s=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;};

function play(u){
if(!ctxOut)return;
const n=u.length>>1;const dv=new DataView(u.buffer,u.byteOffset,u.byteLength);
const buf=ctxOut.createBuffer(1,n,24000);const ch=buf.getChannelData(0);
for(let i=0;i<n;i++)ch[i]=dv.getInt16(i*2,true)/32768;
const s=ctxOut.createBufferSource();s.buffer=buf;s.connect(ctxOut.destination);
if(ctxOut.currentTime>nextT+0.2)nextT=ctxOut.currentTime;
const t=Math.max(ctxOut.currentTime,nextT);s.start(t);nextT=t+buf.duration;
srcs.push(s);s.onended=()=>{srcs=srcs.filter(x=>x!==s);};
}
function stopPlay(){srcs.forEach(s=>{try{s.stop();}catch(e){}});srcs=[];nextT=0;}

async function startMic(){
mic=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true,channelCount:1}});
ctxIn=new AudioContext({sampleRate:16000});
const src=ctxIn.createMediaStreamSource(mic);
proc=ctxIn.createScriptProcessor(2048,1,1);
proc.onaudioprocess=e=>{
if(!ws||ws.readyState!==1||!ready)return;
if(srcs.length||(ctxOut&&ctxOut.currentTime<nextT+0.6))return;
const f=e.inputBuffer.getChannelData(0);const p=new Int16Array(f.length);
for(let i=0;i<f.length;i++){const v=Math.max(-1,Math.min(1,f[i]));p[i]=v<0?v*32768:v*32767;}
ws.send(JSON.stringify({realtimeInput:{audio:{data:b64(new Uint8Array(p.buffer)),mimeType:'audio/pcm;rate=16000'}}}));
};
src.connect(proc);proc.connect(ctxIn.destination);
}

function stopMic(){
try{if(mic)mic.getTracks().forEach(t=>t.stop());}catch(e){}
try{if(proc)proc.disconnect();}catch(e){}
try{if(ctxIn)ctxIn.close();}catch(e){}
mic=null;proc=null;ctxIn=null;
}

function showAp(m){$('apm').textContent=m;$('ap').style.display='block';}
function hideAp(){$('ap').style.display='none';}
$('apy').onclick=async()=>{hideAp();await inv('answer_approval',[true]);};
$('apn').onclick=async()=>{hideAp();await inv('answer_approval',[false]);};

async function executeTask(req){
st('Groq Brain running...');logLine('⚙️ Task',req);
let out='';
try{
const j=await inv('start_job',[req]);
for(let i=0;i<800;i++){
await new Promise(r=>setTimeout(r,150));
const r=await inv('poll_job',[j.id]);
if(r.status==='approval'){showAp(r.msg);}
else{hideAp();if(r.status==='done'){out=r.text;break;}}
}
if(!out)out='Timeout: result abhi nahi aaya, kaam chal raha ho sakta hai.';
}catch(e){out='Tool error: '+e;}
logLine('💡 Result',String(out));
st('live - ready Sir!');
return out;
}

const RT={};
async function runTool(fc){
const req=(fc.args&&fc.args.request)||'';
const k=req.toLowerCase().replace(/\W+/g,' ').trim();
if(RT[k]&&Date.now()-RT[k].t<25000){const o=await RT[k].p;if(ws&&ws.readyState===1)ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:fc.id,name:fc.name,response:{output:{value:String(o).slice(0,1800)}}}]}}));return;}
RT[k]={t:Date.now(),p:executeTask(req)};
const out=await RT[k].p;
if(ws&&ws.readyState===1)ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:fc.id,name:fc.name,response:{output:{value:String(out).slice(0,1800)}}}]}}));
}

async function onMsg(ev){
const txt=typeof ev.data==='string'?ev.data:await ev.data.text();
const m=JSON.parse(txt);
if(m.setupComplete){ready=true;st('live - ready Sir!');return;}
const sc=m.serverContent;
if(sc){
if(sc.interrupted)stopPlay();
if(sc.modelTurn&&sc.modelTurn.parts)for(const p of sc.modelTurn.parts){if(p.inlineData&&p.inlineData.data)play(unb64(p.inlineData.data));}
if(sc.inputTranscription&&sc.inputTranscription.text)addChunk('in',sc.inputTranscription.text);
if(sc.outputTranscription&&sc.outputTranscription.text)addChunk('out',sc.outputTranscription.text);
if(sc.turnComplete){cur.in=null;cur.out=null;}
}
if(m.toolCall&&m.toolCall.functionCalls)for(const fc of m.toolCall.functionCalls)runTool(fc);
}

async function handleChatInput(){
const v=$('tx').value.trim();
if(!v)return;
logLine('Tum (chat)',v);
$('tx').value='';
await executeTask(v);
}

$('bsend').onclick=handleChatInput;
$('tx').onkeydown=e=>{if(e.key==='Enter')handleChatInput();};

$('bup').onclick=()=>{$('fi').click();};
$('fi').onchange=async()=>{
const f=$('fi').files[0];
if(!f)return;
if(f.size>30*1024*1024){logLine('❌','File 30MB se badi hai');$('fi').value='';return;}
const uid=Math.random().toString(36).slice(2,10);
const CH=196608;
const total=Math.max(1,Math.ceil(f.size/CH));
let path='';
st('uploading '+f.name+'...');
for(let i=0;i<total;i++){
const buf=new Uint8Array(await f.slice(i*CH,(i+1)*CH).arrayBuffer());
const r=await inv('save_chunk',[uid,f.name,i,total,b64(buf)]);
if(r.error||!r.ok){logLine('❌','Upload fail: '+(r.error||r.msg||''));st('upload fail');$('fi').value='';return;}
if(r.done)path=r.path;
}
logLine('📎','Upload ho gaya: '+f.name);
const q=$('tx').value.trim();
$('tx').value='';
$('fi').value='';
await executeTask('Uploaded file path: '+path+'. '+(q||'Is file ko dekho aur batao isme kya hai.'));
};

$('bgo').onclick=async()=>{
try{
if(ws)return;
st('token le raha hoon...');
ctxOut=new AudioContext({sampleRate:24000});await ctxOut.resume();
const t=await inv('get_token',[]);
if(t.error){st('token error: '+t.error);logLine('❌',t.error);return;}
ws=new WebSocket(URL_+encodeURIComponent(t.token));
ws.onopen=()=>{ws.send(JSON.stringify(SETUP));st('connecting...');};
ws.onerror=()=>{st('ws error');};
ws.onclose=e=>{ready=false;ws=null;stopMic();stopPlay();st('disconnected');};
ws.onmessage=onMsg;
await startMic();
}catch(e){st('Error: '+e);logLine('❌',String(e));}
};
$('bstop').onclick=()=>{try{if(ws)ws.close();}catch(e){}stopMic();stopPlay();};
})();
</script>
"""
display(HTML(PAGE))