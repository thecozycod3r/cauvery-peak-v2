"""Commerce pass over the product pages (_src_pages/p-*.html). Idempotent:
a page that already carries data-upg="2" is skipped.

  * price + taste line directly under the name; price per 100 g
  * grind as "Whole beans / Ground", ground opening a brew-method list
  * quantity stepper in the buy bar
  * real (or clearly-labelled generated) pack shots, with a thumbnail gallery
  * coffee facts: varietal, process, grown, roasted; brew + storage notes
  * "compare the estates" row and a sampler upsell on coffee pages
  * the tour: date, departure, guests; "Book tickets"; honest walk-in copy
  * non-roasted goods no longer promise "roasted after you order"

Usage: python3 scripts/upgrade_pdp.py
"""
import glob, html, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "_src_pages")
R = "assets/shop/real/"
ex = lambda p: os.path.exists(os.path.join(HERE, p))

# handle -> (taste line, [gallery images]) ; first image is the main pack shot
INFO = {
    "coffee-powder-she": ("Bright and citrusy, medium body. Best black: pour-over or French press.", [R + "coffee-powder-she-pack.webp", R + "coffee-powder-she-studio.webp"]),
    "coffee-powder-cp": ("Balanced and chocolatey, full body, low acidity. Black or with milk.", [R + "coffee-powder-cp-bag.webp", R + "coffee-powder-cp-life.webp"]),
    "glenfell-4": ("Rounded and gently spiced, low acidity. Smooth black, good with milk.", [R + "glenfell-4-pack.webp", R + "glenfell-4-life.webp"]),
    "espresso-blend-5": ("Sweet acidity and a rich, creamy body. For espresso machines and moka pots.", [R + "espresso-blend-5-pack.webp", R + "espresso-blend-5-studio.webp"]),
    "indian-filter-blend-5": ("Thick body, aroma and bite, for a strong South Indian filter decoction.", [R + "indian-filter-blend-5-pack.webp", R + "indian-filter-blend-5-studio.webp"]),
    "sample-pack": ("One pack each of Shevaroys, Cauvery Peak and Glenfell, to taste side by side.", [R + "sample-pack-pack.webp"]),
    "blend-sampler-pack-23": ("One pack each of the Espresso and Indian Filter blends.", [R + "blend-sampler-pack-23-pack.webp"]),
    "drip-bags": ("Six single-serve sachets. Hang one on a mug, pour hot water, done.", [R + "drip-bags-life.webp", "assets/shop/drip-bags-0.webp"]),
    "pepper": ("Whole black peppercorns, grown between the coffee and sun-dried.", [R + "pepper-life.webp", "assets/shop/pepper-0.webp"]),
    "nutmeg-mace": ("Whole nutmeg with its mace, grown on the estate.", [R + "nutmeg-mace-pack.webp", R + "nutmeg-mace-life.webp"]),
    "clove": ("Whole, hand-picked cloves from the estate.", [R + "clove-life.webp", "assets/shop/clove-0.webp"]),
    "honey": ("Honey from hives that sit among the coffee.", ["assets/shop/honey-0.webp"]),
    "cauvery-peak-green-beans": ("Unroasted Hawaiian Red Caturra Arabica, for home roasters.", ["assets/shop/cauvery-peak-green-beans-0.webp"]),
    "coffee-scrub": ("Estate coffee with nourishing oils and essential oils. For skin, not for drinking.", [R + "coffee-scrub-pack.webp", R + "coffee-scrub-life2.webp", R + "coffee-scrub-life.webp"]),
    "coffee-experience-tours-11": ("Ninety minutes through a working 150-year-old estate, in your own vehicle with a coffee guide, ending with a cup at the café.", None),
    "coffee": ("Monthly deliveries of any coffee, paid once for the whole term.", None),
}
ESTATES = {"coffee-powder-she": ("1,450 m · 4,800 ft"), "coffee-powder-cp": ("1,400 m · 4,600 ft"), "glenfell-4": ("1,250 m · 4,100 ft")}
BLENDS = {"espresso-blend-5", "indian-filter-blend-5"}
ROASTED = set(ESTATES) | BLENDS | {"sample-pack", "blend-sampler-pack-23", "drip-bags", "coffee"}
GRIND_HINT = {"Coffee Filter": "Coffee Filter (paper filter or drip machine)", "Indian Filter": "Indian Filter (South Indian steel filter)",
              "Inverted Aeropress": "AeroPress, inverted", "Aeropress": "AeroPress"}


