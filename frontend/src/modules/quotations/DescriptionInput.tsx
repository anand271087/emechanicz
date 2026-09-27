import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { Textarea } from "../../components/ui";
import { api } from "../../lib/api";
import type { ItemDescription } from "../../lib/types";
import { matchParts, sameDescription } from "./descriptionMatch";

interface Props {
  value: string;
  onChange: (value: string) => void;
  label: string;
}

/** Description box with a dropdown of saved descriptions; free text is still allowed. */
export default function DescriptionInput({ value, onChange, label }: Props) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ItemDescription[]>([]);
  const [active, setActive] = useState(-1);
  const request = useRef(0);

  useEffect(() => {
    if (!open) return;
    const id = ++request.current;
    const t = setTimeout(() => {
      api<ItemDescription[]>(`/api/v1/item-descriptions?q=${encodeURIComponent(value)}&limit=5`)
        .then((rows) => {
          if (id !== request.current) return;
          setItems(rows.filter((r) => !sameDescription(r.description, value)));
          setActive(-1);
        })
        .catch(() => id === request.current && setItems([]));
    }, 150);
    return () => clearTimeout(t);
  }, [open, value]);

  const shown = open ? items : [];

  function choose(item: ItemDescription) {
    onChange(item.description);
    setOpen(false);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown" && shown.length) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i + 1) % shown.length);
    } else if (e.key === "ArrowUp" && shown.length) {
      e.preventDefault();
      setActive((i) => (i <= 0 ? shown.length - 1 : i - 1));
    } else if (e.key === "Enter" && active >= 0 && shown[active]) {
      e.preventDefault();
      choose(shown[active]);
    }
  }

  return (
    <div className="relative">
      <Textarea
        role="combobox" aria-label={label} aria-autocomplete="list" aria-expanded={shown.length > 0}
        aria-controls={listId} aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
        rows={1} value={value} placeholder="Type or pick an item description" autoComplete="off"
        onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        onKeyDown={onKeyDown}
        className="field-sizing-content min-h-10 resize-none"
      />
      {shown.length > 0 && (
        <ul id={listId} role="listbox" aria-label="Saved descriptions"
          className="absolute inset-x-0 top-full z-20 mt-1 overflow-hidden rounded-md border border-line bg-white
            shadow-lg">
          {shown.map((item, i) => (
            <li key={item.id} id={`${listId}-${i}`} role="option" aria-selected={i === active}
              onPointerDown={(e) => e.preventDefault()} onClick={() => choose(item)}
              onMouseEnter={() => setActive(i)}
              className={`cursor-pointer px-3 py-2.5 text-[15px] ${i === active ? "bg-fixture-soft text-navy" : ""}`}>
              {matchParts(item.description, value).map((p, k) =>
                p.match ? <strong key={k} className="font-semibold text-navy">{p.text}</strong> : <span key={k}>{p.text}</span>)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
