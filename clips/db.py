import hashlib
import sqlite3
import time

HISTORY_KINDS = ("text", "email", "image")


class Database:
    FILTERS = {"all": HISTORY_KINDS, "text": ("text", "email"),
               "image": ("image",), "pinned": HISTORY_KINDS}

    def __init__(self, path):
        self.c = sqlite3.connect(str(path), check_same_thread=False)
        self.c.row_factory = sqlite3.Row
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
                content TEXT, image BLOB, pinned INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL, digest TEXT, expires REAL)""")
        self.c.execute("CREATE INDEX IF NOT EXISTS ix_items_created ON items(created)")
        self.c.commit()
        self.purge_expired()

    # ----------------------------------------------------------- writing
    def add(self, kind, content=None, image=None, expires=None):
        now, digest = time.time(), None
        if kind != "password":
            raw = content.encode("utf-8") if content is not None else (image or b"")
            digest = hashlib.sha1(raw).hexdigest()
            row = self.c.execute("SELECT id FROM items WHERE digest=? AND kind=?", (digest, kind)).fetchone()
            if row:  # same item copied again: just bring it to the top
                self.c.execute("UPDATE items SET created=? WHERE id=?", (now, row["id"]))
                self.c.commit()
                return row["id"]
        cur = self.c.execute(
            "INSERT INTO items(kind,content,image,pinned,created,digest,expires) VALUES(?,?,?,0,?,?,?)",
            (kind, content, image, now, digest, expires))
        self.c.commit()
        return cur.lastrowid

    def touch(self, item_id):
        self.c.execute("UPDATE items SET created=? WHERE id=?", (time.time(), item_id))
        self.c.commit()

    def set_pinned(self, item_id, flag):
        self.c.execute("UPDATE items SET pinned=? WHERE id=?", (1 if flag else 0, item_id))
        self.c.commit()

    def delete(self, item_id):
        self.c.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.c.commit()

    def clear(self, keep_pinned=True):
        sql = "DELETE FROM items WHERE kind='password' OR " + ("pinned=0" if keep_pinned else "1=1")
        self.c.execute(sql)
        self.c.commit()

    def trim(self, max_items):
        self.c.execute(
            """DELETE FROM items WHERE id IN (
                 SELECT id FROM items WHERE pinned=0 AND kind IN ('text','email','image')
                 ORDER BY created DESC LIMIT -1 OFFSET ?)""", (max(10, int(max_items)),))
        self.c.commit()

    def purge_expired(self):
        cur = self.c.execute("DELETE FROM items WHERE kind='password' AND expires IS NOT NULL AND expires<?",
                             (time.time(),))
        self.c.commit()
        return cur.rowcount

    # ----------------------------------------------------------- reading
    def get(self, item_id):
        return self.c.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()

    def list(self, flt="all", query="", limit=200):
        kinds = self.FILTERS[flt]
        sql = "SELECT * FROM items WHERE kind IN (%s)" % ",".join("?" * len(kinds))
        args = list(kinds)
        if flt == "pinned":
            sql += " AND pinned=1"
        if query:
            esc = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            sql += " AND kind!='image' AND content LIKE ? ESCAPE '\\'"
            args.append(f"%{esc}%")
        sql += " ORDER BY pinned DESC, created DESC LIMIT ?"
        args.append(limit)
        return self.c.execute(sql, args).fetchall()

    def by_kind(self, kind, limit=20):
        return self.c.execute("SELECT * FROM items WHERE kind=? ORDER BY created DESC LIMIT ?",
                              (kind, limit)).fetchall()

    def passwords_rows(self):
        return self.by_kind("password", 50)
