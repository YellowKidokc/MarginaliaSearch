(()=>{'use strict';const $=id=>document.getElementById(id),KEY='theophysics.behavior.v1',types=new Set(['query_submitted','result_impression','result_opened','click_depth','active_dwell_time','return_to_results','repeated_visit','saved','crawler_preservation_requested','media_download_requested','usefulness_judgment','query_reformulation']);let events=[];try{events=JSON.parse(localStorage.getItem(KEY)||'[]')}catch{events=[]}
const providerStatus={Marginalia:'CONNECTED','local index':'NOT CONNECTED',Hister:'NOT CONNECTED',SearXNG:'NOT CONNECTED',Brave:'NOT CONNECTED',Exa:'NOT CONNECTED'};$('providers').innerHTML=Object.entries(providerStatus).map(([n,s])=>`<li class="${s==='CONNECTED'?'connected':'not-connected'}">${n}: ${s}</li>`).join('');
function enabled(){return $('tracking').checked}function valid(e){return e&&e.schemaVersion==='1.0.0'&&types.has(e.type)&&e.localOnly===true&&e.truthGrade===null}function persist(){if(enabled())localStorage.setItem(KEY,JSON.stringify(events));render()}function record(type,extra={}){if(!enabled())return;const e={schemaVersion:'1.0.0',id:crypto.randomUUID(),type,occurredAt:new Date().toISOString(),localOnly:true,truthGrade:null,...extra};if(valid(e)){events.push(e);persist()}}
function render(){ $('events').textContent=enabled()?(events.length?JSON.stringify(events,null,2):'No local events.'):'History disabled.';const negatives=events.filter(e=>e.judgment==='irrelevant'||e.judgment==='hostile_control').map(e=>e.result?.url).filter(Boolean);$('projection').textContent=JSON.stringify({label:'PERSONAL RELEVANCE — NOT A TRUTH OR QUALITY GRADE',domainSeedWeights:{},topicAffinities:{},navigationTransitionProbabilities:{},explicitNegativePreferences:[...new Set(negatives)]},null,2)}
function parts(){let q=$('base').value.trim();if($('phrase').value.trim())q+=` "${$('phrase').value.trim().replaceAll('"','')}"`;for(const t of $('required').value.split(',').map(x=>x.trim()).filter(Boolean))q+=` +${t}`;for(const t of $('excluded').value.split(',').map(x=>x.trim()).filter(Boolean))q+=` -${t}`;if($('site').value.trim())q+=` site:${$('site').value.trim()}`;if($('title').checked)q+=' intitle:true';if($('file').value)q+=` filetype:${$('file').value}`;const recipes=[...document.querySelectorAll('.recipe:checked')].map(x=>x.value);return{q:q.trim(),recipes}}
function preview(){const p=parts();$('preview').textContent=p.q+(p.recipes.length?`\nRecipes: ${p.recipes.join(' + ')}`:'');$('explanations').innerHTML=p.recipes.map(x=>`<p>Applied preference: ${x} (visible, rule-based recipe)</p>`).join('')||'<p>No optional recipe applied.</p>'}document.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',preview));
$('tracking').addEventListener('change',()=>{if(enabled()){try{events=JSON.parse(localStorage.getItem(KEY)||'[]').filter(valid)}catch{events=[]}}render()});$('clear').onclick=()=>{events=[];localStorage.removeItem(KEY);render()};$('search').onclick=()=>{const p=parts();record('query_submitted',{query:p.q,details:{recipes:p.recipes,profile:$('profile').value}});location.href=`/search?query=${encodeURIComponent(p.q)}&profile=${encodeURIComponent($('profile').value)}&provider=marginalia`};
const result={url:'https://plato.stanford.edu/entries/consciousness/',provider:'marginalia'};document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{const a=b.dataset.action,s=$('action-status');if(a==='open'){record('result_opened',{result});window.open(result.url,'_blank','noopener');s.textContent='Opened. Provider provenance: Marginalia.'}else if(['useful','irrelevant','hostile_control','primary_source'].includes(a)){record('usefulness_judgment',{result,judgment:a});s.textContent='Local judgment saved; it is not a truth or quality grade.'}else if(a==='preserve'){record('crawler_preservation_requested',{result,details:{explicitUserIntent:true}});s.textContent='Explicit intent recorded locally. Crawl4AI adapter is NOT CONNECTED; no crawl started.'}else if(a==='native_crawl'){s.textContent='Native queue requires the live authenticated local service; no request sent.'}else if(a==='save'||a==='return_later'){record('saved',{result,details:{bucket:a}});s.textContent='Saved locally only; saving does not canonize.'}else{s.textContent='Upstream relevance signals plus visible profile recipes; personal history is not applied.'};s.className='status'});
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({schemaVersion:'1.0.0',exportedAt:new Date().toISOString(),events},null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='theophysics-local-events.json';a.click();URL.revokeObjectURL(a.href)};$('import').onchange=async e=>{try{const d=JSON.parse(await e.target.files[0].text());if(!Array.isArray(d.events)||!d.events.every(valid))throw Error('Invalid event contract');events=d.events;persist()}catch(err){$('action-status').textContent=`Import rejected: ${err.message}`}};preview();render();window.TheophysicsWorkbench={parts,valid,providerStatus};})();

