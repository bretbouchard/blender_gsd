var D=Object.defineProperty;var j=(t,e,n)=>e in t?D(t,e,{enumerable:!0,configurable:!0,writable:!0,value:n}):t[e]=n;var $=(t,e,n)=>j(t,typeof e!="symbol"?e+"":e,n);(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))s(o);new MutationObserver(o=>{for(const a of o)if(a.type==="childList")for(const r of a.addedNodes)r.tagName==="LINK"&&r.rel==="modulepreload"&&s(r)}).observe(document,{childList:!0,subtree:!0});function n(o){const a={};return o.integrity&&(a.integrity=o.integrity),o.referrerPolicy&&(a.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?a.credentials="include":o.crossOrigin==="anonymous"?a.credentials="omit":a.credentials="same-origin",a}function s(o){if(o.ep)return;o.ep=!0;const a=n(o);fetch(o.href,a)}})();const N="modulepreload",B=function(t){return"/"+t},C={},p=function(e,n,s){let o=Promise.resolve();if(n&&n.length>0){document.getElementsByTagName("link");const r=document.querySelector("meta[property=csp-nonce]"),c=(r==null?void 0:r.nonce)||(r==null?void 0:r.getAttribute("nonce"));o=Promise.allSettled(n.map(i=>{if(i=B(i),i in C)return;C[i]=!0;const m=i.endsWith(".css"),l=m?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${i}"]${l}`))return;const d=document.createElement("link");if(d.rel=m?"stylesheet":N,m||(d.as="script"),d.crossOrigin="",d.href=i,c&&d.setAttribute("nonce",c),document.head.appendChild(d),m)return new Promise((L,R)=>{d.addEventListener("load",L),d.addEventListener("error",()=>R(new Error(`Unable to preload CSS for ${i}`)))})}))}function a(r){const c=new Event("vite:preloadError",{cancelable:!0});if(c.payload=r,window.dispatchEvent(c),!c.defaultPrevented)throw r}return o.then(r=>{for(const c of r||[])c.status==="rejected"&&a(c.reason);return e().catch(a)})};async function q(){try{const t=await p(()=>import("./config-BcITQeUW.js"),[]);return t.default||t}catch(t){return console.error("Failed to load config:",t),{categories:[{id:"character",name:"Characters",color:"#3498db"},{id:"wardrobe",name:"Wardrobe",color:"#9b59b6"},{id:"prop",name:"Props",color:"#e67e22"},{id:"set",name:"Sets",color:"#27ae60"},{id:"shot",name:"Shots",color:"#e74c3c"},{id:"asset",name:"Assets",color:"#1abc9c"},{id:"audio",name:"Audio",color:"#f39c12"}],statuses:[{id:"complete",name:"Complete",color:"#27ae60"},{id:"in_progress",name:"In Progress",color:"#f1c40f"},{id:"planned",name:"Planned",color:"#3498db"},{id:"vague",name:"Vague",color:"#95a5a6"},{id:"blocked",name:"Blocked",color:"#e74c3c"}]}}}async function z(){const t=[];try{const e=Object.assign({"../../.planning/tracking/items/CHAR-001.yaml":()=>p(()=>import("./CHAR-001-CqHA3GbM.js"),[]),"../../.planning/tracking/items/CHAR-002.yaml":()=>p(()=>import("./CHAR-002-CaEH7iDC.js"),[]),"../../.planning/tracking/items/CHAR-003.yaml":()=>p(()=>import("./CHAR-003-CslOgAZ4.js"),[]),"../../.planning/tracking/items/PROP-015.yaml":()=>p(()=>import("./PROP-015-BM7Qwgqz.js"),[]),"../../.planning/tracking/items/PROP-016.yaml":()=>p(()=>import("./PROP-016-BLHy_sTn.js"),[]),"../../.planning/tracking/items/SET-001.yaml":()=>p(()=>import("./SET-001-VjVEyGVT.js"),[]),"../../.planning/tracking/items/SHOT-001.yaml":()=>p(()=>import("./SHOT-001-BGOUxH3r.js"),[]),"../../.planning/tracking/items/WARD-001.yaml":()=>p(()=>import("./WARD-001-DUR43te2.js"),[]),"../../.planning/tracking/items/WARD-002.yaml":()=>p(()=>import("./WARD-002-CKxzSjx3.js"),[])});for(const n in e)try{const s=await e[n](),o=s.default||s;o&&o.id&&t.push(o)}catch(s){console.warn(`Failed to load item: ${n}`,s)}}catch(e){console.error("Failed to load items:",e)}return t.sort((e,n)=>e.id.localeCompare(n.id))}async function F(){try{const t=await p(()=>import("./blockers-aXfo_T2t.js"),[]);return(t.default||t).blockers||[]}catch(t){return console.error("Failed to load blockers:",t),[]}}class g{constructor(e){$(this,"_value");$(this,"subscribers",[]);this._value=e}get(){return this._value}set(e){this._value!==e&&(this._value=e,this.subscribers.forEach(n=>n(e)))}subscribe(e){return this.subscribers.push(e),e(this._value),()=>{this.subscribers=this.subscribers.filter(n=>n!==e)}}}const f=new g([]),y=new g(null),E=new g([]),b=new g({}),P=new g("kanban"),v=new g(null),x=new g(!0),I=new g(null);function V(){const t=f.get(),e=b.get();return t.filter(n=>{var s;if(e.status&&n.status!==e.status||e.category&&n.category!==e.category)return!1;if(e.search){const o=e.search.toLowerCase(),a=n.id.toLowerCase().includes(o),r=n.name.toLowerCase().includes(o),c=((s=n.description)==null?void 0:s.toLowerCase().includes(o))??!1;if(!a&&!r&&!c)return!1}return!0})}function U(){return f.get().filter(t=>t.blockers.length>0||t.status==="blocked")}function M(){const t=f.get();return{total:t.length,complete:t.filter(e=>e.status==="complete").length,in_progress:t.filter(e=>e.status==="in_progress").length,planned:t.filter(e=>e.status==="planned").length,vague:t.filter(e=>e.status==="vague").length,blocked:t.filter(e=>e.status==="blocked"||e.blockers.length>0).length,blockers:E.get().length}}function W(){const t=document.createElement("div");t.className="filter-bar";function e(){var r,c,i,m;const n=y.get(),s=b.get(),o=P.get();t.innerHTML=`
      <div class="filters">
        <select id="status-filter" title="Filter by status">
          <option value="">All Statuses</option>
          ${(n==null?void 0:n.statuses.map(l=>`
            <option value="${l.id}" ${s.status===l.id?"selected":""}>
              ${l.name}
            </option>
          `).join(""))||""}
        </select>

        <select id="category-filter" title="Filter by category">
          <option value="">All Categories</option>
          ${(n==null?void 0:n.categories.map(l=>`
            <option value="${l.id}" ${s.category===l.id?"selected":""}>
              ${l.name}
            </option>
          `).join(""))||""}
        </select>

        <input
          type="text"
          id="search"
          placeholder="Search items..."
          value="${s.search||""}"
          title="Search by name, ID, or description"
        />

        <button id="clear-filters" class="btn-clear" title="Clear all filters">
          ✕ Clear
        </button>
      </div>

      <div class="view-toggle">
        <button class="${o==="kanban"?"active":""}" data-view="kanban" title="Board view">
          ▦ Board
        </button>
        <button class="${o==="table"?"active":""}" data-view="table" title="Table view">
          ☰ Table
        </button>
      </div>
    `,(r=t.querySelector("#status-filter"))==null||r.addEventListener("change",l=>{const d=l.target.value;b.set({...s,status:d||void 0})}),(c=t.querySelector("#category-filter"))==null||c.addEventListener("change",l=>{const d=l.target.value;b.set({...s,category:d||void 0})});let a;(i=t.querySelector("#search"))==null||i.addEventListener("input",l=>{clearTimeout(a),a=window.setTimeout(()=>{const d=l.target.value;b.set({...s,search:d||void 0})},200)}),(m=t.querySelector("#clear-filters"))==null||m.addEventListener("click",()=>{b.set({}),t.querySelector("#status-filter").value="",t.querySelector("#category-filter").value="",t.querySelector("#search").value=""}),t.querySelectorAll("[data-view]").forEach(l=>{l.addEventListener("click",d=>{const L=d.target.dataset.view;P.set(L)})})}return e(),y.subscribe(e),t}const G={width:800,height:1e3,heroImageSize:{width:800,height:450},thumbSize:{width:180,height:100},showQRCode:!0,showDependencies:!0,theme:"dark"},Q={character:{id:"character",name:"Character",color:"#3498db"},prop:{id:"prop",name:"Prop",color:"#9b59b6"},wardrobe:{id:"wardrobe",name:"Wardrobe",color:"#e91e63"},set:{id:"set",name:"Set",color:"#795548"},shot:{id:"shot",name:"Shot",color:"#ff9800"},asset:{id:"asset",name:"Asset",color:"#607d8b"},audio:{id:"audio",name:"Audio",color:"#4caf50"}},K={todo:{id:"todo",name:"Todo",color:"#9e9e9e"},in_progress:{id:"in_progress",name:"In Progress",color:"#2196f3"},review:{id:"review",name:"Review",color:"#ff9800"},done:{id:"done",name:"Done",color:"#4caf50"},blocked:{id:"blocked",name:"Blocked",color:"#f44336"}};function h(t){var i,m,l;const{item:e,heroImage:n,thumbnails:s,dependencies:o,config:a}=t,r=Q[e.category]||{id:e.category,name:e.category,color:"#666"},c=K[e.status]||{id:e.status,name:e.status,color:"#666"};return`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${u(e.name)} - 1-Sheet</title>
  <style>
    ${Y(a)}
  </style>
</head>
<body>
  <div class="onesheet" style="width: ${a.width}px;">
    ${n?`
      <div class="hero-image">
        <img src="${u(n)}" alt="${u(e.name)}" />
      </div>
    `:`
      <div class="hero-placeholder">
        <span>No Image</span>
      </div>
    `}

    <div class="content">
      <header class="header">
        <div class="title-block">
          <h1 class="name">${u(e.name)}</h1>
          <span class="id">${u(e.id)}</span>
        </div>
        <div class="badges">
          <span class="category" style="background: ${r.color}">${u(r.name)}</span>
          <span class="status" style="background: ${c.color}">${u(c.name)}</span>
        </div>
      </header>

      ${e.description?`
        <section class="description">
          <h2>Description</h2>
          <p>${u(e.description)}</p>
        </section>
      `:""}

      ${s.length>0?`
        <section class="thumbnails">
          ${s.map(d=>`
            <img src="${u(d)}" class="thumb" alt="thumbnail" />
          `).join("")}
        </section>
      `:""}

      ${a.showDependencies&&o.length>0?`
        <section class="dependencies">
          <h2>Dependencies</h2>
          <ul>
            ${o.map(d=>`
              <li>
                <span class="dep-id">${u(d.id)}</span>
                <span class="dep-name">${u(d.name)}</span>
              </li>
            `).join("")}
          </ul>
        </section>
      `:""}

      <footer class="footer">
        <div class="source">
          <span>Source:</span>
          ${(i=e.source)!=null&&i.spec?`<span class="source-path">${u(e.source.spec)}</span>`:"<span>N/A</span>"}
        </div>
        <div class="meta">
          ${(m=e.source)!=null&&m.created_at?`Created: ${u(e.source.created_at)}`:""}
          ${(l=e.source)!=null&&l.created_by?` by ${u(e.source.created_by)}`:""}
        </div>
        ${a.showQRCode?`
          <div class="qr-placeholder">
            [QR: ${u(e.id)}]
          </div>
        `:""}
        <div class="project">blender_gsd</div>
      </footer>
    </div>
  </div>
</body>
</html>
  `.trim()}function Y(t){const e=t.theme==="dark"?{bg:"#1a1a2e",fg:"#eaeaea",muted:"#888",card:"#16213e",border:"#2a2a4a",accent:"#3498db"}:{bg:"#f5f5f5",fg:"#1a1a2e",muted:"#666",card:"#ffffff",border:"#ddd",accent:"#3498db"};return`
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: ${e.bg};
      color: ${e.fg};
      display: flex;
      justify-content: center;
      padding: 2rem;
      line-height: 1.5;
    }

    .onesheet {
      background: ${e.card};
      border: 1px solid ${e.border};
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .hero-image {
      width: 100%;
      height: ${t.heroImageSize.height}px;
      overflow: hidden;
      background: ${e.bg};
    }

    .hero-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .hero-placeholder {
      width: 100%;
      height: ${t.heroImageSize.height}px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: ${e.bg};
      color: ${e.muted};
      font-size: 1.5rem;
    }

    .content {
      padding: 1.5rem;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid ${e.border};
    }

    .title-block {
      flex: 1;
    }

    .name {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
      color: ${e.fg};
    }

    .id {
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
      font-size: 0.875rem;
      color: ${e.muted};
    }

    .badges {
      display: flex;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .category, .status {
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 500;
      color: white;
    }

    .description {
      margin-bottom: 1.5rem;
    }

    .description h2 {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: ${e.muted};
      margin-bottom: 0.5rem;
    }

    .description p {
      font-size: 0.9375rem;
      line-height: 1.6;
      color: ${e.fg};
    }

    .thumbnails {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      overflow-x: auto;
      padding-bottom: 0.5rem;
    }

    .thumb {
      width: ${t.thumbSize.width}px;
      height: ${t.thumbSize.height}px;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid ${e.border};
      flex-shrink: 0;
    }

    .dependencies {
      margin-bottom: 1.5rem;
    }

    .dependencies h2 {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: ${e.muted};
      margin-bottom: 0.5rem;
    }

    .dependencies ul {
      list-style: none;
    }

    .dependencies li {
      padding: 0.5rem 0.75rem;
      background: ${e.bg};
      border-radius: 4px;
      margin-bottom: 0.25rem;
      font-size: 0.875rem;
    }

    .dep-id {
      font-family: 'SF Mono', 'Monaco', monospace;
      color: ${e.accent};
      margin-right: 0.75rem;
    }

    .dep-name {
      color: ${e.fg};
    }

    .footer {
      border-top: 1px solid ${e.border};
      padding-top: 1rem;
      font-size: 0.75rem;
      color: ${e.muted};
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
    }

    .source {
      display: flex;
      gap: 0.25rem;
    }

    .source-path {
      font-family: monospace;
      color: ${e.accent};
    }

    .qr-placeholder {
      margin-left: auto;
      background: ${e.bg};
      padding: 0.5rem;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.625rem;
    }

    .project {
      width: 100%;
      text-align: center;
      margin-top: 0.5rem;
      font-weight: 500;
      padding-top: 0.5rem;
      border-top: 1px dashed ${e.border};
    }

    @media print {
      body {
        padding: 0;
        background: white;
      }
      .onesheet {
        box-shadow: none;
        border: none;
      }
    }
  `}function u(t){const e={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"};return t.replace(/[&<>"']/g,n=>e[n])}function J(t){return h(t)}function X(t){return h(t)}function Z(t){return h(t)}const ee={character:J,prop:X,wardrobe:h,set:h,shot:Z,asset:h,audio:h};function A(t){return(ee[t.item.category]||h)(t)}function O(t){return A(t)}function te(t){const e=O(t),n=new Blob([e],{type:"text/html;charset=utf-8"}),s=URL.createObjectURL(n),o=document.createElement("a");o.href=s,o.download=`${t.item.id}.html`,document.body.appendChild(o),o.click(),document.body.removeChild(o),URL.revokeObjectURL(s)}function ne(t){const e=A(t),n=window.open("","_blank");if(!n){alert("Please allow popups to print 1-sheets");return}n.document.write(e),n.document.close(),n.onload=()=>{setTimeout(()=>{n.print()},250)}}class oe{constructor(e,n={}){$(this,"config");$(this,"allItems");this.config={...G,...n},this.allItems=e}generate(e){var r;const n=this.allItems(),s=(e.depends_on||[]).map(c=>n.find(i=>i.id===c)).filter(Boolean),o=(r=e.images)==null?void 0:r[0],a=(e.images||[]).slice(1,5);return{item:e,heroImage:o,thumbnails:a,dependencies:s,config:this.config}}generateHTML(e){const n=this.generate(e);return O(n)}downloadHTML(e){const n=this.generate(e);te(n)}printPDF(e){const n=this.generate(e);ne(n)}generateAll(){const e=this.allItems(),n=[];for(const s of e)try{this.generate(s),n.push({id:s.id,status:"success",path:`.gsd-state/onesheets/${s.id}.html`})}catch(o){n.push({id:s.id,status:"error",error:String(o)})}return n}}let S=null;function se(t){return S||(S=new oe(t)),S}const ae=`
.onesheet-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.onesheet-modal.hidden {
  display: none;
}

.onesheet-preview {
  background: #1a1a2e;
  border-radius: 12px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #2a2a4a;
}

.preview-header h2 {
  font-size: 1.25rem;
  color: #eaeaea;
}

.preview-close {
  background: none;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
}

.preview-close:hover {
  color: #fff;
}

.preview-frame {
  border: none;
  flex: 1;
  min-height: 500px;
  background: #1a1a2e;
}

.preview-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #2a2a4a;
}

.preview-actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-html {
  background: #3498db;
  color: white;
}

.btn-html:hover {
  background: #2980b9;
}

.btn-pdf {
  background: #e74c3c;
  color: white;
}

.btn-pdf:hover {
  background: #c0392b;
}

.btn-close {
  background: #333;
  color: #888;
  margin-left: auto;
}

.btn-close:hover {
  background: #444;
  color: #fff;
}
`;if(typeof document<"u"&&!document.getElementById("onesheet-styles")){const t=document.createElement("style");t.id="onesheet-styles",t.textContent=ae,document.head.appendChild(t)}function re(t){var c,i,m,l;const e=se(()=>f.get()),n=e.generateHTML(t),s=document.createElement("div");s.className="onesheet-preview";const o=document.createElement("div");o.className="preview-header",o.innerHTML=`
    <h2>1-Sheet: ${t.name}</h2>
    <button class="preview-close" aria-label="Close">&times;</button>
  `;const a=document.createElement("iframe");a.className="preview-frame",a.srcdoc=n;const r=document.createElement("div");return r.className="preview-actions",r.innerHTML=`
    <button class="btn-html">Download HTML</button>
    <button class="btn-pdf">Print PDF</button>
    <button class="btn-close">Close</button>
  `,(c=o.querySelector(".preview-close"))==null||c.addEventListener("click",()=>{k()}),(i=r.querySelector(".btn-html"))==null||i.addEventListener("click",()=>{e.downloadHTML(t)}),(m=r.querySelector(".btn-pdf"))==null||m.addEventListener("click",()=>{e.printPDF(t)}),(l=r.querySelector(".btn-close"))==null||l.addEventListener("click",()=>{k()}),s.appendChild(o),s.appendChild(a),s.appendChild(r),s}let _=null;function ie(t){k();const e=document.createElement("div");e.className="onesheet-modal",e.appendChild(re(t)),e.addEventListener("click",s=>{s.target===e&&k()});const n=s=>{s.key==="Escape"&&(k(),document.removeEventListener("keydown",n))};document.addEventListener("keydown",n),document.body.appendChild(e),_=e}function k(){_&&(_.remove(),_=null)}function ce(t){const e=y.get(),n=e==null?void 0:e.categories.find(r=>r.id===t.category),s=t.blockers.length>0||t.status==="blocked",o=document.createElement("div");o.className="item-card",o.dataset.id=t.id,o.dataset.status=t.status,s&&o.classList.add("has-blockers"),o.innerHTML=`
    <div class="item-header">
      <span class="item-category" style="background: ${(n==null?void 0:n.color)||"#666"}">
        ${(n==null?void 0:n.name)||t.category}
      </span>
      <span class="item-id">${t.id}</span>
    </div>
    <h4 class="item-name">${H(t.name)}</h4>
    ${t.description?`<p class="item-description">${H(t.description)}</p>`:""}
    ${t.images.length>0?`<img src="${t.images[0]}" class="item-thumb" alt="${t.name}" onerror="this.style.display='none'" />`:""}
    ${s?`<div class="item-blocked">⚠️ ${t.blockers.length||1} blocker(s)</div>`:""}
    ${t.depends_on.length>0?`<div class="item-deps">↳ ${t.depends_on.length} dependencies</div>`:""}
    <div class="item-footer">
      ${t.assigned_to?`<span class="assigned">👤 ${t.assigned_to}</span>`:""}
      <button class="btn-onesheet" title="Generate 1-Sheet">📄</button>
    </div>
  `,o.addEventListener("click",()=>{v.set(t)});const a=o.querySelector(".btn-onesheet");return a==null||a.addEventListener("click",r=>{r.stopPropagation(),ie(t)}),o}function H(t){const e=document.createElement("div");return e.textContent=t,e.innerHTML}function le(){const t=document.createElement("div");t.className="board",t.id="board";function e(){const n=y.get(),s=V();if(!n){t.innerHTML='<p class="loading-text">Loading...</p>';return}t.innerHTML="",n.statuses.forEach(r=>{const c=s.filter(d=>d.status===r.id),i=document.createElement("div");i.className="board-column",i.style.setProperty("--status-color",r.color);const m=document.createElement("div");m.className="column-header",m.innerHTML=`
        <h3>${r.name}</h3>
        <span class="count" style="background: ${r.color}">${c.length}</span>
      `,i.appendChild(m);const l=document.createElement("div");l.className="column-content",c.length===0?l.innerHTML='<p class="empty-column">No items</p>':c.forEach(d=>{l.appendChild(ce(d))}),i.appendChild(l),t.appendChild(i)});const o=document.createElement("div");o.className="board-stats";const a=s.length;o.innerHTML=`<span>Total: ${a} items</span>`,t.appendChild(o)}return e(),f.subscribe(e),b.subscribe(e),t}function de(){const t=document.createElement("div");t.className="blocker-panel";function e(){const n=M(),s=U(),o=E.get();t.innerHTML=`
      <h3>⚠️ Blockers</h3>

      <div class="stats-summary">
        <span class="stat blocked">${n.blocked} blocked</span>
        <span class="stat total">${n.total} total</span>
      </div>

      ${s.length===0?'<p class="empty">No blockers! 🎉</p>':`
          <ul class="blocker-list">
            ${s.map(a=>`
              <li class="blocker-item" data-id="${a.id}">
                <div class="blocker-header">
                  <strong>${a.id}</strong>
                  <span class="blocker-name">${T(a.name)}</span>
                </div>
                ${a.blockers.length>0?`<ul class="blocker-reasons">
                      ${a.blockers.map(r=>`<li>${T(r)}</li>`).join("")}
                    </ul>`:'<p class="blocker-reason">Status: blocked</p>'}
              </li>
            `).join("")}
          </ul>
        `}

      ${o.length>0?`
        <div class="blocker-details">
          <h4>Active Blockers</h4>
          <ul class="blocker-detail-list">
            ${o.map(a=>`
              <li class="blocker-detail">
                <span class="blocker-id">${a.id}</span>
                <p class="blocker-reason">${T(a.reason)}</p>
                <span class="blocker-since">Since: ${a.blocking_since}</span>
              </li>
            `).join("")}
          </ul>
        </div>
      `:""}
    `,t.querySelectorAll(".blocker-item").forEach(a=>{a.addEventListener("click",()=>{const r=a.dataset.id;console.log("Blocked item:",r)})})}return e(),f.subscribe(e),E.subscribe(e),t}function T(t){const e=document.createElement("div");return e.textContent=t,e.innerHTML}function me(){const t=document.createElement("div");t.className="item-detail-overlay",t.style.display="none";function e(){var c;const n=v.get(),s=y.get();if(!n){t.style.display="none";return}t.style.display="flex";const o=s==null?void 0:s.categories.find(i=>i.id===n.category),a=s==null?void 0:s.statuses.find(i=>i.id===n.status);t.innerHTML=`
      <div class="item-detail-modal">
        <button class="close-btn" title="Close">✕</button>

        <div class="detail-header">
          <span class="detail-category" style="background: ${o==null?void 0:o.color}">
            ${o==null?void 0:o.name}
          </span>
          <span class="detail-status" style="background: ${a==null?void 0:a.color}">
            ${a==null?void 0:a.name}
          </span>
        </div>

        <h2 class="detail-id">${n.id}</h2>
        <h3 class="detail-name">${w(n.name)}</h3>

        ${n.description?`
          <p class="detail-description">${w(n.description)}</p>
        `:""}

        ${n.images.length>0?`
          <div class="detail-images">
            ${n.images.map((i,m)=>`
              <img src="${i}" alt="${n.name} image ${m+1}"
                   class="detail-image"
                   onerror="this.style.display='none'" />
            `).join("")}
          </div>
        `:""}

        <div class="detail-meta">
          <div class="meta-row">
            <span class="meta-label">Created by:</span>
            <span class="meta-value">${n.source.created_by}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Created at:</span>
            <span class="meta-value">${n.source.created_at}</span>
          </div>
          ${n.assigned_to?`
            <div class="meta-row">
              <span class="meta-label">Assigned to:</span>
              <span class="meta-value">${n.assigned_to}</span>
            </div>
          `:""}
          ${n.source.spec?`
            <div class="meta-row">
              <span class="meta-label">Source:</span>
              <a href="${n.source.spec}" class="meta-link" target="_blank">
                ${n.source.spec} →
              </a>
            </div>
          `:""}
        </div>

        ${n.blockers.length>0?`
          <div class="detail-section">
            <h4>⚠️ Blockers</h4>
            <ul class="detail-blockers">
              ${n.blockers.map(i=>`<li>${w(i)}</li>`).join("")}
            </ul>
          </div>
        `:""}

        ${n.depends_on.length>0?`
          <div class="detail-section">
            <h4>↳ Dependencies</h4>
            <ul class="detail-deps">
              ${n.depends_on.map(i=>`<li>${i}</li>`).join("")}
            </ul>
          </div>
        `:""}

        ${n.notes?`
          <div class="detail-section">
            <h4>📝 Notes</h4>
            <p class="detail-notes">${w(n.notes)}</p>
          </div>
        `:""}

        ${n.onesheet?`
          <div class="detail-actions">
            <a href="${n.onesheet}" class="btn-onesheet" target="_blank">
              View 1-Sheet →
            </a>
          </div>
        `:""}
      </div>
    `,(c=t.querySelector(".close-btn"))==null||c.addEventListener("click",()=>{v.set(null)}),t.addEventListener("click",i=>{i.target===t&&v.set(null)});const r=i=>{i.key==="Escape"&&(v.set(null),document.removeEventListener("keydown",r))};document.addEventListener("keydown",r)}return e(),v.subscribe(e),t}function w(t){const e=document.createElement("div");return e.textContent=t,e.innerHTML}async function ue(){const t=document.getElementById("app");if(!t){console.error("App container not found");return}try{x.set(!0);const[e,n,s]=await Promise.all([q(),z(),F()]);y.set(e),f.set(n),E.set(s),t.innerHTML="";const o=document.createElement("header"),a=M();o.innerHTML=`
      <h1>📋 Production Tracking</h1>
      <div class="header-stats">
        <span class="header-stat">${a.complete} complete</span>
        <span class="header-stat">${a.in_progress} in progress</span>
        <span class="header-stat">${a.blocked} blocked</span>
      </div>
    `,t.appendChild(o),t.appendChild(W());const r=document.createElement("main");r.className="main-content",r.appendChild(le()),r.appendChild(de()),t.appendChild(r),t.appendChild(me()),x.set(!1),console.log(`Loaded ${n.length} items, ${s.length} blockers`)}catch(e){x.set(!1),I.set(e instanceof Error?e.message:"Failed to load data"),t.innerHTML=`
      <div class="error-container">
        <h2>⚠️ Failed to Load</h2>
        <p>${I.get()}</p>
        <button onclick="location.reload()">Retry</button>
      </div>
    `}}ue().catch(console.error);
//# sourceMappingURL=index-XrURC3jG.js.map