def gallery(imgs, alt):
    imgs = [i for i in imgs if ex(i)]
    if len(imgs) < 2: return ""
    b = "".join(f'<button type="button" class="pdp__th{" is-on" if j == 0 else ""}" data-gimg="{i}" data-gmode="{"photo" if ("life" in i or "studio" in i or "-0." in i) else "pack"}" aria-label="Photo {j + 1} of {len(imgs)}"{" aria-current=\"true\"" if j == 0 else ""}><img src="{i}" alt="" loading="lazy"></button>'
                for j, i in enumerate(imgs))
    return f'\n      <div class="pdp__thumbs" role="group" aria-label="{html.escape(alt)} photos">{b}</div>'


def grind_block(m):
    vals = re.findall(r'<input type="radio" name="o1" value="([^"]+)"', m.group(0))
    opts = "".join(f'<option value="{html.escape(v)}"{" hidden" if v == "Whole Beans" else ""}{" selected" if v == "Indian Filter" else ""}>{html.escape(GRIND_HINT.get(v, v))}</option>' for v in vals)
    return f'''<fieldset class="opts opts--grind">
        <legend class="cof__k">Grind</legend>
        <div class="opts__row gmode">
<label class="opt"><input type="radio" name="gmode" value="whole" checked><span>Whole beans</span><small>freshest, if you have a grinder</small></label>
<label class="opt"><input type="radio" name="gmode" value="ground"><span>Ground</span><small>we grind it for your brewer</small></label>
        </div>
        <label class="gsel" data-gsel hidden><span class="cof__k">Ground for</span><select name="o1" data-gselect>{opts}</select></label>
        <p class="opts__hint">Not sure? <a href="grind.html">See every grind side by side.</a></p>
      </fieldset>'''


QTY = '''<div class="qtyf" role="group" aria-label="Quantity"><button type="button" data-qd="-1" aria-label="One fewer">&minus;</button><input name="qty" type="number" min="1" max="20" value="1" inputmode="numeric" aria-label="Quantity"><button type="button" data-qd="1" aria-label="One more">+</button></div>
          '''

TOUR_FORM = '''<fieldset class="opts tourf">
        <legend class="cof__k">Your visit</legend>
        <label class="tourf__f"><span>Date</span><input type="date" name="tdate" required aria-describedby="tour-closed"></label>
        <p class="opts__hint" id="tour-closed">Open every day except Tuesday.</p>
        <div class="tourf__f"><span>Departure</span>
          <div class="opts__row">
<label class="opt"><input type="radio" name="tslot" value="11am"><span>11am</span></label>
<label class="opt"><input type="radio" name="tslot" value="1pm"><span>1pm</span></label>
<label class="opt"><input type="radio" name="tslot" value="3pm"><span>3pm</span></label>
          </div>
        </div>
        <p class="opts__hint">Please arrive at the Cauvery Peak caf&eacute; 30 minutes before your departure.</p>
        <p class="tourf__err" data-terr role="alert"></p>
      </fieldset>
'''

COMPARE = '''
<section class="pcompare" aria-labelledby="cmp-h">
  <div class="wrap">
    <h2 id="cmp-h" class="cgroup">Compare the estates</h2>
    <div class="pcompare__row">
      <a class="pcompare__c" href="p-coffee-powder-she.html" style="--est:#795159"><b>Shevaroys</b><span>1,450 m · bright, citrusy</span><em>&#8377;620 / 250 g</em></a>
      <a class="pcompare__c" href="p-coffee-powder-cp.html" style="--est:#394951"><b>Cauvery Peak</b><span>1,400 m · balanced, chocolatey</span><em>&#8377;600 / 250 g</em></a>
      <a class="pcompare__c" href="p-glenfell-4.html" style="--est:#00808C"><b>Glenfell</b><span>1,250 m · rounded, spicy</span><em>&#8377;580 / 250 g</em></a>
      <a class="pcompare__c pcompare__c--up" href="p-sample-pack.html"><b>Can&rsquo;t decide?</b><span>All three, 100 g each</span><em>Sampler &middot; &#8377;670</em></a>
    </div>
  </div>
</section>
'''


