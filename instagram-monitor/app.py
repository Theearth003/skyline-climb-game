import os, json, re, sqlite3
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, send_from_directory

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = os.getenv("DATABASE_URL", "")
DB_PATH = os.path.join(APP_DIR, "monitor.db")
TARGET = "amar.achi8774"
TARGET_URL = f"https://www.instagram.com/{TARGET}/"
BASELINE_REPOSTS = 2

app = Flask(__name__, static_folder="public", static_url_path="")

def now():
    return datetime.now(timezone.utc).isoformat()

def db():
    if DB_URL:
        import psycopg2
        return psycopg2.connect(DB_URL)
    return sqlite3.connect(DB_PATH)

def init_db():
    c=db(); cur=c.cursor()
    if DB_URL:
        cur.execute("""CREATE TABLE IF NOT EXISTS snapshots(
          id SERIAL PRIMARY KEY, scanned_at TEXT NOT NULL, username TEXT NOT NULL,
          bio TEXT, followers BIGINT, following BIGINT, posts BIGINT, profile_pic TEXT,
          payload TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS events(
          id SERIAL PRIMARY KEY, created_at TEXT NOT NULL, kind TEXT NOT NULL,
          title TEXT NOT NULL, detail TEXT, source_url TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS posts(
          id SERIAL PRIMARY KEY, shortcode TEXT UNIQUE NOT NULL, kind TEXT, url TEXT,
          first_detected TEXT NOT NULL, original_time TEXT, title TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scans(
          id SERIAL PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
          status TEXT NOT NULL, message TEXT)""")
    else:
        cur.executescript("""CREATE TABLE IF NOT EXISTS snapshots(
          id INTEGER PRIMARY KEY AUTOINCREMENT, scanned_at TEXT NOT NULL, username TEXT NOT NULL,
          bio TEXT, followers INTEGER, following INTEGER, posts INTEGER, profile_pic TEXT,
          payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, kind TEXT NOT NULL,
          title TEXT NOT NULL, detail TEXT, source_url TEXT);
          CREATE TABLE IF NOT EXISTS posts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, shortcode TEXT UNIQUE NOT NULL, kind TEXT, url TEXT,
          first_detected TEXT NOT NULL, original_time TEXT, title TEXT);
          CREATE TABLE IF NOT EXISTS scans(
          id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT,
          status TEXT NOT NULL, message TEXT);""")
    c.commit(); c.close()

def parse_count(text):
    if not text: return None
    m=re.search(r'([\d,.]+)\s*(K|M|B)?', text, re.I)
    if not m: return None
    n=float(m.group(1).replace(',',''))
    mult={'k':1000,'m':1000000,'b':1000000000}.get((m.group(2) or '').lower(),1)
    return int(n*mult)

def fetch_profile():
    headers={"User-Agent":"Mozilla/5.0 (compatible; PublicAccountMonitor/1.0)"}
    r=requests.get(TARGET_URL,headers=headers,timeout=20,allow_redirects=True)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    title=(soup.title.string if soup.title else "") or ""
    desc=""
    m=soup.find("meta",attrs={"name":"description"})
    if m: desc=m.get("content","")
    im=soup.find("meta",property="og:image")
    ogimg=im.get("content") if im else None
    followers=following=posts=None
    fm=re.search(r'([\d,.]+(?:[KMB])?)\s+Followers',desc,re.I)
    pm=re.search(r'([\d,.]+(?:[KMB])?)\s+Posts',desc,re.I)
    if fm: followers=parse_count(fm.group(1))
    if pm: posts=parse_count(pm.group(1))
    bio=desc[:500]
    links=set()
    for a in soup.find_all("a",href=True):
        href=a["href"]
        if re.search(r'^/(p|reel|tv)/[^/]+/?$',href):
            links.add(urljoin(TARGET_URL,href))
    return {"username":TARGET,"url":TARGET_URL,"bio":bio,"followers":followers,
      "following":following,"posts":posts,"profile_pic":ogimg,
      "discovered_posts":sorted(links),"title":title,"fetched_at":now(),
      "source":"public Instagram profile page"}

def last_snapshot(c):
    cur=c.cursor()
    q="SELECT scanned_at,bio,followers,following,posts,profile_pic,payload FROM snapshots WHERE username=%s ORDER BY id DESC LIMIT 1" if DB_URL else "SELECT scanned_at,bio,followers,following,posts,profile_pic,payload FROM snapshots WHERE username=? ORDER BY id DESC LIMIT 1"
    cur.execute(q,(TARGET,))
    return cur.fetchone()

def insert_event(cur,kind,title,detail,url):
    q="INSERT INTO events(created_at,kind,title,detail,source_url) VALUES(%s,%s,%s,%s,%s)" if DB_URL else "INSERT INTO events(created_at,kind,title,detail,source_url) VALUES(?,?,?,?,?)"
    cur.execute(q,(now(),kind,title,detail,url))

