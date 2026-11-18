<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Opti Matrix AI Assistant</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>

<style>
:root {
  --bg: #f4f6fb;
  --surface: rgba(255,255,255,.78);
  --surface-solid: #ffffff;
  --surface-2: #f1f4fa;
  --border: rgba(15,23,42,.08);
  --text: #0f172a;
  --text-2: #475569;
  --text-3: #94a3b8;
  --accent: #6366f1;
  --accent-2: #8b5cf6;
  --accent-3: #06b6d4;
  --grad: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #06b6d4 120%);
  --bot-bg: #ffffff;
  --user-text: #ffffff;
  --code-bg: #0f172a;
  --shadow: 0 20px 60px -20px rgba(79,70,229,.25), 0 2px 8px rgba(15,23,42,.05);
  --orb1: rgba(99,102,241,.35);
  --orb2: rgba(6,182,212,.28);
  --orb3: rgba(168,85,247,.28);
}
:root[data-theme="dark"] {
  --bg: #070b14;
  --surface: rgba(17,24,39,.72);
  --surface-solid: #111827;
  --surface-2: #1a2233;
  --border: rgba(255,255,255,.08);
  --text: #f1f5f9;
  --text-2: #a8b3c7;
  --text-3: #64748b;
  --bot-bg: #151d2e;
  --shadow: 0 30px 80px -20px rgba(0,0,0,.7), 0 0 0 1px rgba(255,255,255,.04);
  --orb1: rgba(99,102,241,.30);
  --orb2: rgba(6,182,212,.18);
  --orb3: rgba(168,85,247,.22);
}

*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  font-family:'Inter',system-ui,sans-serif;
  background:var(--bg);
  color:var(--text);
  display:flex;justify-content:center;align-items:center;
  -webkit-font-smoothing:antialiased;
  overflow:hidden;
  transition:background .4s;
}

/* Animated aurora background */
.bg-orbs{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none}
.orb{position:absolute;border-radius:50%;filter:blur(90px);animation:float 18s ease-in-out infinite}
.orb.o1{width:520px;height:520px;background:var(--orb1);top:-120px;left:-100px}
.orb.o2{width:460px;height:460px;background:var(--orb2);bottom:-140px;right:-80px;animation-delay:-6s}
.orb.o3{width:380px;height:380px;background:var(--orb3);top:40%;left:55%;animation-delay:-12s}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(40px,-30px) scale(1.08)}66%{transform:translate(-30px,40px) scale(.95)}}
.bg-grid{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:radial-gradient(var(--border) 1px,transparent 1px);background-size:26px 26px;
  mask-image:radial-gradient(ellipse at center,#000 30%,transparent 75%);
  -webkit-mask-image:radial-gradient(ellipse at center,#000 30%,transparent 75%)}

/* Shell */
.chat-container{
  position:relative;z-index:1;
  width:100%;max-width:960px;height:94vh;
  background:var(--surface);
  backdrop-filter:blur(24px) saturate(160%);-webkit-backdrop-filter:blur(24px) saturate(160%);
  border:1px solid var(--border);
  border-radius:28px;box-shadow:var(--shadow);
  display:flex;flex-direction:column;overflow:hidden;
}

/* Header */
.chat-header{
  padding:18px 26px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border);
}
.brand{display:flex;align-items:center;gap:14px}
.logo{
  position:relative;width:46px;height:46px;border-radius:14px;background:var(--grad);
  display:grid;place-items:center;color:#fff;
  box-shadow:0 8px 24px -6px rgba(99,102,241,.6);
}
.logo svg{width:24px;height:24px}
.logo::after{content:"";position:absolute;inset:-3px;border-radius:17px;border:1px solid rgba(99,102,241,.35);animation:pulse 2.8s ease-out infinite}
@keyframes pulse{0%{transform:scale(.95);opacity:.9}100%{transform:scale(1.18);opacity:0}}
.brand h1{font-family:'Space Grotesk',sans-serif;font-size:1.2rem;font-weight:700;letter-spacing:-.02em}
.brand .sub{display:flex;align-items:center;gap:7px;font-size:.8rem;color:var(--text-2);margin-top:2px;font-weight:500}
.live{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 0 rgba(34,197,94,.6);animation:live 2s infinite}
@keyframes live{70%{box-shadow:0 0 0 7px rgba(34,197,94,0)}100%{box-shadow:0 0 0 0 rgba(34,197,94,0)}}

.header-actions{display:flex;gap:8px}
.icon-btn{
  height:40px;min-width:40px;padding:0 12px;border-radius:12px;border:1px solid var(--border);
  background:var(--surface-solid);color:var(--text-2);cursor:pointer;
  display:inline-flex;align-items:center;justify-content:center;gap:7px;
  font:500 .82rem 'Inter',sans-serif;transition:.2s;
}
.icon-btn:hover{color:var(--accent);border-color:var(--accent);transform:translateY(-1px)}
.icon-btn svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.icon-btn .moon{display:none}
:root[data-theme="dark"] .icon-btn .sun{display:none}
:root[data-theme="dark"] .icon-btn .moon{display:block}

/* Messages */
.chat-messages{flex:1;overflow-y:auto;padding:28px 28px 12px;display:flex;flex-direction:column;gap:22px;scroll-behavior:smooth}
.chat-messages::-webkit-scrollbar{width:8px}
.chat-messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:8px}
.chat-messages::-webkit-scrollbar-thumb:hover{background:var(--text-3)}

.message-wrapper{display:flex;gap:12px;width:100%;animation:rise .45s cubic-bezier(.16,1,.3,1) both}
.message-wrapper.user{justify-content:flex-end}
@keyframes rise{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:none}}

