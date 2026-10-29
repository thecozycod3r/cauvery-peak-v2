"""Generate _src_pages/shop.html from catalog.json (the live Shopify catalogue)
plus the merchandising layer below: taste lines, brew use, badge, image.

Every card is a working buy control: size, grind or type, and "Add · ₹price",
wired to the shared basket by SHOP_JS in build.py (`.pc[data-v]`). Prices and
availability come straight from the catalogue, so re-running after
scripts/fetch_catalog.py keeps the shop honest.

Usage: python3 scripts/gen_shop.py
"""
import html, json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = {p["handle"]: p for p in json.load(open(os.path.join(HERE, "_src_pages", "catalog.json")))}
E = lambda s: html.escape(s, quote=True)


def img(name):
    """Prefer a real or generated pack shot when it exists."""
    for cand in name if isinstance(name, list) else [name]:
        if os.path.exists(os.path.join(HERE, cand)):
            return cand
    raise FileNotFoundError(name)


# handle -> merchandising. kind: pack = transparent cut-out shown whole on paper;
# photo = a full-bleed photograph.
M = {
    "coffee-powder-she": dict(name="Shevaroys", sub="Estate Reserve · 1,450 m", taste="Bright and citrusy, medium body.",
        use="Best black: pour-over, French press.", tags="bright black", est="#795159",
        img=["assets/shop/real/coffee-powder-she-pack.webp", "assets/p_sh.webp"], kind="pack"),
    "coffee-powder-cp": dict(name="Cauvery Peak", sub="Estate Heritage · 1,400 m", taste="Balanced and chocolatey, full body.",
        use="Black or with milk. Where most people start.", tags="balanced milk filter black", est="#394951", badge="Start here",
        img=["assets/shop/real/coffee-powder-cp-bag.webp"], kind="pack"),
    "glenfell-4": dict(name="Glenfell", sub="Estate Classic · 1,250 m", taste="Rounded and gently spiced, low acidity.",
        use="Smooth black, good with milk.", tags="rounded milk filter", est="#00808C",
        img=["assets/shop/real/glenfell-4-pack.webp"], kind="pack"),
    "espresso-blend-5": dict(name="Espresso Blend", sub="All three estates", taste="Sweet acidity, rich creamy body.",
        use="For espresso machines and moka pots.", tags="espresso milk", est="#3B2A1E",
        img=["assets/shop/real/espresso-blend-5-pack.webp", "assets/p_eb.webp"], kind="pack"),
    "indian-filter-blend-5": dict(name="Indian Filter Blend", sub="All three estates", taste="Thick body, aroma and bite.",
        use="For a strong South Indian filter decoction.", tags="filter milk", est="#7F3634",
        img=["assets/shop/real/indian-filter-blend-5-pack.webp", "assets/p_ib.webp"], kind="pack"),
    "sample-pack": dict(name="3 Single Estates Sampler", sub="Shevaroys · Cauvery Peak · Glenfell", taste="One pack of each estate, side by side.",
        use="The best first order if you are unsure.", tags="bright balanced rounded black milk", badge="Sampler",
        img=["assets/shop/real/sample-pack-pack.webp", "assets/p_sampler.webp"], kind="pack"),
    "blend-sampler-pack-23": dict(name="2 Blends Sampler", sub="Espresso · Indian Filter", taste="One pack of each blend.",
        use="For a home that makes both.", tags="espresso filter milk", badge="Sampler",
        img=["assets/shop/real/blend-sampler-pack-23-pack.webp", "assets/p_blends.webp"], kind="pack"),
    "drip-bags": dict(name="Drip Bags", sub="6 sachets · ₹60 a cup", taste="Single-estate coffee in a hang-on filter.",
        use="No equipment: a mug and hot water.", tags="black", badge="No equipment needed",
        img=["assets/shop/real/drip-bags-life.webp", "assets/shop/drip-bags-0.webp"], kind="photo"),
    "pepper": dict(name="Whole Black Pepper", sub="Grown between the coffee", taste="Sun-dried whole peppercorns.",
        use="For the grinder and the tadka.", tags="",
        img=["assets/shop/real/pepper-life.webp"], kind="photo"),
    "nutmeg-mace": dict(name="Nutmeg & Mace", sub="100 g", taste="Whole nutmeg with its mace.",
        use="Grate fresh into sweets and garam masala.", tags="",
        img=["assets/shop/real/nutmeg-mace-pack.webp"], kind="pack"),
    "clove": dict(name="Cloves", sub="100 g", taste="Whole, hand-picked cloves.", use="For biryani, chai and pickles.", tags="",
        img=["assets/shop/real/clove-life.webp"], kind="photo"),
    "honey": dict(name="Estate Honey", sub="500 g", taste="From hives that sit among the coffee.", use="Raw, straight from the estate.", tags="",
        img=["assets/shop/honey-0.webp"], kind="photo"),
    "cauvery-peak-green-beans": dict(name="Green Coffee Beans", sub="Unroasted · Cauvery Peak", taste="Raw Hawaiian Red Caturra Arabica.",
        use="For home roasters. Not ready to brew.", tags="", badge="Unroasted",
        img=["assets/shop/cauvery-peak-green-beans-0.webp"], kind="photo"),
    "coffee-scrub": dict(name="Coffee Scrub", sub="Orange · Eucalyptus · Pine", taste="Estate coffee, oils and essential oils.",
        use="For skin. Not for drinking.", tags="", badge="For skin",
        img=["assets/shop/real/coffee-scrub-pack.webp"], kind="pack"),
}

