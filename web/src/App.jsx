import { useEffect, useState } from 'react'

// 배포 시 VITE_API_BASE에 Cloud Run api URL 주입. 로컬은 빈 값 → vite 프록시 사용.
const API_BASE = import.meta.env.VITE_API_BASE || ''

export default function App() {
  const [query, setQuery] = useState('')
  const [age, setAge] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!loading) return undefined
    setElapsed(0)
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000)
    return () => window.clearInterval(timer)
  }, [loading])

  async function ask(e) {
    e.preventDefault()
    if (!query.trim()) {
      setError('어떤 지원이 궁금한지 입력해 주세요.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 90000)
    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          query: query.trim(),
          age: Number(age) || null,
          k: 5,
        }),
      })
      if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
      setResult(await res.json())
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('서버 준비가 예상보다 오래 걸리고 있습니다. 잠시 후 다시 검색해 주세요.')
      } else {
        setError('검색 서버에 연결하지 못했습니다. 잠시 후 같은 내용으로 다시 시도해 주세요.')
      }
    } finally {
      window.clearTimeout(timeout)
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🧭 혜택나침반</h1>
        <p>궁금한 걸 물어보면, 받을 수 있는 청년 정책을 근거와 함께 찾아드려요.</p>
      </header>

      <form className="card form" onSubmit={ask}>
        <label className="field full">
          <span>무엇이 궁금하세요?</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 월세 지원 받고 싶어 / 창업 자금이 필요해"
          />
          <small className="hint">지역명 대신 필요한 지원 내용으로 검색하세요 (예: 월세, 창업 자금, 자격증 교육)</small>
        </label>
        <label className="field">
          <span>나이 (선택)</span>
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="예: 28"
            min="0"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? (elapsed < 8 ? '관련 정책을 찾는 중…' : '검색 서버를 준비하는 중…') : '청년 정책 찾기'}
        </button>
        {loading ? (
          <div className="loading-note" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            <div>
              <strong>{elapsed < 8 ? '질문과 정책을 비교하고 있어요.' : '무료 서버를 깨우고 있어요.'}</strong>
              <small>{elapsed < 8 ? '검색 결과를 정리하는 데 잠시 시간이 필요합니다.' : `첫 요청은 최대 60초 정도 걸릴 수 있습니다. (${elapsed}초 경과)`}</small>
            </div>
          </div>
        ) : (
          <small className="cold-start-hint">첫 검색은 무료 서버 준비로 30~60초 걸릴 수 있습니다.</small>
        )}
      </form>

      {error && <div className="card error"><strong>요청을 완료하지 못했어요.</strong><p>{error}</p></div>}

      {result && (
        <>
          <section className="card answer">
            <h2>답변</h2>
            <p className="answer-text">{result.answer}</p>
          </section>

          {result.sources.length > 0 && (
            <section className="sources">
              <h2>근거 정책 {result.sources.length}건</h2>
              {result.sources.map((p) => (
                <article className="card policy" key={p.source_id}>
                  <div className="policy-head">
                    <h3>{p.title}</h3>
                  </div>
                  <div className="meta">
                    <span>{p.org}</span>
                    {p.age_min != null && <span>· {p.age_min}~{p.age_max}세</span>}
                    {p.income_etc && <span>· {p.income_etc}</span>}
                  </div>
                  {p.support_content && <p className="support">{p.support_content}</p>}
                  {p.apply_url && (
                    <a className="apply" href={p.apply_url} target="_blank" rel="noreferrer">
                      신청 페이지 →
                    </a>
                  )}
                </article>
              ))}
            </section>
          )}
        </>
      )}

      <footer>데이터 출처: 온통청년 (공공데이터포털)</footer>
    </div>
  )
}