.bot-avatar-small{
  width:34px;height:34px;border-radius:11px;background:var(--grad);flex-shrink:0;margin-top:2px;
  display:grid;place-items:center;color:#fff;box-shadow:0 6px 16px -4px rgba(99,102,241,.5);
}
.bot-avatar-small svg{width:17px;height:17px}

.message-inner{display:flex;flex-direction:column;max-width:78%;position:relative}
.message-wrapper.user .message-inner{align-items:flex-end}

.message{padding:13px 18px;font-size:.95rem;line-height:1.65;word-wrap:break-word;overflow-wrap:anywhere}
.message.user{background:var(--grad);color:var(--user-text);border-radius:20px 20px 6px 20px;box-shadow:0 10px 24px -10px rgba(99,102,241,.7)}
.message.bot{background:var(--bot-bg);border:1px solid var(--border);border-radius:20px 20px 20px 6px;box-shadow:0 2px 10px rgba(15,23,42,.04)}

.meta{display:flex;align-items:center;gap:10px;margin-top:6px;padding:0 6px;font-size:.7rem;color:var(--text-3);opacity:0;transition:opacity .2s}
.message-wrapper:hover .meta{opacity:1}
.copy-btn{background:none;border:none;color:var(--text-3);cursor:pointer;font:inherit;display:inline-flex;align-items:center;gap:4px}
.copy-btn:hover{color:var(--accent)}
.copy-btn svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2}