// URL → Markdown is served by the local companion process. No API credential enters this browser bundle.
(() => {
    "use strict";
    const byId = (id) => document.getElementById(id);
    const urls = byId("markdown-urls");
    if (!urls) return;
    const review = byId("markdown-review");
    const status = byId("markdown-status");
    const actionIds = ["markdown-copy", "markdown-download", "markdown-save", "markdown-claims"];
    let previews = [];

    function enableActions(enabled) {
        actionIds.forEach((id) => { byId(id).disabled = !enabled; });
    }

    function escapeHtml(value) {
        const element = document.createElement("span");
        element.textContent = value;
        return element.innerHTML;
    }

    function renderReview() {
        review.className = "";
        review.innerHTML = previews.map((item, index) => {
            if (item.status === "failed") {
                return `<article class="capture-review error"><strong>${escapeHtml(item.originalUrl)}</strong><p>Failed: ${escapeHtml(item.error)}</p><p>Providers tried: local. Optional fallbacks available separately: ${item.fallbacks.join(", ")}.</p></article>`;
            }
            const warnings = item.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
            return `<article class="capture-review"><label><input class="capture-approved" data-index="${index}" type="checkbox"> Reviewed and approved to save</label><h4>${escapeHtml(item.pageTitle)}</h4><div class="capture-meta">Original URL: ${escapeHtml(item.originalUrl)}<br>Retrieved: ${escapeHtml(item.retrievedAt)}<br>Hash: ${escapeHtml(item.contentHash)}<br>Method: ${escapeHtml(item.extractionMethod)}<br>Provider succeeded: ${escapeHtml(item.provider)}</div>${warnings ? `<ul class="error">${warnings}</ul>` : ""}<textarea class="markdown-preview" readonly>${escapeHtml(item.markdown)}</textarea><strong>${escapeHtml(item.evidenceStatus)}</strong></article>`;
        }).join("");
        review.querySelectorAll(".capture-approved").forEach((checkbox) => checkbox.addEventListener("change", updateSaveState));
        enableActions(previews.some((item) => item.status !== "failed"));
        updateSaveState();
    }

    function approvedTokens() {
        return [...review.querySelectorAll(".capture-approved:checked")].map((box) => previews[Number(box.dataset.index)].previewToken);
    }

    function updateSaveState() {
        const approved = approvedTokens().length > 0;
        byId("markdown-save").disabled = !approved;
        byId("markdown-claims").disabled = !approved;
    }

    async function post(path, body) {
        const response = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
        return payload;
    }

    byId("markdown-preview").addEventListener("click", async () => {
        const list = urls.value.split(/\r?\n/).map((url) => url.trim()).filter(Boolean);
        if (!list.length) { status.textContent = "Paste at least one URL."; return; }
        status.textContent = "Previewing without writing…";
        enableActions(false);
        try {
            const payload = await post("/theophysics/api/markdown/preview", {urls: list, provider: "local"});
            previews = payload.items;
            renderReview();
            status.textContent = `Previewed ${previews.length}; no capture was written. Review and approve before saving.`;
        } catch (error) {
            status.textContent = `Preview failed: ${error.message}. Start the local Markdown service described in the README.`;
        }
    });

    byId("markdown-copy").addEventListener("click", async () => {
        await navigator.clipboard.writeText(previews.filter((item) => item.markdown).map((item) => item.markdown).join("\n\n---\n\n"));
        status.textContent = "Preview Markdown copied; no capture was saved.";
    });

    byId("markdown-download").addEventListener("click", () => {
        const markdown = previews.filter((item) => item.markdown).map((item) => item.markdown).join("\n\n---\n\n");
        const anchor = document.createElement("a");
        anchor.href = URL.createObjectURL(new Blob([markdown], {type: "text/markdown"}));
        anchor.download = previews.length === 1 ? "capture.md" : "capture-batch.md";
        anchor.click();
        URL.revokeObjectURL(anchor.href);
    });

    async function save(destination) {
        status.textContent = "Saving reviewed immutable version…";
        try {
            const payload = await post("/theophysics/api/markdown/save", {previewTokens: approvedTokens(), destination});
            status.textContent = `${payload.saved.length} immutable version(s) saved. Canonized: ${payload.canonized}.`;
        } catch (error) {
            status.textContent = `Save failed: ${error.message}`;
        }
    }
    byId("markdown-save").addEventListener("click", () => save("research-intake"));
    byId("markdown-claims").addEventListener("click", () => save("claim-extraction-staging"));

    function queueResult(url) {
        urls.value = url;
        urls.scrollIntoView({behavior: "smooth", block: "center"});
        status.textContent = "Result URL added. Select Preview Markdown to begin; nothing has been written.";
    }
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".convert-result");
        if (button) queueResult(button.dataset.resultUrl);
    });
    document.querySelector('[data-action="convert_markdown"]')?.addEventListener("click", () => queueResult("https://plato.stanford.edu/entries/consciousness/"));

    // Decorate result elements added by normal or mock rendering without changing provider/ranking behavior.
    function decorateResults(root = document) {
        root.querySelectorAll(".result:not([data-markdown-action])").forEach((result) => {
            const link = result.querySelector("a[href^='http']");
            if (!link) return;
            const button = document.createElement("button");
            button.className = "convert-result";
            button.dataset.resultUrl = link.href;
            button.textContent = "Convert to Markdown";
            result.append(button);
            result.dataset.markdownAction = "true";
        });
    }
    decorateResults();
    new MutationObserver(() => decorateResults()).observe(document.body, {childList: true, subtree: true});
})();
