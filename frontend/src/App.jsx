import { useState } from 'react'
import './App.css'

const STEPS = [
  { node: 'research:product_researcher',  label: 'Researching product' },
  { node: 'research:market_researcher',   label: 'Researching market' },
  { node: 'research:business_researcher', label: 'Researching business' },
  { node: 'research:profile_synthesizer', label: 'Synthesizing company profile' },
  { node: 'analysis:extractor',           label: 'Extracting structured data' },
  { node: 'analysis:scorer',              label: 'Scoring dimensions' },
  { node: 'analysis:advisor',             label: 'Writing investment advice' },
  { node: 'analysis:report_generator',    label: 'Generating report' },
  { node: 'analysis:evaluator',           label: 'Evaluating quality' },
]

function ScoreBar({ label, score, max = 10 }) {
  const pct = (score / max) * 100
  const color = pct >= 80 ? '#22c55e' : pct >= 60 ? '#f59e0b' : '#ef4444'
  return (
    <div className="score-row">
      <span className="score-label">{label}</span>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-value">{score}/{max}</span>
    </div>
  )
}

function parseBold(text) {
  return text.split(/(\*\*[^*]+\*\*)/).map((p, j) =>
    p.startsWith('**') ? <strong key={j}>{p.slice(2, -2)}</strong> : p
  )
}

function ReportBody({ text }) {
  const elements = []
  let listItems = []

  const flushList = () => {
    if (listItems.length) {
      elements.push(<ul key={`ul-${elements.length}`}>{listItems}</ul>)
      listItems = []
    }
  }

  text.split('\n').forEach((line, i) => {
    if (line.startsWith('## ')) {
      flushList()
      elements.push(<h2 key={i}>{line.slice(3)}</h2>)
    } else if (line.startsWith('### ')) {
      flushList()
      elements.push(<h3 key={i}>{line.slice(4)}</h3>)
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      listItems.push(<li key={i}>{parseBold(line.slice(2))}</li>)
    } else if (line.startsWith('|')) {
      flushList()
      // skip separator rows like |---|---|
      if (/^\|[-| ]+\|$/.test(line)) return
      const cells = line.split('|').map(c => c.trim()).filter(Boolean)
      if (cells.length >= 2) {
        elements.push(
          <div key={i} className="inline-row">
            <span className="inline-key">{parseBold(cells[0])}</span>
            <span className="inline-val">{parseBold(cells.slice(1).join(' '))}</span>
          </div>
        )
      }
    } else if (line.trim() === '' || line.match(/^-{3,}$/)) {
      flushList()
      elements.push(<div key={i} className="gap" />)
    } else {
      flushList()
      elements.push(<p key={i}>{parseBold(line)}</p>)
    }
  })
  flushList()
  return <div className="report-body">{elements}</div>
}

function Report({ data }) {
  const scores = data.dimension_scores || {}
  const info = data.structured_info || {}
  const total = Object.values(scores).reduce((a, b) => a + b, 0)
  const maxTotal = Object.keys(scores).length * 10

  return (
    <div className="report">
      <div className="report-header">
        <div>
          <h2 className="report-title">{info.company_name || data.company_name}</h2>
          <span className="report-sub">Investment Analysis Report</span>
        </div>
        <span className={`badge ${data.is_pass ? 'badge-pass' : 'badge-warn'}`}>
          {data.is_pass ? '✓ Evaluation Passed' : '⚠ Needs Review'}
        </span>
      </div>

      <div className="two-col">
        <div className="card">
          <h3>Key Facts</h3>
          <div className="facts">
            {[
              ['Founded',      info.founded_year],
              ['HQ',           info.headquarters],
              ['Stage',        info.funding_stage],
              ['Valuation',    info.valuation_usd ? `$${(info.valuation_usd/1e9).toFixed(1)}B` : null],
              ['Revenue',      info.revenue_model],
              ['Competitors',  info.key_competitors?.join(', ')],
              ['Investors',    info.notable_investors?.join(', ')],
            ].filter(([, v]) => v).map(([k, v]) => (
              <div key={k} className="fact-row">
                <span className="fact-key">{k}</span>
                <span className="fact-val">{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3>Hexagon Score <span className="score-total">{total} / {maxTotal}</span></h3>
          {Object.entries(scores).map(([k, v]) => (
            <ScoreBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1)} score={v} />
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Full Report</h3>
        <ReportBody text={data.analysis_report || ''} />
      </div>

      {data.eval_feedback && (
        <div className="card card-muted">
          <h3>Quality Assessment</h3>
          <p>{data.eval_feedback}</p>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [company, setCompany]   = useState('')
  const [status, setStatus]     = useState('idle')
  const [doneNodes, setDoneNodes] = useState(new Set())
  const [result, setResult]     = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleAnalyze() {
    if (!company.trim() || status === 'loading') return
    setStatus('loading')
    setDoneNodes(new Set())
    setResult(null)
    setErrorMsg('')

    const collected = {}
    try {
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company: company.trim() }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') { setStatus('done'); setResult({ ...collected }); return }
          try {
            const evt = JSON.parse(raw)
            setDoneNodes(prev => new Set([...prev, evt.node]))
            Object.assign(collected, evt.data)
          } catch { /* skip */ }
        }
      }
    } catch (e) {
      setStatus('error')
      setErrorMsg(e.message)
    }
  }

  const activeIdx = doneNodes.size

  return (
    <div className="app">
      <header className="app-header">
        <h1>Research Agent</h1>
        <p>AI-powered company analysis · Claude + LangGraph</p>
      </header>

      <div className="search-box">
        <input
          type="text"
          placeholder="Company name — e.g. Notion, OpenAI, Stripe…"
          value={company}
          onChange={e => setCompany(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
          disabled={status === 'loading'}
        />
        <button onClick={handleAnalyze} disabled={status === 'loading' || !company.trim()}>
          {status === 'loading' ? 'Analyzing…' : 'Analyze →'}
        </button>
      </div>

      {status === 'loading' && (
        <div className="progress-panel">
          {STEPS.map(({ node, label }, idx) => {
            const done   = doneNodes.has(node)
            const active = idx === activeIdx
            return (
              <div key={node} className={`step ${done ? 'done' : active ? 'active' : 'pending'}`}>
                <span className="step-icon">{done ? '✓' : active ? '●' : '○'}</span>
                <span>{label}</span>
              </div>
            )
          })}
        </div>
      )}

      {status === 'error' && <div className="error-msg">⚠ {errorMsg}</div>}
      {status === 'done' && result && <Report data={result} />}
    </div>
  )
}