GRIND = "Select Grind"


def clean(v):
    """'250 gm (serves approximately 30 cups)' -> '250 g'; '100GM x 3Packs' -> '100 g × 3'."""
    v = re.sub(r"\s*\(.*?\)", "", v).strip()
    m = re.match(r"(\d+)\s*GM\s*x\s*(\d+)\s*Packs", v, re.I)
    if m: return f"{m.group(1)} g × {m.group(2)}"
    v = re.sub(r"(\d)\s*(gm|Gm|GM)\b", r"\1 g", v)
    v = re.sub(r"(\d)\s*(Kg|kg)\b", r"\1 kg", v)
    return v.replace(" Coffee Scrub", "").replace("Estate ", "")


def grams(v):
    m = re.search(r"([\d.]+)\s*(kg|g)\b", clean(v), re.I)
    if not m: return 0
    n = float(m.group(1)) * (1000 if m.group(2).lower() == "kg" else 1)
    k = re.search(r"×\s*(\d+)", clean(v))
    return n * (int(k.group(1)) if k else 1)


def card(h):
    p, m = CAT[h], M[h]
    opts = [o for o in p["options"] if o["values"] != ["Default Title"]]
    vs = [{"id": v["id"], "p": v["p"], "av": v["av"], "o": [v["o1"], v["o2"], v["o3"]]} for v in p["variants"]]
    lo = min(v["p"] for v in vs if v["av"]) if any(v["av"] for v in vs) else min(v["p"] for v in vs)
    fields = []
    for i, o in enumerate(opts, 1):
        vals = o["values"]
        if o["name"] == GRIND:
            # whole beans first; every ground option is a brew method
            order = ["Whole Beans"] + [x for x in vals if x != "Whole Beans"]
            opt = "".join(f'<option value="{E(x)}">{"Whole beans" if x == "Whole Beans" else "Ground for " + E(x)}</option>' for x in order)
            fields.append(f'<label class="pc__sel"><span class="sr">Grind</span><select name="o{i}">{opt}</select></label>')
        elif len(vals) > 1 and len(vals) <= 4 and all(grams(x) for x in vals):
            # sizes: smallest first, smallest checked
            order = sorted(vals, key=grams)
            r = "".join(f'<label class="pc__sz"><input type="radio" name="o{i}" value="{E(x)}"{" checked" if j == 0 else ""}><span>{E(clean(x))}</span></label>'
                        for j, x in enumerate(order))
            fields.append(f'<fieldset class="pc__sizes"><legend class="sr">Size</legend>{r}</fieldset>')
        elif len(vals) > 1:
            opt = "".join(f'<option value="{E(x)}">{E(clean(x))}</option>' for x in vals)
            fields.append(f'<label class="pc__sel"><span class="sr">{E(o["name"].replace("Select ", "") or "Option")}</span><select name="o{i}">{opt}</select></label>')
        else:
            fields.append(f'<input type="hidden" name="o{i}" value="{E(vals[0])}">')
    per = '<p class="pc__per num" data-per></p>' if any(grams(x) for o in opts for x in o["values"]) else ""
    badge = f'<span class="pc__badge">{E(m["badge"])}</span>' if m.get("badge") else ""
    src = img(m["img"])
    first = next((v for v in vs if v["av"]), vs[0])
    return f'''<article class="pc pc--{m["kind"]}" data-handle="{h}" data-tags="{m["tags"]}" data-price="{int(lo)}"{f' style="--est:{m["est"]}"' if m.get("est") else ""}
  data-v='{json.dumps(vs, separators=(",", ":"))}' data-title="{E(m["name"])}" data-img="{src}">
  <a class="pc__img" href="p-{h}.html" tabindex="-1" aria-hidden="true"><img src="{src}" alt="" loading="lazy" width="500" height="625"></a>{badge}
  <div class="pc__body">
    <h3 class="pc__n"><a href="p-{h}.html">{E(m["name"])}</a></h3>
    <p class="pc__sub">{E(m["sub"])}</p>
    <p class="pc__t">{E(m["taste"])} <span>{E(m["use"])}</span></p>
    <form class="pc__buy" onsubmit="return false">
      {"".join(fields)}
      <button class="pc__add" type="button" data-qadd>Add <span class="num" data-qprice>&#8377;{int(first["p"]):,}</span></button>
      {per}
    </form>
  </div>
</article>'''


