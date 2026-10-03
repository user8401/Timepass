const SITES = {
  chandukaka: {
    url: "https://chandukakasaraf.in/todays-gold-rate/",
    rate: /(\d{2})\s*KT\s*Gold[^\d₹]{0,8}₹\s*([\d,]+)/g,
    updated: /Updated\s*On:?\s*([\d\-]+\s[\d:]+)/i,
  },
  png: {
    url: "https://www.pngjewellers.com/pages/metal-rates",
    rate: /(\d{1,2})\s*K\s*Gold[^\d₹]{0,8}₹\s*([\d,]+)/g,
    updated: /Updated on\s*([A-Za-z]+,\s*[A-Za-z]+ \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M)/i,
  },
};

function strip(html) {
  return html
    .replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&#8377;|&#x20B9;/g, "₹")
    .replace(/\s+/g, " ");
}

export default {
  async fetch() {
    const out = { fetchedAt: new Date().toISOString() };
    await Promise.all(
      Object.entries(SITES).map(async ([key, cfg]) => {
        try {
          const r = await fetch(cfg.url, {
            headers: { "User-Agent": "Mozilla/5.0 (Linux; Android 13) Chrome/124.0 Mobile Safari/537.36" },
          });
          if (!r.ok) throw new Error("HTTP " + r.status);
          const text = strip(await r.text());
          const rates = {};
          for (const m of text.matchAll(cfg.rate)) {
            const k = parseInt(m[1], 10);
            if (!(k in rates)) rates[k] = parseInt(m[2].replace(/,/g, ""), 10);
          }
          if (!Object.keys(rates).length) throw new Error("no rates found on page");
          const u = text.match(cfg.updated);
          out[key] = { rates, updated: u ? u[1] : "time not shown on page" };
        } catch (e) {
          out[key] = { rates: {}, updated: "unknown", error: String(e.message || e).slice(0, 150) };
        }
      })
    );
    return new Response(JSON.stringify(out), {
      headers: {
        "content-type": "application/json",
        "access-control-allow-origin": "*",
        "cache-control": "no-store",
      },
    });
  },
};
