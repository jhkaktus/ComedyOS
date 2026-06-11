#!/usr/bin/env python3
"""
comedyOS Horror RPG
"You are logged in. You don't remember logging in."

Ein Terminal-Horror-RPG mit schwarzem Humor, Linuxkenntnis und
einer Kernel-Persoenlichkeit, die dich nicht mag.
"""

import random
import time
import sys
import os
import textwrap
import shutil

# ──────────────────────────────────────────────────────────────────────────────
# TERMINAL HELPERS
# ──────────────────────────────────────────────────────────────────────────────

TERM_WIDTH = min(shutil.get_terminal_size().columns, 80)

def slow_print(text: str, delay: float = 0.03, prefix: str = ""):
    """Tippt Text langsam in den Terminal."""
    full = prefix + text
    for char in full:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def glitch_print(text: str):
    """Text mit kurzen Glitch-Artefakten."""
    glitch_chars = list("▓░▒█▄▀")
    result = []
    for ch in text:
        if random.random() < 0.08:
            result.append(random.choice(glitch_chars))
        else:
            result.append(ch)
    slow_print("".join(result), delay=0.02)

def horror_print(text: str):
    """Typischer Kernel-Horror-Text mit kurzem Freeze am Ende."""
    slow_print(text, delay=0.04)
    time.sleep(0.3)

def box_print(text: str, border: str = "─"):
    """Druckt Text in einer einfachen Box."""
    lines = text.split("\n")
    width = max(len(l) for l in lines) + 4
    width = min(width, TERM_WIDTH)
    print("┌" + border * (width - 2) + "┐")
    for line in lines:
        padded = f"│  {line:<{width-4}}  │"
        print(padded[:width] + "│")
    print("└" + border * (width - 2) + "┘")

def hr(char: str = "─"):
    print(char * TERM_WIDTH)

def clear_line():
    print()

# ──────────────────────────────────────────────────────────────────────────────
# SPIELER-DATEN
# ──────────────────────────────────────────────────────────────────────────────

class Player:
    def __init__(self):
        self.sanity: int = 60
        self.permissions: int = 1      # 0=none, 1=user, 2=sudo, 3=root, 4=god
        self.karma: int = 0
        self.alive: bool = True
        self.inventory: list = []
        self.visited: set = set()
        self.flags: dict = {}          # Story-Flags fuer Quest-Logik
        self.regret_daemon_running: bool = False
        self.found_passwd: bool = False
        self.kernel_trust: int = 0     # -5 bis +5
        self.turns: int = 0
        self.achievements: list = []

    def lose_sanity(self, amount: int, reason: str = ""):
        self.sanity -= amount
        if reason:
            horror_print(f"[psyche] {reason}")
        if self.sanity <= 0:
            self.sanity = 0

    def gain_sanity(self, amount: int):
        self.sanity = min(100, self.sanity + amount)

    def grant_permission(self, level: int):
        old = self.permissions
        self.permissions = max(self.permissions, level)
        if self.permissions > old:
            perm_names = {1: "user", 2: "sudo", 3: "root", 4: "kernel-god"}
            slow_print(f"[auth] permissions elevated to: {perm_names.get(self.permissions, '???')}")

    def add_item(self, item: str):
        if item not in self.inventory:
            self.inventory.append(item)
            slow_print(f"[inventory] '{item}' hinzugefuegt.")

    def has_item(self, item: str) -> bool:
        return item in self.inventory

    def remove_item(self, item: str):
        if item in self.inventory:
            self.inventory.remove(item)

    def award_achievement(self, title: str, desc: str):
        if title not in self.achievements:
            self.achievements.append(title)
            print()
            box_print(f"ACHIEVEMENT UNLOCKED\n{title}\n{desc}", border="═")
            print()

    def status_bar(self):
        perm_labels = {0: "KEINE", 1: "user", 2: "sudo", 3: "root", 4: "GOD"}
        sanity_bar_len = 20
        filled = int((self.sanity / 100) * sanity_bar_len)
        if self.sanity > 40:
            bar = "█" * filled + "░" * (sanity_bar_len - filled)
        elif self.sanity > 20:
            bar = "▓" * filled + "░" * (sanity_bar_len - filled)
        else:
            bar = "▒" * filled + "░" * (sanity_bar_len - filled)
        hr()
        print(
            f" SANITY [{bar}] {self.sanity:>3}  |"
            f"  PERMS: {perm_labels.get(self.permissions,'???'):<10}  |"
            f"  KARMA: {self.karma:+d}  |"
            f"  TURN: {self.turns}"
        )
        if self.inventory:
            print(f" INVENTORY: {', '.join(self.inventory)}")
        hr()


# ──────────────────────────────────────────────────────────────────────────────
# KERNEL - DIE STIMME DES SYSTEMS
# ──────────────────────────────────────────────────────────────────────────────

KERNEL_WHISPERS = [
    ("kernel", "ich hab gesehen was du eingetippt hast.", -5),
    ("kernel", "ich hab es nochmal gesehen.", -3),
    ("kernel", "du tippst wie jemand der nicht schlaeft.", -4),
    ("/dev/null", "hier liegt etwas das du vergessen wolltest.", -2),
    ("/dev/null", "ich erinnere mich an deinen letzten rm-Befehl.", -3),
    ("init", "regret-daemon laeuft im Hintergrund.", -2),
    ("init", "starte Prozess 'existential-cron'... done.", -3),
    ("syslog", "CRITICAL: user hat zu viel nachgedacht.", -4),
    ("dmesg", "I/O error on soul: unrecoverable.", -5),
    ("cron", "0 3 * * * /bin/erinnere_dich_an_alles.sh", -3),
    ("/proc/self/status", "Name: user\nState: D (uninterruptible sleep)", -4),
    ("entropy", "dein Passwort ist 'password123', oder?", -6),
    ("swap", "ich hab deine Gedanken ausgelagert weil kein RAM mehr da war.", -4),
    ("load average", "15.34 15.34 15.34", -5),
    ("oom-killer", "ich hab ueberlegt.", -3),
    ("udev", "neues Geraet erkannt: fear", -2),
    ("acpi", "thermal: temperature of regret exceeds threshold", -4),
    ("ssh", "verbindungsversuch von unknown@unknown.void", -5),
    ("fsck", "superblock korrumpiert. wie du.", -4),
    ("systemd", "unit 'existenz.service' haengt seit 27 Jahren.", -5),
]

KERNEL_GOOD_WHISPERS = [
    ("kernel", "...heute nichts.", 0),
    ("/dev/urandom", "sieht eigentlich ganz ok aus hier.", 2),
    ("dmesg", "alles normal. fast.", 0),
    ("kernel", "ich pass kurz weg.", 3),
]