def grid(handles, cls=""):
    return f'<div class="pgrid{cls}">\n' + "\n".join(card(h) for h in handles) + "\n</div>"


SUB = CAT["coffee"]
sub_lo = min(v["p"] for v in SUB["variants"] if v["o1"] == "6 Months" and v["o3"] == "250 gm")

page = f'''<header class="shead">
  <div class="wrap shead__in">
    <div>
      <p class="eyebrow eyebrow--d">The estate shop</p>
      <h1 class="d1 shead__h">Estate-grown coffee, <em>roasted after you order.</em></h1>
      <p class="lede">Three single estates and two blends from one hill in the Shevaroys. Coffee from &#8377;580 for 250&nbsp;g.</p>
    </div>
    <ul class="shead__trust">
      <li><b>Free shipping</b> across India</li>
      <li><b>Roasted to order</b>, dispatched in 3&ndash;5 business days</li>
      <li><b>Damaged in transit?</b> Replaced or refunded &mdash; <a href="returns.html">returns</a></li>
    </ul>
  </div>
</header>

<nav class="schips" aria-label="Shop sections">
  <div class="wrap schips__in">
    <a href="#estates">Single estates</a><a href="#blends">Blends</a><a href="#samplers">Samplers &amp; drip bags</a><a href="#subscriptions">Subscriptions</a><a href="#extras">Spices &amp; honey</a><a class="schips__tour" href="#tour">The tour &rarr;</a>
  </div>
</nav>

<section class="staste" aria-labelledby="taste-h">
  <div class="wrap">
    <h2 id="taste-h" class="cgroup">Choose by taste</h2>
    <div class="staste__row" role="group" aria-label="Filter coffee by taste or brew">
      <button type="button" class="tchip" data-filter="" aria-pressed="true">All coffee</button>
      <button type="button" class="tchip" data-filter="bright" aria-pressed="false">Bright &amp; citrusy</button>
      <button type="button" class="tchip" data-filter="balanced" aria-pressed="false">Balanced &amp; chocolatey</button>
      <button type="button" class="tchip" data-filter="rounded" aria-pressed="false">Rounded &amp; spicy</button>
      <button type="button" class="tchip" data-filter="milk" aria-pressed="false">With milk</button>
      <button type="button" class="tchip" data-filter="filter" aria-pressed="false">For Indian filter</button>
      <button type="button" class="tchip" data-filter="espresso" aria-pressed="false">For espresso</button>
    </div>
    <p class="staste__help">Not sure? <a href="#samplers">Try the sampler</a> &mdash; all three estates for &#8377;670. <span class="staste__count" data-fcount aria-live="polite"></span></p>
  </div>
</section>

<section id="estates" class="ssec" aria-labelledby="est-h">
  <div class="wrap">
    <div class="ssec__head"><h2 id="est-h" class="cgroup">Single estates</h2><p class="body">Same hill, three heights. Higher is brighter, lower is rounder.</p></div>
    {grid(["coffee-powder-she", "coffee-powder-cp", "glenfell-4"], " pgrid--coffee")}
  </div>
</section>

<section id="blends" class="ssec" aria-labelledby="bl-h">
  <div class="wrap">
    <div class="ssec__head"><h2 id="bl-h" class="cgroup">Blends</h2><p class="body">Drawn from all three estates, blended for a brew method.</p></div>
    {grid(["espresso-blend-5", "indian-filter-blend-5"], " pgrid--coffee")}
  </div>
</section>

<section id="samplers" class="ssec" aria-labelledby="sm-h">
  <div class="wrap">
    <div class="ssec__head"><h2 id="sm-h" class="cgroup">Samplers &amp; drip bags</h2><p class="body">The easy way in: taste them side by side, or brew with nothing but a mug.</p></div>
    {grid(["sample-pack", "blend-sampler-pack-23", "drip-bags"], " pgrid--coffee")}
  </div>
</section>

<section id="subscriptions" class="ssec" aria-labelledby="sb-h">
  <div class="wrap">
    <div class="ssub">
      <div class="ssub__copy">
        <p class="eyebrow">Subscriptions</p>
        <h2 id="sb-h" class="d2">One pack a month, <em>paid once.</em></h2>
        <p class="body">Choose 6, 12 or 24 monthly deliveries of any coffee, in 250&nbsp;g, 500&nbsp;g or 1&nbsp;kg. You pay for the whole term up front and save up to 15% on buying the packs one by one. Each pack is roasted to order before it ships.</p>
        <ul class="ssub__facts">
          <li><b class="num">&#8377;{int(sub_lo):,}</b><span>6 months of 250&nbsp;g, paid up front</span></li>
          <li><b>Up to 15%</b><span>off the single-pack price</span></li>
          <li><b>Mixed Bag</b><span>a different coffee each month</span></li>
        </ul>
        <div class="btns"><a class="btn btn--fill" href="subscribe.html">Build a subscription</a></div>
      </div>
    </div>
  </div>
</section>

<section id="extras" class="ssec" aria-labelledby="ex-h">
  <div class="wrap">
    <div class="ssec__head"><h2 id="ex-h" class="cgroup">Spices, honey &amp; more</h2><p class="body">Grown between the coffee, on the same land.</p></div>
    {grid(["pepper", "nutmeg-mace", "clove", "honey", "cauvery-peak-green-beans", "coffee-scrub"], " pgrid--small")}
  </div>
</section>

<section id="tour" class="stour" aria-labelledby="tour-h">
  <div class="wrap stour__in">
    <div class="stour__img"><img src="assets/media/stop-roast.webp" alt="Coffee being roasted on the estate" loading="lazy" width="800" height="1000"></div>
    <div class="stour__copy">
      <p class="eyebrow eyebrow--d">The Coffee Experience Tour</p>
      <h2 id="tour-h" class="d2">See where it grows, <em>then taste it.</em></h2>
      <ul class="stour__facts">
        <li><b class="num">&#8377;600</b><span>per person</span></li>
        <li><b class="num">90 min</b><span>in your own vehicle</span></li>
        <li><b>11 · 1 · 3</b><span>departures, from the café</span></li>
      </ul>
      <p class="lede">Walk-ins welcome every day except Tuesday; buy online to pick your date and departure in advance.</p>
      <div class="btns"><a class="btn btn--gold" href="p-coffee-experience-tours-11.html">Book tickets</a></div>
    </div>
  </div>
</section>

<section class="sfaq" aria-labelledby="faq-h">
  <div class="wrap sfaq__in">
    <h2 id="faq-h" class="cgroup">Before you order</h2>
    <div class="sfaq__list">
      <details><summary>When will it arrive?</summary><p class="body">We roast after you order and dispatch within 3&ndash;5 business days. Standard delivery then takes 5&ndash;7 business days within India, with tracking by email or WhatsApp. Shipping is free.</p></details>
      <details><summary>Which grind should I choose?</summary><p class="body">Whole beans stay fresh longest if you have a grinder. Otherwise pick how you brew and we grind it for that method. <a href="grind.html">The grind guide</a> shows each one.</p></details>
      <details><summary>How do I keep it fresh?</summary><p class="body">Close the zip after each use and keep the pack somewhere cool and dark. Whole beans hold their flavour longer than ground coffee, so grind just before brewing if you can.</p></details>
      <details><summary>What if it arrives damaged?</summary><p class="body">Tell us within 48 hours with a photo and we replace it or refund in full. <a href="returns.html">Returns policy</a>.</p></details>
      <details><summary>Is it really one estate?</summary><p class="body">Each single estate comes from one of the family&rsquo;s three estates on the same hill. The blends are drawn from all three. Everything is grown, processed, roasted and packed on the estate.</p></details>
    </div>
  </div>
</section>
'''

open(os.path.join(HERE, "_src_pages", "shop.html"), "w").write(page)
print("wrote _src_pages/shop.html")
