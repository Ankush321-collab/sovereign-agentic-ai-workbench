import React, { useState } from 'react';

/**
 * High-performance, zero-dependency Markdown Renderer for VAJRA Sovereign AI Workbench
 * Handles headers, code blocks (with copy), lists, tables, bold/italics, quotes, and badges.
 */

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block-container">
      <div className="code-block-header">
        <span className="code-block-lang">{language || 'code'}</span>
        <button className="code-block-copy" onClick={handleCopy}>
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <pre className="code-block-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function parseInlineFormatting(text) {
  if (!text) return text;

  // Split by inline code first
  const parts = [];
  const codeRegex = /`([^`]+)`/g;
  let lastIndex = 0;
  let match;

  while ((match = codeRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(renderTextWithFormatting(text.substring(lastIndex, match.index)));
    }
    parts.push(
      <code key={`code-${match.index}`} className="inline-code">
        {match[1]}
      </code>
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(renderTextWithFormatting(text.substring(lastIndex)));
  }

  return parts.length > 0 ? parts : text;
}

function renderTextWithFormatting(rawText) {
  if (!rawText) return '';

  // Replace bold & italics with simple tokens
  // E.g. **bold** or *italic*
  const tokens = [];
  let cur = '';
  let i = 0;

  while (i < rawText.length) {
    if (rawText.substr(i, 2) === '**') {
      const end = rawText.indexOf('**', i + 2);
      if (end !== -1) {
        tokens.push(cur);
        cur = '';
        tokens.push(<strong key={`b-${i}`}>{rawText.substring(i + 2, end)}</strong>);
        i = end + 2;
        continue;
      }
    }
    if (rawText[i] === '*' && rawText[i + 1] !== '*') {
      const end = rawText.indexOf('*', i + 1);
      if (end !== -1) {
        tokens.push(cur);
        cur = '';
        tokens.push(<em key={`em-${i}`}>{rawText.substring(i + 1, end)}</em>);
        i = end + 1;
        continue;
      }
    }
    cur += rawText[i];
    i++;
  }
  if (cur) tokens.push(cur);

  return tokens;
}

export default function MarkdownRenderer({ content = '' }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let inCodeBlock = false;
  let codeLang = '';
  let codeBuffer = [];
  let tableBuffer = [];

  const flushTable = (key) => {
    if (tableBuffer.length === 0) return;
    const rows = tableBuffer.map(r => 
      r.split('|')
       .map(c => c.trim())
       .filter((c, idx, arr) => idx !== 0 && idx !== arr.length - 1)
    ).filter(r => r.length > 0 && !r.every(cell => cell.match(/^[-:]+$/)));

    if (rows.length > 0) {
      const headerRow = rows[0];
      const dataRows = rows.slice(1);
      elements.push(
        <div key={`table-${key}`} className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                {headerRow.map((th, thIdx) => (
                  <th key={thIdx}>{parseInlineFormatting(th)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataRows.map((tr, trIdx) => (
                <tr key={trIdx}>
                  {tr.map((td, tdIdx) => (
                    <td key={tdIdx}>{parseInlineFormatting(td)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    tableBuffer = [];
  };

  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];

    // Handle Code Blocks
    if (line.trim().startsWith('```')) {
      if (!inCodeBlock) {
        flushTable(idx);
        inCodeBlock = true;
        codeLang = line.trim().replace('```', '').trim();
        codeBuffer = [];
      } else {
        inCodeBlock = false;
        elements.push(
          <CodeBlock
            key={`codeblock-${idx}`}
            language={codeLang}
            code={codeBuffer.join('\n')}
          />
        );
        codeBuffer = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    // Handle Tables
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      tableBuffer.push(line.trim());
      continue;
    } else if (tableBuffer.length > 0) {
      flushTable(idx);
    }

    // Handle Headers
    if (line.startsWith('#### ')) {
      elements.push(<h4 key={idx} className="md-h4">{parseInlineFormatting(line.replace('#### ', ''))}</h4>);
      continue;
    }
    if (line.startsWith('### ')) {
      elements.push(<h3 key={idx} className="md-h3">{parseInlineFormatting(line.replace('### ', ''))}</h3>);
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h2 key={idx} className="md-h2">{parseInlineFormatting(line.replace('## ', ''))}</h2>);
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(<h1 key={idx} className="md-h1">{parseInlineFormatting(line.replace('# ', ''))}</h1>);
      continue;
    }

    // Handle Horizontal Rule
    if (line.trim() === '---' || line.trim() === '***') {
      elements.push(<hr key={idx} className="md-hr" />);
      continue;
    }

    // Handle Blockquote / Callouts
    if (line.startsWith('> ')) {
      const quoteText = line.replace('> ', '');
      elements.push(
        <blockquote key={idx} className="md-blockquote">
          {parseInlineFormatting(quoteText)}
        </blockquote>
      );
      continue;
    }

    // Handle Lists
    if (line.trim().match(/^[-*]\s+/)) {
      const itemText = line.trim().replace(/^[-*]\s+/, '');
      elements.push(
        <li key={idx} className="md-list-item">
          {parseInlineFormatting(itemText)}
        </li>
      );
      continue;
    }

    // Handle Numbered Lists
    if (line.trim().match(/^\d+\.\s+/)) {
      const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
      elements.push(
        <li key={idx} className="md-list-item numbered" value={numMatch[1]}>
          <span className="md-list-num">{numMatch[1]}.</span> {parseInlineFormatting(numMatch[2])}
        </li>
      );
      continue;
    }

    // Empty lines
    if (!line.trim()) {
      elements.push(<div key={idx} className="md-spacer" />);
      continue;
    }

    // Regular Paragraph
    elements.push(
      <p key={idx} className="md-p">
        {parseInlineFormatting(line)}
      </p>
    );
  }

  if (tableBuffer.length > 0) {
    flushTable('end');
  }

  return <div className="markdown-body">{elements}</div>;
}
