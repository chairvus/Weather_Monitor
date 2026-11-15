# ui/widgets.py
import customtkinter as ctk


class WeatherCard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=15, fg_color="#2b2b2b")

        self.location_label = ctk.CTkLabel(
            self,
            text="Waiting for location...",
            font=("Arial", 18, "bold"),
            wraplength=450,
            justify="center",
        )
        self.location_label.pack(pady=(20, 5))

        self.local_time_label = ctk.CTkLabel(
            self, text="", font=("Arial", 12), text_color="gray"
        )
        self.local_time_label.pack(pady=(0, 10))

        self.icon_label = ctk.CTkLabel(self, text="☁️", font=("Arial", 40))
        self.icon_label.pack()

        self.temp_label = ctk.CTkLabel(self, text="-- °C", font=("Arial", 48, "bold"))
        self.temp_label.pack()

        # NEW: This label will say "High / Low" for historical data
        self.temp_desc_label = ctk.CTkLabel(
            self, text="", font=("Arial", 12), text_color="gray"
        )
        self.temp_desc_label.pack()

        self.condition_label = ctk.CTkLabel(self, text="Waiting...", font=("Arial", 18))
        self.condition_label.pack(pady=(5, 10))

        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.pack(pady=(0, 20))

        self.humidity_label = ctk.CTkLabel(
            self.details_frame, text="Humidity: --%", text_color="gray"
        )
        self.humidity_label.pack(side="left", padx=10)

        self.wind_label = ctk.CTkLabel(
            self.details_frame, text="Wind: -- km/h", text_color="gray"
        )
        self.wind_label.pack(side="left", padx=10)

        self.feels_like_label = ctk.CTkLabel(
            self, text="Feels like: -- | UV Index: --", text_color="gray"
        )
        self.feels_like_label.pack(pady=(0, 10))

    def set_loading_state(self, location_name):
        self.location_label.configure(text=location_name)
        self.local_time_label.configure(text="Fetching weather data...")
        self.temp_label.configure(text="-- °C")
        self.temp_desc_label.configure(text="")
        self.condition_label.configure(text="Loading...")
        self.humidity_label.configure(text="Humidity: --%")
        self.wind_label.configure(text="Wind: -- km/h")
        self.feels_like_label.configure(text="Feels like: -- | UV Index: --")
        self.icon_label.configure(text="⏳")

    def update_data(self, data):
        self.location_label.configure(text=data["city"])
        self.local_time_label.configure(text=data["local_time"])
        self.condition_label.configure(text=data["condition"])
        self.wind_label.configure(text=f"Wind: {data['wind_speed']} km/h")
        self.feels_like_label.configure(
            text=f"Feels like: {data['feels_like']}{data['temp_symbol']} | UV Index: {data['uv_index']}"
        )

        if data.get("is_historical"):
            # Split the string "30.5 / 22.7" into two separate numbers
            temps = data["temp"].split("/")
            high_temp = temps[0].strip()
            low_temp = temps[1].strip()

            # Show the High temperature big, and explain it below
            self.temp_label.configure(
                text=f"{high_temp} {data['temp_symbol']}", font=("Arial", 48, "bold")
            )
            self.temp_desc_label.configure(
                text=f"Daytime High (Nighttime Low: {low_temp}{data['temp_symbol']})"
            )

            # Clean up humidity label
            self.humidity_label.configure(
                text=f"Humidity: {data['humidity']}% (Max/Min)"
            )
        else:
            # Current weather
            self.temp_label.configure(
                text=f"{data['temp']} {data['temp_symbol']}", font=("Arial", 48, "bold")
            )
            self.temp_desc_label.configure(text="Current Temperature")
            self.humidity_label.configure(text=f"Humidity: {data['humidity']}%")

        condition = data["condition"]
        if "Sunny" in condition or "Clear" in condition:
            self.icon_label.configure(text="☀️")
        elif "Rain" in condition or "Drizzle" in condition:
            self.icon_label.configure(text="🌧️")
        else:
            self.icon_label.configure(text="☁️")
