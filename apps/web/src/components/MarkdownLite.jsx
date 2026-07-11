import React from 'react';

// Lightweight, dependency-free renderer for the LLM's markdown-ish analysis text:
// headers, numbered/bulleted lists, bold spans, and fenced ```code``` blocks
// rendered as terminal-style panels.

function renderInline(text, keyPrefix) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={`${keyPrefix}-b-${i}`} className="text-neon-cyan font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <React.Fragment key={`${keyPrefix}-t-${i}`}>{part}</React.Fragment>;
  });
}

function CodeBlock({ code, lang }) {
  return (
    <div className="my-4 rounded-lg overflow-hidden border border-neon-violet/30 shadow-neon-sm">
      <div className="flex items-center gap-1.5 bg-[#1a1a28] px-3 py-2 border-b border-neon-violet/20">
        <span className="w-2.5 h-2.5 rounded-full bg-neon-pink/70" />
        <span className="w-2.5 h-2.5 rounded-full bg-neon-cyan/70" />
        <span className="w-2.5 h-2.5 rounded-full bg-neon-green/70" />
        <span className="ml-2 text-xs text-slate-400 font-mono-code uppercase tracking-wider">
          {lang || 'dockerfile'}
        </span>
      </div>
      <pre className="bg-[#0d0d16] text-slate-200 text-sm font-mono-code p-4 overflow-x-auto whitespace-pre-wrap leading-relaxed">
        {code}
      </pre>
    </div>
  );
}

const MarkdownLite = ({ text }) => {
  if (!text) return null;

  const segments = text.split(/```/g);

  return (
    <div className="text-slate-200 leading-relaxed">
      {segments.map((segment, segIdx) => {
        const isCode = segIdx % 2 === 1;

        if (isCode) {
          const lines = segment.split('\n');
          const maybeLang = lines[0].trim();
          const hasLang = /^[a-zA-Z0-9_-]{1,20}$/.test(maybeLang) && lines.length > 1;
          const lang = hasLang ? maybeLang : null;
          const code = (hasLang ? lines.slice(1) : lines).join('\n').replace(/^\n+|\n+$/g, '');
          return <CodeBlock key={segIdx} code={code} lang={lang} />;
        }

        const lines = segment.split('\n');
        return (
          <React.Fragment key={segIdx}>
            {lines.map((line, i) => {
              const key = `${segIdx}-${i}`;
              const trimmed = line.trim();

              if (!trimmed) return <div key={key} className="h-2" />;

              if (trimmed.startsWith('### ')) {
                return (
                  <h4 key={key} className="font-display text-base font-semibold text-neon-cyan mt-4 mb-1">
                    {renderInline(trimmed.slice(4), key)}
                  </h4>
                );
              }
              if (trimmed.startsWith('## ')) {
                return (
                  <h3 key={key} className="font-display text-lg font-bold gradient-text mt-5 mb-2">
                    {renderInline(trimmed.slice(3), key)}
                  </h3>
                );
              }
              if (trimmed.startsWith('# ')) {
                return (
                  <h2 key={key} className="font-display text-xl font-bold gradient-text mt-2 mb-3">
                    {renderInline(trimmed.slice(2), key)}
                  </h2>
                );
              }
              if (/^[-*]\s+/.test(trimmed)) {
                return (
                  <div key={key} className="flex gap-2 pl-2 my-1">
                    <span className="text-neon-violet mt-1">▹</span>
                    <span>{renderInline(trimmed.replace(/^[-*]\s+/, ''), key)}</span>
                  </div>
                );
              }
              if (/^\d+\.\s+/.test(trimmed)) {
                const match = trimmed.match(/^(\d+)\.\s+(.*)/);
                return (
                  <div key={key} className="flex gap-2 pl-2 my-1">
                    <span className="text-neon-cyan font-mono-code font-semibold">{match[1]}.</span>
                    <span>{renderInline(match[2], key)}</span>
                  </div>
                );
              }
              return (
                <p key={key} className="my-1">
                  {renderInline(line, key)}
                </p>
              );
            })}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default MarkdownLite;