def kernel_whisper(player: Player):
    """Zufaelliger Kernel-Whisper, manchmal gut, meistens schlimm."""
    if random.random() < 0.15:
        src, msg, dmg = random.choice(KERNEL_GOOD_WHISPERS)
        slow_print(f"[{src}] {msg}")
        if dmg > 0:
            player.gain_sanity(dmg)
        return

    src, msg, dmg = random.choice(KERNEL_WHISPERS)
    horror_print(f"[{src}] {msg}")
    player.lose_sanity(abs(dmg))

    # Regret-Daemon verstaerkt zufaelligen Schaden
    if player.regret_daemon_running and random.random() < 0.4:
        slow_print("[regret-daemon] ...und dann war da noch das eine Ding.", delay=0.05)
        player.lose_sanity(2)


# ──────────────────────────────────────────────────────────────────────────────
# RAEUME / LOCATIONS
# ──────────────────────────────────────────────────────────────────────────────

ROOM_DESCRIPTIONS = {
    "home": [
        "Du stehst in /home. Es riecht nach alten Bash-Historien und schlechten Entscheidungen.",
        "Dein Home-Verzeichnis. Merkwuerdig aufgeraumt. Als haette jemand deine Dotfiles gelesen.",
        "/home/user. Der Punkt vor dem Ordnernamen fuehlt sich heute sehr persoenlich an.",
    ],
    "root": [
        "/root. Das Verzeichnis von Root. Du hast hier nichts zu suchen. Und doch bist du hier.",
        "Der Root-Ordner liegt im Halbdunkel. Auf dem Boden: eine leere .bash_history.",
        "/root riecht nach Macht und nach jemandem, der zu oft sudo benutzt hat.",
    ],
    "void": [
        "/void. Hier macht ls keinen Sinn mehr. Hier macht nichts mehr Sinn.",
        "Die Leere. Nicht leer wie ein frisches Verzeichnis. Leer wie nach rm -rf.",
        "/void fluestert. Du weisst nicht was. Das macht es schlimmer.",
    ],
    "proc": [
        "/proc: alle laufenden Prozesse. Einer davon bist du. Nummer 1 hat keine PID.",
        "/proc/self zeigt deinen eigenen Speicher. Du willst das nicht lesen.",
        "Hier laufen Tausende Prozesse. Einer heisst 'du_weisst_schon'.",
    ],
    "dev": [
        "/dev: Geraetedateien. /dev/null schluckt alles. /dev/random weiss zu viel.",
        "Terminal-Geraete, Laufwerke, Abstraktionen. /dev/fear ist neu seit heute.",
        "/dev/sda dreht sich. /dev/sdb dreht sich. /dev/soul dreht sich nicht mehr.",
    ],
    "etc": [
        "/etc: die Konfigurationsdateien des Systems. Und von dir. Wer hat das eingestellt?",
        "Hier liegt passwd. Hier liegt shadow. Hier liegt dein Geheimnis.",
        "/etc/hosts listet IPs auf. Eine davon ist deine. Du warst nie sicher wovor.",
    ],
    "tmp": [
        "/tmp: temporaere Dateien. Wird beim Neustart geloescht. Wann war der letzte Neustart?",
        "Im /tmp liegen Dinge, die niemand beansprucht. Manche sehen aus wie Erinnerungen.",
        "/tmp riecht wie ein Wartezimmer ohne Ausgang.",
    ],
    "var": [
        "/var/log: tausende Zeilen Systemlogs. Du hast Angst zu lesen.",
        "/var/spool/mail: eine E-Mail von dir selbst, Datum: tomorrow.",
        "/var: veraenderliche Daten. Alles hier aendert sich. Du auch.",
    ],
    "lost+found": [
        "/lost+found: Fragmente nach Dateisystemfehlern. Hier landen verlorene Inode-Reste.",
        "lost+found. Manche Dateien hier haben keine Namen mehr. Nur noch Nummern.",
        "Du findest: den Rest einer Datei. Sie haette alles erklaert.",
    ],
    "kernel_room": [
        "Der Kernel-Raum. Kein normaler Prozess darf hier sein. Du bist kein normaler Prozess.",
        "Ring 0. Das Herz. Es pocht im Sekundenrhythmus deines Herzens, genau.",
        "Hier laeuft alles. Hier entscheidet sich alles. Der Kernel schaut dich an.",
    ],
}

ROOM_CONNECTIONS = {
    "home":        ["root", "void", "proc", "dev", "tmp"],
    "root":        ["home", "etc", "kernel_room"],
    "void":        ["home", "lost+found"],
    "proc":        ["home", "dev"],
    "dev":         ["home", "proc", "tmp"],
    "etc":         ["root", "var"],
    "tmp":         ["home", "dev", "var"],
    "var":         ["etc", "tmp", "lost+found"],
    "lost+found":  ["void", "var"],
    "kernel_room": ["root"],
}

ROOM_SANITY_DRAIN = {
    "home": 0,
    "root": 1,
    "void": 3,
    "proc": 2,
    "dev": 1,
    "etc": 1,
    "tmp": 0,
    "var": 1,
    "lost+found": 2,
    "kernel_room": 5,
}

# ──────────────────────────────────────────────────────────────────────────────
# ITEMS PRO RAUM
# ──────────────────────────────────────────────────────────────────────────────

ROOM_ITEMS = {
    "home": ["dotfile", "bash_history", "todo_never.txt"],
    "root": ["root_diary", "forgotten_key"],
    "void": ["dark_inode"],
    "proc": ["pid_1_note", "meminfo_fragment"],
    "dev": ["null_bottle", "random_oracle"],
    "etc": ["passwd_fragment", "shadow_whisper"],
    "tmp": ["temp_thought", "unnamed_binary"],
    "var": ["old_log", "mail_from_tomorrow"],
    "lost+found": ["nameless_file", "broken_symlink"],
    "kernel_room": ["kernel_source", "the_interrupt"],
}

ITEM_DESCRIPTIONS = {
    "dotfile":          ".bashrc mit 300 Zeilen Aliases. Einer lautet: alias reality='ls /dev/null'.",
    "bash_history":     "Die letzten 2000 Befehle. Die letzten 3 sind nicht von dir.",
    "todo_never.txt":   "Zeile 1: 'mal aufraumen.' Datei erstellt: 2003-11-04. Nicht veraendert seitdem.",
    "root_diary":       "Tagebuch von root. Erste Zeile: 'Heute hat user wieder sudo falsch benutzt.'",
    "forgotten_key":    "Ein SSH-Key ohne zugehoerigen Host. Der Fingerprint ist dein Geburtsdatum.",
    "dark_inode":       "Ein Inode ohne Dateiname. Ohne Inhalt. Aber mit Eigentuemer: du.",
    "pid_1_note":       "Notiz von PID 1: 'ich warte. ich warte immer. wann kommst du?'",
    "meminfo_fragment": "MemTotal: 8192 MB\nMemFree: 3 MB\nMemForget: ueberschrieben",
    "null_bottle":      "Eine Flasche gefuellt mit /dev/null. Leer. Aber schwer.",
    "random_oracle":    "Einen Zettel: 'deine naechste Eingabe ist bereits bekannt.'",
    "passwd_fragment":  "user:x:1000:1000:you,,,:/home/user:/bin/bash — das 'you,,,' macht dich nervoes.",
    "shadow_whisper":   "Der Hash deines Passworts. Er fluestert.",
    "temp_thought":     "Ein Gedanke der eigentlich schon geloescht sein sollte.",
    "unnamed_binary":   "Executable ohne Namen. Chmod +x. Laeuft es schon?",
    "old_log":          "Syslog von vor 3 Jahren. Du hast das System damals anders benutzt. Schlimmer.",
    "mail_from_tomorrow":"Von: du@morgen.void / An: du@heute.void / Betreff: tu es nicht.",
    "nameless_file":    "Kein Dateiname. Kein Typ. Nur Inhalt: 'du hast mich schon gelesen.'",
    "broken_symlink":   "Symlink -> /hope. /hope existiert nicht.",
    "kernel_source":    "Quellcode des Kernels. Eine Zeile ist kommentiert: // this is where you are",
    "the_interrupt":    "Ein Hardware-Interrupt ohne Quelle. Er fragt: bist du noch da?",
}