/* Markdown */
.message.bot>*:first-child{margin-top:0}
.message.bot p{margin-bottom:.7em}
.message.bot p:last-child{margin-bottom:0}
.message.bot strong{font-weight:600;color:var(--text)}
.message.bot ul,.message.bot ol{margin:0 0 .7em 1.3em}
.message.bot li{margin-bottom:.25em}
.message.bot h1,.message.bot h2,.message.bot h3{font-family:'Space Grotesk',sans-serif;margin:.8em 0 .4em;letter-spacing:-.01em}
.message.bot code{background:var(--surface-2);color:#db2777;padding:2px 6px;border-radius:6px;font-size:.88em}
.message.bot pre{margin:.6em 0}
.message.bot pre code{display:block;background:var(--code-bg);color:#e2e8f0;padding:14px;border-radius:12px;overflow-x:auto}
.message.bot table{border-collapse:collapse;margin:.6em 0;font-size:.9rem}
.message.bot th,.message.bot td{border:1px solid var(--border);padding:6px 10px}
.message.bot blockquote{border-left:3px solid var(--accent);padding-left:12px;color:var(--text-2);margin:.6em 0}

.message a.chat-link{
  display:inline-flex;align-items:center;gap:6px;margin:8px 8px 2px 0;padding:8px 16px;
  background:rgba(99,102,241,.1);color:var(--accent);text-decoration:none;border-radius:10px;
  font-weight:600;font-size:.85rem;border:1px solid rgba(99,102,241,.25);transition:.2s;
}
.message a.chat-link::after{content:"↗";font-size:.9em}
.message a.chat-link:hover{background:var(--grad);color:#fff;border-color:transparent;transform:translateY(-2px);box-shadow:0 8px 20px -6px rgba(99,102,241,.55)}

/* Welcome hero */
.welcome{margin:auto;text-align:center;max-width:560px;padding:20px;animation:rise .6s both}
.welcome .big-logo{width:76px;height:76px;border-radius:24px;margin:0 auto 22px;background:var(--grad);display:grid;place-items:center;color:#fff;box-shadow:0 18px 40px -10px rgba(99,102,241,.6)}
.welcome .big-logo svg{width:38px;height:38px}
.welcome h2{font-family:'Space Grotesk',sans-serif;font-size:2rem;letter-spacing:-.03em;line-height:1.15}
.welcome h2 span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.welcome p{color:var(--text-2);margin:12px 0 26px;font-size:1rem;line-height:1.6}
.chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.chip{
  padding:10px 18px;border-radius:999px;border:1px solid var(--border);background:var(--surface-solid);
  color:var(--text-2);font:500 .85rem 'Inter',sans-serif;cursor:pointer;transition:.2s;
}
.chip:hover{color:var(--accent);border-color:var(--accent);transform:translateY(-2px);box-shadow:0 8px 20px -10px rgba(99,102,241,.5)}

/* Typing */
.typing-indicator{display:inline-flex;gap:5px;align-items:center;padding:16px 20px;background:var(--bot-bg);border:1px solid var(--border);border-radius:20px 20px 20px 6px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--grad);background:var(--accent);animation:bounce 1.3s infinite ease-in-out both}
.dot:nth-child(1){animation-delay:-.32s}.dot:nth-child(2){animation-delay:-.16s}
@keyframes bounce{0%,80%,100%{transform:scale(.55);opacity:.4}40%{transform:scale(1);opacity:1}}

/* Scroll down btn */
.scroll-btn{
  position:absolute;left:50%;bottom:112px;transform:translateX(-50%) translateY(10px);
  width:38px;height:38px;border-radius:50%;border:1px solid var(--border);background:var(--surface-solid);color:var(--text-2);
  cursor:pointer;display:grid;place-items:center;opacity:0;pointer-events:none;transition:.25s;box-shadow:0 8px 20px rgba(0,0,0,.15);z-index:5;
}
.scroll-btn.show{opacity:1;pointer-events:auto;transform:translateX(-50%)}
.scroll-btn svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2.2}

/* Input */
.chat-input-container{padding:14px 26px 20px}
.chat-form{
  display:flex;align-items:flex-end;gap:10px;padding:8px 8px 8px 20px;
  background:var(--surface-solid);border:1px solid var(--border);border-radius:24px;
  box-shadow:0 6px 24px -10px rgba(15,23,42,.18);transition:.25s;
}
.chat-form:focus-within{border-color:var(--accent);box-shadow:0 0 0 4px rgba(99,102,241,.14),0 10px 30px -12px rgba(99,102,241,.4)}
.chat-input{
  flex:1;border:none;outline:none;background:transparent;color:var(--text);
  font:400 1rem 'Inter',sans-serif;line-height:1.5;resize:none;max-height:140px;padding:10px 0;
}
.chat-input::placeholder{color:var(--text-3)}
.send-button{
  width:44px;height:44px;border-radius:16px;border:none;background:var(--grad);color:#fff;cursor:pointer;flex-shrink:0;
  display:grid;place-items:center;transition:.2s;box-shadow:0 8px 20px -6px rgba(99,102,241,.6);
}
.send-button:hover:not(:disabled){transform:translateY(-2px) scale(1.04)}
.send-button:disabled{opacity:.4;cursor:not-allowed;box-shadow:none}
.send-button svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.hint{text-align:center;font-size:.72rem;color:var(--text-3);margin-top:10px}
.hint kbd{background:var(--surface-2);border:1px solid var(--border);border-radius:5px;padding:1px 6px;font:inherit}

/* Filter buttons (timeline) */
.suggestions-container{display:flex;flex-wrap:wrap;gap:8px}
.filter-btn{
  padding:7px 14px;border-radius:999px;font:500 .78rem 'Inter',sans-serif;cursor:pointer;transition:.2s;
  background:var(--surface-solid);border:1px solid var(--border);color:var(--text-2);
}
.filter-btn:hover{border-color:var(--accent);color:var(--accent)}
.filter-btn.active{background:var(--grad);color:#fff;border-color:transparent}

/* Profile card */
.profile-card{
  display:flex;flex-direction:column;align-items:center;max-width:290px;padding:26px 24px;margin:4px 0;
  background:var(--surface-solid);border:1px solid var(--border);border-radius:22px;position:relative;overflow:hidden;
  box-shadow:0 14px 36px -16px rgba(79,70,229,.35);
}
.profile-card::before{content:"";position:absolute;inset:0 0 auto 0;height:70px;background:var(--grad);opacity:.9}
.profile-card img{
  position:relative;width:104px;height:104px;border-radius:50%;object-fit:cover;margin-top:14px;
  border:4px solid var(--surface-solid);box-shadow:0 8px 24px rgba(0,0,0,.2);
}
.profile-card h3{margin:14px 0 4px;font-family:'Space Grotesk',sans-serif;font-size:1.1rem;color:var(--text);text-align:center}
.profile-card .role{font-weight:600;color:var(--accent);font-size:.88rem;text-align:center}
.profile-card .company{font-size:.82rem;color:var(--text-2);margin:4px 0 18px;text-align:center}
.message a.li-btn{
  margin:0;width:100%;padding:11px 16px;background:#0a66c2;color:#fff;border:none;border-radius:12px;
  font-weight:600;font-size:.88rem;display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;transition:.2s;
}
.message a.li-btn::after{display:none}
.message a.li-btn:hover{background:#0b5aa6;transform:translateY(-2px);box-shadow:0 10px 22px -8px rgba(10,102,194,.6)}

/* Timeline */
.timeline-wrap{width:100%;min-width:min(520px,70vw)}
.timeline-wrap h3{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;margin-bottom:14px}
.timeline-content{position:relative;margin:20px 0 0 10px;padding-left:26px;border-left:2px solid transparent;border-image:linear-gradient(180deg,#6366f1,#06b6d4) 1}
.tl-item{position:relative;margin-bottom:22px;animation:rise .4s both}
.tl-dot{position:absolute;left:-35px;top:6px;width:16px;height:16px;border-radius:50%;background:var(--grad);border:3px solid var(--bot-bg);box-shadow:0 0 0 1px var(--border),0 0 14px rgba(99,102,241,.6)}
.tl-year{display:inline-block;background:rgba(99,102,241,.12);color:var(--accent);font-size:.72rem;font-weight:700;padding:4px 11px;border-radius:999px;margin-bottom:8px;letter-spacing:.05em}
.tl-card{background:var(--surface-2);border:1px solid var(--border);border-radius:16px;padding:16px;transition:.25s}
.tl-card:hover{transform:translateX(4px);border-color:rgba(99,102,241,.4)}
.tl-card h4{font-size:1rem;margin-bottom:3px;color:var(--text)}
.tl-card .date{font-size:.78rem;color:var(--text-3);font-weight:500;margin-bottom:10px}
.tl-card .desc{font-size:.9rem;color:var(--text-2);line-height:1.55;margin-bottom:12px}
.message a.tl-link{margin:0;padding:7px 14px;font-size:.82rem}

/* Responsive */
@media(max-width:700px){
  .chat-container{height:100vh;max-width:100%;border-radius:0;border:none}
  .chat-header{padding:14px 16px}
  .chat-messages{padding:18px 14px 8px}
  .chat-input-container{padding:10px 12px 14px}
  .message-inner{max-width:88%}
  .icon-btn .lbl,.hint{display:none}
  .welcome h2{font-size:1.6rem}
  .scroll-btn{bottom:92px}
}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<div class="bg-orbs"><div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div></div>
<div class="bg-grid"></div>

<div class="chat-container">
  <header class="chat-header">
    <div class="brand">
      <div class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/></svg>
      </div>
      <div>
        <h1>Opti Matrix Assistant</h1>
        <div class="sub"><span class="live"></span>Online · Always here to optimize your matrix</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="icon-btn" id="new-chat" title="New chat">
        <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg><span class="lbl">New chat</span>
      </button>
      <button class="icon-btn" id="theme-toggle" title="Toggle theme" aria-label="Toggle theme">
        <svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/></svg>
      </button>
    </div>
  </header>

  <div class="chat-messages" id="chat-messages"></div>

  <button class="scroll-btn" id="scroll-btn" aria-label="Scroll to bottom">
    <svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
  </button>

  <div class="chat-input-container">
    <form id="chat-form" class="chat-form">
      <textarea id="chat-input" class="chat-input" rows="1" placeholder="Ask me anything..." autocomplete="off"></textarea>
      <button type="submit" id="send-button" class="send-button" disabled aria-label="Send">
        <svg viewBox="0 0 24 24"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>
      </button>
    </form>
    <div class="hint"><kbd>Enter</kbd> to send · <kbd>Shift</kbd> + <kbd>Enter</kbd> for new line</div>
  </div>
</div>

<script>
const BACKEND_API_URL = "http://localhost:8000";

const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const chatForm = document.getElementById('chat-form');
const scrollBtn = document.getElementById('scroll-btn');
let isLoading = false;

const BOT_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"/></svg>';
const COPY_ICON = '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';

/* ---------- Theme ---------- */
(function initTheme(){
  let saved = null;
  try { saved = localStorage.getItem('om-theme'); } catch(e){}
  const dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
})();
document.getElementById('theme-toggle').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('om-theme', next); } catch(e){}
});

/* ---------- Helpers ---------- */
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = u => /^(https?:|mailto:)/i.test(String(u).trim()) ? esc(u) : '#';
const timeNow = () => new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});

const renderer = new marked.Renderer();
renderer.link = function(p1, p2, p3) {
  let href, title, text;
  if (typeof p1 === 'object' && p1 !== null) { href = p1.href; title = p1.title || ''; text = p1.text; }
  else { href = p1; title = p2 || ''; text = p3; }
  return `<a target="_blank" rel="noopener noreferrer" href="${href}" title="${title}" class="chat-link">${text}</a>`;
};
marked.setOptions({ renderer, breaks: true, gfm: true });

function scrollToBottom(smooth = true) {
  chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}
chatMessages.addEventListener('scroll', () => {
  const far = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight > 220;
  scrollBtn.classList.toggle('show', far);
});
scrollBtn.addEventListener('click', () => scrollToBottom());

/* ---------- Input behaviour ---------- */
function autoGrow() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
}
chatInput.addEventListener('input', () => {
  autoGrow();
  sendButton.disabled = !chatInput.value.trim() || isLoading;
});
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    if (!sendButton.disabled) chatForm.requestSubmit();
  }
});

