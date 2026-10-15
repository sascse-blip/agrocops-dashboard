"""
AgroCops Central Command — simulated/demo version
Uses synthetic sensor data; no Arduino, COM port, logo.png, or serial connection required.

Install dependencies:
    python -m pip install matplotlib

Run:
    python Dashboard_FakeData.py
"""

import random
import tkinter as tk
from tkinter import ttk
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------------- CONFIGURATION ----------------
GRID_ROWS = 10
GRID_COLS = 10
UPDATE_MS = 1000
GAS_WARNING = 400
GAS_CRITICAL = 1000

BG = "#121212"
PANEL = "#1e1e1e"
GRID_BG = "#242424"
GREEN = "#2e7d32"
ORANGE = "#f57c00"
RED = "#d32f2f"
GREY = "#424242"
CYAN = "#00d4ff"
WHITE = "#f4f4f4"

# A deterministic starting dataset: most sensors are normal, a few have
# warning/critical values so the dashboard has useful demo data immediately.
def make_fake_sensors():
    sensors = {}
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            gas = random.randint(240, 360)
            temp = round(random.uniform(25.0, 31.5), 1)
            humidity = round(random.uniform(55.0, 72.0), 1)
            sensors[(r, c)] = {
                "gas": gas,
                "temp": temp,
                "humidity": humidity,
                "history": deque([gas + random.randint(-18, 18) for _ in range(50)], maxlen=50),
                "timestamps": deque([""] * 49 + [datetime.now().strftime("%H:%M:%S")], maxlen=50),
                "active": True,
                "status": "NOMINAL",
            }

    # Seed visible demo alerts.
    for key in [(1, 2), (4, 7), (7, 1)]:
        sensors[key]["gas"] = random.randint(450, 650)
        sensors[key]["status"] = "WARNING"
    sensors[(3, 4)]["gas"] = random.randint(1080, 1240)
    sensors[(3, 4)]["temp"] = round(random.uniform(36.0, 40.0), 1)
    sensors[(3, 4)]["status"] = "CRITICAL"
    return sensors


def status_for(gas):
    if gas > GAS_CRITICAL:
        return "CRITICAL"
    if gas > GAS_WARNING:
        return "WARNING"
    return "NOMINAL"


def color_for(status):
    return {"NOMINAL": GREEN, "WARNING": ORANGE, "CRITICAL": RED, "OFFLINE": GREY}[status]


