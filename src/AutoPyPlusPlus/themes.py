def set_dark_mode(style, master):
    style.theme_use("clam")
    bg = "#0c0411"
    fg = "green2"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background="black", foreground=fg)
    style.configure("TButton", background="#200530", foreground=fg)
    style.configure("Treeview", background="black", foreground=fg, fieldbackground="#383838")
    style.configure("Treeview.Heading", background="black", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#2e2e2e", background="#ff0000", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background="#2e2e2e")


def set_light_mode(style, master):
    style.theme_use("clam")
    bg = "#f0f0f0"
    fg = "#000000"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#e0e0e0", foreground=fg)
    style.configure("Treeview", background="#ffffff", foreground=fg, fieldbackground="#ffffff")
    style.configure("Treeview.Heading", background="#e0e0e0", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#0078D7", foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#d3d3d3", background="#ff4040", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_arcticblue_mode(style, master):
    style.theme_use("clam")
    bg = "#072763"
    fg = "#ffffff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#0680a7", foreground=fg)
    style.configure("Treeview", background="#41729f", foreground=fg, fieldbackground="#274472")
    style.configure("Treeview.Heading", background="#41729f", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#61a5c2", foreground="#1a1a1a", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#274472", background="#61a5c2", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background="#274472")


def set_sunset_mode(style, master):
    style.theme_use("clam")
    bg = "#2b1700"
    fg = "#ff9933"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#09718a", foreground=fg)
    style.configure("Treeview", background="#4b2600", foreground=fg, fieldbackground="#663300")
    style.configure("Treeview.Heading", background="#4b2600", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#ff9933", foreground="#1a1a1a", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#ff6600", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_forest_mode(style, master):
    style.theme_use("clam")
    bg = "#1b3a1b"
    fg = "#a3d977"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#2e5939", foreground=fg)
    style.configure("Treeview", background="#2e5939", foreground=fg, fieldbackground="#345c46")
    style.configure("Treeview.Heading", background="#2e5939", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background=fg, foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#66cc66", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_retro_mode(style, master):
    style.theme_use("clam")
    bg = "#000080"
    fg = "#ffcc00"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background=fg, foreground=bg)
    style.configure("Treeview", background="#003366", foreground=fg, fieldbackground=bg)
    style.configure("Treeview.Heading", background="#003366", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#ff6600", foreground="black", font=("Courier New", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#ff6600", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_pastel_mode(style, master):
    style.theme_use("clam")
    bg = "#f8f0e3"
    fg = "#7a5c61"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#d6cbd3", foreground="#1a1a1a")
    style.configure("Treeview", background=bg, foreground=fg, fieldbackground="#e8d7d1")
    style.configure("Treeview.Heading", background="#d6cbd3", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#e4a0a1", foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#e4a0a1", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_galaxy_mode(style, master):
    style.theme_use("clam")
    bg = "#0b0c10"
    fg = "#66fcf1"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#1f2833", foreground=fg)
    style.configure("Treeview", background="#1f2833", foreground=fg, fieldbackground="#1f2833")
    style.configure("Treeview.Heading", background=bg, foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#45a29e", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background=fg, thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_autumn_mode(style, master):
    style.theme_use("clam")
    bg = "#4a2c2a"
    fg = "#f2c94c"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#6d4c41", foreground=fg)
    style.configure("Treeview", background="#6d4c41", foreground=fg, fieldbackground="#8d6e63")
    style.configure("Treeview.Heading", background="#6d4c41", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#f2994a", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#d35400", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_candy_mode(style, master):
    style.theme_use("clam")
    bg = "#ff99cc"
    fg = "#1a1a1a"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#66ccff", foreground=fg)
    style.configure("Treeview", background="#ffb3d9", foreground=fg, fieldbackground=bg)
    style.configure("Treeview.Heading", background="#ffb3d9", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#66ccff", foreground=fg, font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background="#66ccff", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_inferno_mode(style, master):
    style.theme_use("clam")
    bg = "#330000"
    fg = "#ff3300"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#6d4c41", foreground="#f2c94c")
    style.configure("Treeview", background="#660000", foreground=fg, fieldbackground="#800000")
    style.configure("Treeview.Heading", background="#660000", foreground=fg)
    style.map("Treeview", background=[("selected", bg)], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background=fg, foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor=bg, background=fg, thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)

def set_cyberpunk_mode(style, master):
    style.theme_use("clam")
    bg = "#000000"
    fg = "#ff00ff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#5500aa", foreground=fg)
    style.configure("Treeview", background="#220022", foreground=fg, fieldbackground="#220022")
    style.configure("Treeview.Heading", background="#5500aa", foreground=fg)
    style.map("Treeview", background=[("selected", "#aa00ff")], foreground=[("selected", "#00ffff")])
    style.configure("Accent.TButton", background="#00ffff", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#5500aa", background=fg, thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_obsidian_mode(style, master):
    style.theme_use("clam")
    bg = "#000000"
    fg = "#ffffff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#333333", foreground=fg)
    style.configure("Treeview", background="#1a1a1a", foreground=fg, fieldbackground="#1a1a1a")
    style.configure("Treeview.Heading", background="#333333", foreground=fg)
    style.map("Treeview", background=[("selected", "#555555")], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#ffffff", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#333333", background="#ffffff", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_nebula_mode(style, master):
    style.theme_use("clam")
    bg = "#0a0022"
    fg = "#c0c0ff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#220044", foreground=fg)
    style.configure("Treeview", background="#220044", foreground=fg, fieldbackground="#110033")
    style.configure("Treeview.Heading", background="#220044", foreground=fg)
    style.map("Treeview", background=[("selected", "#440088")], foreground=[("selected", "#ffffff")])
    style.configure("Accent.TButton", background="#ffffff", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#110033", background=fg, thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_midnight_forest_mode(style, master):
    style.theme_use("clam")
    bg = "#001a0f"
    fg = "#66ff66"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#003300", foreground=fg)
    style.configure("Treeview", background="#002a1a", foreground=fg, fieldbackground="#001f14")
    style.configure("Treeview.Heading", background="#003300", foreground=fg)
    style.map("Treeview", background=[("selected", "#005522")], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background=fg, foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#001a0f", background="#66ff66", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_phantom_mode(style, master):
    style.theme_use("clam")
    bg = "#0b0014"
    fg = "#d0b0ff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#220044", foreground=fg)
    style.configure("Treeview", background="#220044", foreground=fg, fieldbackground="#140022")
    style.configure("Treeview.Heading", background="#220044", foreground=fg)
    style.map("Treeview", background=[("selected", "#440088")], foreground=[("selected", "#ffffff")])
    style.configure("Accent.TButton", background=fg, foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#140022", background=fg, thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_deep_space_mode(style, master):
    style.theme_use("clam")
    bg = "#00010a"
    fg = "#a9eaff"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#003366", foreground=fg)
    style.configure("Treeview", background="#001f33", foreground=fg, fieldbackground="#001a2a")
    style.configure("Treeview.Heading", background="#003366", foreground=fg)
    style.map("Treeview", background=[("selected", "#004488")], foreground=[("selected", "#ffffff")])
    style.configure("Accent.TButton", background="#1c3f54", foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#001a2a", background="#1c3f54", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_onyx_mode(style, master):
    style.theme_use("clam")
    bg = "#0a0a0a"
    fg = "#dddddd"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#222222", foreground=fg)
    style.configure("Treeview", background="#1a1a1a", foreground=fg, fieldbackground="#1a1a1a")
    style.configure("Treeview.Heading", background="#222222", foreground=fg)
    style.map("Treeview", background=[("selected", "#444444")], foreground=[("selected", fg)])
    style.configure("Accent.TButton", background="#aaaaaa", foreground="black", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#333333", background="#aaaaaa", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)


def set_lava_flow_mode(style, master):
    style.theme_use("clam")
    bg = "#1c0b00"
    fg = "#ff5500"
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background="#552200", foreground=fg)
    style.configure("Treeview", background="#330d00", foreground=fg, fieldbackground="#220800")
    style.configure("Treeview.Heading", background="#552200", foreground=fg)
    style.map("Treeview", background=[("selected", "#aa3300")], foreground=[("selected", "#ffffff")])
    style.configure("Accent.TButton", background="#ff5500", foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Red.Horizontal.TProgressbar", troughcolor="#220800", background="#ff5500", thickness=20)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    master.configure(background=bg)