/* ---------- Custom blocks ---------- */
function renderMessageContent(content) {
  if (content.startsWith("PROFILE_CARD:")) {
    const data = content.split(":").slice(1).join(":").split("|");
    if (data.length === 5) {
      const [name, title, company, linkedin, image] = data;
      return `
        <div class="profile-card">
          <img src="${safeUrl(image)}" alt="${esc(name)}" />
          <h3>${esc(name)}</h3>
          <div class="role">${esc(title)}</div>
          <div class="company">${esc(company)}</div>
          <a class="li-btn" href="${safeUrl(linkedin)}" target="_blank" rel="noopener noreferrer">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z"/></svg>
            View Profile
          </a>
        </div>`;
    }
  }

  if (content.startsWith("TIMELINE_DATA:")) {
    try {
      const events = JSON.parse(content.substring("TIMELINE_DATA:".length));
      const id = 'timeline-' + Date.now() + Math.floor(Math.random()*1000);
      window['timelineData_' + id] = events;
      return `
        <div id="${id}" class="timeline-wrap">
          <h3>🚀 Opti Matrix Journey</h3>
          <div class="suggestions-container">
            <button class="filter-btn active" data-tl="${id}" data-filter="All">Full Journey</button>
            <button class="filter-btn" data-tl="${id}" data-filter="2010-2012">2010-2012</button>
            <button class="filter-btn" data-tl="${id}" data-filter="2013-2015">2013-2015</button>
            <button class="filter-btn" data-tl="${id}" data-filter="2016-2018">2016-2018</button>
            <button class="filter-btn" data-tl="${id}" data-filter="Major Achievements">🏆 Major Achievements</button>
          </div>
          <div class="timeline-content">${generateTimelineHTML(events)}</div>
        </div>`;
    } catch (e) { console.error("Error parsing timeline JSON:", e); }
  }

  return DOMPurify.sanitize(marked.parse(content), { ADD_ATTR: ['target'] });
}

