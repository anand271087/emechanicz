-- Saved item descriptions start with a capital letter; the rest of the text is kept as typed.
update item_descriptions
set description = upper(left(btrim(description), 1)) || substr(btrim(description), 2)
where description <> upper(left(btrim(description), 1)) || substr(btrim(description), 2);