def facts(h):
    rows = []
    if h in ESTATES:
        rows = [("Variety", "Hawaiian Red Caturra (Arabica)"), ("Grown at", ESTATES[h]),
                ("Process", "Washed: pulped the day it is picked, fermented, washed and sun-dried on the estate")]
    elif h in BLENDS:
        rows = [("Made from", "All three estates: Shevaroys, Cauvery Peak and Glenfell"), ("Variety", "Hawaiian Red Caturra (Arabica)"),
                ("Process", "Washed and sun-dried on the estate")]
    if not rows: return ""
    rows.append(("Roasted", "On the estate, after you order"))
    li = "".join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    return f'''
      <div class="pdp__facts"><h2 class="cof__k">The coffee</h2><dl>{li}</dl>
        <h2 class="cof__k">Brew &amp; store</h2>
        <p class="body">A good start is 15&nbsp;g of coffee to 250&nbsp;ml of water just off the boil; adjust to taste. <a href="brewing.html">Recipes for every brewer</a>. Close the zip after each use and keep the pack somewhere cool and dark; whole beans stay fresh longest.</p></div>'''


done = []
for f in sorted(glob.glob(os.path.join(SRC, "p-*.html"))):
    s = open(f).read()
    if 'data-upg="2"' in s: continue
    h = re.search(r'data-handle="([^"]+)"', s).group(1)
    taste, imgs = INFO.get(h, ("", None))
    title = re.search(r'<h1 class="d2">([^<]+)</h1>', s).group(1)

    s = s.replace('<section class="pdp"', '<section class="pdp" data-upg="2"', 1)
    # images
    if imgs:
        main = next((i for i in imgs if ex(i)), None)
        if main:
            mode = "photo" if ("life" in main or "studio" in main or "-0." in main) else "pack"
            s = re.sub(r'<img class="pdp__pack" src="[^"]*"', f'<img class="pdp__pack" data-gmain data-mode="{mode}" src="{main}"', s, 1)
            s = s.replace("    </figure>\n    <div class=\"pdp__buy\">", f"    </figure>{gallery(imgs, title)}\n    <div class=\"pdp__buy\">", 1) if "pdp__thumbs" not in s else s
    # price + taste under the name
    lead = f'\n      <p class="pdp__lead"><span class="pdp__price num" data-price-mirror></span><span class="pdp__per" data-per></span></p>'
    if taste: lead += f'\n      <p class="pdp__taste">{taste}</p>'
    s = re.sub(r'(<h1 class="d2">[^<]+</h1>)', r'\1' + lead.replace("\\", "\\\\"), s, 1)
    # grind
    s = re.sub(r'<fieldset class="opts">\s*<legend class="cof__k">Grind</legend>.*?</fieldset>', grind_block, s, 1, flags=re.S)
    # quantity (not for subscriptions)
    if h != "coffee":
        s = s.replace('<button class="btn btn--gold" type="button" data-add>', QTY + '<button class="btn btn--gold" type="button" data-add>', 1)
    # assurances for things that are not roasted
    if h not in ROASTED:
        s = s.replace("<li><b>Roasted after you order</b>, dispatched in 3&ndash;5 business days</li>",
                      "<li><b>Packed on the estate</b> after you order, dispatched in 3&ndash;5 business days</li>")
    # tour
    if h == "coffee-experience-tours-11":
        s = s.replace('<form class="buy" onsubmit="return false">', '<form class="buy" onsubmit="return false">\n' + TOUR_FORM, 1)
        s = s.replace('data-add>Add to cart</button>', 'data-add>Book tickets</button>', 1)
        s = s.replace('aria-label="Quantity"><button', 'aria-label="Guests"><button', 1).replace('inputmode="numeric" aria-label="Quantity"', 'inputmode="numeric" aria-label="Guests"', 1)
        s = s.replace('<li><b>No booking needed.</b> Book here to hold your place, or buy tickets at the caf&eacute; on the day</li>',
                      '<li><b>Walk-ins welcome.</b> Buy here to choose your date and departure in advance; we&rsquo;ll have your tickets at the caf&eacute;</li>\n        <li><b>Meeting point</b> Cauvery Peak caf&eacute;, 15 km from Yercaud Lake &mdash; <a href="visit.html">directions</a></li>')
    # coffee facts after "About this product"
    fx = facts(h)
    if fx:
        s = re.sub(r'(<div class="pdp__about">.*?</div>)', lambda m: m.group(1) + fx, s, 1, flags=re.S)
    # compare + upsell on single-estate and blend pages
    if h in ESTATES or h in BLENDS:
        s = s.replace("\n\n<section>\n  <div class=\"wrap\">\n    <h2 class=\"cgroup\">On the estate</h2>", "\n" + COMPARE + "\n<section>\n  <div class=\"wrap\">\n    <h2 class=\"cgroup\">On the estate</h2>", 1)
    open(f, "w").write(s)
    done.append(h)
print("upgraded:", ", ".join(done))