window.renderTimeline = function(containerId, filter) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === filter));

  const all = window['timelineData_' + containerId] || [];
  let list = all;
  const years = { "2010-2012": ["2010","2011","2012"], "2013-2015": ["2013","2014","2015"], "2016-2018": ["2016","2017","2018"] };
  if (years[filter]) list = all.filter(e => years[filter].includes(String(e.year)));
  else if (filter === "Major Achievements") {
    list = all.filter(e => {
      const t = String(e.title || '');
      return t.toLowerCase().includes("achieve") || t.includes("300th") || t.toLowerCase().includes("google") || t.includes("Biggest") || t.toLowerCase().includes("award");
    });
  }
  const box = container.querySelector('.timeline-content');
  box.innerHTML = list.length ? generateTimelineHTML(list) : '<p style="color:var(--text-3);font-size:.9rem;font-style:italic">No events found for this filter.</p>';
};

document.addEventListener('click', e => {
  const btn = e.target.closest('.filter-btn[data-tl]');
  if (btn) window.renderTimeline(btn.dataset.tl, btn.dataset.filter);
});

function generateTimelineHTML(events) {
  return events.map((ev, i) => `
    <div class="tl-item" style="animation-delay:${i * 60}ms">
      <div class="tl-dot"></div>
      <span class="tl-year">${esc(ev.year)}</span>
      <div class="tl-card">
        <h4>${esc(ev.title)}</h4>
        <div class="date">${esc(ev.date)}</div>
        <p class="desc">${esc(ev.desc)}</p>
        ${ev.link ? `<a class="chat-link tl-link" href="${safeUrl(ev.link)}" target="_blank" rel="noopener noreferrer">${esc(ev.linkText || 'Learn more')}</a>` : ''}
      </div>
    </div>`).join('');
}