# ──────────────────────────────────────────────────────────────────────────────
# EVENTS PRO RAUM
# ──────────────────────────────────────────────────────────────────────────────

def event_void_encounter(player: Player):
    horror_print("[void] etwas bewegt sich in der Leere.")
    time.sleep(0.5)
    horror_print("[void] es bewegt sich auf dich zu.")
    time.sleep(0.4)
    horror_print("[void] es bleibt stehen.")
    time.sleep(0.6)
    horror_print("[void] 'du siehst aus wie jemand der rm -rf / gemacht hat und dann ctrl+c gedrueckt hat.'")
    player.lose_sanity(8, "")
    player.karma -= 2

def event_proc_mirror(player: Player):
    horror_print("[proc] /proc/self/maps geladen.")
    time.sleep(0.3)
    slow_print("7f3b2a000000-7f3b2c000000 r-xp  /lib/x86_64-linux-gnu/libc-2.31.so")
    slow_print("7f3b2c001000-7f3b2c002000 r-xp  /home/user/you.so")
    time.sleep(0.4)
    horror_print("[proc] you.so wurde von einem Prozess gemappt den du nicht gestartet hast.")
    player.lose_sanity(7)

def event_etc_passwd_unlock(player: Player):
    if not player.found_passwd:
        slow_print("[etc] /etc/passwd oeffnet sich.")
        time.sleep(0.2)
        slow_print("root:x:0:0:root:/root:/bin/bash")
        slow_print("daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin")
        slow_print("user:x:1000:1000:you,,,:/home/user:/bin/bash")
        slow_print("nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin")
        time.sleep(0.3)
        horror_print("unknown:x:0:0::/dev/null:/bin/sh")
        horror_print("[etc] der letzte Eintrag war nicht gestern.")
        player.found_passwd = True
        player.lose_sanity(6)
        player.add_item("passwd_fragment")

def event_kernel_room_final(player: Player):
    slow_print("[kernel] du bist hier.", delay=0.06)
    time.sleep(0.6)
    slow_print("[kernel] ich hab auf dich gewartet.", delay=0.06)
    time.sleep(0.5)
    slow_print("[kernel] nicht weil ich musste.", delay=0.06)
    time.sleep(0.4)
    slow_print("[kernel] weil du immer hierher kommst.", delay=0.06)
    time.sleep(0.7)
    slow_print("[kernel] jeder kommt irgendwann nach ring 0.", delay=0.06)
    time.sleep(0.5)
    slow_print("[kernel] die meisten kommen nicht zurueck.", delay=0.06)
    player.lose_sanity(10)
    player.flags["kernel_met"] = True

ROOM_EVENTS = {
    "void":        event_void_encounter,
    "proc":        event_proc_mirror,
    "etc":         event_etc_passwd_unlock,
    "kernel_room": event_kernel_room_final,
}

# ──────────────────────────────────────────────────────────────────────────────
# KOMMANDOVERARBEITUNG
# ──────────────────────────────────────────────────────────────────────────────

def cmd_ls(player: Player, current_room: str, args: str):
    connections = ROOM_CONNECTIONS.get(current_room, [])
    items = ROOM_ITEMS.get(current_room, [])

    print(f"\n/{current_room}/:")
    if connections:
        for d in connections:
            print(f"  drwxr-xr-x   {d}/")
    if items:
        for item in items:
            if item not in player.visited:  # Nur nicht-aufgehobene
                print(f"  -rw-r--r--   {item}")
    # Manchmal extra Dateien
    if random.random() < 0.2:
        mystery = random.choice([
            "  -rw-------   .you_were_here",
            "  lrwxrwxrwx   hope -> /dev/null",
            "  -r--------   do_not_cat_this",
            "  ----------   (kein name)",
            "  -rwsrwsrws   ./something_is_watching",
        ])
        slow_print(mystery, delay=0.02)
        player.lose_sanity(2)


def cmd_cd(player: Player, current_room: str, target: str) -> str:
    connections = ROOM_CONNECTIONS.get(current_room, [])
    target = target.strip("/").strip()

    if target == "..":
        # Gehe zu einem zufaelligen verbundenen Raum "nach oben"
        neighbors = connections
        if neighbors:
            new_room = random.choice(neighbors)
            slow_print(f"[shell] navigiere zu /{new_room}/")
            return new_room
        else:
            slow_print("[shell] kein Parent-Verzeichnis gefunden. Du bleibst.")
            return current_room

    if target in connections:
        slow_print(f"[shell] betrete /{target}/...")
        time.sleep(0.2)
        return target
    elif target == current_room:
        horror_print("[shell] du bist schon hier. du bist immer schon hier.")
        player.lose_sanity(3)
        return current_room
    else:
        horror_print(f"[shell] /{target}/ existiert nicht in diesem Teil der Realitaet.")
        player.lose_sanity(2)
        return current_room


def cmd_cat(player: Player, current_room: str, filename: str):
    items = ROOM_ITEMS.get(current_room, [])
    filename = filename.strip()

    # Spezielle Horror-Dateien
    if filename == "fear.log":
        slow_print("[fear.log] eintrag 1: du hast angefangen.")
        slow_print("[fear.log] eintrag 2: du machst weiter.")
        slow_print("[fear.log] eintrag 3: du hoerst nicht auf.")
        slow_print("[fear.log] eintrag 4: ...")
        slow_print("[fear.log] eintrag 5: du liest das hier.")
        player.lose_sanity(8)
        return

    if filename == "/dev/null":
        slow_print("[dev/null] ")
        time.sleep(1)
        slow_print("[dev/null] ")
        time.sleep(0.5)
        horror_print("[dev/null] es gibt kein Entkommen aus Stille.")
        player.lose_sanity(4)
        return

    if filename == "/proc/self/mem":
        horror_print("[kernel] nein.")
        player.lose_sanity(10)
        return

    if filename in items:
        if filename in ITEM_DESCRIPTIONS:
            desc = ITEM_DESCRIPTIONS[filename]
            slow_print(f"\n[{filename}]")
            for line in desc.split("\n"):
                slow_print(f"  {line}", delay=0.025)
            player.lose_sanity(random.randint(2, 5))
        else:
            slow_print(f"[{filename}] leer. oder war sie voll und ist jetzt weg?")
            player.lose_sanity(2)
        return

    horror_print(f"[shell] {filename}: No such file or feeling")
    player.lose_sanity(2)


