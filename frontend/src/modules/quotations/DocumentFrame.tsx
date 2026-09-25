import { useEffect, useRef, useState } from "react";

const PAGE_PX = 794; // 210mm at 96dpi

/** Renders the server's quote HTML exactly as the PDF, scaled down to fit narrow screens. */
export default function DocumentFrame({ html }: { html: string }) {
  const box = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  const [scale, setScale] = useState(1);
  const [height, setHeight] = useState(1123);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setScale(Math.min(1, entry.contentRect.width / PAGE_PX)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const measure = () => {
    const doc = frame.current?.contentDocument;
    if (doc?.body) setHeight(doc.documentElement.scrollHeight);
  };

  return (
    <div ref={box} className="w-full">
      <div className="mx-auto overflow-hidden rounded-md shadow-[0_1px_3px_rgba(15,39,68,.12),0_8px_24px_rgba(15,39,68,.08)]"
        style={{ width: PAGE_PX * scale, height: height * scale }}>
        <iframe ref={frame} title="Quotation preview" srcDoc={html} sandbox="allow-same-origin" onLoad={measure}
          style={{ width: PAGE_PX, height, border: 0, transform: `scale(${scale})`, transformOrigin: "0 0",
            background: "white" }} />
      </div>
    </div>
  );
}