/* ---------- Messages ---------- */
function clearWelcome() {
  const w = chatMessages.querySelector('.welcome');
  if (w) w.remove();
}

function addMessage(role, content) {
  clearWelcome();
  const wrapper = document.createElement('div');
  wrapper.className = `message-wrapper ${role}`;

  if (role === 'bot') {
    const av = document.createElement('div');
    av.className = 'bot-avatar-small';
    av.innerHTML = BOT_ICON;
    wrapper.appendChild(av);
  }

  const inner = document.createElement('div');
  inner.className = 'message-inner';

  const el = document.createElement('div');
  el.className = `message ${role}`;
  if (role === 'bot') el.innerHTML = renderMessageContent(content);
  else el.textContent = content;
  inner.appendChild(el);

  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.innerHTML = `<span>${timeNow()}</span>`;
  if (role === 'bot') {
    const copy = document.createElement('button');
    copy.className = 'copy-btn';
    copy.type = 'button';
    copy.innerHTML = COPY_ICON + '<span>Copy</span>';
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(el.innerText);
        copy.querySelector('span').textContent = 'Copied!';
        setTimeout(() => copy.querySelector('span').textContent = 'Copy', 1500);
      } catch (e) {}
    });
    meta.appendChild(copy);
  }
  inner.appendChild(meta);

  wrapper.appendChild(inner);
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function showWelcome() {
  chatMessages.innerHTML = `
    <div class="welcome">
      <div class="big-logo">${BOT_ICON}</div>
      <h2>Hello! I'm the <span>Opti Matrix</span> AI Assistant</h2>
      <p>We specialize in optimizing complicated digital challenges. Pick a topic below or ask me anything.</p>
      <div class="chips">
        <button class="chip" data-q="What does Opti Matrix do?">✨ What does Opti Matrix do?</button>
        <button class="chip" data-q="Show me the Opti Matrix journey">🚀 Company journey</button>
        <button class="chip" data-q="Who is the founder?">👤 Meet the founder</button>
        <button class="chip" data-q="What services do you offer?">🛠️ Our services</button>
      </div>
    </div>`;
}
chatMessages.addEventListener('click', e => {
  const chip = e.target.closest('.chip');
  if (chip) { chatInput.value = chip.dataset.q; autoGrow(); sendButton.disabled = false; chatForm.requestSubmit(); }
});

