import { useMemo, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';

type AskResponse = {
  answer: string;
  matched_services: string[];
  triage_level: string;
  confidence: number;
  suggested_slots: string[];
};

type FacilityRow = {
  "Denominazione struttura"?: string;
  "Nome struttura"?: string;
  "Comune struttura"?: string;
  "Indirizzo"?: string;
  "Codice prestazione ambulatoriale"?: string;
};

type FacilityResponse = {
  count: number;
  matches: string[];
  rows: FacilityRow[];
};

type PharmacyRow = {
  Farmacia: string;
  Comune: string;
  Indirizzo: string;
  "Aperta 24h": string;
  "Farmaci disponibili (mock)": string;
};

type PharmacyResponse = {
  count: number;
  rows: PharmacyRow[];
};

type PharmacyMapPin = {
  name: string;
  lat: number;
  lng: number;
  address?: string;
  open24h?: string;
};

type ChatMessage = {
  role: 'user' | 'assistant';
  text: string;
  triage?: string;
  confidence?: number;
  services?: string[];
  slots?: string[];
};

type CityMeta = { city: string; province: string; active: boolean };

type StructureCard = {
  name: string;
  city: string;
  address: string;
  service: string;
  image: string;
};

type ContactInfo = {
  structureName: string;
  phone: string;
  email: string;
  bookingEmail: string;
  hours: string;
  contactPerson: string;
  notes: string;
};

const CITIES: CityMeta[] = [
  { city: 'Milano', province: 'MI', active: true },
  { city: 'Sesto San Giovanni', province: 'MI', active: false },
  { city: 'Rho', province: 'MI', active: false },
  { city: 'Monza', province: 'MB', active: false },
  { city: 'Bergamo', province: 'BG', active: false },
  { city: 'Brescia', province: 'BS', active: false },
  { city: 'Como', province: 'CO', active: false },
  { city: 'Varese', province: 'VA', active: false },
  { city: 'Lecco', province: 'LC', active: false },
  { city: 'Pavia', province: 'PV', active: false },
  { city: 'Cremona', province: 'CR', active: false },
  { city: 'Mantova', province: 'MN', active: false },
  { city: 'Lodi', province: 'LO', active: false },
  { city: 'Sondrio', province: 'SO', active: false },
];

const HEALTH_IMAGES = [
  'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1100&q=80',
  'https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&w=1100&q=80',
  'https://images.unsplash.com/photo-1666214280391-8ff5bd3c0bf0?auto=format&fit=crop&w=1100&q=80',
  'https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?auto=format&fit=crop&w=1100&q=80',
  'https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=1100&q=80',
  'https://images.unsplash.com/photo-1666214277653-2d3ecaf0f230?auto=format&fit=crop&w=1100&q=80',
];

const FALLBACK_CLINIC_IMG =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='700'>
      <defs>
        <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='#0f766e'/>
          <stop offset='100%' stop-color='#14b8a6'/>
        </linearGradient>
      </defs>
      <rect width='100%' height='100%' fill='url(#g)'/>
      <g fill='white' opacity='0.95'>
        <rect x='430' y='220' width='340' height='260' rx='22'/>
        <rect x='575' y='155' width='50' height='90' rx='8'/>
        <rect x='520' y='190' width='160' height='50' rx='8'/>
      </g>
      <text x='50%' y='88%' dominant-baseline='middle' text-anchor='middle' fill='white' font-family='Arial' font-size='44'>Struttura Sanitaria</text>
    </svg>`
  );

const api = async <T,>(path: string, body?: unknown, formData?: FormData): Promise<T> => {
  const res = await fetch(`/api${path}`, {
    method: body || formData ? 'POST' : 'GET',
    headers: formData ? undefined : { 'Content-Type': 'application/json' },
    body: formData ? formData : body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Errore API');
  return data as T;
};

const stripMarkdown = (text: string): string =>
  text
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`(.*?)`/g, '$1')
    .replace(/^[-*_]{3,}$/gm, '')
    .trim();

const parseAnswerBlocks = (raw: string): string[] => {
  const cleaned = stripMarkdown(raw).replace(/\r/g, '').replace(/\n{3,}/g, '\n\n').trim();
  if (!cleaned) return ['Nessun contenuto disponibile.'];

  const lines = cleaned
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .filter((l) => !/^dettaglio\s+\d+$/i.test(l))
    .filter((l) => !/^risposta al paziente$/i.test(l));

  const deduped: string[] = [];
  for (const line of lines) {
    if (deduped[deduped.length - 1]?.toLowerCase() === line.toLowerCase()) continue;
    deduped.push(line);
  }

  const paragraphs = deduped.join('\n').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return paragraphs.length ? paragraphs : ['Nessun contenuto disponibile.'];
};

const cleanBody = (text: string) =>
  text
    .replace(/^-\s+/gm, '• ')
    .replace(/\s+([0-9]+[\).]\s)/g, '\n$1')
    .replace(/\s+([•]\s)/g, '\n$1')
    .replace(/:\s+(?=[0-9]+[\).]|•)/g, ':\n');

const inferDrugsFromText = (text: string): string[] => {
  const t = text.toLowerCase();
  const known = ['ibuprofene', 'tachipirina', 'paracetamolo', 'amoxicillina', 'omeprazolo', 'aspirina', 'brufen'];
  return known.filter((d) => t.includes(d));
};

const inferServicesFromQuery = (text: string): string[] => {
  const t = text.toLowerCase();
  const out: string[] = [];
  if (t.includes('petto') || t.includes('torac') || t.includes('cardio')) out.push('VISITA CARDIOLOGICA');
  if (t.includes('piede') || t.includes('cavig') || t.includes('trauma')) out.push('VISITA ORTOPEDICA');
  if (t.includes('sangue') || t.includes('analisi')) out.push('ESAMI DEL SANGUE');
  if (t.includes('occhi') || t.includes('vista')) out.push('VISITA OCULISTICA');
  if (t.includes('pelle') || t.includes('derma')) out.push('VISITA DERMATOLOGICA');
  if (!out.length) out.push('VISITA SPECIALISTICA');
  return Array.from(new Set(out));
};

const inferActionPlanFromQuery = (text: string): string[] => {
  const t = text.toLowerCase();

  if (t.includes('petto') || t.includes('torac')) {
    return [
      'Se il dolore aumenta, compare fiato corto o forte malessere: contatta subito il 118.',
      'Se il dolore resta lieve ma persistente: richiedi una valutazione medica in giornata.',
      'Evita sforzi intensi finché non hai fatto una valutazione clinica.',
      'Porta con te eventuali esami recenti per accelerare la visita.',
    ];
  }

  if (t.includes('piede') || t.includes('cavig') || t.includes('trauma')) {
    return [
      'Riposo, ghiaccio 15-20 minuti, compressione leggera ed elevazione.',
      'Se dolore o gonfiore peggiorano, richiedi valutazione ortopedica rapida.',
      'Se non riesci a caricare il peso, considera un accesso in urgenza.',
    ];
  }

  return [
    'Descrivi sintomi, durata e intensità per una valutazione più precisa.',
    'Prenota la prima visita specialistica coerente con il bisogno segnalato.',
    'Se i sintomi peggiorano rapidamente, richiedi assistenza medica immediata.',
  ];
};

const inferServiceFromText = (text: string): string => {
  const t = text.toLowerCase();
  if (t.includes('cardio') || t.includes('torac')) return 'VISITA CARDIOLOGICA';
  if (t.includes('sangue') || t.includes('analisi')) return 'ESAMI DEL SANGUE';
  if (t.includes('occhi') || t.includes('vista')) return 'VISITA OCULISTICA';
  if (t.includes('pelle') || t.includes('derma')) return 'VISITA DERMATOLOGICA';
  return 'VISITA SPECIALISTICA';
};

const toStructureCards = (rows: FacilityRow[], serviceHint: string, city: string): StructureCard[] => {
  const out: StructureCard[] = [];
  const seen = new Set<string>();

  rows.forEach((r, i) => {
    const name = r['Nome struttura'] || r['Denominazione struttura'] || `Centro Salute ${i + 1}`;
    if (seen.has(name)) return;
    seen.add(name);

    out.push({
      name,
      city: r['Comune struttura'] || city,
      address: r['Indirizzo'] || 'Indirizzo non disponibile',
      service: r['Codice prestazione ambulatoriale'] || serviceHint,
      image: HEALTH_IMAGES[i % HEALTH_IMAGES.length],
    });
  });

  return out.slice(0, 6);
};

const mockStructureCards = (service: string, city: string): StructureCard[] => [
  { name: 'Poliambulatorio San Marco', city, address: 'Via Manzoni 12', service, image: HEALTH_IMAGES[0] },
  { name: 'Centro Medico Navigli', city, address: 'Alzaia Naviglio 45', service, image: HEALTH_IMAGES[1] },
  { name: 'Clinica Città Studi', city, address: 'Via Pacini 22', service, image: HEALTH_IMAGES[2] },
  { name: 'Ambulatorio Porta Romana', city, address: 'Corso Lodi 18', service, image: HEALTH_IMAGES[3] },
  { name: 'Istituto Salute Duomo', city, address: 'Via Torino 8', service, image: HEALTH_IMAGES[4] },
  { name: 'Centro Diagnostico Isola', city, address: 'Via Borsieri 30', service, image: HEALTH_IMAGES[5] },
];

const generateMassiveMockStructures = (service: string, city: string, count = 360): StructureCard[] => {
  const nameA = ['Centro Medico', 'Poliambulatorio', 'Istituto Clinico', 'Casa della Salute', 'Clinica', 'Ambulatorio'];
  const nameB = ['Duomo', 'Navigli', 'Bicocca', 'Porta Nuova', 'CityLife', 'Brera', 'Isola', 'Lambrate', 'Loreto', 'Sempione'];
  const streets = ['Via Roma', 'Corso Italia', 'Via Torino', 'Viale Monza', 'Via Cenisio', 'Viale Certosa', 'Via Washington', 'Via Ripamonti'];
  const out: StructureCard[] = [];
  for (let i = 0; i < count; i += 1) {
    const a = nameA[i % nameA.length];
    const b = nameB[i % nameB.length];
    const n = 10 + (i % 190);
    out.push({
      name: `${a} ${b} ${Math.floor(i / 10) + 1}`,
      city,
      address: `${streets[i % streets.length]} ${n}`,
      service,
      image: HEALTH_IMAGES[i % HEALTH_IMAGES.length],
    });
  }
  return out;
};

const toContactInfo = (s: StructureCard | null): ContactInfo | null => {
  if (!s) return null;

  const seed = s.name.length + s.city.length;
  const phone = `02 ${7000 + seed}${(100 + seed).toString().slice(-3)} ${100 + (seed % 900)}`;
  const slug = s.name.toLowerCase().replace(/[^a-z0-9]+/g, '.').replace(/^\.|\.$/g, '');

  return {
    structureName: s.name,
    phone,
    email: `info@${slug}.it`,
    bookingEmail: `prenotazioni@${slug}.it`,
    hours: 'Lun-Ven 08:00-19:00 • Sab 08:00-13:00',
    contactPerson: 'Ufficio Relazioni Pazienti',
    notes: `Servizio richiesto: ${s.service}. Disponibilità agenda verificabile via email o telefono.`,
  };
};

export default function App() {
  const [province, setProvince] = useState('MI');
  const [city, setCity] = useState('Milano');

  const [q, setQ] = useState('');
  const [chatOut, setChatOut] = useState<AskResponse | null>(null);
  const [chatError, setChatError] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Ciao, dimmi cosa ti serve. Ti aiuto a trovare il percorso sanitario più adatto.' },
  ]);

  const [file, setFile] = useState<File | null>(null);
  const [ocrPriv, setOcrPriv] = useState('NO');
  const [ocrOut, setOcrOut] = useState<{ terms: string[]; matches: string[]; answer: string; context?: any } | null>(null);
  const [ocrError, setOcrError] = useState('');

  const [prestazione, setPrestazione] = useState('VISITA CARDIOLOGICA');
  const [svcOut, setSvcOut] = useState<FacilityResponse | null>(null);
  const [svcCards, setSvcCards] = useState<StructureCard[]>(mockStructureCards('VISITA CARDIOLOGICA', 'Milano'));
  const [selectedStructure, setSelectedStructure] = useState<StructureCard | null>(mockStructureCards('VISITA CARDIOLOGICA', 'Milano')[0]);
  const [svcError, setSvcError] = useState('');

  const [drug, setDrug] = useState('ibuprofene');
  const [only24, setOnly24] = useState(false);
  const [phOut, setPhOut] = useState<PharmacyResponse | null>(null);
  const [phError, setPhError] = useState('');

  const provinces = useMemo(() => Array.from(new Set(CITIES.map((c) => c.province))), []);
  const citiesInProvince = useMemo(() => CITIES.filter((c) => c.province === province), [province]);
  const selectedCity = CITIES.find((c) => c.city === city);
  const isCityActive = Boolean(selectedCity?.active);

  const comingSoonMsg = `La città ${city} è in Coming Soon. Per la demo completa seleziona Milano.`;
  const activeContact = toContactInfo(selectedStructure);
  const pharmacyMapPins = useMemo<PharmacyMapPin[]>(() => {
    const baseCoords = [
      { lat: 45.4642, lng: 9.19 },
      { lat: 45.4721, lng: 9.1824 },
      { lat: 45.4587, lng: 9.2041 },
      { lat: 45.4782, lng: 9.2151 },
      { lat: 45.4528, lng: 9.1762 },
      { lat: 45.4669, lng: 9.2223 },
      { lat: 45.4876, lng: 9.1714 },
    ];
    const fallback = [
      { Farmacia: 'Farmacia Duomo', Indirizzo: 'Piazza Duomo', 'Aperta 24h': 'SI' },
      { Farmacia: 'Farmacia Navigli', Indirizzo: 'Alzaia Naviglio Grande', 'Aperta 24h': 'NO' },
      { Farmacia: 'Farmacia Centrale', Indirizzo: 'Piazza Duca d Aosta', 'Aperta 24h': 'SI' },
      { Farmacia: 'Farmacia Città Studi', Indirizzo: 'Via Pacini', 'Aperta 24h': 'NO' },
      { Farmacia: 'Farmacia Porta Romana', Indirizzo: 'Corso Lodi', 'Aperta 24h': 'SI' },
    ];
    const rows = phOut?.rows?.length ? phOut.rows : fallback;
    return rows.slice(0, 7).map((r, i) => ({
      name: r.Farmacia,
      address: r.Indirizzo,
      open24h: r['Aperta 24h'],
      lat: baseCoords[i % baseCoords.length].lat,
      lng: baseCoords[i % baseCoords.length].lng,
    }));
  }, [phOut]);

  const intelligence = useMemo(() => {
    const entities = ocrOut?.context?.entities || {};
    const docDrugs: string[] = entities.drugs || [];
    const docServices: string[] = entities.services || [];
    const docActions: string[] = entities.action_items || [];

    const chatServices = inferServicesFromQuery(q);
    const chatDrugs = inferDrugsFromText(q);
    const chatActions = inferActionPlanFromQuery(q);

    const drugs: string[] = Array.from(new Set([...docDrugs, ...chatDrugs]));
    const services: string[] = Array.from(new Set([...chatServices, ...docServices]));
    const actions: string[] = Array.from(new Set([...docActions, ...chatActions]));

    const quickSummary = [
      services.length ? `Servizi rilevati: ${services.slice(0, 4).join(', ')}` : null,
      drugs.length ? `Farmaci rilevati: ${drugs.slice(0, 4).join(', ')}` : null,
      actions.length ? `Azioni rilevate: ${actions.length}` : null,
    ].filter(Boolean) as string[];

    return { drugs, services, actions, quickSummary };
  }, [ocrOut, chatOut, q]);

  const runFacilitySearch = async (serviceToFind: string) => {
    const d = await api<FacilityResponse>('/facility-search', { prestazione: serviceToFind, comune: city });
    setSvcOut(d);
    const cards = toStructureCards(d.rows, serviceToFind, city);
    const normalized = cards.length ? cards : mockStructureCards(serviceToFind, city);
    const expanded = normalized.length < 40 ? [...normalized, ...generateMassiveMockStructures(serviceToFind, city, 360)] : normalized;
    setSvcCards(expanded.slice(0, 400));
    setSelectedStructure(expanded[0] || null);
  };

  const resetAll = () => {
    const defaultCards = mockStructureCards('VISITA CARDIOLOGICA', 'Milano');
    setProvince('MI');
    setCity('Milano');
    setQ('');
    setFile(null);
    setChatOut(null);
    setChatError('');
    setOcrError('');
    setOcrOut(null);
    setPrestazione('VISITA CARDIOLOGICA');
    setSvcOut(null);
    setSvcCards(defaultCards);
    setSelectedStructure(defaultCards[0] || null);
    setSvcError('');
    setDrug('ibuprofene');
    setOnly24(false);
    setPhOut(null);
    setPhError('');
    setChatMessages([{ role: 'assistant', text: 'Ciao, dimmi cosa ti serve. Ti aiuto a trovare il percorso sanitario più adatto.' }]);
  };

  const resetChatOnly = () => {
    setQ('');
    setFile(null);
    setChatOut(null);
    setChatError('');
    setOcrError('');
    setChatMessages([{ role: 'assistant', text: 'Ciao, dimmi cosa ti serve. Ti aiuto a trovare il percorso sanitario più adatto.' }]);
  };

  return (
    <main className="page">
      <div className="shell">
        <header className="top-hero">
          <div>
            <p className="kicker">PSS HEALTHCARE</p>
            <h1>Piattaforma di Orientamento Sanitario</h1>
            <p className="subtitle">Un assistente digitale pensato per accompagnare cittadini e famiglie nella scelta rapida di servizi, strutture e supporto farmaceutico.</p>
            <div className="chips-row"><span>Salute Digitale</span><span>Prevenzione</span><span>Accesso Alle Cure</span><span>Sanità Territoriale</span></div>
          </div>
          <img src={HEALTH_IMAGES[0]} alt="Clinica" onError={(e) => { (e.currentTarget as HTMLImageElement).src = FALLBACK_CLINIC_IMG; }} />
        </header>

        <section className="panel filters">
          <h2>Scegli La Tua Città</h2>
          <div className="filter-grid">
            <select className="input" value={province} onChange={(e) => { setProvince(e.target.value); const first = CITIES.find((c) => c.province === e.target.value); if (first) setCity(first.city); }}>
              {provinces.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <select className="input" value={city} onChange={(e) => setCity(e.target.value)}>
              {citiesInProvince.map((c) => <option key={c.city} value={c.city}>{c.city}{c.active ? '' : ' (Coming Soon)'}</option>)}
            </select>
            <button className="reset-btn" onClick={resetAll}>Reset</button>
          </div>
          {!isCityActive ? <p className="error-text">{comingSoonMsg}</p> : null}
        </section>

        <div className="layout-grid">
          <section className="panel card-a row-top">
            <div className="assistant-head">
              <h3>Care Navigator</h3>
              <p className="hint">Racconta il tuo bisogno e allega eventuali documenti: ricevi un percorso chiaro tra opzioni e prossimi passi.</p>
            </div>
            <div className="chat-window chat-conversation">
              {chatMessages.map((m, i) => (
                <div key={`${m.role}-${i}`} className={`msg ${m.role === 'user' ? 'user-msg' : 'bot-msg'}`}>
                  <p>{cleanBody(m.text)}</p>
                  {m.role === 'assistant' && m.triage ? (
                    <div className="msg-meta">
                      <span className={`triage ${m.triage === 'high' ? 'triage-high' : m.triage === 'medium' ? 'triage-medium' : 'triage-standard'}`}>
                        Priorità: {m.triage.toUpperCase()} • Affidabilità: {m.confidence ?? '-'}
                      </span>
                      {m.services?.length ? <div className="chips">{m.services.slice(0, 4).map((s) => <span key={s}>{s}</span>)}</div> : null}
                      {m.slots?.length ? <div className="slots">{m.slots.slice(0, 3).map((s) => <span key={s}>{s}</span>)}</div> : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
            <div className="composer">
              <button className="new-chat-btn" onClick={resetChatOnly}>Nuova chat</button>
              <label className="attach-btn">
                <input className="hidden-file" type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                Allega
              </label>
              <input
                className="composer-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Scrivi un messaggio..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    (document.getElementById('send-btn') as HTMLButtonElement | null)?.click();
                  }
                }}
              />
              <button id="send-btn" className="btn btn-primary composer-send" onClick={async () => {
                setChatError('');
                setOcrError('');
                if (!isCityActive) { setChatError(comingSoonMsg); return; }
                try {
                  const userText = q.trim() || 'Analizza documento allegato';
                  setChatMessages((prev) => [...prev, { role: 'user', text: userText }]);
                  let extractedTerms: string[] = [];
                  if (file) {
                    const fd = new FormData();
                    fd.append('file', file);
                    fd.append('comune', city);
                    fd.append('struttura_privata', ocrPriv);
                    const ocr = await api<any>('/extract-and-match-upload', undefined, fd);
                    extractedTerms = ocr.extracted_terms || [];
                    setOcrOut({ terms: extractedTerms, matches: ocr.matched_services || [], answer: ocr.answer || '', context: ocr.document_context || {} });
                  }
                  const d = await api<AskResponse>('/ask', { text: userText, comune: city, extracted_terms: extractedTerms });
                  setChatOut(d);
                  setChatMessages((prev) => [
                    ...prev,
                    {
                      role: 'assistant',
                      text: parseAnswerBlocks(d.answer).join('\n\n'),
                      triage: d.triage_level,
                      confidence: d.confidence,
                      services: d.matched_services,
                      slots: d.suggested_slots,
                    },
                  ]);
                  const service = d.matched_services?.[0] || extractedTerms[0] || inferServiceFromText(userText);
                  setPrestazione(service);
                  await runFacilitySearch(service);
                  setQ('');
                } catch (e: any) { setChatError(e.message); }
              }}>Invia</button>
            </div>
            {file ? <p className="file-chip">Documento: {file.name}</p> : null}
            {ocrError ? <p className="error-text">{ocrError}</p> : null}
            {chatError ? <p className="error-text">{chatError}</p> : null}
          </section>

          <section className="panel card-b row-top">
            <h3>Intelligence Box</h3>
            <p className="hint">Quadro rapido: sintetizza i prossimi passi in base alla richiesta utente e ai documenti caricati.</p>
            <div className="result intel-box mt-2">
              {intelligence.quickSummary.length ? (
                <>
                  <p className="small-title">Sintesi Rapida</p>
                  <ul className="intel-list">
                    {intelligence.quickSummary.map((q, i) => <li key={`${q}-${i}`}>{q}</li>)}
                  </ul>
                </>
              ) : <p className="hint">Carica un documento in chat per popolare l'intelligence.</p>}

              {intelligence.services.length ? (
                <>
                  <p className="small-title">Servizi Rilevati</p>
                  <div className="chips">
                    {intelligence.services.slice(0, 8).map((svc: string) => (
                      <button key={svc} className="chip-btn" onClick={async () => {
                        setPrestazione(svc);
                        setSvcError('');
                        try {
                          await runFacilitySearch(svc);
                        } catch (e: any) {
                          setSvcError(e.message);
                        }
                      }}>{svc}</button>
                    ))}
                  </div>
                </>
              ) : null}

              {intelligence.drugs.length ? (
                <>
                  <p className="small-title">Farmaci Rilevati</p>
                  <div className="chips">
                    {intelligence.drugs.slice(0, 8).map((d: string) => (
                      <button key={d} className="chip-btn" onClick={async () => {
                        setDrug(d);
                        setPhError('');
                        try {
                          const r = await api<PharmacyResponse>('/pharmacies', { farmaco: d, comune: city, only_24h: only24 });
                          setPhOut(r);
                        } catch (e: any) {
                          setPhError(e.message);
                        }
                      }}>{d}</button>
                    ))}
                  </div>
                </>
              ) : null}

              {intelligence.actions.length ? (
                <>
                  <p className="small-title">Piano d'Azione (estratto)</p>
                  <ul className="intel-list">
                    {intelligence.actions.slice(0, 8).map((a: string, i: number) => <li key={`${a}-${i}`}>{a}</li>)}
                  </ul>
                </>
              ) : null}
            </div>
          </section>

          <section className="panel card-d row-top">
            <h3>Farmacie e Farmaci</h3>
            <p className="hint">Ricerca disponibilità farmaci e farmacie di zona con filtro apertura continuata.</p>
            <div className="search-row">
              <input className="input" value={drug} onChange={(e) => setDrug(e.target.value)} placeholder="Farmaco" />
              <label className="check"><input type="checkbox" checked={only24} onChange={(e) => setOnly24(e.target.checked)} />Solo 24h</label>
            </div>
            <button className="btn" onClick={async () => {
              setPhError('');
              if (!isCityActive) { setPhError(comingSoonMsg); return; }
              try { const d = await api<PharmacyResponse>('/pharmacies', { farmaco: drug, comune: city, only_24h: only24 }); setPhOut(d); } catch (e: any) { setPhError(e.message); }
            }}>Trova farmacie</button>
            {phError ? <p className="error-text">{phError}</p> : null}
            {phOut ? <div className="result mt-3"><p className="small-title">Farmacie trovate: {phOut.count}</p><div className="table-wrap"><table><thead><tr><th>Farmacia</th><th>Comune</th><th>24h</th><th>Farmaci</th></tr></thead><tbody>{phOut.rows.slice(0, 8).map((r, i) => <tr key={`${r.Farmacia}-${i}`}><td>{r.Farmacia}</td><td>{r.Comune}</td><td>{r['Aperta 24h']}</td><td>{r['Farmaci disponibili (mock)']}</td></tr>)}</tbody></table></div></div> : <p className="hint">Esegui una ricerca per vedere le farmacie disponibili.</p>}
            <div className="ph-map">
              <p className="small-title">Mappa Farmacie</p>
              <div className="leaflet-wrap">
                <MapContainer center={[45.4642, 9.19]} zoom={12} scrollWheelZoom className="leaflet-map">
                  <TileLayer
                    attribution='&copy; OpenStreetMap contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {pharmacyMapPins.map((p) => (
                    <Marker key={`${p.name}-${p.lat}-${p.lng}`} position={[p.lat, p.lng]}>
                      <Popup>
                        <b>{p.name}</b><br />
                        {p.address || 'Milano'}<br />
                        Apertura 24h: {p.open24h || 'N/D'}
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
              <div className="map-legend">
                {pharmacyMapPins.map((p) => <span key={`legend-${p.name}`}>{p.name}</span>)}
              </div>
            </div>
          </section>

          <section className="panel card-c">
            <h3>Ricerca Strutture</h3>
            <p className="hint">Selezione strutture con suggerimenti dinamici in base alle esigenze dell'utente.</p>
            <div className="search-row">
              <input className="input" value={prestazione} onChange={(e) => setPrestazione(e.target.value)} placeholder="Prestazione" />
              <button className="btn" onClick={async () => {
                setSvcError('');
                if (!isCityActive) { setSvcError(comingSoonMsg); return; }
                try { await runFacilitySearch(prestazione); } catch (e: any) { setSvcError(e.message); }
              }}>Cerca</button>
            </div>
            {svcError ? <p className="error-text">{svcError}</p> : null}
            <div className="structures">
              {svcCards.map((s, i) => (
                <article className={`s-card ${selectedStructure?.name === s.name ? 'selected' : ''}`} key={`${s.name}-${i}`} onClick={() => setSelectedStructure(s)}>
                  <img src={s.image} alt={s.name} onError={(e) => { (e.currentTarget as HTMLImageElement).src = FALLBACK_CLINIC_IMG; }} />
                  <div>
                    <h4>{s.name}</h4>
                    <p>{s.city} • {s.address}</p>
                    <span>{s.service}</span>
                  </div>
                </article>
              ))}
            </div>
            <p className="hint">{svcOut ? `Strutture trovate: ${svcOut.count}` : 'Mostro suggerimenti iniziali per Milano.'}</p>
          </section>

          <section className="panel card-e">
            <div className="contact-box">
              <p className="contact-title">Contatti Struttura Selezionata</p>
              {activeContact ? (
                <div className="contact-grid">
                  <div><b>Struttura:</b> {activeContact.structureName}</div>
                  <div><b>Telefono:</b> {activeContact.phone}</div>
                  <div><b>Email info:</b> {activeContact.email}</div>
                  <div><b>Email prenotazioni:</b> {activeContact.bookingEmail}</div>
                  <div><b>Orari:</b> {activeContact.hours}</div>
                  <div><b>Referente:</b> {activeContact.contactPerson}</div>
                  <div className="contact-note"><b>Note:</b> {activeContact.notes}</div>
                </div>
              ) : (
                <p className="hint">Clicca una struttura o avvia una ricerca via chat/OCR per attivare i contatti.</p>
              )}
            </div>
          </section>

        </div>
      </div>
    </main>
  );
}