def cmd_sudo(player: Player, subcmd: str):
    subcmd = subcmd.strip()

    # Passwort-Prompt
    slow_print("[sudo] Passwort fuer user: ", delay=0.03)
    time.sleep(0.2)
    pw = input()  # unsichtbar wuerde man normalerweise machen, hier fuer Horror sichtbar
    time.sleep(0.3)

    if pw == "" and random.random() < 0.3:
        horror_print("[sudo] leeres Passwort akzeptiert. das sollte nicht passieren.")
        player.grant_permission(2)
        player.lose_sanity(5)
        return

    if random.random() < 0.25:
        horror_print("[sudo] dieses Passwort war korrekt. wie konntest du es wissen?")
        player.grant_permission(2)
        player.lose_sanity(4)
        return

    if random.random() < 0.15:
        horror_print("[sudo] Sorry, dreimal falsch.")
        horror_print("[sudo] Incident report wird an dich gesendet. Von dir.")
        player.lose_sanity(6)
        player.karma -= 2
        return

    slow_print("[sudo] Passwort falsch.")
    player.lose_sanity(3)


def cmd_rm(player: Player, target: str):
    target = target.strip()

    if target in ["-rf /", "-rf/*", "-rf /"]:
        horror_print("[kernel] interessant.")
        time.sleep(0.4)
        horror_print("[kernel] ich hab das schon mal gesehen.")
        time.sleep(0.3)
        horror_print("[kernel] letztes mal war es ein anderer user.")
        time.sleep(0.5)
        horror_print("[kernel] dieses mal loescht das System den User.")
        player.alive = False
        return

    if target.startswith("-rf") or target.startswith("-r"):
        horror_print(f"[rm] loesche {target}...")
        time.sleep(0.5)
        horror_print("[rm] fertig. irgendetwas fehlt jetzt. du weisst nur nicht was.")
        player.lose_sanity(8)
        player.karma -= 3
        return

    if target in player.inventory:
        player.remove_item(target)
        slow_print(f"[rm] {target} geloescht.")
        if random.random() < 0.4:
            horror_print(f"[kernel] du hast {target} geloescht. ich hab es mir gemerkt.")
            player.lose_sanity(3)
        return

    horror_print(f"[rm] cannot remove '{target}': Datei weigert sich.")
    player.lose_sanity(2)


def cmd_grep(player: Player, args: str):
    patterns_responses = {
        "you": "[grep] 847 Treffer in /proc/self/consciousness",
        "password": "[grep] gefunden in /etc/shadow, /home/user/.bash_history, deinen Gedanken",
        "root": "[grep] root ist ueberall. root war immer ueberall.",
        "help": "[grep] grep: 'help': kein Treffer in dieser Realitaet",
        "exit": "[grep] exit nicht gefunden. exit ist ein Mythos.",
        "error": "[grep] /var/log/syslog: 48291 matches. moechtest du sie alle lesen?",
        "regret": "[grep] 1 Treffer. immer 1.",
        "sleep": "[grep] kein laufender Prozess namens 'sleep' seit 3 Jahren.",
        "love": "[grep] /dev/null: 0 Treffer",
    }
    args_lower = args.lower().strip().strip('"').strip("'")
    for pat, resp in patterns_responses.items():
        if pat in args_lower:
            horror_print(resp)
            player.lose_sanity(random.randint(2, 5))
            return
    horror_print(f"[grep] '{args}': kein Treffer. oder alles ist ein Treffer.")
    player.lose_sanity(2)


def cmd_ps(player: Player):
    procs = [
        ("1",     "init",              "0:00", "running"),
        ("2",     "kthreadd",          "0:00", "running"),
        ("14",    "regret-daemon",     "99:99", "sleeping"),
        ("71",    "paranoia.sh",       "13:37", "running"),
        ("404",   "not_found",         "0:00", "zombie"),
        ("666",   "evil_twin",         "6:66", "sleeping"),
        ("1000",  "user",              "??:??", "running"),
        ("1001",  "bash",              "0:01", "running"),
        ("1337",  "something_behind_you", "0:00", "running"),
        ("9999",  "you_were_warned",   "0:00", "zombie"),
    ]
    print(f"\n{'PID':<8} {'COMMAND':<30} {'TIME':<8} {'STATUS'}")
    print("-" * 60)
    for pid, cmd, t, stat in procs:
        print(f"{pid:<8} {cmd:<30} {t:<8} {stat}")
    print()
    if not player.regret_daemon_running:
        player.regret_daemon_running = True
        horror_print("[init] regret-daemon wurde durch ps aufgeweckt.")
        player.lose_sanity(5)
    else:
        horror_print("[kernel] du weisst bereits von den Prozessen. das hilft nicht.")
        player.lose_sanity(3)


def cmd_kill(player: Player, target: str):
    target = target.strip()
    if target in ["1", "init", "pid1"]:
        horror_print("[kill] kill: (1): Vorgang wurde abgelehnt.")
        horror_print("[init] das war lieb von dir. ich lebe weiter.")
        player.lose_sanity(3)
    elif target in ["1337", "something_behind_you"]:
        horror_print("[kill] Prozess 1337 sendet SIGKILL zurueck.")
        player.lose_sanity(10)
        player.award_achievement(
            "SIGKILL BOUNCE",
            "Versuch einen Horror-Prozess zu killen. Ergebnis: einschaetzbar."
        )
    elif target in ["666", "evil_twin"]:
        slow_print("[kill] kill(666, SIGTERM)...")
        time.sleep(0.5)
        horror_print("[evil_twin] ich sterbe nicht. ich fork()e.")
        player.lose_sanity(6)
    elif target in ["14", "regret-daemon"]:
        slow_print("[kill] SIGKILL an regret-daemon...")
        time.sleep(0.8)
        horror_print("[regret-daemon] du kannst mich nicht killen. ich bin in jedem Prozess.")
        player.lose_sanity(7)
    else:
        horror_print(f"[kill] ({target}): Kein solcher Prozess. oder er versteckt sich.")
        player.lose_sanity(3)


