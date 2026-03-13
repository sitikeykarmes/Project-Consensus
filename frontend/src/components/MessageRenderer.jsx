// src/components/MessageRenderer.jsx
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import remarkGfm from "remark-gfm";

// ── Copy Button ───────────────────────────────────────────────────────────────
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback for older browsers
      const el = document.createElement("textarea");
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        background: copied ? "#22c55e" : "#3f3f46",
        color: "#fff",
        border: "none",
        borderRadius: "5px",
        padding: "3px 10px",
        fontSize: "11px",
        cursor: "pointer",
        transition: "background 0.2s",
        fontFamily: "sans-serif",
        whiteSpace: "nowrap",
      }}
    >
      {copied ? "✓ Copied" : "Copy"}
    </button>
  );
}

// ── Main Markdown Renderer ────────────────────────────────────────────────────
export default function MessageRenderer({ content, dimText = false }) {
  const textColor = dimText ? "#8696a0" : "#e9edef";
  const baseStyle = { color: textColor, fontSize: "13px", lineHeight: "1.6" };

  return (
    <div style={baseStyle}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // ── Fenced code blocks ─────────────────────────────────────────────
          code({ node, inline, className, children, ...props }) {
            const language = className?.replace("language-", "") || "text";
            const code = String(children).replace(/\n$/, "");

            if (inline) {
              return (
                <code
                  style={{
                    background: "#0d1117",
                    color: "#79c0ff",
                    padding: "1px 6px",
                    borderRadius: "4px",
                    fontSize: "12px",
                    fontFamily: "monospace",
                    border: "1px solid #30363d",
                  }}
                  {...props}
                >
                  {code}
                </code>
              );
            }

            return (
              <div
                style={{
                  borderRadius: "8px",
                  overflow: "hidden",
                  margin: "10px 0",
                  border: "1px solid #30363d",
                }}
              >
                {/* Header: language + copy */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    background: "#161b22",
                    padding: "6px 14px",
                    borderBottom: "1px solid #30363d",
                  }}
                >
                  <span
                    style={{
                      color: "#7d8590",
                      fontSize: "11px",
                      fontFamily: "monospace",
                      textTransform: "lowercase",
                    }}
                  >
                    {language}
                  </span>
                  <CopyButton text={code} />
                </div>

                {/* Syntax-highlighted code */}
                <SyntaxHighlighter
                  language={language}
                  style={oneDark}
                  customStyle={{
                    margin: 0,
                    borderRadius: 0,
                    fontSize: "12.5px",
                    padding: "14px 16px",
                    background: "#0d1117",
                  }}
                  showLineNumbers={code.split("\n").length > 4}
                  lineNumberStyle={{ color: "#30363d", minWidth: "2.5em" }}
                  wrapLongLines={false}
                >
                  {code}
                </SyntaxHighlighter>
              </div>
            );
          },

          // ── Headings ───────────────────────────────────────────────────────
          h1: ({ children }) => (
            <h1
              style={{
                color: "#e9edef",
                fontSize: "17px",
                fontWeight: 700,
                margin: "14px 0 6px",
              }}
            >
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2
              style={{
                color: "#e9edef",
                fontSize: "15px",
                fontWeight: 700,
                margin: "12px 0 5px",
              }}
            >
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3
              style={{
                color: "#e9edef",
                fontSize: "13px",
                fontWeight: 600,
                margin: "10px 0 4px",
              }}
            >
              {children}
            </h3>
          ),

          // ── Paragraph ─────────────────────────────────────────────────────
          p: ({ children }) => (
            <p
              style={{
                margin: "4px 0 8px",
                color: textColor,
                lineHeight: "1.65",
              }}
            >
              {children}
            </p>
          ),

          // ── Lists ──────────────────────────────────────────────────────────
          ul: ({ children }) => (
            <ul
              style={{
                paddingLeft: "18px",
                margin: "4px 0 8px",
                color: textColor,
              }}
            >
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol
              style={{
                paddingLeft: "18px",
                margin: "4px 0 8px",
                color: textColor,
              }}
            >
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li
              style={{ margin: "2px 0", color: textColor, lineHeight: "1.55" }}
            >
              {children}
            </li>
          ),

          // ── Bold / Italic ──────────────────────────────────────────────────
          strong: ({ children }) => (
            <strong style={{ color: "#e9edef", fontWeight: 600 }}>
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em style={{ color: "#adbac7" }}>{children}</em>
          ),

          // ── Blockquote ─────────────────────────────────────────────────────
          blockquote: ({ children }) => (
            <blockquote
              style={{
                borderLeft: "3px solid #00a884",
                paddingLeft: "12px",
                margin: "8px 0",
                color: "#8696a0",
                fontStyle: "italic",
              }}
            >
              {children}
            </blockquote>
          ),

          // ── Horizontal rule ────────────────────────────────────────────────
          hr: () => (
            <hr
              style={{
                border: "none",
                borderTop: "1px solid #2a3942",
                margin: "12px 0",
              }}
            />
          ),

          // ── Tables (GFM) ───────────────────────────────────────────────────
          table: ({ children }) => (
            <div style={{ overflowX: "auto", margin: "8px 0" }}>
              <table
                style={{
                  borderCollapse: "collapse",
                  width: "100%",
                  fontSize: "12px",
                  color: textColor,
                }}
              >
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th
              style={{
                padding: "6px 12px",
                textAlign: "left",
                fontWeight: 600,
                color: "#e9edef",
                background: "#1f2c34",
                borderBottom: "1px solid #2a3942",
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              style={{
                padding: "5px 12px",
                borderBottom: "1px solid #1a2530",
              }}
            >
              {children}
            </td>
          ),

          // ── Links ──────────────────────────────────────────────────────────
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#00a884", textDecoration: "underline" }}
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
