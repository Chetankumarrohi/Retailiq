import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'

const SUGGESTED_QUESTIONS = [
  'Which store has the highest total sales?',
  'Which departments perform best?',
  'Compare holiday and normal-week sales.',
  'Forecast Store 1 Department 1 for four weeks.',
  'What is the markdown policy?',
  'What is the returns policy?'
]

const TOOL_DISPLAY_NAMES = {
  sql_analytics_tool: 'SQL Analytics',
  forecast_tool: 'Forecast Model',
  retrieval_tool: 'Policy Retrieval',
  knowledge_guardrail: 'Knowledge Guardrail'
}

const TOOL_ICONS = {
  sql_analytics_tool: '🗄️',
  forecast_tool: '📈',
  retrieval_tool: '📄',
  knowledge_guardrail: '🛡️'
}

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '👋 **Welcome to RetailIQ Business Assistant**.\n\nAsk questions about historical sales, future demand, and internal retail policies. I utilize specialized tools to inspect the star schema database, generate ML forecasts, and search company policy documentation.',
      tools_used: [],
      trace: [],
      sources: []
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTrace, setActiveTrace] = useState(null)
  const [activeSources, setActiveSources] = useState([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim()
    if (!query || loading) return

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: query
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await api.postChat(query)
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer || 'No response generated.',
        tools_used: response.tools_used || [],
        trace: response.trace || [],
        sources: response.sources || [],
        error: response.error
      }
      setMessages((prev) => [...prev, assistantMsg])
      if (response.trace && response.trace.length > 0) {
        setActiveTrace(response.trace)
      }
      if (response.sources && response.sources.length > 0) {
        setActiveSources(response.sources)
      }
    } catch (err) {
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ **Error processing request**: ${err.message}`,
        tools_used: [],
        trace: [],
        sources: []
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleSelectMessage = (msg) => {
    if (msg.trace && msg.trace.length > 0) {
      setActiveTrace(msg.trace)
    }
    if (msg.sources && msg.sources.length > 0) {
      setActiveSources(msg.sources)
    }
  }

  return (
    <div className="assistant-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>RetailIQ Business Assistant</h2>
          <p>Ask questions about historical sales, future demand and internal retail policies.</p>
        </div>
        <button
          className="btn-primary"
          style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 14px', fontSize: '12px' }}
          onClick={() => {
            setMessages([messages[0]])
            setActiveTrace(null)
            setActiveSources([])
          }}
        >
          🧹 Reset Chat
        </button>
      </div>

      <div className="assistant-layout">
        {/* Main Chat Conversation Panel */}
        <div className="chat-panel">
          <div className="chat-messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-msg ${msg.role}`}
                onClick={() => handleSelectMessage(msg)}
                style={{ cursor: msg.role === 'assistant' ? 'pointer' : 'default' }}
              >
                <div className="msg-bubble">
                  {msg.role === 'user' ? (
                    msg.content
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  )}

                  {msg.tools_used && msg.tools_used.length > 0 && (
                    <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {msg.tools_used.map((tool, idx) => (
                        <span
                          key={idx}
                          className="feature-chip"
                          style={{
                            background: 'rgba(59, 130, 246, 0.15)',
                            borderColor: 'rgba(59, 130, 246, 0.3)',
                            fontSize: '11px',
                            padding: '2px 8px'
                          }}
                        >
                          {TOOL_ICONS[tool] || '⚙️'} {TOOL_DISPLAY_NAMES[tool] || tool}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="msg-meta">
                  {msg.role === 'user' ? 'You' : 'RetailIQ Assistant'}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-msg assistant">
                <div className="msg-bubble" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                  <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                    Agent is planning & executing tools...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompts */}
          <div className="suggested-queries">
            {SUGGESTED_QUESTIONS.map((q, idx) => (
              <button key={idx} onClick={() => handleSend(q)} disabled={loading}>
                {q}
              </button>
            ))}
          </div>

          {/* Chat Input */}
          <div className="chat-input-area">
            <input
              type="text"
              placeholder="Ask a question about sales, forecasting, or policies..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              disabled={loading}
            />
            <button
              className="btn-primary"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              {loading ? 'Thinking...' : 'Send'}
            </button>
          </div>
        </div>

        {/* Right Trace & Citations Panel */}
        <div className="trace-panel">
          {/* Tool Execution Trace */}
          <div className="trace-section">
            <h4>⚙️ How RetailIQ Answered</h4>
            {activeTrace && activeTrace.length > 0 ? (
              activeTrace.map((step, idx) => (
                <div key={idx} className="trace-step">
                  <div className="trace-tool">
                    <span>{TOOL_ICONS[step.tool] || '🔧'}</span>
                    <span>Step {step.step || idx + 1} — {TOOL_DISPLAY_NAMES[step.tool] || step.tool}</span>
                  </div>
                  <div className="trace-reason">{step.reason}</div>
                  {step.output_summary && (
                    <div className="trace-output">
                      {step.output_summary}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', padding: '6px 0' }}>
                Tool execution traces (SQL Analytics, Forecast Model, Policy Retrieval) will appear here.
              </div>
            )}
          </div>

          {/* Policy Citations */}
          <div className="trace-section">
            <h4>📄 Policy Citations</h4>
            {activeSources && activeSources.length > 0 ? (
              <>
                {activeSources.map((source, idx) => (
                  <div key={idx} className="citation-item">
                    <div className="citation-section">
                      📌 Source: {source.document} — Section {source.section}
                    </div>
                    <div className="citation-snippet">{source.snippet}</div>
                  </div>
                ))}
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '10px' }}>
                  *Note: policy_docs.txt is synthetic project demonstration documentation.*
                </div>
              </>
            ) : (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', padding: '6px 0' }}>
                Grounded policy citations and synthetic documentation sources appear here.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