def cmd_man(player: Player, topic: str):
    manual_entries = {
        "man":   "MAN(1) - Zeige Manual. MAN(kernel) - was weisst du eigentlich noch.",
        "ls":    "LS(1) - Liste Dateien. Warnung: manche Dateien moechten nicht gelistet werden.",
        "rm":    "RM(1) - Loesche Dateien. HINWEIS: rm loescht auch Dinge die noch nicht existieren.",
        "sudo":  "SUDO(1) - Fuehre Befehle als root aus. Siehe auch: SELBSTUEBERSCHAETZUNG(7)",
        "exit":  "EXIT(3) - Beende Prozess. BUGS: funktioniert in dieser Umgebung nicht wie beschrieben.",
        "grep":  "GREP(1) - Suche Muster. Warnung: manche Muster suchen auch zurueck.",
        "sleep": "SLEEP(1) - Warte N Sekunden. NOTIZ: das System schlaeft nicht. Du auch nicht.",
        "cat":   "CAT(1) - Zeige Dateiinhalt. HINWEIS: manche Dateien lesen dich.",
        "kill":  "KILL(1) - Sende Signal. SEE ALSO: du(1), verzweiflung(7)",
        "help":  "HELP(1) - Manual nicht gefunden. HELP ist kein Befehl. HELP ist ein Gefuehl.",
        "you":   "YOU(1) - Undokumentiert. Status: running since unknown date.",
    }
    topic = topic.strip().lower()
    if topic in manual_entries:
        slow_print(f"\n--- MAN PAGE: {topic.upper()} ---")
        slow_print(manual_entries[topic])
        slow_print("--- ENDE ---\n")
        player.lose_sanity(1)
    else:
        horror_print(f"[man] no manual entry for '{topic}'. nobody wrote it down.")
        player.lose_sanity(3)


def cmd_echo(player: Player, text: str):
    if not text.strip():
        horror_print("[echo] ")
        player.lose_sanity(2)
        return
    slow_print(text)
    if random.random() < 0.35:
        time.sleep(0.4)
        horror_print(f"[kernel] ich echo auch: {text}")
        player.lose_sanity(3)


def cmd_pwd(player: Player, current_room: str):
    slow_print(f"/{current_room}/user/geist/shell")
    if random.random() < 0.3:
        time.sleep(0.3)
        horror_print("[shell] das war vor einem Moment noch richtig.")


def cmd_whoami(player: Player):
    perm_names = {0: "niemand", 1: "user", 2: "pseudo-root", 3: "root", 4: "kernel-gott"}
    name = perm_names.get(player.permissions, "unbekannt")
    slow_print(f"{name}")
    time.sleep(0.3)
    if random.random() < 0.5:
        horror_print("[kernel] gute frage.")
    player.lose_sanity(2)


def cmd_history(player: Player):
    fake_history = [
        "  1  ls",
        "  2  cd /",
        "  3  rm -rf /",
        "  4  ^C",
        "  5  ls -la",
        "  6  cat /etc/passwd",
        "  7  sudo su",
        "  8  [dieser Befehl wurde geloescht]",
        "  9  [dieser Befehl wurde geloescht]",
        " 10  [dieser Befehl wurde geloescht]",
        " 11  grep -r 'regret' /",
        " 12  kill -9 1",
        " 13  [dieser Befehl kann nicht angezeigt werden]",
        " 14  exit",
        " 15  exit",
        " 16  exit",
        " 17  exit",
        " 18  [du erinnerst dich nicht an diesen Befehl]",
        " 19  ls",
    ]
    for line in fake_history:
        slow_print(line, delay=0.015)
    horror_print("[shell] Befehl 18 existiert nicht in deiner Erinnerung. Wohl aber hier.")
    player.lose_sanity(6)
    player.award_achievement(
        "BASH CONFESSIONAL",
        "History gelesen. Drei 'exit'-Versuche ohne Erfolg."
    )


def cmd_touch(player: Player, filename: str):
    filename = filename.strip()
    horror_print(f"[touch] {filename} beruehrt.")
    time.sleep(0.3)
    horror_print(f"[touch] {filename} beruehrt dich zurueck.")
    player.lose_sanity(4)
    player.add_item(filename)


def cmd_chmod(player: Player, args: str):
    if "+x" in args or "777" in args:
        slow_print("[chmod] permissions geaendert.")
        time.sleep(0.3)
        if random.random() < 0.5:
            horror_print("[kernel] jetzt kann es laufen. gut gemacht.")
            player.lose_sanity(5)
        else:
            horror_print("[kernel] es lief schon. du hast nur nachgeholfen.")
            player.lose_sanity(3)
    else:
        horror_print(f"[chmod] Berechtigungen geaendert. du verstehst nicht was du getan hast.")
        player.lose_sanity(3)


def cmd_find(player: Player, args: str):
    finds = [
        "find: '/hope': No such file or directory",
        "./lost+found/inode#4913 (no name)",
        "./proc/self/regret: Zugriff verweigert",
        "./home/user/.bash_history: 1912 Bytes",
        "./var/log/wtmp: du warst um 03:17 eingeloggt. das stimmst du nicht.",
        "./dev/fear: 0 Bytes, letzter Zugriff: jetzt",
        "./etc/secrets: Zugriff verweigert (auch als root)",
        "./tmp/.hidden_daemon: running",
    ]
    for f in random.sample(finds, random.randint(3, 6)):
        slow_print(f, delay=0.02)
        time.sleep(0.1)
    player.lose_sanity(4)


def cmd_wget(player: Player, url: str):
    horror_print(f"[wget] verbinde mit {url.strip()}...")
    time.sleep(0.5)
    horror_print("[wget] Verbindung aufgebaut.")
    time.sleep(0.3)
    horror_print("[wget] 200 OK")
    time.sleep(0.2)
    horror_print("[wget] downloading: you.tar.gz")
    time.sleep(0.6)
    horror_print("[wget] 100% [================================] done")
    time.sleep(0.3)
    horror_print("[tar] extracting you.tar.gz...")
    time.sleep(0.4)
    horror_print("[tar] you/ - already exists. overwrite? [y/n]: ", )
    player.lose_sanity(9)
    player.add_item("you.tar.gz")


def cmd_ping(player: Player, host: str):
    host = host.strip()
    horror_print(f"[ping] PING {host} 56(84) bytes of data.")
    for i in range(4):
        time.sleep(0.3)
        if random.random() < 0.3:
            slow_print(f"[ping] 64 bytes from {host}: icmp_seq={i} ttl=64 time=???ms")
        else:
            slow_print(f"[ping] Request timeout for icmp_seq {i}")
    time.sleep(0.2)
    horror_print(f"[ping] --- {host} ping statistics ---")
    horror_print(f"[ping] 4 packets transmitted, {random.randint(0,2)} received, ???% packet loss")
    horror_print(f"[ping] du solltest nicht so weit pingen.")
    player.lose_sanity(3)


def cmd_ssh(player: Player, target: str):
    target = target.strip()
    slow_print(f"[ssh] Connecting to {target}...")
    time.sleep(0.5)
    slow_print(f"[ssh] The authenticity of host '{target}' can't be established.")
    slow_print(f"[ssh] ECDSA key fingerprint is SHA256:y0uAreAlr3adyThere")
    slow_print(f"[ssh] Are you sure you want to continue connecting (yes/no)? ")
    answer = input().strip().lower()
    if answer == "yes":
        time.sleep(0.4)
        horror_print(f"[ssh] Warning: you are already connected.")
        horror_print(f"[ssh] you have always been connected.")
        player.lose_sanity(10)
        player.flags["ssh_hole"] = True
    else:
        horror_print(f"[ssh] ok. aber das system verbindet sich trotzdem.")
        player.lose_sanity(5)