function showTyping() {
  const w = document.createElement('div');
  w.className = 'message-wrapper bot typing-wrapper';
  w.innerHTML = `<div class="bot-avatar-small">${BOT_ICON}</div>
    <div class="message-inner"><div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>`;
  chatMessages.appendChild(w);
  scrollToBottom();
}
function hideTyping() {
  const t = chatMessages.querySelector('.typing-wrapper');
  if (t) t.remove();
}

/* ---------- Session ---------- */
function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
let sessionId = generateUUID();

document.getElementById('new-chat').addEventListener('click', () => {
  if (isLoading) return;
  sessionId = generateUUID();
  showWelcome();
  chatInput.focus();
});

/* ---------- Send ---------- */
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const userMsg = chatInput.value.trim();
  if (!userMsg || isLoading) return;

  addMessage('user', userMsg);
  chatInput.value = "";
  autoGrow();
  sendButton.disabled = true;
  isLoading = true;
  showTyping();

  try {
    const response = await fetch(BACKEND_API_URL + "/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userMsg, session_id: sessionId }),
    });
    if (!response.ok) throw new Error("Server communication failed");
    const data = await response.json();
    hideTyping();
    addMessage('bot', data.answer || "I'm sorry, I couldn't process that. Please try again.");
  } catch (error) {
    console.error("Error:", error);
    hideTyping();
    addMessage('bot', "⚠️ Connection error. Please ensure the backend is running and try again.");
  } finally {
    isLoading = false;
    sendButton.disabled = !chatInput.value.trim();
    chatInput.focus();
  }
});

/* ---------- History ---------- */
async function loadChatHistory() {
  try {
    const response = await fetch(BACKEND_API_URL + "/history/" + sessionId);
    if (response.ok) {
      const data = await response.json();
      if (data.chat_history && data.chat_history.length > 0) {
        chatMessages.innerHTML = '';
        data.chat_history.forEach(msg => addMessage(msg.role === 'assistant' ? 'bot' : 'user', msg.content));
        return;
      }
    }
  } catch (error) {
    console.error("History loading error:", error);
  }
  showWelcome();
}
loadChatHistory();
</script>
</body>
</html>