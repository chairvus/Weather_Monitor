# ui/app_window.py
import customtkinter as ctk
import threading
from datetime import datetime
from tkinter import messagebox
from utils.storage import (
    save_to_csv,
    save_last_location,
    load_last_location,
    save_manual_snapshot,
)
from utils.logger import log_info, log_error
from ui.widgets import WeatherCard
from config import Config
from services.weather_api import (
    search_locations_nominatim,
    fetch_weather_by_coords,
    reverse_geocode_nominatim,
)


class WeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Weather Monitor System")
        self.geometry("750x850")
        ctk.set_appearance_mode("dark")

        self._refresh_timer = None
        self._found_locations = []
        self.current_unit = "celsius"
        self._last_data = None
        self._dropdown_map = {}

        self.title_label = ctk.CTkLabel(
            self, text="Weather Dashboard", font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=15)

        # --- Search Frame ---
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(pady=5)

        self.city_entry = ctk.CTkEntry(
            self.search_frame, placeholder_text="Enter location...", width=200
        )
        self.city_entry.pack(side="left", padx=5)
        self.city_entry.bind("<Return>", lambda event: self.on_search_click())

        self.date_entry = ctk.CTkEntry(
            self.search_frame, placeholder_text="YYYY-MM-DD (Optional)", width=160
        )
        self.date_entry.pack(side="left", padx=5)
        self.date_entry.bind("<Return>", lambda event: self.on_search_click())

        self.search_btn = ctk.CTkButton(
            self.search_frame, text="Search", width=70, command=self.on_search_click
        )
        self.search_btn.pack(side="left", padx=5)

        self.unit_btn = ctk.CTkButton(
            self.search_frame,
            text="°C / °F",
            width=60,
            fg_color="#444444",
            hover_color="#555555",
            command=self.toggle_unit,
        )
        self.unit_btn.pack(side="left", padx=5)

        # --- Location Selection Dropdown ---
        self._menu_font = ctk.CTkFont(size=12)  # popup list
        self._bar_font = ctk.CTkFont(size=12)  # text inside the bar
        self._selected_loc = None
        self._resize_job = None

        self.location_dropdown = ctk.CTkComboBox(
            self,
            values=[],
            state="disabled",
            command=self.on_dropdown_changed,
            font=self._bar_font,
            dropdown_font=self._menu_font,
        )
        self.location_dropdown.pack(fill="x", padx=40, pady=10)
        self.bind("<Configure>", self._on_window_resize)

        # --- Weather Card ---
        self.weather_card = WeatherCard(self)
        self.weather_card.pack(fill="x", padx=40, pady=10)

        # --- Bottom Buttons ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(side="bottom", pady=20)

        self.save_btn = ctk.CTkButton(
            self.bottom_frame,
            text="💾 Save Snapshot",
            width=150,
            fg_color="green",
            hover_color="darkgreen",
            command=self.manual_save,
        )
        self.save_btn.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            self, text="Status: Waiting...", text_color="gray"
        )
        self.status_label.pack(side="bottom")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.load_previous_session)

    # ---------- dropdown text helpers ----------
    def _max_text_px(self):
        width = self.winfo_width()
        if width <= 1:  # window not mapped yet
            width = 750
        # window width - side padding (2*40) - arrow button/inner padding
        return max(150, width - 80 - 50)

    def _fit_text(self, text):
        """Show the full address in the bar: shrink the font a little first,
        and only cut with an ellipsis if it still doesn't fit."""
        max_px = self._max_text_px()
        for size in (12, 11, 10):
            self._bar_font.configure(size=size)
            if self._bar_font.measure(text) <= max_px:
                return text
        ell = "…"
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._bar_font.measure(text[:mid] + ell) <= max_px:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo].rstrip() + ell

    def _wrap_text(self, text):
        """Word-wrap the full address so the popup never exceeds the window."""
        max_px = self._max_text_px()
        lines, line = [], ""
        for word in text.split(" "):
            candidate = f"{line} {word}".strip()
            if line and self._menu_font.measure(candidate) > max_px:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return "\n".join(lines)

    def _rebuild_dropdown(self):
        if not self._found_locations:
            return
        state = self.location_dropdown.cget("state")
        self._dropdown_map = {
            self._wrap_text(loc["full_address"]): loc for loc in self._found_locations
        }
        self.location_dropdown.configure(
            state="normal", values=list(self._dropdown_map.keys())
        )
        if self._selected_loc:
            self.location_dropdown.set(
                self._fit_text(self._selected_loc["full_address"])
            )
        self.location_dropdown.configure(state=state)

    def _on_window_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(150, self._rebuild_dropdown)

    # ---------- session / controls ----------
    @staticmethod
    def _looks_truncated(text):
        return text.rstrip().endswith(("...", "…"))

    def load_previous_session(self):
        last_loc = load_last_location()
        if not last_loc:
            return

        if "full_address" not in last_loc:
            last_loc["full_address"] = last_loc.get("name", "Unknown Location")

        self.status_label.configure(text="Status: Restoring...", text_color="yellow")

        # The saved location may come from an older version that stored a
        # shortened address ("Bantul, Daerah Istimewa Yogyakar..."). Rebuild the
        # full address from the saved coordinates instead of showing it as-is.
        if self._looks_truncated(last_loc["full_address"]):
            threading.Thread(
                target=self._worker_heal_address, args=(last_loc,), daemon=True
            ).start()
        else:
            self._finish_restore(last_loc, None)

    def _worker_heal_address(self, loc):
        full = reverse_geocode_nominatim(loc["latitude"], loc["longitude"])
        self.after(0, self._finish_restore, loc, full)

    def _finish_restore(self, loc, full_address):
        if full_address:
            loc["full_address"] = full_address
            loc["label"] = full_address
            loc["name"] = full_address

        self.city_entry.delete(0, "end")
        self.city_entry.insert(0, loc.get("name", ""))
        self._found_locations = [loc]
        self._selected_loc = loc
        self._rebuild_dropdown()
        self.on_location_selected(loc)  # also re-saves the healed location

    def toggle_unit(self):
        self.current_unit = (
            "fahrenheit" if self.current_unit == "celsius" else "celsius"
        )
        if self._selected_loc:
            self.on_location_selected(self._selected_loc)

    def manual_save(self):
        if not self._last_data:
            messagebox.showwarning("No Data", "Please fetch weather data first.")
            return
        success = save_manual_snapshot(self._last_data)
        if success:
            self.status_label.configure(
                text="Status: Snapshot saved successfully!", text_color="green"
            )

    def cancel_refresh_timer(self):
        if self._refresh_timer is not None:
            self.after_cancel(self._refresh_timer)
            self._refresh_timer = None

    # ---------- search ----------
    def on_search_click(self):
        query = self.city_entry.get().strip()
        date_query = self.date_entry.get().strip()

        if not query:
            self.status_label.configure(
                text="Status: Error - Please enter a location", text_color="red"
            )
            return

        if date_query:
            try:
                selected_date = datetime.strptime(date_query, "%Y-%m-%d").date()
                today = datetime.now().date()
                if selected_date > today:
                    self.status_label.configure(
                        text="Status: Error - Cannot fetch future dates.",
                        text_color="red",
                    )
                    return
            except ValueError:
                self.status_label.configure(
                    text="Status: Error - Date must be YYYY-MM-DD", text_color="red"
                )
                return

        self.status_label.configure(
            text="Status: Searching locations...", text_color="yellow"
        )
        self.search_btn.configure(state="disabled")
        self.location_dropdown.configure(state="disabled", values=[])
        self.cancel_refresh_timer()

        threading.Thread(target=self._worker_search, args=(query,), daemon=True).start()

    def _worker_search(self, query):
        locations = search_locations_nominatim(query)
        self.after(0, self._update_search_results, locations)

    def _update_search_results(self, locations):
        self.search_btn.configure(state="normal")

        if not locations:
            self.status_label.configure(
                text="Status: No locations found.", text_color="red"
            )
            return

        self._found_locations = locations
        self._selected_loc = locations[0]
        self._rebuild_dropdown()
        self.on_location_selected(locations[0])

    def on_dropdown_changed(self, selected_label):
        loc = self._dropdown_map.get(selected_label)
        if not loc:
            return
        self._selected_loc = loc
        # CTkComboBox put the wrapped (multi-line) text in the bar; replace it
        self.location_dropdown.set(self._fit_text(loc["full_address"]))
        self.on_location_selected(loc)

    def on_location_selected(self, selected_loc):
        if not selected_loc:
            return

        self._selected_loc = selected_loc
        date_query = self.date_entry.get().strip() or None

        self.status_label.configure(text="Status: FETCHING...", text_color="yellow")
        self.search_btn.configure(state="disabled")
        self.location_dropdown.configure(state="disabled")
        self.cancel_refresh_timer()

        save_last_location(selected_loc)

        # Use FULL address for the Weather Card display
        display_name = selected_loc.get(
            "full_address", selected_loc.get("name", "Unknown Location")
        )
        self.weather_card.set_loading_state(display_name)

        threading.Thread(
            target=self._worker_fetch_weather,
            args=(
                selected_loc["latitude"],
                selected_loc["longitude"],
                display_name,
                self.current_unit,
                date_query,
            ),
            daemon=True,
        ).start()

    # ---------- weather fetch ----------
    def _worker_fetch_weather(self, lat, lon, location_name, unit, date_str):
        try:
            data = fetch_weather_by_coords(lat, lon, location_name, unit, date_str)
            self.after(0, self.update_gui_success, data)
        except Exception as e:
            self.after(0, self.update_gui_error, str(e))

    def update_gui_success(self, data):
        self._last_data = data
        self.weather_card.update_data(data)
        self.status_label.configure(text="Status: OK", text_color="green")
        self.search_btn.configure(state="normal")
        self.location_dropdown.configure(state="normal")

        log_info(f"GUI updated for {data['city']}")
        save_to_csv(data)

        if not data.get("is_historical"):
            self._refresh_timer = self.after(
                Config.REFRESH_INTERVAL * 1000,
                lambda: self.on_location_selected(self._selected_loc),
            )

    def update_gui_error(self, error_msg):
        self.status_label.configure(text=f"Error: {error_msg}", text_color="red")
        self.search_btn.configure(state="normal")
        self.location_dropdown.configure(state="normal")
        log_error(f"GUI encountered error: {error_msg}")

    def on_close(self):
        log_info("Application closing. Cleaning up...")
        self.cancel_refresh_timer()
        if self._resize_job:
            self.after_cancel(self._resize_job)
            self._resize_job = None
        for after_id in self.tk.call("after", "info"):
            self.after_cancel(after_id)
        self.destroy()