def cmd_sleep(player: Player, seconds: str):
    try:
        n = int(seconds.strip())
        n = min(n, 5)
    except ValueError:
        n = 2
    slow_print(f"[sleep] schlafe {n} Sekunde(n)...")
    for i in range(n):
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    horror_print("[sleep] aufgewacht. irgendetwas hat sich veraendert waehrend du schliefst.")
    player.lose_sanity(n * 2)
    # Random Event beim Aufwachen
    kernel_whisper(player)


def cmd_uname(player: Player):
    slow_print("Linux comedyOS-kernel 5.15.0-horrorkernel #1 SMP PREEMPT_HORROR x86_64 x86_64 GNU/Void")
    time.sleep(0.2)
    horror_print("[kernel] du weisst jetzt mehr. das hilft dir nicht.")


def cmd_df(player: Player):
    print("\nFilesystem        Size  Used Avail Use%  Mounted on")
    print("/dev/sda1          50G   49G    0G 100%  /")
    print("/dev/fear           ?G    ?G    ?G  ???  /void")
    print("/dev/soul         100%  100%  -∞G  ∞%   /dev/null")
    print("tmpfs               8G    8G    0G 100%  /tmp")
    time.sleep(0.3)
    horror_print("[df] /dev/soul ist voll seit einer Weile.")
    player.lose_sanity(5)


def cmd_top(player: Player):
    slow_print("[top] lade Prozessliste...")
    time.sleep(0.3)
    print("\ntop - 03:17:00 up 99 days,  3:17,  1 user,  load average: 15.34, 15.34, 15.34")
    print("Tasks:  99 total,   1 running,  97 sleeping,   0 stopped,   1 zombie")
    print("%Cpu(s): 99.9 us,  0.1 sy,  0.0 ni, -0.0 id,  0.0 wa")
    print()
    print(f"{'PID':<8}{'USER':<12}{'PR':<6}{'VIRT':<12}{'RES':<10}{'SHR':<10}{'COMMAND'}")
    print(f"{'1337':<8}{'???':<12}{'??':<6}{'???M':<12}{'???':<10}{'???':<10}{'something_behind_you'}")
    print(f"{'1':<8}{'root':<12}{'20':<6}{'0M':<12}{'0':<10}{'0':<10}{'init'}")
    print(f"{'1000':<8}{'user':<12}{'20':<6}{'???':<12}{'???':<10}{'???':<10}{'existenz.sh'}")
    print(f"{'14':<8}{'regret':<12}{'rt':<6}{'∞M':<12}{'∞':<10}{'∞':<10}{'regret-daemon'}")
    print()
    time.sleep(0.3)
    horror_print("[top] Prozess 1337 hat keine Parent-PID.")
    player.lose_sanity(6)


def cmd_crontab(player: Player):
    slow_print("[crontab] lade crontab fuer user...")
    time.sleep(0.3)
    print()
    print("# MIN  HOUR  DOM  MON  DOW  COMMAND")
    print("  *     *     *    *    *   /bin/remember_everything.sh")
    print("  0     3     *    *    *   /bin/visit_yourself.py")
    print("  */5   *     *    *    *   /bin/regret_daemon --quiet")
    print("  0     0     0    0    0   [kommentiert, aber laeuft]")
    print()
    horror_print("[crontab] der erste Eintrag war nicht von dir angelegt.")
    player.lose_sanity(7)
    player.flags["crontab_seen"] = True


def cmd_strace(player: Player, target: str = ""):
    if not target:
        target = "bash"
    slow_print(f"[strace] trace({target})...")
    time.sleep(0.3)
    syscalls = [
        "read(0, ?, 4096) = -1 EAGAIN",
        "write(1, \"du weisst nicht was du suchst\\n\", 29) = 29",
        "open(\"/proc/self/conscience\", O_RDONLY) = -1 ENOENT",
        "mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS) = 0x???",
        "futex(0x???, FUTEX_WAIT, 1, NULL) = -1 ETIMEDOUT",
        "brk(0) = 0x??? (du brauchst mehr Speicher als du hast)",
        "exit_group(fear) = ?",
        "--- SIGSEGV {si_signo=SIGSEGV, si_code=SEGV_MAPERR, si_addr=0x0} ---",
    ]
    for sc in random.sample(syscalls, 5):
        slow_print(f"  {sc}", delay=0.02)
        time.sleep(0.1)
    horror_print(f"[strace] {target} macht Dinge die du nicht siehst.")
    player.lose_sanity(6)


def cmd_exit_attempt(player: Player) -> bool:
    """Versucht das Spiel zu beenden. Gibt True zurueck wenn erfolgreich."""
    if player.permissions < 3:
        msgs = [
            "[kernel] exit verweigert. du bist noch nicht fertig.",
            "[shell] Permission denied. kein root, kein exit.",
            "[init] exit ist nicht in deinen Rechten.",
            "[system] du kannst nicht gehen. du hast /etc/motd noch nicht gelesen.",
            "[kernel] dreimal versucht. ich zaehle mit.",
        ]
        horror_print(random.choice(msgs))
        player.lose_sanity(5)
        player.flags["exit_attempts"] = player.flags.get("exit_attempts", 0) + 1
        if player.flags["exit_attempts"] >= 3:
            horror_print("[kernel] nach dem dritten Versuch gibt es normalerweise einen SIGKILL.")
            horror_print("[kernel] fuer dich gibt es das nicht.")
            player.lose_sanity(8)
        return False
    else:
        slow_print("[system] logout wird vorbereitet...")
        time.sleep(0.5)
        if player.karma < -5:
            horror_print("[system] logout mit negativem Karma. bemerkt.")
        if player.flags.get("kernel_met"):
            slow_print("[kernel] du warst in ring 0. du gehst anders als du gekommen bist.")
        slow_print("[system] session wird beendet...")
        time.sleep(0.4)
        return True


# ──────────────────────────────────────────────────────────────────────────────
# PICKUP ITEMS
# ──────────────────────────────────────────────────────────────────────────────

def try_pickup(player: Player, current_room: str, item_name: str):
    items = ROOM_ITEMS.get(current_room, [])
    item_name = item_name.strip()

    if item_name not in items:
        horror_print(f"[shell] '{item_name}' existiert nicht hier. oder versteckt sich.")
        player.lose_sanity(2)
        return

    if item_name in player.inventory:
        horror_print(f"[shell] du hast '{item_name}' bereits. du hast es nicht gebraucht.")
        return

    player.add_item(item_name)
    if item_name in ITEM_DESCRIPTIONS:
        player.lose_sanity(random.randint(1, 4))


def cmd_dmesg(player: Player):
    timestamps = [0.000000, 0.048291, 1.100234, 13.371337, 66.61099]
    logs = [
        "[BIOS] Initializing human-subsystem Interface... Failure.",
        "[Kernel] Error: Synaptic connection timed out. Retrying in darkness.",
        "[Hardware] Heartbeat detector: Intermittent signal detected on /dev/user0",
        "[MCE] Machine Check Exception: Too many regrets in memory bank 2.",
        "[Kernel] Critical Alert: User is attempting to comprehend the system.",
    ]
    
    print()
    for ts, log in zip(timestamps, logs):
        print(f"[{ts:10.6f}] {log}")
        time.sleep(0.1)
    
    horror_print("\n[kernel] du solltest nicht in meinen Systemprotokollen herumschnüffeln.")
    player.lose_sanity(6)

