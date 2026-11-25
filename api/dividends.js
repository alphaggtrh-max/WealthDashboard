export default async function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=1800, stale-while-revalidate=3600');
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const token = process.env.EODHD_API_TOKEN;
  if (!token) return res.status(503).json({ error: 'Dividend data provider is not configured. Add EODHD_API_TOKEN to Vercel environment variables.' });
  try {
    const symbols = [...new Set((Array.isArray(req.body?.symbols) ? req.body.symbols : [])
      .map(x => String(x || '').trim().toUpperCase()).filter(x => /^[A-Z0-9.^_-]{1,24}(\.[A-Z]{1,5})?$/.test(x)))].slice(0, 100);
    if (!symbols.length) return res.status(400).json({ error: 'No valid ticker symbols supplied.' });
    const from = new Date(); from.setMonth(from.getMonth() - 12);
    const to = new Date(); to.setMonth(to.getMonth() + 12);
    const fmt = d => d.toISOString().slice(0,10);
    const results = await Promise.all(symbols.map(async symbol => {
      const url = new URL('https://eodhd.com/api/div/' + encodeURIComponent(symbol));
      url.searchParams.set('api_token', token); url.searchParams.set('fmt', 'json');
      url.searchParams.set('from', fmt(from)); url.searchParams.set('to', fmt(to));
      const response = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!response.ok) return { symbol, error: response.status === 404 ? 'Symbol not found by provider' : 'Provider returned HTTP ' + response.status, events: [] };
      const body = await response.json();
      const events = Array.isArray(body) ? body : (Array.isArray(body.data) ? body.data : []);
      return { symbol, events: events.map(e => ({
        exDate: e.date || e.exDate || null, declarationDate: e.declarationDate || null,
        recordDate: e.recordDate || null, paymentDate: e.paymentDate || null,
        amount: Number(e.value ?? e.dividend ?? e.amount), currency: e.currency || null,
        period: e.period || e.periodicity || null
      })).filter(e => Number.isFinite(e.amount) && e.amount > 0) };
    }));
    const currencies = [...new Set(results.flatMap(x => x.events.map(e => e.currency).filter(c => c && c !== 'EUR')))];
    const fx = { EUR: 1 };
    await Promise.all(currencies.map(async currency => {
      try {
        const response = await fetch('https://api.frankfurter.app/latest?from=' + encodeURIComponent(currency) + '&to=EUR');
        if (response.ok) { const data = await response.json(); if (Number.isFinite(Number(data.rates?.EUR))) fx[currency] = Number(data.rates.EUR); }
      } catch (_) {}
    }));
    results.forEach(result => result.events.forEach(event => {
      const rate = event.currency ? fx[event.currency] : null;
      event.fxToEUR = rate ?? null;
      event.amountEUR = rate == null ? null : event.amount * rate;
    }));
    return res.status(200).json({ provider: 'EOD Historical Data', fetchedAt: new Date().toISOString(), fxAsOf: new Date().toISOString().slice(0,10), results });
  } catch (error) {
    return res.status(502).json({ error: 'Dividend provider request failed: ' + String(error.message || error) });
  }
}
