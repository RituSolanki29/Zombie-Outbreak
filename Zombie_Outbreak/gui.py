from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from scenarios import SCENARIOS
from simulation import ZombieSimulation
from agents import SurvivorStatus

# A compact, dark survival-game dashboard. The simulation itself remains continuous-space.
BG = '#101820'
PANEL = '#192630'
PANEL_EDGE = '#2A3B47'
TEXT = '#EAF1F4'
MUTED = '#9AAEB8'
ACCENT = '#56C7A5'
RED = '#F06464'
BLUE = '#62B6E7'
GREEN = '#62D49A'
PURPLE = '#C18AF2'
ORANGE = '#F3B45C'
COLORS = {'S1': BLUE, 'S2': GREEN, 'S3': ORANGE}

class ZombieApp:
    def __init__(self, root, default_algorithm='A*'):
        self.root = root
        root.title('OUTBREAK // Continuous Survival Simulator')
        root.geometry('1360x860')
        root.minsize(1050, 680)
        root.configure(bg=BG)
        self.sim = ZombieSimulation(path_algorithm=default_algorithm)
        self.auto = False
        self.job = None
        self._play_generation = 0
        self._map_geometry = None

        header = tk.Frame(root, bg=BG)
        header.pack(fill='x', padx=22, pady=(18, 14))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side='left', fill='x', expand=True)
        tk.Label(brand, text='OUTBREAK', font=('Segoe UI', 23, 'bold'), bg=BG, fg=TEXT).pack(anchor='w')
        tk.Label(brand, text='CONTINUOUS SURVIVAL SIMULATOR  /  2D FIELD OPERATIONS', font=('Consolas', 9), bg=BG, fg=ACCENT).pack(anchor='w', pady=(2, 0))
        self.phase = tk.Label(header, text='●  SIMULATION READY', font=('Consolas', 10, 'bold'), bg=BG, fg=GREEN)
        self.phase.pack(side='right', anchor='n', pady=8)

        body = tk.Frame(root, bg=BG)
        body.pack(fill='both', expand=True, padx=22, pady=(0, 20))
        left = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=PANEL_EDGE)
        left.pack(side='left', fill='both', expand=True, padx=(0, 16))
        maphead = tk.Frame(left, bg=PANEL)
        maphead.pack(fill='x', padx=15, pady=(13, 7))
        tk.Label(maphead, text='FIELD MAP', font=('Segoe UI', 11, 'bold'), bg=PANEL, fg=TEXT).pack(side='left')
        tk.Label(maphead, text='LIVE POSITION TRACKING', font=('Consolas', 8), bg=PANEL, fg=MUTED).pack(side='right')
        self.canvas = tk.Canvas(left, bg='#172B2B', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.canvas.bind('<Configure>', lambda _e: self.render())
        legend = tk.Frame(left, bg=PANEL)
        legend.pack(fill='x', padx=15, pady=(0, 13))
        for color, label in [(BLUE, 'SURVIVOR'), ('#E76F71', 'ZOMBIE'), (ORANGE, 'SUPPLY'), (GREEN, 'EXTRACTION'), ('#667B7A', 'STRUCTURE')]:
            item = tk.Frame(legend, bg=PANEL)
            item.pack(side='left', padx=(0, 13))
            tk.Label(item, text='●', font=('Segoe UI', 10), bg=PANEL, fg=color).pack(side='left')
            tk.Label(item, text=label, font=('Consolas', 8), bg=PANEL, fg=MUTED).pack(side='left', padx=(4, 0))

        right = tk.Frame(body, bg=BG, width=330)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)
        controls = self.panel(right, 'MISSION SETUP')
        self.scenario = tk.StringVar(value=self.sim.scenario_name)
        style = ttk.Style()
        # Use the clam theme so selected text, field background and arrow colors
        # remain readable across Windows/Linux ttk themes.
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('Outbreak.TCombobox', fieldbackground='#22333E', background='#22333E', foreground=TEXT,
                        arrowcolor=TEXT, bordercolor=PANEL_EDGE, lightcolor=PANEL_EDGE, darkcolor=PANEL_EDGE,
                        padding=(9, 8), arrowsize=14)
        style.map('Outbreak.TCombobox', fieldbackground=[('readonly', '#22333E'), ('focus', '#2B4553')],
                  foreground=[('readonly', TEXT)], selectbackground=[('readonly', '#2B4553')],
                  selectforeground=[('readonly', TEXT)])
        self.combo = ttk.Combobox(controls, textvariable=self.scenario, values=list(SCENARIOS), state='readonly',
                                  style='Outbreak.TCombobox', font=('Segoe UI', 10), height=8)
        self.combo.pack(fill='x', ipady=2, pady=(0, 10))
        self.combo.option_add('*TCombobox*Listbox.background', '#22333E')
        self.combo.option_add('*TCombobox*Listbox.foreground', TEXT)
        self.combo.option_add('*TCombobox*Listbox.selectBackground', '#34705F')
        self.combo.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
        self.combo.bind('<<ComboboxSelected>>', lambda _e: self.reset())
        tk.Label(controls, text='SURVIVOR PATH-PLANNING ALGORITHM', font=('Consolas', 8), bg=PANEL, fg=MUTED).pack(anchor='w', pady=(0, 5))
        self.algorithm = tk.StringVar(value=self.sim.path_algorithm)
        self.algorithm_combo = ttk.Combobox(controls, textvariable=self.algorithm, values=('A*', 'GBFS'),
                                            state='readonly', style='Outbreak.TCombobox',
                                            font=('Segoe UI', 10), height=2)
        self.algorithm_combo.pack(fill='x', ipady=2, pady=(0, 9))
        self.algorithm_combo.bind('<<ComboboxSelected>>', lambda _e: self.reset())
        buttons = tk.Frame(controls, bg=PANEL)
        buttons.pack(fill='x')
        self.button(buttons, '▶  PLAY', self.toggle, ACCENT, '#10251F').pack(fill='x', pady=3)
        row = tk.Frame(controls, bg=PANEL); row.pack(fill='x')
        self.button(row, 'STEP', self.step, '#2B4553', TEXT).pack(side='left', fill='x', expand=True, padx=(0, 4), pady=3)
        self.button(row, 'RESET', self.reset, '#57343B', '#FFD8D8').pack(side='left', fill='x', expand=True, padx=(4, 0), pady=3)
        tk.Label(controls, text='ANIMATION SPEED', font=('Consolas', 8), bg=PANEL, fg=MUTED).pack(anchor='w')
        self.delay = tk.IntVar(value=90)
        tk.Scale(controls, from_=20, to=400, variable=self.delay, orient='horizontal', bg=PANEL, fg=TEXT, troughcolor='#2B4553', activebackground=ACCENT, highlightthickness=0, bd=0, showvalue=True).pack(fill='x')

        metrics = self.panel(right, 'PATH-PLANNER PERFORMANCE')
        tk.Label(metrics, text='Cumulative metrics freeze when paused or complete',
                 font=('Segoe UI', 8), bg=PANEL, fg=MUTED, wraplength=270,
                 justify='left').pack(anchor='w', pady=(0, 5))
        self.metric_vars = {}
        for key, label in [
            ('algorithm', 'SELECTED ALGORITHM'),
            ('calls', 'PLANNING CALLS'),
            ('success', 'PLAN SUCCESS RATE'),
            ('nodes', 'NODES EXPANDED'),
            ('plantime', 'PLANNING TIME (MS)'),
            ('route', 'MEAN ROUTE LENGTH'),
            ('rescued', 'SURVIVORS RESCUED'),
            ('infected', 'SURVIVORS INFECTED'),
        ]:
            line = tk.Frame(metrics, bg=PANEL)
            line.pack(fill='x', pady=2)
            tk.Label(line, text=label, font=('Consolas', 8), bg=PANEL, fg=MUTED).pack(side='left')
            var = tk.StringVar(value='—')
            self.metric_vars[key] = var
            tk.Label(line, textvariable=var, font=('Consolas', 9, 'bold'), bg=PANEL, fg=TEXT).pack(side='right')

        agents = self.panel(right, 'UNIT STATUS')
        self.status_rows = {}
        for sid in ('S1', 'S2', 'S3', 'Z1', 'Z2', 'Z3'):
            card = tk.Frame(agents, bg='#22333E', padx=9, pady=7)
            card.pack(fill='x', pady=3)
            dot = tk.Label(card, text='●', font=('Segoe UI', 10), bg='#22333E', fg=COLORS.get(sid, '#E76F71'))
            dot.pack(side='left')
            name = tk.Label(card, text=sid, font=('Consolas', 9, 'bold'), bg='#22333E', fg=TEXT, width=4, anchor='w')
            name.pack(side='left', padx=(5, 0))
            value = tk.Label(card, text='WAITING', font=('Consolas', 8), bg='#22333E', fg=MUTED, anchor='e')
            value.pack(side='right', fill='x', expand=True)
            self.status_rows[sid] = (card, dot, value)

        self.render()

    def panel(self, parent, title):
        frame = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=PANEL_EDGE, padx=13, pady=12)
        frame.pack(fill='x', pady=(0, 12))
        tk.Label(frame, text=title, font=('Consolas', 9, 'bold'), bg=PANEL, fg=ACCENT).pack(anchor='w', pady=(0, 10))
        return frame

    def button(self, parent, label, command, bg, fg):
        return tk.Button(parent, text=label, command=command, bg=bg, fg=fg, activebackground=bg, activeforeground=fg, relief='flat', bd=0, padx=10, pady=9, font=('Consolas', 9, 'bold'), cursor='hand2')

    def reset(self):
        self.stop(); self.sim.reset(self.scenario.get(), path_algorithm=self.algorithm.get()); self.render()

    def step(self):
        self.sim.step(); self.render()

    def finish(self):
        self.stop()
        for _ in range(self.sim.max_steps - self.sim.time_step):
            if self.sim.game_over: break
            self.sim.step()
        self.render()

    def toggle(self):
        if self.auto:
            self.stop()
        else:
            if self.sim.game_over:
                self.reset()
            self.auto = True
            self._play_generation += 1
            generation = self._play_generation
            self.play(generation)
        self.update_play_button()
        self.render()

    def update_play_button(self):
        # Find the play button by its text, so the label always reflects current state.
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Button) and (
                    str(child.cget('text')).endswith('PLAY') or
                    str(child.cget('text')).endswith('PAUSE')
                ):
                    child.configure(text='Ⅱ  PAUSE' if self.auto else '▶  PLAY')
                walk(child)
        walk(self.root)

    def play(self, generation=None):
        # A generation token prevents stale callbacks from continuing after pause/reset.
        if generation is None:
            generation = self._play_generation
        if generation != self._play_generation or not self.auto:
            return
        self.job = None
        if self.sim.game_over:
            self.stop()
            self.update_play_button()
            self.render()
            return
        self.sim.step()
        self.render()
        # Schedule exactly one next callback, and retain its ID so stop() can cancel it.
        if self.auto and generation == self._play_generation and not self.sim.game_over:
            self.job = self.root.after(self.delay.get(), lambda g=generation: self.play(g))
        elif self.sim.game_over:
            self.stop()
            self.update_play_button()
            self.render()

    def stop(self):
        # Invalidate any callback already queued, then cancel the known Tk callback.
        self.auto = False
        self._play_generation += 1
        if self.job is not None:
            try:
                self.root.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def render(self):
        c = self.canvas
        c.delete('all')
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 300)
        pad = 22
        scale = min((w-2*pad)/15, (h-2*pad)/15)
        ox, oy = (w-15*scale)/2, (h-15*scale)/2
        self._map_geometry = (ox, oy, scale)
        def xy(p): return ox+p[0]*scale, oy+p[1]*scale
        # Ground plane and subtle terrain grid.
        c.create_rectangle(ox, oy, ox+15*scale, oy+15*scale, fill='#263F39', outline='#73918A', width=2)
        for i in range(16):
            x, y = ox+i*scale, oy+i*scale
            c.create_line(x, oy, x, oy+15*scale, fill='#315047', width=1)
            c.create_line(ox, y, ox+15*scale, y, fill='#315047', width=1)
        # Worn paths running through the environment.
        c.create_line(*[v for p in [(0,7.5),(3.2,7.5),(5.5,7.5),(7.5,8.5),(11.5,7.5),(15,7.5)] for v in xy(p)], fill='#4B5B53', width=max(4,scale*.65), smooth=True)
        c.create_line(*[v for p in [(7.5,0),(7.5,3.5),(6.5,6.5),(7.5,8.5),(7.5,12),(10.5,15)] for v in xy(p)], fill='#4B5B53', width=max(4,scale*.65), smooth=True)
        # Small scattered terrain flecks, deterministic so the map does not flicker.
        for i in range(70):
            gx = ((i*37) % 149)/10
            gy = ((i*61+17) % 149)/10
            px, py = xy((gx, gy))
            c.create_oval(px-1.2, py-1.2, px+1.2, py+1.2, fill='#3C5C4D', outline='')
        # Ruined buildings with drop shadows, roofs and window slits.
        for idx, (x1,y1,x2,y2) in enumerate(self.sim.grid.obstacles):
            ax, ay = xy((x1,y1)); bx, by = xy((x2,y2))
            c.create_rectangle(ax+4, ay+5, bx+4, by+5, fill='#172322', outline='')
            c.create_rectangle(ax, ay, bx, by, fill='#68736F', outline='#A5B0A9', width=1.4)
            c.create_rectangle(ax+3, ay+3, bx-3, by-3, outline='#4D5B57', width=2)
            # Cracked roof accents and dark window openings.
            c.create_line(ax+5, ay+5, (ax+bx)/2, (ay+by)/2, bx-5, by-5, fill='#89948D', width=1)
            win = max(3, scale*.12)
            for wx in (ax+(bx-ax)*.28, ax+(bx-ax)*.68):
                for wy in (ay+(by-ay)*.3, ay+(by-ay)*.68):
                    c.create_rectangle(wx-win, wy-win, wx+win, wy+win, fill='#293B39', outline='#46544F')
            c.create_text((ax+bx)/2, ay+8, text=f'ZONE {idx+1:02}', fill='#D3DAD4', font=('Consolas', max(6, int(scale*.10)), 'bold'))
        # Planned paths are translucent-looking dashed trails.
        for a in list(self.sim.survivors.values()) + list(self.sim.zombies.values()):
            if len(a.path) > 1:
                pts = []
                for q in a.path:
                    xx, yy = xy(q); pts.extend((xx, yy))
                if len(pts) >= 4:
                    color = COLORS.get(a.sid, '#E76F71') if hasattr(a, 'sid') else '#E76F71'
                    c.create_line(*pts, fill=color, dash=(5, 5), width=2, smooth=True)
        # Highlight the latest Alpha–Beta-selected continuous movement.
        for sid, (_tick, _zid, decision) in self.sim.last_decisions.items():
            survivor = self.sim.survivors.get(sid)
            if survivor is not None and survivor.status == SurvivorStatus.ACTIVE:
                ax, ay = xy(survivor.pos); bx, by = xy(decision.action)
                c.create_line(ax, ay, bx, by, fill='#F7E27D', width=3, arrow=tk.LAST, dash=(4, 2))
                c.create_oval(bx-5, by-5, bx+5, by+5, outline='#F7E27D', width=2)
        # Supplies and extraction beacon.
        for name, resource in self.sim.grid.resources.items():
            x, y = xy(resource.pos); r = max(7, scale*.22)
            c.create_oval(x-r, y-r, x+r, y+r, fill='#5C442A', outline=ORANGE, width=2)
            c.create_text(x, y, text={'Food':'F','Water':'W','Medicine':'+'}.get(name,'•'), fill='#FFE1A8', font=('Segoe UI', max(8,int(scale*.16)), 'bold'))
            c.create_text(x, y+r+10, text=name.upper(), fill='#FFE0A5', font=('Consolas', max(6,int(scale*.10)), 'bold'))
        x, y = xy(self.sim.grid.safe_pos); r = max(10, scale*.26)
        c.create_oval(x-r-4, y-r-4, x+r+4, y+r+4, outline='#73DDA8', width=2, dash=(3,3))
        c.create_oval(x-r, y-r, x+r, y+r, fill='#1B704D', outline=GREEN, width=2)
        c.create_text(x, y, text='E', fill='#E0FFED', font=('Segoe UI', max(9,int(scale*.18)), 'bold'))
        c.create_text(x, y+r+12, text='EXTRACTION', fill='#9AF0BF', font=('Consolas', max(6,int(scale*.10)), 'bold'))
        # Draw units with a glow ring and directional/identity marker.
        for s in self.sim.survivors.values():
            x, y = xy(s.pos); r = max(7, scale*.20)
            color = COLORS.get(s.sid, BLUE)
            if s.status == SurvivorStatus.INFECTED: color = PURPLE
            elif s.status == SurvivorStatus.RESCUED: color = GREEN
            elif s.status == SurvivorStatus.DEAD: color = '#77818A'
            c.create_oval(x-r-3, y-r-3, x+r+3, y+r+3, outline=color, width=1, dash=(2,2))
            c.create_oval(x-r, y-r, x+r, y+r, fill=color, outline='#EAF1F4', width=2)
            c.create_text(x, y, text=s.sid[-1], fill='#102029', font=('Consolas', max(8,int(scale*.15)), 'bold'))
        for z in self.sim.zombies.values():
            x, y = xy(z.pos); r = max(7, scale*.20)
            c.create_oval(x-r-3, y-r-3, x+r+3, y+r+3, outline='#E76F71', width=1, dash=(2,2))
            c.create_polygon(x, y-r, x+r, y, x, y+r, x-r, y, fill='#C74752', outline='#FFE2E2', width=2)
            c.create_text(x, y, text='Z', fill='#FFF0F0', font=('Consolas', max(8,int(scale*.15)), 'bold'))
        # Coordinate ruler labels outside the play field.
        for i in range(0,16,3):
            x, y = xy((i,0)); c.create_text(x, oy-9, text=str(i), fill=MUTED, font=('Consolas', 8))
            x, y = xy((0,i)); c.create_text(ox-10, y, text=str(i), fill=MUTED, font=('Consolas', 8))
        m = self.sim.metrics
        self.metric_vars['algorithm'].set(self.sim.path_algorithm)
        self.metric_vars['calls'].set(str(m.planner_calls))
        self.metric_vars['success'].set(f'{m.planning_success_rate:.1f}%')
        self.metric_vars['nodes'].set(f'{m.pathfinding_nodes_expanded:,}')
        self.metric_vars['plantime'].set(f'{m.pathfinding_time_ms:.2f}')
        self.metric_vars['route'].set(f'{m.mean_route_length:.2f} units')
        self.metric_vars['rescued'].set(f'{m.rescued}/{m.survivors_started} ({m.survival_rate:.1f}%)')
        self.metric_vars['infected'].set(str(m.survivors_infected))
        all_units = {**self.sim.survivors, **self.sim.zombies}
        for sid, (card, dot, value) in self.status_rows.items():
            unit = all_units.get(sid)
            if unit is None:
                card.pack_forget()
                continue
            card.pack(fill='x', pady=3)
            pos = unit.pos
            if sid.startswith('S'):
                status = unit.status.value.upper()
                color = GREEN if unit.status == SurvivorStatus.RESCUED else PURPLE if unit.status == SurvivorStatus.INFECTED else '#77818A' if unit.status == SurvivorStatus.DEAD else COLORS.get(sid, BLUE)
            else:
                status = unit.status.value.upper()
                color = '#E76F71'
            dot.configure(fg=color)
            value.configure(text=f'{status}  ·  {pos[0]:.1f}, {pos[1]:.1f}', fg=color if status in ('RESCUED','INFECTED','DEAD') else MUTED)
        if self.sim.game_over:
            self.phase.configure(text='●  MISSION COMPLETE', fg=GREEN if m.rescued == m.survivors_started else ORANGE)
        elif self.auto:
            self.phase.configure(text='●  SIMULATION RUNNING', fg=ACCENT)
        else:
            self.phase.configure(text='●  SIMULATION PAUSED', fg=ORANGE)
        self.update_play_button()

def main(default_algorithm='A*'):
    root = tk.Tk()
    ZombieApp(root, default_algorithm=default_algorithm)
    root.mainloop()

if __name__ == '__main__':
    main()