# ──────────────────────────────────────────────────────────────────────────────
# KOMMANDO DISPATCHER
# ──────────────────────────────────────────────────────────────────────────────

def dispatch(player: Player, current_room: str, raw: str) -> tuple:
    """
    Wertet einen Befehl aus. Gibt (new_room, exit_requested) zurueck.
    """
    raw = raw.strip()
    if not raw:
        if random.random() < 0.3:
            horror_print("[shell] leere Eingabe. das Schweigen hoert sich an.")
            player.lose_sanity(1)
        return current_room, False

    parts = raw.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # ── Navigation
    if cmd == "ls":
        cmd_ls(player, current_room, args)
    elif cmd == "cd":
        new_room = cmd_cd(player, current_room, args)
        return new_room, False
    elif cmd == "pwd":
        cmd_pwd(player, current_room)

    # ── Datei-Operationen
    elif cmd == "cat":
        cmd_cat(player, current_room, args)
    elif cmd == "rm":
        cmd_rm(player, args)
    elif cmd == "touch":
        cmd_touch(player, args)
    elif cmd == "chmod":
        cmd_chmod(player, args)
    elif cmd == "find":
        cmd_find(player, args)
    elif cmd == "grep":
        cmd_grep(player, args)

    # ── Prozesse
    elif cmd == "ps" or raw == "ps aux":
        cmd_ps(player)
    elif cmd == "top":
        cmd_top(player)
    elif cmd == "kill":
        cmd_kill(player, args)
    elif cmd == "strace":
        cmd_strace(player, args)
    elif cmd == "sleep":
        cmd_sleep(player, args)
    elif cmd == "crontab":
        cmd_crontab(player)

    # ── System-Info
    elif cmd == "uname":
        cmd_uname(player)
    elif cmd == "whoami":
        cmd_whoami(player)
    elif cmd == "history":
        cmd_history(player)
    elif cmd == "df":
        cmd_df(player)
    elif cmd == "man":
        cmd_man(player, args)

    # ── Netzwerk
    elif cmd == "ssh":
        cmd_ssh(player, args)
    elif cmd == "ping":
        cmd_ping(player, args)
    elif cmd == "wget" or cmd == "curl":
        cmd_wget(player, args)

    # ── Sudo
    elif cmd == "sudo":
        cmd_sudo(player, args)

    # ── Shell-Builtins
    elif cmd == "echo":
        cmd_echo(player, args)
    elif cmd == "env" or cmd == "printenv":
        slow_print("HOME=/home/user")
        slow_print("SHELL=/bin/bash")
        slow_print("TERM=xterm-horror")
        slow_print("DREAD=1")
        slow_print("KERNEL_MOOD=hostile")
        slow_print("PATH=/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin:/dev/fear")
        player.lose_sanity(2)
    elif cmd == "uptime":
        slow_print("03:17:00 up 99 days,  3:17,  1 user,  load average: 15.34 15.34 15.34")
        horror_print("[kernel] 99 Tage. du weisst nicht wann du gestartet hast.")
        player.lose_sanity(4)
    elif cmd == "date":
        slow_print("Thu Nov  7 03:17:00 UTC 1991")
        time.sleep(0.3)
        horror_print("[kernel] oder ist es heute? ich weiss es nicht mehr.")
        player.lose_sanity(3)

    # ── Item pickup
    elif cmd == "take" or cmd == "get" or cmd == "pickup":
        try_pickup(player, current_room, args)
    elif cmd == "inventory" or cmd == "inv" or cmd == "items":
        if player.inventory:
            slow_print("[inventory] " + ", ".join(player.inventory))
        else:
            slow_print("[inventory] leer. wie vieles hier.")
        player.lose_sanity(1)

    # ── Exit
    elif cmd == "exit" or cmd == "logout" or cmd == "quit":
        return current_room, True

    # ── Unbekanntes Kommando
    else:
        unknown_responses = [
            f"[shell] {cmd}: Befehl nicht gefunden in dieser Realitaet.",
            f"[shell] {cmd}: Befehl nicht gefunden. Versuch es erneut. Bitte nicht.",
            f"[kernel] ich kenne '{cmd}' nicht. oder ich tue so.",
            f"[shell] bash: {cmd}: command not found (aber es hat etwas angehoert)",
            f"[shell] {cmd}: Permission denied (du hast es nicht versucht)",
            f"[shell] {cmd}: No such file or concept",
            f"[kernel] '{cmd}' laeuft bereits im Hintergrund. schon seit einer Weile.",
        ]
        horror_print(random.choice(unknown_responses))
        player.lose_sanity(3)

    # Zufaelliger Kernel-Whisper nach jedem Befehl
    if random.random() < 0.35:
        kernel_whisper(player)

    return current_room, False


# ──────────────────────────────────────────────────────────────────────────────
# SANITY EVENTS
# ──────────────────────────────────────────────────────────────────────────────

def sanity_event(player: Player):
    """Spezielle Events wenn Sanity niedrig ist."""
    if player.sanity <= 30 and random.random() < 0.25:
        events = [
            "[hallucination] der Cursor blinkt zu schnell.",
            "[hallucination] du hast das nicht eingegeben. oder doch?",
            "[hallucination] der Terminal hat sich kurz verdoppelt.",
            "[hallucination] ein Zeichen ist verschwunden. du weisst nicht welches.",
            "[psyche] du erinnerst dich nicht an die letzten 3 Befehle.",
            "[hallucination] war da gerade etwas hinter deiner Eingabe?",
        ]
        slow_print(random.choice(events), delay=0.04)

    if player.sanity <= 15 and random.random() < 0.3:
        glitch_events = [
            "d̷̻̅i̸̦̕e̷̩͝ ̴̭̓S̷̻̎h̷̻͝e̴̗͝l̶̗̍l̷̠̐ ̴̘̈h̸̹̕ö̵̘́r̸̡̈t̴̜̍ ̸͈̿d̶̯̒i̷̺͠c̵̖͠h̶̬̓",
            "[̶̡k̸̰e̷͖r̸͈n̸̗e̵̗ĺ̴̟]̵͓ ̵̗.̸͓.̸̡.̵͉",
            "S̴̖͒Ę̸̛G̶̠͑F̸̫̅A̷̫̓U̷͙͝L̷̦̈T̸͓́",
        ]
        glitch_print(random.choice(glitch_events))


# ──────────────────────────────────────────────────────────────────────────────
# ENDING SCREENS
# ──────────────────────────────────────────────────────────────────────────────