class SensorPopup:
    def __init__(self, parent, sensor_id, sensor):
        self.sensor_id = sensor_id
        self.sensor = sensor
        self.window = tk.Toplevel(parent)
        self.window.title(f"Sensor S-{sensor_id[0]}-{sensor_id[1]} | Details")
        self.window.geometry("850x600")
        self.window.configure(bg=BG)

        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(
            header, text=f"SENSOR S-{sensor_id[0]}-{sensor_id[1]}",
            font=("Segoe UI", 18, "bold"), bg=BG, fg=WHITE
        ).pack(side="left")
        self.status_label = tk.Label(
            header, text="", font=("Consolas", 13, "bold"), bg=BG, fg=GREEN
        )
        self.status_label.pack(side="right")

        self.metrics = tk.Frame(self.window, bg=BG)
        self.metrics.pack(fill="x", padx=18, pady=10)
        self.gas_label = self.make_metric(self.metrics, "VOC / GAS LEVEL", "0")
        self.temp_label = self.make_metric(self.metrics, "TEMPERATURE", "0 °C")
        self.hum_label = self.make_metric(self.metrics, "HUMIDITY", "0 %")

        chart_frame = tk.Frame(self.window, bg=PANEL)
        chart_frame.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        self.fig = Figure(figsize=(7.4, 3.7), dpi=100)
        self.fig.patch.set_facecolor(PANEL)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#292929")
        self.line, = self.ax.plot(
            list(range(len(sensor["history"]))), list(sensor["history"]),
            color=CYAN, linewidth=2
        )
        self.ax.set_title("Simulated Gas Level — Recent Readings", color=WHITE)
        self.ax.set_xlabel("Recent sample", color="#bbbbbb")
        self.ax.set_ylabel("Gas level", color="#bbbbbb")
        self.ax.tick_params(colors="#bbbbbb")
        self.ax.grid(True, color="#444444", linestyle="--", linewidth=0.5)
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.refresh()

    @staticmethod
    def make_metric(parent, title, value):
        frame = tk.Frame(parent, bg=PANEL, padx=18, pady=12)
        frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(frame, text=title, bg=PANEL, fg="#aaaaaa",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        label = tk.Label(frame, text=value, bg=PANEL, fg=WHITE,
                         font=("Segoe UI", 19, "bold"))
        label.pack(anchor="w", pady=(5, 0))
        return label

    def refresh(self):
        s = self.sensor
        status = status_for(s["gas"])
        self.status_label.config(text=f"STATUS: {status}", fg=color_for(status))
        self.gas_label.config(text=f'{s["gas"]} ppm')
        self.temp_label.config(text=f'{s["temp"]:.1f} °C')
        self.hum_label.config(text=f'{s["humidity"]:.1f} %')
        self.line.set_ydata(list(s["history"]))
        self.line.set_color(color_for(status) if status != "NOMINAL" else CYAN)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
        if self.window.winfo_exists():
            self.window.after(UPDATE_MS, self.refresh)


class AgroDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AgroCops — Central Command (Fake Dataset)")
        self.root.geometry("1250x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg=BG)
        self.sensors = make_fake_sensors()
        self.sensor_buttons = {}

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=22, pady=(16, 8))
        tk.Label(top, text="AGROCOPS CENTRAL COMMAND",
                 font=("Segoe UI", 23, "bold"), bg=BG, fg="#00e676").pack(anchor="w")
        tk.Label(top, text="Smart Harvest Security System • Synthetic demo data",
                 font=("Segoe UI", 10), bg=BG, fg="#aaaaaa").pack(anchor="w", pady=(2, 0))

        self.system_label = tk.Label(
            top, text="SYSTEM STATUS: MONITORING (SIMULATION MODE)",
            font=("Consolas", 12, "bold"), bg=BG, fg="#00e676"
        )
        self.system_label.pack(anchor="w", pady=(10, 0))

        self.summary_frame = tk.Frame(root, bg=BG)
        self.summary_frame.pack(fill="x", padx=22, pady=8)
        self.summary_labels = {}
        for key, title in [
            ("total", "TOTAL SENSORS"), ("nominal", "NOMINAL"),
            ("warning", "WARNING"), ("critical", "CRITICAL")
        ]:
            card = tk.Frame(self.summary_frame, bg=PANEL, padx=14, pady=10)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(card, text=title, bg=PANEL, fg="#aaaaaa",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            value = tk.Label(card, text="0", bg=PANEL, fg=WHITE,
                             font=("Segoe UI", 21, "bold"))
            value.pack(anchor="w", pady=(4, 0))
            self.summary_labels[key] = value

        controls = tk.Frame(root, bg=BG)
        controls.pack(fill="x", padx=22, pady=(8, 0))
        tk.Label(controls, text="Sensor grid (click a sensor to view details)",
                 font=("Segoe UI", 11, "bold"), bg=BG, fg=WHITE).pack(side="left")
        tk.Button(
            controls, text="Generate new demo readings", command=self.randomize_readings,
            bg="#00695c", fg="white", activebackground="#00897b",
            relief="flat", padx=12, pady=6
        ).pack(side="right")

        grid_outer = tk.Frame(root, bg=BG)
        grid_outer.pack(fill="both", expand=True, padx=22, pady=12)
        for r in range(GRID_ROWS):
            grid_outer.rowconfigure(r, weight=1)
        for c in range(GRID_COLS):
            grid_outer.columnconfigure(c, weight=1)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                sid = (r, c)
                btn = tk.Button(
                    grid_outer, text=f"S-{r}-{c}", fg="white",
                    bg=color_for(status_for(self.sensors[sid]["gas"])),
                    activeforeground="white", activebackground="#555555",
                    font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                    command=lambda sensor_id=sid: self.open_sensor(sensor_id)
                )
                btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                self.sensor_buttons[sid] = btn

        footer = tk.Label(
            root, text="Demo only: readings are randomly generated and are not connected to physical hardware.",
            bg=BG, fg="#888888", font=("Segoe UI", 9)
        )
        footer.pack(fill="x", padx=22, pady=(0, 12))
        self.update_dashboard()

    def open_sensor(self, sensor_id):
        SensorPopup(self.root, sensor_id, self.sensors[sensor_id])

    def randomize_readings(self):
        # Simulate a fresh set of measurements without waiting for the next tick.
        for sensor in self.sensors.values():
            sensor["gas"] = max(150, min(1350, sensor["gas"] + random.randint(-100, 130)))
            sensor["temp"] = round(max(20, min(45, sensor["temp"] + random.uniform(-1.2, 1.2))), 1)
            sensor["humidity"] = round(max(30, min(95, sensor["humidity"] + random.uniform(-3, 3))), 1)
            sensor["status"] = status_for(sensor["gas"])
            sensor["history"].append(sensor["gas"])
            sensor["timestamps"].append(datetime.now().strftime("%H:%M:%S"))
        self.update_dashboard()

    def update_dashboard(self):
        counts = {"NOMINAL": 0, "WARNING": 0, "CRITICAL": 0}
        for sid, sensor in self.sensors.items():
            # Smoothly vary readings to simulate live monitoring.
            if random.random() < 0.72:
                sensor["gas"] = max(150, min(1350, sensor["gas"] + random.randint(-35, 45)))
                sensor["temp"] = round(max(20, min(45, sensor["temp"] + random.uniform(-0.3, 0.3))), 1)
                sensor["humidity"] = round(max(30, min(95, sensor["humidity"] + random.uniform(-0.8, 0.8))), 1)
            sensor["status"] = status_for(sensor["gas"])
            sensor["history"].append(sensor["gas"])
            sensor["timestamps"].append(datetime.now().strftime("%H:%M:%S"))
            counts[sensor["status"]] += 1
            self.sensor_buttons[sid].configure(
                bg=color_for(sensor["status"]),
                text=f"S-{sid[0]}-{sid[1]}\n{sensor['gas']}"
            )

        self.summary_labels["total"].config(text=str(len(self.sensors)))
        self.summary_labels["nominal"].config(text=str(counts["NOMINAL"]), fg="#66bb6a")
        self.summary_labels["warning"].config(text=str(counts["WARNING"]), fg="#ffb74d")
        self.summary_labels["critical"].config(text=str(counts["CRITICAL"]), fg="#ef5350")
        self.root.after(UPDATE_MS, self.update_dashboard)


if __name__ == "__main__":
    random.seed()
    root = tk.Tk()
    app = AgroDashboard(root)
    root.mainloop()