def scan():
    c=db(); cur=c.cursor()
    q="INSERT INTO scans(started_at,status) VALUES(%s,%s) RETURNING id" if DB_URL else "INSERT INTO scans(started_at,status) VALUES(?,?)"
    cur.execute(q,(now(),"running")); sid=cur.fetchone()[0]; c.commit()
    try:
        data=fetch_profile()
        prev=last_snapshot(c)
        if prev:
            _,pb,pf,pfo,pp,pi,_=prev
            for label,a,b in [("followers",pf,data["followers"]),("following",pfo,data["following"]),("posts",pp,data["posts"])]:
                if a is not None and b is not None and a!=b:
                    insert_event(cur,"stats",f"{label.title()} changed",f"{a:,} → {b:,}",TARGET_URL)
            if pb != data["bio"] and data["bio"]:
                insert_event(cur,"profile","Bio changed","Public bio content changed.",TARGET_URL)
            if pi != data["profile_pic"] and data["profile_pic"]:
                insert_event(cur,"profile","Profile image changed","A different public profile image was detected.",TARGET_URL)
        q="INSERT INTO snapshots(scanned_at,username,bio,followers,following,posts,profile_pic,payload) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)" if DB_URL else "INSERT INTO snapshots(scanned_at,username,bio,followers,following,posts,profile_pic,payload) VALUES(?,?,?,?,?,?,?,?)"
        cur.execute(q,(now(),TARGET,data["bio"],data["followers"],data["following"],data["posts"],data["profile_pic"],json.dumps(data)))
        for url in data["discovered_posts"]:
            shortcode=url.rstrip("/").split("/")[-1]
            cur.execute("SELECT 1 FROM posts WHERE shortcode=%s" if DB_URL else "SELECT 1 FROM posts WHERE shortcode=?",(shortcode,))
            if not cur.fetchone():
                kind="reel" if "/reel/" in url else "post"
                q="INSERT INTO posts(shortcode,kind,url,first_detected,title) VALUES(%s,%s,%s,%s,%s)" if DB_URL else "INSERT INTO posts(shortcode,kind,url,first_detected,title) VALUES(?,?,?,?,?)"
                cur.execute(q,(shortcode,kind,url,now(),f"New public {kind} detected"))
                insert_event(cur,"content",f"New {kind.title()} detected","Original publication timestamp was not exposed; first-detected time is recorded instead.",url)
        q="UPDATE scans SET finished_at=%s,status=%s,message=%s WHERE id=%s" if DB_URL else "UPDATE scans SET finished_at=?,status=?,message=? WHERE id=?"
        cur.execute(q,(now(),"success","Public profile scan completed.",sid))
        c.commit(); c.close(); return data
    except Exception as e:
        q="UPDATE scans SET finished_at=%s,status=%s,message=%s WHERE id=%s" if DB_URL else "UPDATE scans SET finished_at=?,status=?,message=? WHERE id=?"
        cur.execute(q,(now(),"error",str(e),sid)); c.commit(); c.close(); raise

@app.route("/")
def home(): return send_from_directory("public","index.html")

@app.get("/health")
def health(): return jsonify({"ok":True,"time":now(),"target":TARGET})

@app.get("/api/overview")
def overview():
    c=db(); cur=c.cursor()
    q="SELECT scanned_at,bio,followers,following,posts,profile_pic,payload FROM snapshots WHERE username=%s ORDER BY id DESC LIMIT 1" if DB_URL else "SELECT scanned_at,bio,followers,following,posts,profile_pic,payload FROM snapshots WHERE username=? ORDER BY id DESC LIMIT 1"
    cur.execute(q,(TARGET,)); row=cur.fetchone()
    cur.execute("SELECT created_at,kind,title,detail,source_url FROM events ORDER BY id DESC LIMIT 100")
    events=cur.fetchall()
    cur.execute("SELECT shortcode,kind,url,first_detected,original_time,title FROM posts ORDER BY id DESC LIMIT 100")
    posts=cur.fetchall()
    cur.execute("SELECT started_at,finished_at,status,message FROM scans ORDER BY id DESC LIMIT 20")
    scans=cur.fetchall(); c.close()
    snap=None
    if row: snap={"scanned_at":row[0],"username":TARGET,"bio":row[1],"followers":row[2],"following":row[3],"posts":row[4],"profile_pic":row[5]}
    return jsonify({"target":TARGET,"target_url":TARGET_URL,"baseline_reposts":BASELINE_REPOSTS,
      "snapshot":snap,
      "events":[dict(created_at=x[0],kind=x[1],title=x[2],detail=x[3],source_url=x[4]) for x in events],
      "posts":[dict(shortcode=x[0],kind=x[1],url=x[2],first_detected=x[3],original_time=x[4],title=x[5]) for x in posts],
      "scans":[dict(started_at=x[0],finished_at=x[1],status=x[2],message=x[3]) for x in scans]})

@app.post("/api/scan")
def manual_scan():
    try: return jsonify({"ok":True,"data":scan()})
    except Exception as e: return jsonify({"ok":False,"error":str(e)}),502

init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