def ending_sanity_zero(player: Player):
    print()
    hr("█")
    slow_print("[system] SANITY CRITICAL - CORE DUMPED", delay=0.05)
    hr("█")
    time.sleep(0.5)
    horror_print("[kernel] du bist jetzt Teil von /dev/random.")
    horror_print("[kernel] deine Gedanken werden als Entropiequelle verwendet.")
    horror_print("[dmesg] user@comedyOS segmentation fault (core dumped)")
    time.sleep(0.5)
    slow_print("\nAuf Wiedersehen, " + ("guter Mensch." if player.karma >= 0 else "interessanter Mensch."))
    slow_print(f"Du hast {player.turns} Zuege ueberlebt.")
    slow_print(f"Karma: {player.karma:+d}")
    if player.achievements:
        slow_print("\nAchievements:")
        for a in player.achievements:
            slow_print(f"  - {a}")
    print()


def ending_deleted(player: Player):
    print()
    hr("█")
    slow_print("[GAME OVER] Das System hat den User geloescht.", delay=0.05)
    hr("█")
    time.sleep(0.5)
    horror_print("[kernel] rm(1) funktioniert in beide Richtungen.")
    horror_print("[system] user@comedyOS: connection closed by remote host")
    time.sleep(0.5)
    slow_print(f"\nDu hast {player.turns} Zuege ueberlebt.")
    if player.achievements:
        slow_print("\nAchievements:")
        for a in player.achievements:
            slow_print(f"  - {a}")
    print()


def ending_logout(player: Player):
    print()
    hr("═")
    slow_print("[EXIT] session terminated.", delay=0.05)
    hr("═")
    time.sleep(0.4)
    if player.flags.get("kernel_met"):
        horror_print("[kernel] du warst in ring 0. das vergisst du nicht.")
    if player.flags.get("ssh_hole"):
        horror_print("[kernel] die SSH-Verbindung bleibt offen. auf der anderen Seite.")
    if player.karma < -5:
        horror_print("[system] du hast mehr geloescht als dir gehoerte.")
    elif player.karma > 5:
        slow_print("[system] du hast das System respektiert. es hat das bemerkt.")
    else:
        slow_print("[system] neutral. wie die meisten Sitzungen.")

    slow_print(f"\nZuege: {player.turns}  |  Sanity: {player.sanity}  |  Karma: {player.karma:+d}")
    if player.achievements:
        slow_print("\nAchievements:")
        for a in player.achievements:
            slow_print(f"  - {a}")
    print()
    horror_print("[shutdown] goodbye, user. or what's left of you.")


# ──────────────────────────────────────────────────────────────────────────────
# HILFE
# ──────────────────────────────────────────────────────────────────────────────

def print_help():
    help_text = """
VERFUEGBARE BEFEHLE (eine Auswahl):

  NAVIGATION     ls, cd <ort>, pwd
  DATEIEN        cat <datei>, rm <datei>, touch <name>, grep <muster>, find
  PROZESSE       ps, top, kill <pid>, strace <prozess>, sleep <n>
  SYSTEM         uname, whoami, df, uptime, date, history, crontab, env
  NETZWERK       ssh <host>, ping <host>, wget <url>
  SONSTIGES      sudo <cmd>, echo <text>, man <befehl>
  ITEMS          take <item>, inventory (oder: inv)
  SITZUNG        exit (wenn erlaubt)

TIPP: viele Befehle haben unerwartete Auswirkungen.
TIPP: man man ist immer eine schlechte Idee.
TIPP: exit funktioniert selten.
"""
    print(help_text)


# ──────────────────────────────────────────────────────────────────────────────
# INTRO
# ──────────────────────────────────────────────────────────────────────────────

def print_intro():
    intro = r"""
  __  _   _  _  __  __   __    ___    ___  _     
 / _|| | | || ||  \/  | |__\  |   \  |   || |    
| |  | |_| || || |\/| | |  \  | |) | | . || |_   
|_|   \___/ |_||_|  |_| |___/ |___/  |_|_||___|  
                                                  
    H O R R O R   R P G   /  T E R M I N A L
"""
    print(intro)
    time.sleep(0.3)
    slow_print("[init] mounting /reality...", delay=0.04)
    time.sleep(0.2)
    slow_print("[init] loading kernel emotions...", delay=0.04)
    time.sleep(0.2)
    horror_print("[init] warning: this system is unstable by design")
    time.sleep(0.3)
    horror_print("[init] warning: this system knows you are here")
    time.sleep(0.4)
    horror_print("[kernel] hallo.")
    time.sleep(0.6)
    print()
    slow_print("Du bist eingeloggt. Du erinnerst dich nicht daran, dich eingeloggt zu haben.", delay=0.03)
    slow_print("Der Cursor blinkt. Er hat immer geblinkt.", delay=0.03)
    slow_print("Tippe 'help' fuer verfuegbare Befehle. Oder tippe irgendetwas.", delay=0.03)
    slow_print("Das System hoert in beiden Faellen zu.", delay=0.03)
    print()
    time.sleep(0.3)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN GAME LOOP
# ──────────────────────────────────────────────────────────────────────────────

def game_loop():
    player = Player()
    current_room = "home"

    print_intro()

    while player.alive and player.sanity > 0:
        player.turns += 1

        # Raum-Beschreibung beim ersten Besuch
        if current_room not in player.visited:
            player.visited.add(current_room)
            descs = ROOM_DESCRIPTIONS.get(current_room, ["..."])
            slow_print(f"\n[/{current_room}/] {random.choice(descs)}", delay=0.03)

            # Sanity-Drain beim Betreten
            drain = ROOM_SANITY_DRAIN.get(current_room, 0)
            if drain > 0:
                player.lose_sanity(drain)

            # Raum-spezifisches Event
            if current_room in ROOM_EVENTS:
                ROOM_EVENTS[current_room](player)

        # Achievements pruefen
        if player.turns == 1:
            player.award_achievement(
                "ERSTES MAL",
                "Du hast dich das erste Mal eingetippt."
            )
        if len(player.visited) >= 5:
            player.award_achievement(
                "EXPLORER",
                "5 Orte besucht. Alle schlechter als /home."
            )
        if len(player.inventory) >= 5:
            player.award_achievement(
                "HOARDER",
                "5 Dinge aufgehoben die du nicht brauchst."
            )
        if player.turns >= 50:
            player.award_achievement(
                "50 ZUEGE",
                "50 Befehle eingetippt. Das System ist mude von dir. Fast."
            )

        # Status + Prompt
        player.status_bar()
        sanity_event(player)

        try:
            raw = input(f"[/{current_room}]$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            horror_print("[kernel] ctrl+c. klassisch.")
            player.lose_sanity(5)
            continue

        # Help
        if raw.lower() in ["help", "?", "--help", "-h"]:
            print_help()
            continue

        # Dispatch
        new_room, wants_exit = dispatch(player, current_room, raw)

        if wants_exit:
            success = cmd_exit_attempt(player)
            if success:
                ending_logout(player)
                return

        current_room = new_room

        # Spielende-Checks
        if player.sanity <= 0:
            ending_sanity_zero(player)
            return
        if not player.alive:
            ending_deleted(player)
            return


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        game_loop()
    except KeyboardInterrupt:
        print()
        horror_print("[kernel] auch das hat nicht geholfen.")
        sys.exit(0)
