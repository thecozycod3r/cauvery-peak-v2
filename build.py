#!/usr/bin/env python3
"""Assemble the Cauvery Peak review site.

Pages are content fragments in _src_pages/. This wraps each one in the shared
document, header, mobile drawer and footer so there is exactly one copy of the
chrome. Assets are real files, not data URIs, so the browser caches them across
pages.
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
SRC = os.path.join(HERE, "_src_pages")

# where this build is actually served from — used for canonical + og:url
BASE = "https://thecozycod3r.github.io/cauvery-peak-v2"

# The nav carries the story. The three things we want people to DO are
# buttons, not nav items — "Coffee" and "Shop" used to be two doors to the
# same job and the visitor had to guess which one bought a bag.
NAV = [
    ("The coffee", "coffee.html"),
    ("The estate", "estate.html"),
    ("The tour",   "visit.html"),
    ("Caf&eacute;s", "cafes.html"),
    ("Learn",      "brewing.html"),
]

# The three actions. One name and one destination for each, used in the
# header, the drawer, the mobile bar, every page closer and the footer.
ACT_SHOP  = ("Shop Coffee",        "shop.html")
ACT_VISIT = ("Visit the Estate",   "visit.html")
ACT_BOOK  = ("Book the Experience","p-coffee-experience-tours-11.html")

FOOT = [
    ("Shop Coffee", [("Estate coffee","shop-coffee.html"),("Samplers &amp; drip bags","shop-samplers.html"),
                ("Subscriptions","subscribe.html"),("Spices &amp; honey","shop-spices-honey.html")]),
    ("Visit the Estate",  [("Book the Experience","p-coffee-experience-tours-11.html"),
                ("What the tour covers","visit.html"),
                ("The three caf&eacute;s","cafes.html"),("Find us","contact.html")]),
    ("The estate", [("Grower to Connoisseur","estate.html"),("Our story","story.html"),
                    ("History","history.html"),("The environment","environment.html"),
                    ("Careers","careers.html")]),
    ("Learn",  [("Brewing guide","brewing.html"),("Grind guide","grind.html"),
                ("In the press","press.html"),("On BBC News Tamil","bbc-news-tamil.html"),
                ("Contact","contact.html")]),
]

# These used to point at cauverypeakestate.com, so clicking "Privacy" on the
# review build dropped you onto the old site in the old design — which rather
# defeats a design review. The pages now live here, carrying the store's own
# policy text verbatim. The live store remains the authoritative copy; if the
# client edits a policy in Shopify, re-run scripts/fetch_policies.py.
LEGAL = [
    ("Privacy",  "privacy.html"),
    ("Terms",    "terms.html"),
    ("Shipping", "shipping.html"),
    ("Returns",  "returns.html"),
]

# Instagram is confirmed. Facebook and WhatsApp are omitted rather than linked
# to "#" — the WhatsApp number is one of the disputed ones (see README).
# (name, url, visible handle). The handle is shown beside the icon: a lone
# glyph in a box was not recognisable as Instagram, and the handle is what
# someone actually needs if they want to find the account themselves.
# YouTube is the channel the live contact page links to.
SOCIAL = [("Instagram", "https://www.instagram.com/cauverypeakcoffee/", "@cauverypeakcoffee"),
          ("YouTube", "https://www.youtube.com/@cauverypeak2249", "@cauverypeak2249")]

PLACES = [
    ("cp", "Cauvery Peak Estate Caf&eacute;", "On the plantation, 15 km from Yercaud town.", "cafe-cauvery-peak.html"),
    ("sh", "Lake View Village Caf&eacute;",   "Yercaud Main Road. Parking available.",       "cafe-lake-view.html"),
    ("gf", "Glenfell Kiosk",                  "17th hairpin bend, Salem&ndash;Yercaud ghat road.", "cafe-glenfell.html"),
]

# Confirmed by MSP Plantations, 16 Aug 2026. The live store's own café pages
# still disagree with these (Glenfell and Lake View say 6pm, and each lists a
# mobile number one digit off) — these are the ones to trust.
CAFES = {
 "cafe-cauvery-peak.html": {"name":"Cauvery Peak Estate Café", "opens":"07:30", "closes":"17:00",
     "tel":["+917598435955","+919487458387"], "street":"MSP Plantations, Cauvery Peak Estate",
     "postal":"636602", "img":"cafe/cp-1.webp"},
 "cafe-lake-view.html": {"name":"Lake View Village Café", "opens":"08:00", "closes":"17:00",
     "tel":["+917598435955","+916380805161"], "street":"MSP Plantations, Yercaud Main Road",
     "postal":None, "img":"cafe/lv-1.webp"},
 "cafe-glenfell.html": {"name":"Glenfell Estate Kiosk", "opens":"07:30", "closes":"17:00",
     "tel":["+917598435955","+919489180236"], "street":"MSP Plantations, 17th Hairpin Bend, Salem–Yercaud Ghat Road",
     "postal":None, "img":"cafe/gf-3.webp"},
}

IG = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
      '<rect x="3" y="3" width="18" height="18" rx="5"/>'
      '<circle cx="12" cy="12" r="4"/>'
      '<circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/>'
      '</svg>')
YT = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round">'
      '<rect x="2.5" y="5" width="19" height="14" rx="4"/>'
      '<path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor" stroke="none"/>'
      '</svg>')
SOCIAL_SVG = {"Instagram": IG, "YouTube": YT}


# pages that belong under a nav item without being its target
NAV_SECTION = {"p-coffee-experience-tours-11.html": "visit.html", "bbc-news-tamil.html": "visit.html",
               "cafe-cauvery-peak.html": "cafes.html", "cafe-lake-view.html": "cafes.html",
               "cafe-glenfell.html": "cafes.html", "grind.html": "brewing.html"}

def header(active):
    active = NAV_SECTION.get(active, active)
    links = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if href == active else ""}>{label}</a>'
        for label, href in NAV)
    # every store page counts as the shop, except the tour (sold as a product)
    shop_section = (active.startswith(("shop", "p-")) and active not in NAV_SECTION) or active == "subscribe.html"
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="top__in">
    <a href="index.html" class="top__home" aria-label="Cauvery Peak, home">
      <img class="top__logo" src="assets/logo_dark.webp" alt="Cauvery Peak" width="300" height="239" fetchpriority="high">
    </a>
    <nav class="top__nav" aria-label="Main">
{links}
      <a class="top__buy" href="{ACT_SHOP[1]}"{" aria-current=\"page\"" if shop_section else ""}><span>Buy coffee</span></a>
    </nav>
    <button class="burger" type="button" id="burger" aria-expanded="false" aria-controls="sitemenu">
      <span class="burger__box" aria-hidden="true"><i></i><i></i><i></i></span>
      <span class="burger__t">Menu</span>
    </button>
    <div class="top__act">
      <a class="btn btn--fill btn--sm top__cta" href="{ACT_BOOK[1]}">Book the tour</a>
      <a class="iconbtn" href="search.html" aria-label="Search"{' aria-current="page"' if active == "search.html" else ""}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/></svg>
      </a>
      <a class="iconbtn" href="wishlist.html" id="wishbtn" aria-label="Wishlist" hidden>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>
        <b class="num">0</b>
      </a>
      <button class="cartbtn" type="button" id="cartbtn" aria-label="Basket, 0 items">Basket <b class="num">0</b></button>
    </div>
  </div>
</header>'''


def drawer(active):
    groups = "\n".join(
        '      <div class="dnav__g">\n        <h2 class="dnav__h">%s</h2>\n        <ul class="dnav__l">\n%s\n        </ul>\n      </div>' % (
            title,
            "\n".join(
                '          <li><a href="%s"%s>%s</a></li>' % (
                    h, ' aria-current="page"' if h.split("#")[0] == active else "", t)
                for t, h in items))
        for title, items in FOOT)
    return f'''<div class="drawer" id="sitemenu">
  <div class="drawer__scrim" data-close></div>
  <div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Site menu">
    <div class="drawer__head">
      <a href="index.html" class="drawer__home">Cauvery Peak</a>
      <button class="drawer__x" type="button" data-close aria-label="Close menu">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>
      </button>
    </div>
    <nav class="dnav" aria-label="All pages">
{groups}
    </nav>
    <div class="drawer__cta">
      <a class="btn btn--fill" href="{ACT_SHOP[1]}">{ACT_SHOP[0]}</a>
      <a class="btn btn--ink" href="{ACT_VISIT[1]}">{ACT_VISIT[0]}</a>
      <a class="btn btn--ink" href="{ACT_BOOK[1]}">{ACT_BOOK[0]}</a>
    </div>
    <p class="drawer__meta">MSP Plantations &middot; Yercaud, Tamil Nadu</p>
  </div>
</div>'''


def footer():
    cols = "\n".join(
        '        <div>\n          <h2 class="foot__h">%s</h2>\n          <ul class="foot__l">\n%s\n          </ul>\n        </div>' % (
            title, "\n".join(f'            <li><a href="{h}">{t}</a></li>' for t, h in items))
        for title, items in FOOT)
    places = "\n".join(
        f'''      <div class="foot__place" style="--c:var(--{c})">
        <h2 class="foot__pn">{name}</h2>
        <p class="foot__pd">{desc}</p>
        <a class="foot__pl" href="{href}">Hours &amp; directions &rarr;</a>
      </div>''' for c, name, desc, href in PLACES)
    legal = "".join(f'<li><a href="{h}">{t}</a></li>' for t, h in LEGAL)
    social = "\n".join(
        f'        <a class="foot__soc" href="{h}" rel="me noopener" target="_blank">'
        f'<span class="foot__ico">{SOCIAL_SVG[n]}</span>'
        f'<span class="foot__handle"><span class="foot__net">{n}</span>{handle}</span></a>'
        for n, h, handle in SOCIAL)
    return f'''<footer class="foot">
  <div class="sheet">
    <div class="foot__grid">
      <div>
        <img class="foot__logo" src="assets/logo_light.webp" alt="Cauvery Peak" width="300" height="239" loading="lazy">
        <p class="mark mark--d" style="margin-top:1rem">Growing since 1867</p>
        <p class="body" style="color:var(--onDark-2); margin-top:.6rem; max-width:32ch">A working coffee estate in the Shevaroy Hills, farmed by the same family for five generations.</p>
      </div>
      <nav class="foot__cols" aria-label="Footer">
{cols}
      </nav>
    </div>
    <div class="foot__places">
{places}
    </div>
    <div class="foot__bar">
      <ul class="foot__legal">{legal}</ul>
      <div class="foot__social">
{social}
      </div>
      <span class="num">11&deg;46&prime;N 78&deg;12&prime;E &middot; 4,100&ndash;4,800 FT</span>
    </div>
  </div>
</footer>'''



# Every editorial page used to dead-end. Each now closes by pointing at the
# shop, in words that follow from what the page just said rather than a
# generic banner bolted on the bottom.
# Every editorial page used to dead-end, and then it closed on the shop and
# only the shop. Each closer now names the action that actually follows from
# what the page just said, and offers a second door beside it — so the
# storytelling leads somewhere instead of looping into more storytelling.
# (eyebrow, heading, lede, primary action, secondary action)
SHOP, VISIT, BOOK = "shop", "visit", "book"
CLOSERS = {
 "brewing.html":     ("Now the coffee", "You have the method.<br>This is what to put in it.",
                      "Every bag is ground for your brewer before it ships &mdash; choose the method on the product page and we do the rest.",
                      SHOP, VISIT),
 "grind.html":       ("Pick a coffee", "You do not need a grinder.",
                      "Whichever grind you landed on is an option on every bag we sell. We grind it to order, after you buy it.",
                      SHOP, VISIT),
 "estate.html":      ("Nine stages done", "All of that, in a bag.<br>Or all of it, in person.",
                      "Every coffee in the shop went through the nine stages on this page. The tour takes you through the mills and the roasting room where they happen.",
                      SHOP, BOOK),
 "environment.html": ("From this ground", "Taste what the forest made.",
                      "Shade, rainfall and bauxite soil are not a story we tell. They are why the cup tastes the way it does.",
                      SHOP, VISIT),
 "history.html":     ("Still growing it", "A hundred and fifty years,<br>and this season&rsquo;s crop.",
                      "The Hawaiian Red Caturra that MSP Rajes carried back in 1965 is what you are buying today.",
                      SHOP, VISIT),
 "story.html":       ("What we grow", "That is who we are.<br>This is what we sell.",
                      "Three single estates, two blends, and the spices and honey grown between them.",
                      SHOP, VISIT),
 "press.html":       ("Judge it yourself", "Read about it, or drink it.",
                      "Kenneth Davids rated it among the top three Indian Arabicas. The bag costs less than the argument.",
                      SHOP, VISIT),
 "cafes.html":       ("Take some home", "Drink it here.<br>Or drink it at home.",
                      "The same coffee poured in all three caf&eacute;s, roasted to order and sent from the estate.",
                      BOOK, SHOP),
 "visit.html":       ("Cannot come up?", "We will send it down.",
                      "The tour is the best way to understand the coffee. Ordering it is the second best.",
                      BOOK, SHOP),
 "contact.html":     ("Or just order", "Roasted after you ask for it.",
                      "Nothing is roasted before an order exists, which is why it does not sit in a warehouse.",
                      SHOP, BOOK),
 "cafe-cauvery-peak.html": ("While you are here", "Walk the estate<br>behind the café.",
                      "The Coffee Experience Tour starts where you are sitting &mdash; ninety minutes through the mills and the roasting room.",
                      BOOK, SHOP),
 "cafe-lake-view.html": ("Fifteen kilometres on", "The coffee comes<br>from up the road.",
                      "The estate itself is a short drive from here, and the tour runs from the plantation café.",
                      VISIT, SHOP),
 "cafe-glenfell.html": ("Halfway up", "Keep climbing.<br>The estate is at the top.",
                      "Glenfell is the lowest of the three estates. Cauvery Peak, where the tour runs, is up the hill.",
                      VISIT, SHOP),
 "bbc-news-tamil.html": ("You have seen the film", "Now take the tour.",
                      "Ninety minutes, &#8377;600 a person, in your own vehicle with a coffee guide: the wet mill, the dry mill, roasting and grinding, the estate museum, and the caf&eacute; to finish. Closed Tuesdays.",
                      BOOK, SHOP),
 "careers.html":     ("Meanwhile", "See the place first.",
                      "The best way to know whether you want to work here is to walk it.",
                      VISIT, SHOP),
 "coffee.html":      ("Buy it", "Pick a grind and a size.",
                      "Eleven grinds, three pack sizes, and we grind to order after you choose.",
                      SHOP, BOOK),
}

ACTIONS = {SHOP: ACT_SHOP, VISIT: ACT_VISIT, BOOK: ACT_BOOK}

def closer(slug):
    """Close the page on the action that follows from it, and name the other
    two so no page is ever a dead end."""
    if slug not in CLOSERS: return ""
    eb, head, lede, a1, a2 = CLOSERS[slug]
    l1, h1 = ACTIONS[a1]
    l2, h2 = ACTIONS[a2]
    # the third door, unless it points back at the page you are already on
    rest = [k for k in (SHOP, VISIT, BOOK)
            if k not in (a1, a2) and ACTIONS[k][1] != slug]
    third = ""
    if rest:
        l3, h3 = ACTIONS[rest[0]]
        third = f'<p class="closer__or">Or <a href="{h3}">{l3.lower()}</a>.</p>'
    return f'''<section class="band">
  <div class="sheet ruled">
    <div class="ruled__mark">
      <span class="ruled__i ruled__i--dot num">&#9679;</span>
      <span class="ruled__l">What next</span>
    </div>
    <div>
      <p class="mark">{eb}</p>
      <h2 class="d2">{head}</h2>
      <p class="lede" style="margin-top:1.25rem">{lede}</p>
      <div class="btns" style="margin-top:1.75rem">
        <a class="btn btn--gold" href="{h1}">{l1}</a>
        <a class="btn btn--ghost" href="{h2}">{l2}</a>
      </div>
      {third}
    </div>
  </div>
</section>'''


CART = '''<div class="cart" id="cart">
  <div class="cart__scrim" data-cclose></div>
  <div class="cart__panel" role="dialog" aria-modal="true" aria-label="Your basket">
    <div class="cart__head">
      <p class="mark" style="margin:0">Your basket</p>
      <button class="drawer__x" type="button" data-cclose aria-label="Close basket">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>
      </button>
    </div>
    <div class="cart__body" data-clines></div>
    <div class="cart__foot">
      <p class="cart__ship" data-cgoods><span>Shipping</span><b>Free across India</b></p>
      <p class="cart__sum"><span>Total</span><b class="num" data-ctotal>&#8377;0</b></p>
      <a class="btn btn--gold" data-ccheckout href="https://cauverypeakestate.com/collections/all">Secure checkout</a>
      <p class="buy__note" style="margin:0" data-cnote>Payment is taken on the estate&rsquo;s Shopify checkout.</p>
    </div>
  </div>
</div>'''

# The bar repeats the hero's own two buttons, so on the homepage it used to
# sit directly under an identical "Shop Coffee". It stays hidden until the
# first screen has scrolled away and there is no longer a CTA in view.
STICKY_JS = """<script>
(function(){
  var bar=document.querySelector('.sticky'); if(!bar) return;
  var hero=document.querySelector('.hero,.phero');
  if(!hero){ bar.classList.add('is-on'); return; }
  if(!('IntersectionObserver' in window)){ bar.classList.add('is-on'); return; }
  new IntersectionObserver(function(es){
    bar.classList.toggle('is-on', !es[0].isIntersecting);
  },{threshold:0}).observe(hero);
})();
</script>"""

STICKY = f'''<div class="sticky">
  <a class="btn btn--gold" href="{ACT_SHOP[1]}">{ACT_SHOP[0]}</a>
  <a class="btn btn--ghost" href="{ACT_BOOK[1]}">Book the tour</a>
</div>'''

STICKY_BUY = '''<div class="sticky sticky--buy">
  <p class="sticky__p num" data-sticky-price></p>
  <button class="btn btn--gold" type="button" data-sticky-add>Add to cart</button>
</div>'''
STICKY_BUY_JS = r"""<script>
(function(){
  var bar=document.querySelector('.sticky--buy'), add=document.querySelector('.pdp [data-add]'),
      price=document.querySelector('.pdp [data-price]'), out=bar&&bar.querySelector('[data-sticky-price]');
  if(!bar||!add||!price) return;
  var btn=bar.querySelector('[data-sticky-add]'); btn.textContent=add.textContent;
  var form=document.querySelector('.pdp .buy');
  function sync(){
    var bits=[]; if(form) form.querySelectorAll('input[name^="o"]:checked, select[name^="o"]').forEach(function(e){
      var v=(e.value||'').replace(/\s*\([^)]*\)/g,''); if(v&&v!=='Default Title') bits.push(v==='Whole Beans'?'Whole beans':v); });
    out.innerHTML=''; out.appendChild(document.createTextNode(price.textContent));
    if(bits.length){ var sm=document.createElement('small'); sm.textContent=bits.join(' · '); out.appendChild(sm); }
  }
  if(form) form.addEventListener('change', function(){ setTimeout(sync,0) });
  sync(); new MutationObserver(sync).observe(price,{childList:true,characterData:true,subtree:true});
  btn.addEventListener('click',function(){ add.click() });
  // on only once the real button is above the viewport. A scroll check, not an
  // IntersectionObserver: a fling or a restored scroll position can jump from
  // below the button to above it without ever intersecting, and IO would miss it.
  var queued=false;
  function check(){ queued=false; bar.classList.toggle('is-on', add.getBoundingClientRect().bottom<0) }
  addEventListener('scroll',function(){ if(!queued){ queued=true; requestAnimationFrame(check) } },{passive:true});
  addEventListener('resize',check); check();
})();
</script>"""

# Live price + availability for every variant, from the catalogue, so a basket
# saved days ago is re-priced (and sold-out lines flagged) before checkout.
def _price_map():
    cat = json.load(open(os.path.join(SRC, "catalog.json")))
    return json.dumps({str(v["id"]): [v["p"], 1 if v["av"] else 0] for p in cat for v in p["variants"]}, separators=(",", ":"))
PRICE_MAP = "<script>window.CPV=%s</script>" % _price_map()

# Small enough to inline. Runs on every page; the drawer is inert until opened.

SHOP_JS = r"""<script>
(function(){
  var KEY='cp-basket', STORE='https://cauverypeakestate.com', TOUR='coffee-experience-tours-11';
  var read=function(){ try{ return JSON.parse(localStorage.getItem(KEY))||[] }catch(e){ return [] } };
  var write=function(v){ try{ localStorage.setItem(KEY, JSON.stringify(v)) }catch(e){} paint(); };
  var inr=function(n){ return '₹'+Math.round(n).toLocaleString('en-IN'); };
  var CPV=window.CPV||{};
  var esc=function(t){ var d=document.createElement('div'); d.textContent=t==null?'':String(t); return d.innerHTML; };
  // one place that puts a variant in the basket
  function addLine(v, t, o, h, img, q, a){
    var b=read(), hit=b.filter(function(l){ return l.id===v.id && JSON.stringify(l.a||null)===JSON.stringify(a||null) })[0];
    if(hit) hit.q+=q||1; else b.push({id:v.id,q:q||1,p:v.p,t:t,o:o,h:h,i:img||'',a:a||null});
    write(b); open();
  }
  function grams(s){
    var m=/([\d.]+)\s*(kg|g|gm)\b/i.exec(s||''); if(!m) return 0;
    var n=parseFloat(m[1])*(/kg/i.test(m[2])?1000:1), k=/x\s*(\d+)/i.exec(s||''); return n*(k?parseInt(k[1],10):1);
  }
  var pretty=function(x){ return (x||'').replace(/\s*\([^)]*\)/g,'') };

  // ---- product page forms ----------------------------------------
  document.querySelectorAll('.pdp[data-variants]').forEach(function(scope){
    var vs, form=scope.querySelector('.buy');
    try{ vs=JSON.parse(scope.getAttribute('data-variants')) }catch(e){ return }
    if(!form||!vs) return;
    var out=scope.querySelector('[data-price]'), unit=scope.querySelector('[data-unit]'), per=scope.querySelector('[data-per]');
    var save=scope.querySelector('[data-save]'), singles=null, add=form.querySelector('[data-add]');
    var label=add?add.textContent:'Add to cart';
    try{ singles=JSON.parse(scope.getAttribute('data-singles')||'null') }catch(e){}
    var handle=scope.getAttribute('data-handle'), title=scope.getAttribute('data-title');
    var pack=scope.querySelector('.pdp__pack'), img=pack?pack.getAttribute('src'):'';
    function chosen(){
      return [1,2,3].map(function(i){
        var el=form.querySelector('input[name="o'+i+'"]:checked')||form.querySelector('select[name="o'+i+'"]');
        return el?el.value:null;
      });
    }
    function match(){
      var c=chosen();
      return vs.filter(function(v){ return c.every(function(x,i){ return x===null || v.o[i]===x; }); })[0];
    }
    function months(s){ var m=/(\d+)\s*month/i.exec(s||''); return m?parseInt(m[1],10):0; }
    function paintPrice(){
      var v=match();
      if(add){ var ok=!!(v&&v.av!==false); add.disabled=!ok; add.textContent=ok?label:'Sold out'; }
      if(!v) return;
      out.textContent=inr(v.p);
      scope.querySelectorAll('[data-price-mirror]').forEach(function(e){ e.textContent=inr(v.p) });
      var c=chosen(), g=0; c.forEach(function(x){ g=g||grams(x) });
      if(per) per.textContent = g && !months(c[0]) ? inr(v.p*100/g)+' per 100 g' : '';
      if(unit){
        var kg=grams(c[2])/1000, mo=months(c[0]);
        unit.textContent = (kg&&mo) ? inr(v.p/(kg*mo))+' per kg · '+mo+' months' : '';
      }
      if(save){
        var one=singles&&singles[c[1]]&&singles[c[1]][c[2]], m2=months(c[0]);
        var d=one&&m2 ? one*m2-v.p : 0;
        save.textContent = d>0 ? 'Saves '+inr(d)+' ('+Math.round(100*d/(one*m2))+'%) against '+m2+' single packs' : '';
      }
      // mark choices the store has no live variant for
      form.querySelectorAll('.opt').forEach(function(l){
        var inp=l.querySelector('input'); if(!/^o\d$/.test(inp.name)) return;
        var i=parseInt(inp.name.slice(1),10)-1;
        var probe=chosen(); probe[i]=inp.value;
        var ok=vs.some(function(v){ return v.av!==false && probe.every(function(x,j){ return x===null||v.o[j]===x }) });
        if(ok) l.removeAttribute('data-out'); else l.setAttribute('data-out','');
      });
    }
    // whole beans vs ground: the brew-method list only matters once 'Ground' is chosen
    var gsel=form.querySelector('[data-gselect]'), gwrap=form.querySelector('[data-gsel]'), lastGround=gsel?gsel.value:null;
    function gmode(){
      if(!gsel) return; var m=form.querySelector('[name="gmode"]:checked'), ground=m&&m.value==='ground';
      gwrap.hidden=!ground;
      if(ground){ if(gsel.value==='Whole Beans') gsel.value=lastGround&&lastGround!=='Whole Beans'?lastGround:'Indian Filter'; }
      else { if(gsel.value!=='Whole Beans') lastGround=gsel.value; gsel.value='Whole Beans'; }
    }
    form.querySelectorAll('[name="gmode"]').forEach(function(r){ r.addEventListener('change', function(){ gmode(); paintPrice(); }) });
    gmode();
    // quantity stepper
    var qty=form.querySelector('[name="qty"]');
    form.querySelectorAll('[data-qd]').forEach(function(b){ b.addEventListener('click', function(){
      qty.value=Math.max(1,Math.min(20,(parseInt(qty.value,10)||1)+parseInt(b.getAttribute('data-qd'),10))); }) });
    // tour: no past dates
    var td=form.querySelector('[name="tdate"]');
    if(td){ var t=new Date(); td.min=new Date(t.getTime()-t.getTimezoneOffset()*6e4).toISOString().slice(0,10);
      td.addEventListener('change', function(){ var e=form.querySelector('[data-terr]'); if(e) e.textContent=td.value&&new Date(td.value+'T12:00').getDay()===2?'The estate is closed on Tuesdays. Choose another day.':''; }); }
    // gallery thumbnails
    var main=scope.querySelector('[data-gmain]');
    scope.querySelectorAll('[data-gimg]').forEach(function(th){ th.addEventListener('click', function(){
      if(!main) return; main.src=th.getAttribute('data-gimg'); main.setAttribute('data-mode', th.getAttribute('data-gmode'));
      scope.querySelectorAll('[data-gimg]').forEach(function(x){ x.classList.toggle('is-on', x===th); if(x===th) x.setAttribute('aria-current','true'); else x.removeAttribute('aria-current'); });
    }) });
    form.addEventListener('change', paintPrice);
    form.addEventListener('input', paintPrice);
    paintPrice();
    if(add) add.addEventListener('click', function(){
      var v=match(); if(!v||v.av===false) return;
      var q=1, a=null, qty=form.querySelector('[name="qty"]');
      if(qty) q=Math.max(1,Math.min(20,parseInt(qty.value,10)||1));
      if(handle===TOUR){
        var d=form.querySelector('[name="tdate"]'), sl=form.querySelector('[name="tslot"]:checked'), err=form.querySelector('[data-terr]');
        var msg=!d||!d.value?'Choose a date.':(new Date(d.value+'T12:00').getDay()===2?'The estate is closed on Tuesdays. Choose another day.':(!sl?'Choose a departure.':''));
        if(err) err.textContent=msg;
        if(msg){ (d&&!d.value?d:(sl?d:form.querySelector('[name="tslot"]'))).focus(); return; }
        a={date:d.value, slot:sl.value};
      }
      var o=chosen().filter(function(x){ return x && x!=='Default Title' }).map(pretty).join(' · ');
      if(a) o=new Date(a.date+'T12:00').toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short'})+' · '+a.slot;
      addLine(v, title, o, handle, img, q, a);
    });
  });

  // ---- shop cards: buy without leaving the grid ---------------------
  document.querySelectorAll('.pc[data-v]').forEach(function(card){
    var vs; try{ vs=JSON.parse(card.getAttribute('data-v')) }catch(e){ return }
    var form=card.querySelector('.pc__buy'), btn=card.querySelector('[data-qadd]'), price=card.querySelector('[data-qprice]'), per=card.querySelector('[data-per]');
    function chosen(){
      return [1,2,3].map(function(i){
        var el=form.querySelector('[name="o'+i+'"]:checked')||form.querySelector('select[name="o'+i+'"],input[type=hidden][name="o'+i+'"]');
        return el?el.value:null;
      });
    }
    function match(){ var c=chosen(); return vs.filter(function(v){ return c.every(function(x,i){ return x===null||v.o[i]===x }) })[0]; }
    function sync(){
      var v=match(), ok=!!(v&&v.av);
      btn.disabled=!ok; price.textContent=ok?inr(v.p):'Sold out';
      btn.firstChild.nodeValue=ok?'Add ':'';
      if(per){ var g=0; chosen().forEach(function(x){ g=g||grams(x) }); per.textContent=ok&&g?inr(v.p*100/g)+' / 100 g':''; }
    }
    form.addEventListener('change', sync); sync();
    btn.addEventListener('click', function(){
      var v=match(); if(!v||!v.av) return;
      var o=chosen().filter(function(x){ return x && x!=='Default Title' }).map(pretty).join(' · ');
      addLine(v, card.getAttribute('data-title'), o, card.getAttribute('data-handle'), card.getAttribute('data-img'));
      btn.classList.add('is-added'); setTimeout(function(){ btn.classList.remove('is-added') }, 1400);
    });
  });

  // ---- shop taste filter ------------------------------------------
  var chips=document.querySelectorAll('[data-filter]');
  if(chips.length){
    var cards=[].slice.call(document.querySelectorAll('.pgrid--coffee .pc')), fc=document.querySelector('[data-fcount]');
    chips.forEach(function(ch){ ch.addEventListener('click', function(){
      var k=ch.getAttribute('data-filter'), n=0;
      chips.forEach(function(c){ c.setAttribute('aria-pressed', c===ch?'true':'false') });
      cards.forEach(function(c){ var on=!k||(' '+c.getAttribute('data-tags')+' ').indexOf(' '+k+' ')>-1; c.hidden=!on; if(on) n++; });
      document.querySelectorAll('.pgrid--coffee').forEach(function(g){ var s=g.closest('.ssec'); if(s) s.hidden=![].some.call(g.children,function(c){ return !c.hidden }) });
      if(fc) fc.textContent=k?n+' coffee'+(n===1?'':'s')+' match.':'';
    }); });
  }

  // ---- wishlist ----------------------------------------------------
  // Kept in this browser only. Same pattern as the basket: no account, no server.
  var WKEY='cp-wish';
  var wread=function(){ try{ return JSON.parse(localStorage.getItem(WKEY))||[] }catch(e){ return [] } };
  var wwrite=function(v){ try{ localStorage.setItem(WKEY, JSON.stringify(v)) }catch(e){} wpaint(); };
  var wbtn=document.getElementById('wishbtn');
  function wpaint(){
    var w=wread();
    if(wbtn){ wbtn.hidden=!w.length; wbtn.querySelector('b').textContent=w.length;
      wbtn.setAttribute('aria-label','Wishlist, '+w.length+' saved'); }
    document.querySelectorAll('[data-wish]').forEach(function(b){
      var on=w.indexOf(b.getAttribute('data-wish'))>-1;
      b.setAttribute('aria-pressed', on?'true':'false');
      var l=b.querySelector('[data-wish-label]'); if(l) l.textContent=on?'Saved':'Save';
    });
    var grid=document.querySelector('[data-wishlist]'); if(!grid) return;
    var data={}; try{ data=JSON.parse(grid.getAttribute('data-wishdata')) }catch(e){}
    var items=w.filter(function(h){ return data[h] });
    grid.innerHTML='';
    items.forEach(function(h){
      var d=data[h], a=document.createElement('article');
      a.className='cof'; a.style.setProperty('--c', d.c);
      a.innerHTML='<img class="cof__pack" src="'+d.i+'" alt="" loading="lazy">'
        +'<h3 class="cof__n"><a class="cof__hit" href="p-'+h+'.html"></a></h3><p class="cof__t"></p>'
        +'<p class="cof__price"><b class="num">From '+inr(d.p)+'</b></p>';
      a.querySelector('.cof__hit').textContent=d.t; a.querySelector('.cof__t').textContent=d.s;
      var rm=document.createElement('button'); rm.type='button'; rm.className='cart__rm wl-rm'; rm.textContent='Remove';
      rm.addEventListener('click', function(){ wwrite(wread().filter(function(x){ return x!==h })) });
      a.appendChild(rm); grid.appendChild(a);
    });
    var empty=document.querySelector('[data-wish-empty]'); if(empty) empty.hidden=!!items.length;
  }
  document.querySelectorAll('[data-wish]').forEach(function(b){
    b.addEventListener('click', function(){
      var h=b.getAttribute('data-wish'), w=wread(), i=w.indexOf(h);
      if(i>-1) w.splice(i,1); else w.push(h);
      wwrite(w);
    });
  });
  window.addEventListener('storage', function(e){ if(e.key===WKEY) wpaint() });
  wpaint();

  // ---- collection sort ---------------------------------------------
  document.querySelectorAll('[data-sortable]').forEach(function(grid){
    var sel=grid.parentNode.querySelector('[data-sort]'), n=grid.parentNode.querySelector('[data-count]');
    var cards=[].slice.call(grid.children);
    if(n) n.textContent=cards.length+' product'+(cards.length>1?'s':'');
    if(!sel) return;
    sel.addEventListener('change', function(){
      var k=sel.value, list=cards.slice();
      if(k) list.sort(function(a,b){ var d=+a.getAttribute('data-price')-(+b.getAttribute('data-price')); return k==='lo'?d:-d });
      list.forEach(function(c){ grid.appendChild(c) });
    });
  });

  // ---- basket ------------------------------------------------------
  var cart=document.getElementById('cart'); if(!cart) return;
  var lines=cart.querySelector('[data-clines]'), total=cart.querySelector('[data-ctotal]');
  var go=cart.querySelector('[data-ccheckout]'), goods=cart.querySelector('[data-cgoods]'), note=cart.querySelector('[data-cnote]');
  var btn=document.getElementById('cartbtn'), count=btn?btn.querySelector('b'):null, last=null;
  // re-price from the live catalogue; flag anything the store no longer sells
  function refresh(b){
    var changed=false;
    b.forEach(function(l){ var c=CPV[String(l.id)]; if(!c) return;
      if(c[0]!==l.p){ l.was=l.p; l.p=c[0]; changed=true }
      var off=!c[1]; if(off!==!!l.off){ l.off=off; changed=true } });
    if(changed) try{ localStorage.setItem(KEY, JSON.stringify(b)) }catch(e){}
    return b;
  }
  function paint(){
    var b=refresh(read()), sum=0, n=0, hasGoods=false, live=b.filter(function(l){ return !l.off });
    lines.innerHTML = b.length ? '' : '<p class="cart__empty">Nothing in the basket yet. <a href="shop.html">Shop coffee</a> or <a href="p-coffee-experience-tours-11.html">book the tour</a>.</p>';
    b.forEach(function(l,i){
      if(!l.off){ sum += l.p*l.q; n += l.q; if(l.h!==TOUR) hasGoods=true; }
      var el=document.createElement('div'); el.className='cart__line'+(l.off?' is-off':'');
      var href=l.h?'p-'+l.h+'.html':'shop.html';
      el.innerHTML=(l.i?'<a class="cart__img" href="'+href+'" tabindex="-1" aria-hidden="true"><img src="'+esc(l.i)+'" alt=""></a>':'<span class="cart__img"></span>')
        +'<div class="cart__info"><p class="cart__t"><a href="'+href+'">'+esc(l.t)+'</a></p>'
        +'<p class="cart__o">'+esc(pretty(l.o))+'</p>'
        +(l.off?'<p class="cart__warn">No longer available. Remove it to check out.</p>':(l.was?'<p class="cart__warn">Price updated from '+inr(l.was)+'.</p>':''))
        +'<div class="cart__ctl"><div class="qty" role="group" aria-label="Quantity of '+esc(l.t)+'">'
        +'<button type="button" data-q="-1" aria-label="One fewer">&minus;</button><span class="num" aria-live="polite">'+l.q+'</span>'
        +'<button type="button" data-q="1" aria-label="One more">+</button></div>'
        +'<button type="button" class="cart__rm">Remove</button></div></div>'
        +'<p class="cart__p num">'+inr(l.p*l.q)+'</p>';
      el.querySelectorAll('[data-q]').forEach(function(q){ q.addEventListener('click', function(){
        var c=read(), d=parseInt(q.getAttribute('data-q'),10); if(!c[i]) return;
        c[i].q=Math.max(0,Math.min(20,c[i].q+d)); delete c[i].was; if(!c[i].q) c.splice(i,1); write(c);
        var again=lines.querySelectorAll('.cart__line')[i]; var t=again&&again.querySelector('[data-q="'+d+'"]'); if(t) t.focus();
      }) });
      el.querySelector('.cart__rm').addEventListener('click', function(){ var c=read(); c.splice(i,1); write(c); (cart.querySelector('.drawer__x')||cart).focus(); });
      lines.appendChild(el);
    });
    total.textContent=inr(sum);
    if(goods) goods.hidden=!hasGoods;
    if(note) note.textContent = (hasGoods?'Coffee is roasted after you order and dispatched in 3–5 business days. ':'')
      +(live.some(function(l){ return l.h===TOUR })?'Tour tickets are collected at the Cauvery Peak café on the day. ':'')
      +'Payment is taken on the estate’s Shopify checkout.';
    if(btn){ if(count) count.textContent=n; btn.setAttribute('aria-label','Basket, '+n+' item'+(n===1?'':'s')); }
    // Shopify cart permalink: real variant ids, plus tour date/departure as cart attributes
    var blocked=b.some(function(l){ return l.off }), qs=[];
    live.forEach(function(l){ if(l.a){ qs.push('attributes%5BTour%20date%5D='+encodeURIComponent(l.a.date)); qs.push('attributes%5BTour%20departure%5D='+encodeURIComponent(l.a.slot)); } });
    go.setAttribute('href', live.length&&!blocked ? STORE+'/cart/'+live.map(function(l){ return l.id+':'+l.q }).join(',')+(qs.length?'?'+qs.join('&'):'') : STORE+'/collections/all');
    go.classList.toggle('is-disabled', !live.length||blocked);
    if(!live.length||blocked) go.setAttribute('aria-disabled','true'); else go.removeAttribute('aria-disabled');
  }
  go.addEventListener('click', function(e){ if(go.getAttribute('aria-disabled')) e.preventDefault(); });
  var bg=function(on){ document.querySelectorAll('body > *:not(#cart)').forEach(function(el){ if(on) el.setAttribute('inert',''); else el.removeAttribute('inert'); }) };
  function open(){ last=document.activeElement; cart.classList.add('is-open'); bg(true);
    document.documentElement.classList.add('no-scroll');
    (cart.querySelector('.drawer__x')||cart).focus(); document.addEventListener('keydown',key,true); }
  function close(){ cart.classList.remove('is-open'); bg(false);
    document.documentElement.classList.remove('no-scroll');
    document.removeEventListener('keydown',key,true); if(last&&last.focus) last.focus(); }
  function key(e){
    if(e.key==='Escape'){ e.preventDefault(); close(); return; }
    if(e.key!=='Tab') return;
    // keep focus inside the drawer while it is open
    var f=[].filter.call(cart.querySelectorAll('a[href],button:not([disabled]),input,select'), function(x){ return x.offsetParent!==null });
    if(!f.length) return;
    var first=f[0], end=f[f.length-1];
    if(e.shiftKey && document.activeElement===first){ e.preventDefault(); end.focus(); }
    else if(!e.shiftKey && document.activeElement===end){ e.preventDefault(); first.focus(); }
  }
  cart.addEventListener('click', function(e){ if(e.target.closest('[data-cclose]')) close(); });
  if(btn) btn.addEventListener('click', open);
  window.addEventListener('storage', function(e){ if(e.key===KEY) paint() });
  paint();
})();
</script>"""

MENU_JS = '''<script>
(function(){
  var b=document.getElementById('burger'), d=document.getElementById('sitemenu');
  if(!b||!d) return;
  var panel=d.querySelector('.drawer__panel'), last=null;
  var Q='a[href],button:not([disabled])';
  function open(){
    last=document.activeElement;
    d.classList.add('is-open'); b.setAttribute('aria-expanded','true');
    document.documentElement.classList.add('no-scroll');
    (panel.querySelector(Q)||panel).focus();
    document.addEventListener('keydown',key,true);
  }
  function close(){
    d.classList.remove('is-open'); b.setAttribute('aria-expanded','false');
    document.documentElement.classList.remove('no-scroll');
    document.removeEventListener('keydown',key,true);
    if(last) last.focus();
  }
  function key(e){
    if(e.key==='Escape'){ e.preventDefault(); close(); return; }
    if(e.key!=='Tab') return;
    var f=[].slice.call(panel.querySelectorAll(Q)).filter(function(el){return el.offsetParent!==null});
    if(!f.length) return;
    var first=f[0], lastEl=f[f.length-1];
    if(e.shiftKey && document.activeElement===first){ e.preventDefault(); lastEl.focus(); }
    else if(!e.shiftKey && document.activeElement===lastEl){ e.preventDefault(); first.focus(); }
  }
  b.addEventListener('click',function(){ d.classList.contains('is-open')?close():open(); });
  d.addEventListener('click',function(e){ if(e.target.closest('[data-close]')) close(); });
  // a viewport that grows past the breakpoint must not leave the drawer stuck open
  matchMedia('(min-width:760px)').addEventListener('change',function(e){ if(e.matches) close(); });
})();
</script>'''


def jsonld(slug, title, desc, og):
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Cauvery Peak",
        "legalName": "MSP Plantations",
        "url": BASE + "/",
        "logo": BASE + "/assets/logo_dark.webp",
        "foundingDate": "1867",
        "sameAs": [h for _, h, _ in SOCIAL] + ["https://cauverypeakestate.com"],
        "address": {"@type": "PostalAddress", "addressLocality": "Yercaud",
                    "addressRegion": "Tamil Nadu", "addressCountry": "IN"},
    }
    blocks = [org]
    if slug == "index.html":
        blocks.append({"@context": "https://schema.org", "@type": "WebSite",
                       "name": "Cauvery Peak", "url": BASE + "/"})
    else:
        blocks.append({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": re.sub(r"\s+—.*$", "", title),
                 "item": f"{BASE}/{slug}"},
            ]})
    if slug in ("cafes.html", "visit.html", "contact.html"):
        blocks.append({
            "@context": "https://schema.org", "@type": "TouristAttraction",
            "name": "Cauvery Peak Estate", "url": f"{BASE}/visit.html",
            "description": "A working 150-year-old coffee plantation in the Shevaroy Hills, open for guided tours.",
            "image": f"{BASE}/assets/{og}",
            "address": {"@type": "PostalAddress", "addressLocality": "Yercaud",
                        "addressRegion": "Tamil Nadu", "addressCountry": "IN"},
            "geo": {"@type": "GeoCoordinates", "latitude": 11.7753, "longitude": 78.2095},
        })
    if slug == "bbc-news-tamil.html":
        blocks.append({
            "@context": "https://schema.org", "@type": "VideoObject",
            "name": "ஏற்காட்டில் 150 ஆண்டு பழைமையான காபி எஸ்டேட்",
            "alternateName": "A 150-year-old coffee estate in Yercaud",
            "description": "BBC News Tamil on the Coffee Experience Tour at Cauvery Peak Estate, Yercaud.",
            "inLanguage": "ta", "uploadDate": "2026-09-27", "duration": "PT1M7S",
            "thumbnailUrl": "https://i.ytimg.com/vi/rXsLBvO9Dkw/maxresdefault.jpg",
            "embedUrl": "https://www.youtube-nocookie.com/embed/rXsLBvO9Dkw",
            "contentUrl": "https://www.youtube.com/shorts/rXsLBvO9Dkw",
            "publisher": {"@type": "Organization", "name": "BBC News Tamil"},
            "about": {"@type": "TouristAttraction", "name": "Cauvery Peak Estate"},
        })
    if slug in CAFES:
        c = CAFES[slug]
        addr = {"@type": "PostalAddress", "streetAddress": c["street"], "addressLocality": "Yercaud",
                "addressRegion": "Tamil Nadu", "addressCountry": "IN"}
        if c["postal"]: addr["postalCode"] = c["postal"]
        blocks.append({
            "@context": "https://schema.org", "@type": "CafeOrCoffeeShop",
            "name": c["name"], "url": f"{BASE}/{slug}", "image": f"{BASE}/assets/{c['img']}",
            "telephone": c["tel"][0], "servesCuisine": "Coffee", "address": addr,
            "parentOrganization": {"@type": "Organization", "name": "Cauvery Peak"},
            "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                "opens": c["opens"], "closes": c["closes"]}],
        })
    return "\n".join(
        '<script type="application/ld+json">%s</script>' % json.dumps(b, separators=(",", ":"))
        for b in blocks)



# GitHub Pages serves assets with a 10-minute cache. Without a version in the
# URL, a visitor arriving just after a deploy gets the new HTML with the old
# stylesheet and script — a page that half-matches itself. A short content
# hash changes the URL exactly when the file changes, and never otherwise.
import hashlib
def v(path):
    with open(os.path.join(HERE, path), "rb") as f:
        return f"{path}?v={hashlib.md5(f.read()).hexdigest()[:8]}"

def document(slug, title, desc, og, body):
    canonical = f"{BASE}/" if slug == "index.html" else f"{BASE}/{slug}"
    return f'''<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#002D3E">
<script>document.documentElement.className="js"</script>
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Cauvery Peak">
<meta property="og:locale" content="en_IN">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{BASE}/assets/{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{desc[:110]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="assets/fraunces.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{v('assets/site.css')}">
<link rel="stylesheet" href="{v('assets/estate.css')}">
{jsonld(slug, title, desc, og)}
</head>
<body>
{header(slug)}
{drawer(slug)}
<main id="main">
{body}
{closer(slug)}
</main>
{footer()}
{STICKY_BUY + STICKY_BUY_JS if 'class="pdp' in body else ('' if 'class="schips' in body else STICKY + STICKY_JS)}
{CART}
{PRICE_MAP}
{MENU_JS}
{SHOP_JS}
<script src="{v('assets/motion.js')}" defer></script>
</body>
</html>
'''


def build():
    pages = json.load(open(os.path.join(SRC, "pages.json")))
    made = []
    for p in pages:
        frag = open(os.path.join(SRC, p["file"])).read()
        html = document(p["slug"], p["title"], p["desc"], p.get("og", "og-default.jpg"), frag)
        out = os.path.join(OUT, p["slug"])
        open(out, "w").write(html)
        made.append((p["slug"], os.path.getsize(out)))
    return made


if __name__ == "__main__":
    for slug, size in build():
        print(f"  {slug:22} {size/1024:6.1f} KB")
