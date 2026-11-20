
print("FLEET SYSTEM STARTING...")

import os
import shutil
import filecmp
from datetime import datetime
import math

from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.image import Image
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

import fleet_core

print("BACKEND FILE:", fleet_core.__file__)

print(
    "DELETE FUNCTION AVAILABLE:",
    hasattr(fleet_core, "delete_maintenance_record")
)

class FleetApp(App):


    def build(self):

        self.title = "Fleet Management System"

        self.root_layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        header = Label(
            text="VEHICLE & FLEET MANAGEMENT",
            font_size="19sp",
            bold=True,
            size_hint_y=None,
            height=dp(65)
        )

        self.root_layout.add_widget(header)

        navigation = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Vehicles", self.show_vehicles),
            ("Drivers", self.show_drivers),
            ("Trips", self.show_trips),
            ("Maintenance", self.show_maintenance),
            ("Reports", self.show_reports)
        ]

        for text, action in buttons:

            button = Button(
                text=text,
                font_size="10sp"
            )

            button.bind(on_release=action)

            navigation.add_widget(button)

        self.root_layout.add_widget(navigation)

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8)
        )

        self.root_layout.add_widget(self.content)

        # =================================
        # APK STORAGE CONFIGURATION
        # =================================

        if os.environ.get("ANDROID_ARGUMENT"):
            fleet_core.configure_storage(self.user_data_dir)

        self.show_dashboard()

        return self.root_layout

    # =====================================
    # DASHBOARD
    # =====================================

  
    
    
    def show_dashboard(self, *args):

        self.content.clear_widgets()

        try:

            # =================================
            # LOAD FLEET RECORDS
            # =================================

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            drivers = fleet_core.read_records(
                fleet_core.DRIVERS_FILE
            )

            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            maintenance = fleet_core.read_records(
                fleet_core.MAINTENANCE_FILE
            )

            if any(
                records is None
                for records in [
                    vehicles,
                    drivers,
                    trips,
                    maintenance
                ]
            ):
                raise ValueError(
                    "Fleet records could not be loaded."
                )

            # =================================
            # FLEET STATISTICS
            # =================================

            total_vehicles = len(vehicles)
            total_drivers = len(drivers)
            total_trips = len(trips)
            total_maintenance = len(maintenance)

            # =================================
            # DASHBOARD HEADING
            # =================================

            self.add_heading("FLEET OVERVIEW")

            # =================================
            # FLEET BANNER IMAGE
            # =================================

            banner_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "fleet_banner.png"
            )

            if not os.path.isfile(banner_path):
                raise FileNotFoundError(
                    "fleet_banner.png was not found "
                    "in the FleetAndroid folder."
                )

            banner = Image(
                source=banner_path,
                size_hint=(1, None),
                height=dp(230),
                allow_stretch=True,
                keep_ratio=False
            )

            self.content.add_widget(banner)

            # =================================
            # SYSTEM STATUS
            # =================================

            status_label = Label(
                text="● SYSTEM STATUS: CONNECTED",
                size_hint_y=None,
                height=dp(35),
                bold=True,
                font_size="14sp",
                color=(0.1, 0.85, 0.75, 1),
                halign="left",
                valign="middle"
            )

            status_container = BoxLayout(
                size_hint_y=None,
                height=dp(42),
                padding=[dp(10), dp(3)]
            )

            with status_container.canvas.before:

                Color(0.04, 0.18, 0.16, 1)

                status_background = RoundedRectangle(
                    pos=status_container.pos,
                    size=status_container.size,
                    radius=[dp(10)]
                )

            status_container.bind(
                pos=lambda instance, value: setattr(
                    status_background, "pos", value
                ),
                size=lambda instance, value: setattr(
                    status_background, "size", value
                )
            )

            status_container.add_widget(status_label)

            self.content.add_widget(status_container)

            # =================================
            # STATISTICS GRID
            # =================================

            statistics_grid = GridLayout(
                cols=2,
                spacing=dp(10),
                size_hint_y=None,
                height=dp(220),
                padding=dp(5)
            )

            statistics = [
                ("VEHICLES", total_vehicles),
                ("DRIVERS", total_drivers),
                ("TRIPS", total_trips),
                ("MAINTENANCE", total_maintenance)
            ]

            # =================================
            # STATISTIC CARDS
            # =================================

            for title, value in statistics:

                card = BoxLayout(
                    orientation="vertical",
                    padding=dp(12),
                    spacing=dp(8)
                )

                with card.canvas.before:

                    Color(0.07, 0.13, 0.23, 1)

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(14)]
                    )

                card.bind(
                    pos=lambda instance, value, bg=background:
                    setattr(bg, "pos", value),

                    size=lambda instance, value, bg=background:
                    setattr(bg, "size", value)
                )

                card.add_widget(
                    Label(
                        text=title,
                        bold=True,
                        font_size="14sp",
                        color=(0.65, 0.78, 0.88, 1)
                    )
                )

                card.add_widget(
                    Label(
                        text=str(value),
                        bold=True,
                        font_size="28sp",
                        color=(0.1, 0.85, 0.75, 1)
                    )
                )

                statistics_grid.add_widget(card)

            self.content.add_widget(statistics_grid)

        except Exception as error:

            self.add_information(
                "DASHBOARD ERROR\n\n" + str(error)
            )



    def show_reports(self, *args):

        try:

            self.content.clear_widgets()

            self.add_heading("FLEET REPORTS & ANALYTICS")

            # ==========================================
            # LOAD FLEET DATA
            # ==========================================

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            drivers = fleet_core.read_records(
                fleet_core.DRIVERS_FILE
            )

            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            if any(
                records is None
                for records in [vehicles, drivers, trips]
            ):

                raise ValueError(
                    "Fleet records could not be loaded."
                )

            # ==========================================
            # CALCULATE FLEET STATISTICS
            # ==========================================

            total_fuel = 0.0
            total_cost = 0.0

            vehicle_trips = {}
            driver_trips = {}
            monthly_reports = {}

            invalid_fuel_records = 0
            invalid_cost_records = 0
            invalid_date_records = 0

            for trip in trips:

                try:

                    fuel = float(
                        trip.get("fuel_litres", 0)
                    )

                    total_fuel += fuel

                except (ValueError, TypeError):

                    fuel = 0.0
                    invalid_fuel_records += 1

                try:

                    cost = float(
                        trip.get("fuel_cost_mwk", 0)
                    )

                    total_cost += cost

                except (ValueError, TypeError):

                    cost = 0.0
                    invalid_cost_records += 1

                registration = (
                    trip.get("registration", "").strip()
                    or "Unspecified"
                )

                driver = (
                    trip.get("driver", "").strip()
                    or "Unspecified"
                )

                vehicle_trips[registration] = (
                    vehicle_trips.get(registration, 0) + 1
                )

                driver_trips[driver] = (
                    driver_trips.get(driver, 0) + 1
                )

                try:

                    trip_date = datetime.strptime(
                        trip.get("trip_date", ""),
                        "%d/%m/%Y"
                    )

                    month_key = trip_date.strftime("%B %Y")

                    if month_key not in monthly_reports:

                        monthly_reports[month_key] = {
                            "trips": 0,
                            "fuel": 0.0,
                            "cost": 0.0,
                            "sort_date": trip_date.replace(day=1)
                        }

                    monthly_reports[month_key]["trips"] += 1
                    monthly_reports[month_key]["fuel"] += fuel
                    monthly_reports[month_key]["cost"] += cost

                except (ValueError, TypeError):

                    invalid_date_records += 1

            # ==========================================
            # REPORT SCROLL AREA
            # ==========================================

            scroll = ScrollView(
                do_scroll_x=False
            )

            report_layout = BoxLayout(
                orientation="vertical",
                spacing=dp(12),
                padding=dp(8),
                size_hint_y=None
            )

            report_layout.bind(
                minimum_height=report_layout.setter("height")
            )

            # ==========================================
            # REPORT SECTION HELPER
            # ==========================================

            def add_report_section(title, body):

                lines = max(
                    len(body.splitlines()),
                    1
                )

                card_height = dp(65 + lines * 23)

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(6),
                    padding=dp(12),
                    size_hint_y=None,
                    height=card_height
                )

                with card.canvas.before:

                    Color(
                        0.055, 0.105, 0.19, 1
                    )

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(12)]
                    )

                card.bind(
                    pos=lambda instance, value:
                    setattr(background, "pos", value)
                )

                card.bind(
                    size=lambda instance, value:
                    setattr(background, "size", value)
                )

                heading = Label(
                    text=title,
                    color=(0.35, 0.85, 0.82, 1),
                    bold=True,
                    font_size="16sp",
                    size_hint_y=None,
                    height=dp(30),
                    halign="left",
                    valign="middle"
                )

                heading.bind(
                    size=lambda instance, value:
                    setattr(instance, "text_size", value)
                )

                details = Label(
                    text=body,
                    color=(0.85, 0.90, 0.96, 1),
                    font_size="13sp",
                    size_hint_y=None,
                    height=card_height - dp(55),
                    halign="left",
                    valign="top"
                )

                details.bind(
                    size=lambda instance, value:
                    setattr(
                        instance,
                        "text_size",
                        (value[0], None)
                    )
                )

                card.add_widget(heading)
                card.add_widget(details)

                report_layout.add_widget(card)

            # ==========================================
            # FLEET SUMMARY CARDS
            # ==========================================

            summary_heading = Label(
                text="FLEET PERFORMANCE OVERVIEW",
                color=(0.65, 0.78, 0.88, 1),
                bold=True,
                font_size="16sp",
                size_hint_y=None,
                height=dp(38)
            )

            report_layout.add_widget(summary_heading)

            summary_grid = GridLayout(
                cols=2,
                spacing=dp(10),
                padding=dp(3),
                size_hint_y=None,
                height=dp(240)
            )

            summary_grid.bind(
                minimum_height=summary_grid.setter("height")
            )

            summary_items = [
                ("TOTAL VEHICLES", str(len(vehicles))),
                ("TOTAL DRIVERS", str(len(drivers))),
                ("RECORDED TRIPS", str(len(trips))),
                (
                    "FUEL CONSUMED",
                    f"{total_fuel:,.2f} L"
                )
            ]

            for title, value in summary_items:

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(5),
                    padding=dp(10),
                    size_hint_y=None,
                    height=dp(105)
                )

                with card.canvas.before:

                    Color(
                        0.055, 0.105, 0.19, 1
                    )

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(12)]
                    )

                card.bind(
                    pos=lambda instance, value, shape=background:
                    setattr(shape, "pos", value)
                )

                card.bind(
                    size=lambda instance, value, shape=background:
                    setattr(shape, "size", value)
                )

                card.add_widget(
                    Label(
                        text=title,
                        color=(0.65, 0.78, 0.88, 1),
                        font_size="11sp",
                        bold=True
                    )
                )

                card.add_widget(
                    Label(
                        text=value,
                        color=(0.1, 0.85, 0.75, 1),
                        font_size="22sp",
                        bold=True
                    )
                )

                summary_grid.add_widget(card)

            report_layout.add_widget(summary_grid)

            # ==========================================
            # FUEL EXPENDITURE
            # ==========================================

            add_report_section(
                "FUEL EXPENDITURE",
                (
                    f"Total fuel consumed: "
                    f"{total_fuel:,.2f} litres\n"
                    f"Total fuel expenditure: "
                    f"MWK {total_cost:,.2f}"
                )
            )

            # ==========================================
            # MONTHLY FLEET PERFORMANCE
            # ==========================================

            add_report_section(
                "MONTHLY FLEET PERFORMANCE",
                "Monthly trip, fuel and expenditure summaries"
            )

            if monthly_reports:

                sorted_months = sorted(
                    monthly_reports.items(),
                    key=lambda item: item[1]["sort_date"],
                    reverse=True
                )

                for month, data in sorted_months:

                    add_report_section(
                        month.upper(),
                        (
                            f"Total trips: {data['trips']}\n"
                            f"Fuel consumed: "
                            f"{data['fuel']:,.2f} litres\n"
                            f"Fuel expenditure: "
                            f"MWK {data['cost']:,.2f}"
                        )
                    )

            else:

                add_report_section(
                    "MONTHLY REPORT",
                    "No valid trip dates available."
                )

            # ==========================================
            # VEHICLE PERFORMANCE
            # ==========================================

            vehicle_text = ""

            if vehicle_trips:

                for registration, count in sorted(
                    vehicle_trips.items(),
                    key=lambda item: item[1],
                    reverse=True
                ):

                    vehicle_text += (
                        f"{registration}: {count} trips\n"
                    )

            else:

                vehicle_text = "No vehicle trip records."

            add_report_section(
                "TRIPS BY VEHICLE",
                vehicle_text.strip()
            )

            # ==========================================
            # DRIVER PERFORMANCE
            # ==========================================

            driver_text = ""

            if driver_trips:

                for driver, count in sorted(
                    driver_trips.items(),
                    key=lambda item: item[1],
                    reverse=True
                ):

                    driver_text += (
                        f"{driver}: {count} trips\n"
                    )

            else:

                driver_text = "No driver trip records."

            add_report_section(
                "TRIPS BY DRIVER",
                driver_text.strip()
            )

            # ==========================================
            # DATA QUALITY
            # ==========================================

            if (
                invalid_fuel_records
                or invalid_cost_records
                or invalid_date_records
            ):

                add_report_section(
                    "DATA QUALITY NOTES",
                    (
                        f"Invalid fuel entries: "
                        f"{invalid_fuel_records}\n"
                        f"Invalid cost entries: "
                        f"{invalid_cost_records}\n"
                        f"Invalid trip dates: "
                        f"{invalid_date_records}"
                    )
                )

            else:

                add_report_section(
                    "DATA QUALITY",
                    "No invalid fuel, cost or trip date entries detected."
                )

            # ==========================================
            # ADD REPORT CONTENT
            # ==========================================

            scroll.add_widget(report_layout)

            self.content.add_widget(scroll)

            # ==========================================
            # BACK TO DASHBOARD
            # ==========================================

            back_button = Button(
                text="BACK TO DASHBOARD",
                size_hint_y=None,
                height=dp(50)
            )

            back_button.bind(
                on_release=self.show_dashboard
            )

            self.content.add_widget(back_button)

        except Exception as error:

            self.content.clear_widgets()

            self.add_heading("REPORTS ERROR")

            self.add_information(
                "Unable to generate fleet reports.\n\n"
                + str(error)
            )

        
            
    # =====================================
    # VEHICLE REGISTER
    # =====================================




    def show_vehicles(self, *args):

        self.content.clear_widgets()

        self.add_heading("REGISTERED VEHICLES")

        add_button = Button(
            text="+ ADD VEHICLE",
            size_hint_y=None,
            height=dp(48),
            background_color=(0.05, 0.55, 0.65, 1)
        )

        add_button.bind(
            on_release=self.show_add_vehicle
        )

        self.content.add_widget(add_button)

        try:

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            if vehicles is None:
                raise ValueError(
                    "Vehicle records could not be read."
                )

            if not vehicles:

                self.add_information(
                    "No vehicles registered."
                )

                return

            scroll = ScrollView(
                do_scroll_x=False
            )

            vehicle_list = BoxLayout(
                orientation="vertical",
                spacing=dp(10),
                padding=dp(5),
                size_hint_y=None
            )

            vehicle_list.bind(
                minimum_height=vehicle_list.setter(
                    "height"
                )
            )

            for index, vehicle in enumerate(vehicles, 1):

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(8),
                    padding=dp(10),
                    size_hint_y=None,
                    height=dp(205)
                )

                with card.canvas.before:

                    Color(0.04, 0.10, 0.20, 1)

                    card.background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(12)]
                    )

                card.bind(
                    pos=lambda instance, value:
                    setattr(
                        instance.background,
                        "pos",
                        value
                    ),

                    size=lambda instance, value:
                    setattr(
                        instance.background,
                        "size",
                        value
                    )
                )

                details = Label(
                    text=(
                        f"VEHICLE {index}\n\n"
                        f"Registration: {vehicle['registration']}\n"
                        f"Vehicle Type: {vehicle['vehicle_type']}\n"
                        f"Licence Category: {vehicle['licence_category']}\n"
                        f"Next Service: {vehicle['next_service_date']}"
                    ),
                    color=(0.75, 0.85, 0.95, 1),
                    font_size="13sp",
                    halign="left",
                    valign="middle"
                )

                details.bind(
                    size=lambda instance, value:
                    setattr(
                        instance,
                        "text_size",
                        value
                    )
                )

                card.add_widget(details)

                # VEHICLE ACTION BUTTONS

                action_row = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(8),
                    size_hint_y=None,
                    height=dp(42)
                )

                selected_vehicle = dict(vehicle)

                # EDIT BUTTON

                edit_button = Button(
                    text="EDIT VEHICLE",
                    background_color=(
                        0.05, 0.55, 0.65, 1
                    )
                )

                edit_button.bind(
                    on_release=lambda instance,
                    selected=selected_vehicle:
                    self.show_edit_vehicle(selected)
                )

                action_row.add_widget(edit_button)

                # DELETE BUTTON

                delete_button = Button(
                    text="DELETE",
                    background_color=(
                        0.75, 0.12, 0.12, 1
                    )
                )

                delete_button.bind(
                    on_release=lambda instance,
                    selected=selected_vehicle:
                    self.confirm_delete_vehicle(selected)
                )

                action_row.add_widget(delete_button)

                card.add_widget(action_row)

                vehicle_list.add_widget(card)

            scroll.add_widget(vehicle_list)

            self.content.add_widget(scroll)

        except Exception as error:

            self.add_information(
                "VEHICLE DISPLAY FAILED\n\n"
                + str(error)
            )

    # =====================================
    # MAINTENANCE REGISTER
    # =====================================

    
    def show_maintenance(self, *args):

        self.content.clear_widgets()

        # =================================
        # MAINTENANCE HEADING
        # =================================

        self.add_heading("MAINTENANCE MANAGEMENT")

        self.add_information(
            "VEHICLE SERVICE REGISTER"
        )

        # =================================
        # ADD MAINTENANCE BUTTON
        # =================================

        add_button = Button(
            text="+ RECORD NEW SERVICE",
            size_hint_y=None,
            height=dp(50),
            bold=True,
            font_size="15sp",
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.02, 0.55, 0.50, 1)
        )

        add_button.bind(
            on_release=self.show_add_maintenance
        )

        self.content.add_widget(add_button)

        # =================================
        # LOAD MAINTENANCE RECORDS
        # =================================

        try:

            records = fleet_core.read_records(
                fleet_core.MAINTENANCE_FILE
            )

            if records is None:

                raise ValueError(
                    "Maintenance records could not be read."
                )

            if not records:

                self.add_information(
                    "NO MAINTENANCE RECORDS FOUND"
                )

                return

            # =================================
            # SCROLL CONTAINER
            # =================================

            scroll = ScrollView(
                do_scroll_x=False
            )

            record_list = BoxLayout(
                orientation="vertical",
                spacing=dp(12),
                size_hint_y=None,
                padding=[dp(4), dp(8)]
            )

            record_list.bind(
                minimum_height=record_list.setter("height")
            )

            # =================================
            # MAINTENANCE CARDS
            # =================================

            for index, record in enumerate(records, 1):

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(6),
                    padding=dp(10),
                    size_hint_y=None,
                    height=dp(230)
                )

                # CARD BACKGROUND

                with card.canvas.before:

                    Color(0.07, 0.13, 0.23, 1)

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(14)]
                    )

                card.bind(
                    pos=lambda instance, value, bg=background:
                    setattr(bg, "pos", value),

                    size=lambda instance, value, bg=background:
                    setattr(bg, "size", value)
                )

                # =================================
                # SERVICE DETAILS
                # =================================

                details = (
                    f"SERVICE RECORD {index}\n\n"
                    f"Reference: {record['maintenance_reference']}\n"
                    f"Service Date: {record['service_date']}\n"
                    f"Vehicle: {record['registration']}\n"
                    f"Description: {record['service_description']}\n"
                    f"Maintenance Cost: MWK {record['maintenance_cost_mwk']}\n"
                    f"Next Service: {record['next_service_date']}"
                )

                details_label = Label(
                    text=details,
                    font_size="13sp",
                    color=(0.85, 0.92, 1, 1),
                    halign="left",
                    valign="middle"
                )

                details_label.bind(
                    size=lambda instance, value:
                    setattr(instance, "text_size", value)
                )

                card.add_widget(details_label)

                # =================================
                # ACTION BUTTONS
                # =================================

                action_buttons = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(8),
                    size_hint_y=None,
                    height=dp(45)
                )

                # EDIT SERVICE

                edit_button = Button(
                    text="EDIT SERVICE",
                    size_hint_x=0.5,
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.02, 0.55, 0.50, 1)
                )

                edit_button.bind(
                    on_release=lambda instance, ref=record[
                        "maintenance_reference"
                    ]: self.show_edit_maintenance(ref)
                )

                # DELETE SERVICE

                delete_button = Button(
                    text="DELETE SERVICE",
                    size_hint_x=0.5,
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.75, 0.12, 0.16, 1)
                )

                delete_button.bind(
                    on_release=lambda instance, ref=record[
                        "maintenance_reference"
                    ]: self.confirm_delete_maintenance(ref)
                )

                action_buttons.add_widget(edit_button)
                action_buttons.add_widget(delete_button)

                card.add_widget(action_buttons)

                record_list.add_widget(card)

            # =================================
            # DISPLAY MAINTENANCE RECORDS
            # =================================

            scroll.add_widget(record_list)

            self.content.add_widget(scroll)

        except Exception as error:

            self.add_information(
                "MAINTENANCE DISPLAY FAILED\n\n"
                + str(error)
            )

    # =====================================
    # ADD MAINTENANCE FORM
    # =====================================

    def show_add_maintenance(self, *args):

        self.content.clear_widgets()

        self.add_heading("RECORD VEHICLE SERVICE")

        try:

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            if vehicles is None:

                raise ValueError(
                    "Vehicle records could not be loaded."
                )

            if not vehicles:

                self.add_information(
                    "No registered vehicles available."
                )

                return

            scroll = ScrollView()

            form = BoxLayout(
                orientation="vertical",
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(5)
            )

            form.bind(
                minimum_height=form.setter("height")
            )

            self.maintenance_inputs = {}

            # VEHICLE SELECTION

            form.add_widget(
                Label(
                    text="Select Vehicle Registration",
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            vehicle_options = [
                vehicle["registration"].strip().upper()
                for vehicle in vehicles
            ]

            from kivy.uix.spinner import Spinner

            vehicle_spinner = Spinner(
                text="Select vehicle",
                values=vehicle_options,
                size_hint_y=None,
                height=dp(48)
            )

            self.maintenance_inputs["registration"] = vehicle_spinner

            form.add_widget(vehicle_spinner)

            # OTHER MAINTENANCE FIELDS

            fields = [
                (
                    "service_date",
                    "Service date",
                    "DD/MM/YYYY"
                ),
                (
                    "service_description",
                    "Service description",
                    "Describe the work performed"
                ),
                (
                    "maintenance_cost_mwk",
                    "Maintenance cost (MWK)",
                    "Enter maintenance cost"
                ),
                (
                    "next_service_date",
                    "Next service date",
                    "DD/MM/YYYY"
                )
            ]

            for key, label_text, hint in fields:

                form.add_widget(
                    Label(
                        text=label_text,
                        size_hint_y=None,
                        height=dp(30)
                    )
                )

                field = TextInput(
                    hint_text=hint,
                    multiline=False,
                    size_hint_y=None,
                    height=dp(48),
                    font_size="16sp"
                )

                self.maintenance_inputs[key] = field

                form.add_widget(field)

            # SAVE BUTTON

            save_button = Button(
                text="SAVE SERVICE RECORD",
                size_hint_y=None,
                height=dp(50)
            )

            save_button.bind(
                on_release=self.save_new_maintenance
            )

            form.add_widget(save_button)

            # CANCEL BUTTON

            cancel_button = Button(
                text="CANCEL",
                size_hint_y=None,
                height=dp(45)
            )

            cancel_button.bind(
                on_release=self.show_maintenance
            )

            form.add_widget(cancel_button)

            scroll.add_widget(form)

            self.content.add_widget(scroll)

        except Exception as error:

            self.add_information(
                "MAINTENANCE FORM ERROR\n\n" + str(error)
            )

    # ==========================================
    # EDIT MAINTENANCE RECORD
    # ==========================================

    def show_edit_maintenance(self, reference):

        self.content.clear_widgets()

        self.add_heading("EDIT VEHICLE SERVICE")

        try:

            maintenance = fleet_core.read_records(
                fleet_core.MAINTENANCE_FILE
            )

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            if maintenance is None or vehicles is None:

                raise ValueError(
                    "Required records could not be loaded."
                )

            matches = [
                record for record in maintenance
                if record["maintenance_reference"].strip().upper()
                == reference.strip().upper()
            ]

            if len(matches) != 1:

                raise ValueError(
                    "Maintenance record was not found or is duplicated."
                )

            record = matches[0]

            if not vehicles:

                raise ValueError(
                    "No registered vehicles are available."
                )

            scroll = ScrollView()

            form = BoxLayout(
                orientation="vertical",
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(5)
            )

            form.bind(
                minimum_height=form.setter("height")
            )

            self.maintenance_inputs = {}

            self.editing_maintenance_reference = reference

            # REFERENCE DISPLAY

            form.add_widget(
                Label(
                    text="Reference: " + reference,
                    size_hint_y=None,
                    height=dp(35)
                )
            )

            # VEHICLE SELECTION

            form.add_widget(
                Label(
                    text="Vehicle Registration",
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            from kivy.uix.spinner import Spinner

            vehicle_options = [
                vehicle["registration"].strip().upper()
                for vehicle in vehicles
            ]

            vehicle_spinner = Spinner(
                text=record["registration"].strip().upper(),
                values=vehicle_options,
                size_hint_y=None,
                height=dp(48)
            )

            self.maintenance_inputs["registration"] = vehicle_spinner

            form.add_widget(vehicle_spinner)

            # OTHER FIELDS

            fields = [
                (
                    "service_date",
                    "Service Date",
                    "DD/MM/YYYY"
                ),
                (
                    "service_description",
                    "Service Description",
                    "Describe the work performed"
                ),
                (
                    "maintenance_cost_mwk",
                    "Maintenance Cost (MWK)",
                    "Enter maintenance cost"
                ),
                (
                    "next_service_date",
                    "Next Service Date",
                    "DD/MM/YYYY"
                )
            ]

            for key, label_text, hint in fields:

                form.add_widget(
                    Label(
                        text=label_text,
                        size_hint_y=None,
                        height=dp(30)
                    )
                )

                field = TextInput(
                    text=record[key],
                    hint_text=hint,
                    multiline=False,
                    size_hint_y=None,
                    height=dp(48),
                    font_size="16sp"
                )

                self.maintenance_inputs[key] = field

                form.add_widget(field)

            # UPDATE BUTTON

            update_button = Button(
                text="UPDATE SERVICE RECORD",
                size_hint_y=None,
                height=dp(50)
            )

            update_button.bind(
                on_release=self.save_edited_maintenance
            )

            form.add_widget(update_button)

            # CANCEL BUTTON

            cancel_button = Button(
                text="CANCEL",
                size_hint_y=None,
                height=dp(45)
            )

            cancel_button.bind(
                on_release=self.show_maintenance
            )

            form.add_widget(cancel_button)

            scroll.add_widget(form)

            self.content.add_widget(scroll)

        except Exception as error:

            self.add_information(
                "EDIT MAINTENANCE ERROR\n\n" + str(error)
            )


    # ==========================================
    # SAVE EDITED MAINTENANCE RECORD
    # ==========================================

    def save_edited_maintenance(self, *args):

        if not hasattr(self, "maintenance_inputs"):

            self.show_message(
                "EDIT ERROR",
                "Maintenance editing form is unavailable."
            )
            return

        reference = getattr(
            self,
            "editing_maintenance_reference",
            ""
        )

        if not reference:

            self.show_message(
                "EDIT ERROR",
                "Maintenance reference is missing."
            )
            return

        registration = (
            self.maintenance_inputs["registration"].text.strip()
        )

        service_date = (
            self.maintenance_inputs["service_date"].text.strip()
        )

        service_description = (
            self.maintenance_inputs["service_description"].text.strip()
        )

        maintenance_cost = (
            self.maintenance_inputs["maintenance_cost_mwk"].text.strip()
        )

        next_service_date = (
            self.maintenance_inputs["next_service_date"].text.strip()
        )

        # VALIDATE REQUIRED FIELDS

        if not all([
            registration,
            service_date,
            service_description,
            maintenance_cost,
            next_service_date
        ]) or registration == "Select vehicle":

            self.show_message(
                "VALIDATION ERROR",
                "All maintenance fields are required."
            )
            return

        # UPDATE THROUGH BACKEND

        try:

            success, message = (
                fleet_core.update_maintenance_record(
                    reference,
                    service_date,
                    registration,
                    service_description,
                    maintenance_cost,
                    next_service_date
                )
            )

        except Exception as error:

            self.show_message(
                "UPDATE ERROR",
                "Maintenance update failed.\n\n" + str(error)
            )
            return

        if not success:

            self.show_message(
                "UPDATE FAILED",
                message
            )
            return

        # SUCCESS

        self.show_maintenance()

        self.show_message(
            "SERVICE UPDATED",
            message + "\n\nReference: " + reference
        )


    # ==========================================
    # CONFIRM MAINTENANCE DELETION
    # ==========================================



    def confirm_delete_vehicle(self, vehicle):

        try:

            registration = (
                vehicle.get("registration", "").strip().upper()
            )

            if not registration:

                raise ValueError(
                    "Vehicle registration is missing."
                )

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            if vehicles is None:

                raise ValueError(
                    "Vehicle records could not be loaded."
                )

            matches = [
                record for record in vehicles
                if record.get("registration", "").strip().upper()
                == registration
            ]

            if len(matches) != 1:

                raise ValueError(
                    "Vehicle was not found or is duplicated."
                )

            record = matches[0]

            popup_content = BoxLayout(
                orientation="vertical",
                spacing=dp(10),
                padding=dp(10)
            )

            message = Label(
                text=(
                    "Are you sure you want to delete this vehicle?\n\n"
                    "Registration: " + record["registration"] + "\n"
                    "Vehicle Type: " + record["vehicle_type"] + "\n"
                    "Licence Category: " + record["licence_category"] + "\n\n"
                    "Vehicles with linked trip or maintenance "
                    "history cannot be deleted.\n\n"
                    "A verified backup will be created."
                ),
                halign="center",
                valign="middle"
            )

            popup_content.add_widget(message)

            buttons = BoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(48)
            )

            cancel_button = Button(
                text="CANCEL"
            )

            delete_button = Button(
                text="CONFIRM DELETE",
                background_color=(0.75, 0.12, 0.12, 1)
            )

            buttons.add_widget(cancel_button)
            buttons.add_widget(delete_button)

            popup_content.add_widget(buttons)

            popup = Popup(
                title="CONFIRM VEHICLE DELETION",
                content=popup_content,
                size_hint=(0.9, 0.65),
                auto_dismiss=False
            )

            cancel_button.bind(
                on_release=popup.dismiss
            )

            delete_button.bind(
                on_release=lambda instance: (
                    popup.dismiss(),
                    self.delete_vehicle_record(registration)
                )
            )

            popup.open()

        except Exception as error:

            self.show_message(
                "DELETION ERROR",
                str(error)
            )

    def delete_vehicle_record(self, registration):

        print("CONFIRM DELETE CALLBACK TRIGGERED")
        print("REGISTRATION:", registration)

        try:

            result = fleet_core.delete_vehicle_record(
                registration
            )

            print("BACKEND RESULT:", result)

            success, message = result

            if success:

                self.show_vehicles()

                self.show_message(
                    "SUCCESS",
                    message
                )

            else:

                self.show_message(
                    "DELETION BLOCKED",
                    message
                )

        except Exception as error:

            print("DELETE ERROR:", repr(error))

            self.show_message(
                "DELETION ERROR",
                str(error)
            )


    def confirm_delete_maintenance(self, reference):

        try:

            maintenance = fleet_core.read_records(
                fleet_core.MAINTENANCE_FILE
            )

            if maintenance is None:

                raise ValueError(
                    "Maintenance records could not be loaded."
                )

            matches = [
                record for record in maintenance
                if record.get("maintenance_reference", "").strip().upper()
                == reference.strip().upper()
            ]

            if len(matches) != 1:

                raise ValueError(
                    "Maintenance record was not found or is duplicated."
                )

            record = matches[0]

            popup_content = BoxLayout(
                orientation="vertical",
                spacing=dp(10),
                padding=dp(10)
            )

            message = Label(
                text=(
                    "Are you sure you want to delete this service record?\n\n"
                    "Reference: " + reference + "\n"
                    "Vehicle: " + record["registration"] + "\n"
                    "Service Date: " + record["service_date"] + "\n\n"
                    "A verified backup will be created before deletion."
                ),
                halign="center",
                valign="middle"
            )

            popup_content.add_widget(message)

            buttons = BoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(48)
            )

            cancel_button = Button(
                text="CANCEL"
            )

            delete_button = Button(
                text="CONFIRM DELETE"
            )

            buttons.add_widget(cancel_button)
            buttons.add_widget(delete_button)

            popup_content.add_widget(buttons)

            popup = Popup(
                title="CONFIRM SERVICE DELETION",
                content=popup_content,
                size_hint=(0.9, 0.55),
                auto_dismiss=False
            )

            cancel_button.bind(
                on_release=popup.dismiss
            )

            delete_button.bind(
                on_release=lambda instance: (
                    popup.dismiss(),
                    self.delete_maintenance_record(reference)
                )
            )

            popup.open()

        except Exception as error:

            self.show_message(
                "DELETION ERROR",
                str(error)
            )

    # ==========================================
    # DELETE MAINTENANCE RECORD
    # ==========================================

    def delete_maintenance_record(self, reference):

        try:

            success, message = (
                fleet_core.delete_maintenance_record(
                    reference
                )
            )

        except Exception as error:

            self.show_message(
                "DELETE ERROR",
                "Deletion failed.\n\n" + str(error)
            )
            return

        if not success:

            self.show_message(
                "DELETION FAILED",
                message
            )
            return

        # REFRESH MAINTENANCE REGISTER

        self.show_maintenance()

        self.show_message(
            "SERVICE DELETED",
            message + "\n\nReference: " + reference
        )


    # =====================================
    # SAVE NEW MAINTENANCE RECORD
    # =====================================


    def save_new_maintenance(self, *args):

        if not hasattr(self, "maintenance_inputs"):

            self.show_message(
                "SAVE ERROR",
                "Maintenance form is unavailable."
            )
            return

        # READ FORM DATA

        registration = (
            self.maintenance_inputs["registration"].text.strip()
        )

        service_date = (
            self.maintenance_inputs["service_date"].text.strip()
        )

        service_description = (
            self.maintenance_inputs["service_description"].text.strip()
        )

        maintenance_cost = (
            self.maintenance_inputs["maintenance_cost_mwk"].text.strip()
        )

        next_service_date = (
            self.maintenance_inputs["next_service_date"].text.strip()
        )

        # VALIDATE REQUIRED FIELDS

        missing_fields = []

        if not registration or registration.lower() == "select vehicle":
            missing_fields.append("Vehicle Registration")

        if not service_date:
            missing_fields.append("Service Date")

        if not service_description:
            missing_fields.append("Service Description")

        if not maintenance_cost:
            missing_fields.append("Maintenance Cost")

        if not next_service_date:
            missing_fields.append("Next Service Date")

        if missing_fields:

            self.show_message(
                "VALIDATION ERROR",
                "Please complete these fields:\n\n"
                + "\n".join(missing_fields)
            )
            return

        # SAVE THROUGH BACKEND

        try:

            success, message, reference = (
                fleet_core.add_maintenance_record(
                    service_date,
                    registration,
                    service_description,
                    maintenance_cost,
                    next_service_date
                )
            )

        except Exception as error:

            self.show_message(
                "SAVE ERROR",
                "Maintenance record could not be saved.\n\n"
                + str(error)
            )
            return

        if not success:

            self.show_message(
                "SAVE FAILED",
                message
            )
            return

        # REFRESH MAINTENANCE REGISTER

        self.show_maintenance()

        self.show_message(
            "SERVICE RECORDED",
            message + "\n\nReference: " + reference
        )

    # =====================================
    # ADD VEHICLE FORM
    # =====================================



    def show_edit_vehicle(self, vehicle):

        self.content.clear_widgets()

        self.add_heading("EDIT VEHICLE")

        self.editing_vehicle = dict(vehicle)

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.vehicle_inputs = {}

        fields = [
            (
                "registration",
                "Vehicle registration",
                "Enter registration"
            ),
            (
                "vehicle_type",
                "Vehicle type",
                "e.g. Truck, Van, Bus"
            ),
            (
                "licence_category",
                "Licence category (C1 or B)",
                "Enter C1 or B"
            ),
            (
                "next_service_date",
                "Next scheduled service date",
                "DD/MM/YYYY"
            )
        ]

        for key, label_text, hint in fields:

            label = Label(
                text=label_text,
                font_size="14sp",
                halign="left",
                size_hint_y=None,
                height=dp(30)
            )

            form.add_widget(label)

            field = TextInput(
                text=str(vehicle.get(key, "")),
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )

            self.vehicle_inputs[key] = field

            form.add_widget(field)

        save_button = Button(
            text="SAVE CHANGES",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.05, 0.55, 0.65, 1)
        )

        save_button.bind(
            on_release=self.save_vehicle_changes
        )

        form.add_widget(save_button)

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_vehicles
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)


    def save_vehicle_changes(self, *args):

        if not hasattr(self, "editing_vehicle"):

            self.show_message(
                "SAVE ERROR",
                "No vehicle is currently selected."
            )

            return

        if not hasattr(self, "vehicle_inputs"):

            self.show_message(
                "SAVE ERROR",
                "Vehicle edit form is unavailable."
            )

            return

        new_registration = (
            self.vehicle_inputs["registration"].text.strip().upper()
        )

        vehicle_type = (
            self.vehicle_inputs["vehicle_type"].text.strip()
        )

        licence_category = (
            self.vehicle_inputs["licence_category"].text.strip().upper()
        )

        next_service_date = (
            self.vehicle_inputs["next_service_date"].text.strip()
        )

        if not all([
            new_registration,
            vehicle_type,
            licence_category,
            next_service_date
        ]):

            self.show_message(
                "VALIDATION ERROR",
                "All vehicle fields are required."
            )

            return

        old_registration = (
            self.editing_vehicle["registration"]
        )

        try:

            success, message = fleet_core.update_vehicle_record(
                old_registration,
                new_registration,
                vehicle_type,
                licence_category,
                next_service_date
            )

            if not success:

                self.show_message(
                    "UPDATE FAILED",
                    message
                )

                return

            self.show_vehicles()

            self.show_message(
                "SUCCESS",
                message
            )

        except Exception as error:

            self.show_message(
                "UPDATE ERROR",
                str(error)
            )


    def show_add_vehicle(self, *args):

        self.content.clear_widgets()

        self.add_heading("ADD NEW VEHICLE")

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.vehicle_inputs = {}

        fields = [
            (
                "registration",
                "Vehicle registration",
                "Enter registration"
            ),
            (
                "vehicle_type",
                "Vehicle type",
                "e.g. Truck, Van, Bus"
            ),
            (
                "licence_category",
                "Licence category (C1 or B)",
                "Enter C1 or B"
            ),
            (
                "next_service_date",
                "Next scheduled service date",
                "DD/MM/YYYY"
            )
        ]

        for key, label_text, hint in fields:

            label = Label(
                text=label_text,
                font_size="14sp",
                halign="left",
                size_hint_y=None,
                height=dp(30)
            )

            form.add_widget(label)

            field = TextInput(
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )

            self.vehicle_inputs[key] = field

            form.add_widget(field)

        save_button = Button(
            text="SAVE VEHICLE",
            size_hint_y=None,
            height=dp(50)
        )

        save_button.bind(
            on_release=self.save_new_vehicle
        )

        form.add_widget(save_button)

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_vehicles
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)



    # =====================================
    # SAVE VEHICLE
    # =====================================

    def save_new_vehicle(self, *args):

        registration = (
            self.vehicle_inputs["registration"]
            .text.strip().upper()
        )

        vehicle_type = (
            self.vehicle_inputs["vehicle_type"]
            .text.strip()
        )

        category = (
            self.vehicle_inputs["licence_category"]
            .text.strip().upper()
        )

        service_date = (
            self.vehicle_inputs["next_service_date"]
            .text.strip()
        )

        # Check required fields.

        if not all([
            registration,
            vehicle_type,
            category,
            service_date
        ]):

            self.show_message(
                "Missing information",
                "All vehicle fields are required."
            )

            return

        # Validate licence category.

        if category not in ["C1", "B"]:

            self.show_message(
                "Invalid licence category",
                "Enter C1 or B only."
            )

            return

        # Validate service date.

        try:

            parsed_date = datetime.strptime(
                service_date,
                "%d/%m/%Y"
            )

            if parsed_date.strftime("%d/%m/%Y") != service_date:

                raise ValueError(
                    "Use the exact DD/MM/YYYY format."
                )

        except ValueError:

            self.show_message(
                "Invalid service date",
                "Enter a valid date using DD/MM/YYYY.\n\n"
                "Example: 05/12/2026"
            )

            return

        # Read existing vehicle records.

        vehicles = fleet_core.read_records(
            fleet_core.VEHICLES_FILE
        )

        if vehicles is None:

            self.show_message(
                "Data unavailable",
                "Vehicle records could not be read.\n"
                "No vehicle was saved."
            )

            return

        # Prevent duplicate registrations.

        duplicate = any(
            vehicle["registration"].strip().upper()
            == registration
            for vehicle in vehicles
        )

        if duplicate:

            self.show_message(
                "Duplicate registration",
                "This vehicle is already registered."
            )

            return

        # Prepare the record.

        record = {
            "registration": registration,
            "vehicle_type": vehicle_type,
            "licence_category": category,
            "next_service_date": service_date
        }

        # Use the original protected saving function.

        saved = fleet_core.save_record(
            fleet_core.VEHICLES_FILE,
            fleet_core.VEHICLE_FIELDS,
            record
        )

        if not saved:

            self.show_message(
                "Registration failed",
                "The vehicle could not be saved.\n\n"
                "Your existing records should remain protected. "
                "Check the Pydroid terminal for the detailed error."
            )

            return

        self.show_vehicles()

        self.show_message(
            "Vehicle registered",
            "Vehicle registered successfully.\n\n"
            f"Registration: {registration}\n"
            f"Vehicle Type: {vehicle_type}\n"
            f"Licence Category: {category}\n"
            f"Next Service: {service_date}"
        )

   
  
    
    # =====================================
    # DRIVER REGISTER
    # =====================================

    
    def show_drivers(self, *args):

        self.content.clear_widgets()

        # =================================
        # DRIVERS HEADING
        # =================================

        self.add_heading("DRIVER MANAGEMENT")

        self.add_information(
            "REGISTERED DRIVERS"
        )

        # =================================
        # ADD DRIVER BUTTON
        # =================================

        add_button = Button(
            text="+ ADD NEW DRIVER",
            size_hint_y=None,
            height=dp(50),
            bold=True,
            font_size="15sp",
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.02, 0.55, 0.50, 1)
        )

        add_button.bind(
            on_release=self.show_add_driver
        )

        self.content.add_widget(add_button)

        # =================================
        # LOAD DRIVER RECORDS
        # =================================

        try:

            drivers = fleet_core.read_records(
                fleet_core.DRIVERS_FILE
            )

            if drivers is None:

                raise ValueError(
                    "Driver records could not be read."
                )

            if not drivers:

                self.add_information(
                    "NO DRIVERS REGISTERED"
                )

                return

            # =================================
            # SCROLL CONTAINER
            # =================================

            scroll = ScrollView(
                do_scroll_x=False
            )

            driver_list = BoxLayout(
                orientation="vertical",
                spacing=dp(12),
                size_hint_y=None,
                padding=[dp(4), dp(8)]
            )

            driver_list.bind(
                minimum_height=driver_list.setter("height")
            )

            # =================================
            # DRIVER CARDS
            # =================================

            for index, driver in enumerate(drivers, 1):

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(6),
                    padding=dp(10),
                    size_hint_y=None,
                    height=dp(235)
                )

                # CARD BACKGROUND

                with card.canvas.before:

                    Color(0.07, 0.13, 0.23, 1)

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(14)]
                    )

                card.bind(
                    pos=lambda instance, value, bg=background:
                    setattr(bg, "pos", value),

                    size=lambda instance, value, bg=background:
                    setattr(bg, "size", value)
                )

                # DRIVER DETAILS

                details = (
                    f"DRIVER {index}\n\n"
                    f"Name: {driver['name']}\n"
                    f"Licence Type: {driver['licence_type']}\n"
                    f"Licence Expiry: {driver['licence_expiry']}\n"
                    f"Defensive Driving Expiry: "
                    f"{driver['defensive_driving_expiry']}"
                )

                details_label = Label(
                    text=details,
                    font_size="14sp",
                    color=(0.85, 0.92, 1, 1),
                    halign="left",
                    valign="middle",
                    size_hint_y=None,
                    height=dp(125)
                )

                details_label.bind(
                    size=lambda instance, value:
                    setattr(instance, "text_size", value)
                )

                card.add_widget(details_label)

                # =================================
                # EDIT DRIVER BUTTON
                # =================================

                edit_button = Button(
                    text="EDIT DRIVER",
                    size_hint_y=None,
                    height=dp(42),
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.02, 0.55, 0.50, 1)
                )

                edit_button.bind(
                    on_release=lambda instance, selected=dict(driver):
                    self.show_edit_driver(selected)
                )

                card.add_widget(edit_button)

                # =================================
                # DELETE DRIVER BUTTON
                # =================================

                delete_button = Button(
                    text="DELETE DRIVER",
                    size_hint_y=None,
                    height=dp(42),
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.75, 0.12, 0.16, 1)
                )

                delete_button.bind(
                    on_release=lambda instance, selected=dict(driver):
                    self.confirm_delete_driver(selected)
                )

                card.add_widget(delete_button)

                driver_list.add_widget(card)

            # =================================
            # DISPLAY DRIVER RECORDS
            # =================================

            scroll.add_widget(driver_list)

            self.content.add_widget(scroll)

        except Exception as error:

            self.add_information(
                "DRIVER DISPLAY FAILED\n\n" + str(error)
            )

    # =====================================
    # EDIT DRIVER FORM
    # =====================================

    def show_edit_driver(self, driver):

        self.content.clear_widgets()

        self.add_heading("EDIT DRIVER")

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.edit_driver_inputs = {}

        fields = [
            ("name", "Driver full name"),
            ("licence_type", "Licence type (C1 or B)"),
            ("licence_expiry", "Driving licence expiry"),
            ("defensive_driving_expiry", "Defensive driving expiry")
        ]

        for key, label_text in fields:

            form.add_widget(
                Label(
                    text=label_text,
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            field = TextInput(
                text=driver.get(key, ""),
                multiline=False,
                size_hint_y=None,
                height=dp(48)
            )

            self.edit_driver_inputs[key] = field

            form.add_widget(field)

        save_button = Button(
            text="SAVE CHANGES",
            size_hint_y=None,
            height=dp(50)
        )

        save_button.bind(
            on_release=lambda instance:
            self.save_driver_edit(driver)
        )

        form.add_widget(save_button)

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_drivers
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)


    # =====================================
    # CONFIRM DRIVER DELETION
    # =====================================

    def confirm_delete_driver(self, driver):

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12)
        )

        message = Label(
            text=(
                "Are you sure you want to delete this driver?\n\n"
                f"Driver: {driver.get('name', '')}\n\n"
                "This action cannot be undone."
            ),
            halign="left",
            valign="middle"
        )

        message.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        popup_content.add_widget(message)

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10)
        )

        confirm_button = Button(
            text="YES, DELETE",
            background_color=(0.8, 0.15, 0.15, 1)
        )

        cancel_button = Button(
            text="CANCEL"
        )

        buttons.add_widget(confirm_button)
        buttons.add_widget(cancel_button)

        popup_content.add_widget(buttons)

        popup = Popup(
            title="CONFIRM DRIVER DELETION",
            content=popup_content,
            size_hint=(0.9, 0.45),
            auto_dismiss=False
        )

        confirm_button.bind(
            on_release=lambda instance:
            self.delete_driver_record(driver, popup)
        )

        cancel_button.bind(
            on_release=popup.dismiss
        )

        popup.open()


    # =====================================
    # DELETE DRIVER RECORD
    # =====================================

    def delete_driver_record(self, selected_driver, popup):

        driver_name = selected_driver.get(
            "name", ""
        ).strip()

        # Reload current records

        drivers = fleet_core.read_records(
            fleet_core.DRIVERS_FILE
        )

        trips = fleet_core.read_records(
            fleet_core.TRIPS_FILE
        )

        if drivers is None or trips is None:

            popup.dismiss()

            self.show_message(
                "Deletion blocked",
                "Driver or trip records could not be read.\n\n"
                "No records were deleted."
            )

            return

        # Locate the driver

        matching_indices = [
            index
            for index, driver in enumerate(drivers)
            if driver.get("name", "").strip().casefold()
            == driver_name.casefold()
        ]

        if len(matching_indices) != 1:

            popup.dismiss()

            self.show_message(
                "Deletion blocked",
                "The driver could not be identified uniquely.\n\n"
                "No records were deleted."
            )

            return

        # Check linked trip history

        linked_trips = [
            trip
            for trip in trips
            if trip.get("driver", "").strip().casefold()
            == driver_name.casefold()
        ]

        if linked_trips:

            popup.dismiss()

            self.show_message(
                "Deletion not allowed",
                f"{driver_name} has {len(linked_trips)} "
                "recorded trip(s).\n\n"
                "Drivers with trip history cannot be deleted."
            )

            return

        # Create backup before deletion

        try:

            backup_path = fleet_core.backup_data()

        except Exception as error:

            popup.dismiss()

            self.show_message(
                "Backup failed",
                "Driver was not deleted.\n\n"
                + str(error)
            )

            return

        if not backup_path:

            popup.dismiss()

            self.show_message(
                "Backup failed",
                "Driver was not deleted because "
                "a backup could not be created."
            )

            return

        # Remove driver from records

        updated_drivers = [
            driver
            for driver in drivers
            if driver.get("name", "").strip().casefold()
            != driver_name.casefold()
        ]

        # Save updated records

        try:

            deleted = fleet_core.write_records(
                fleet_core.DRIVERS_FILE,
                fleet_core.DRIVER_FIELDS,
                updated_drivers
            )

        except Exception:

            deleted = False

        if not deleted:

            popup.dismiss()

            self.show_message(
                "Deletion failed",
                "The driver could not be deleted.\n\n"
                "Check the Pydroid terminal for details."
            )

            return

        # Successful deletion

        popup.dismiss()

        self.show_drivers()

        self.show_message(
            "Driver deleted",
            f"{driver_name} was successfully deleted.\n\n"
            "A backup was created before deletion."
        )

    
    # =====================================
    # ADD DRIVER FORM
    # =====================================

    def show_add_driver(self, *args):

        self.content.clear_widgets()

        self.add_heading("ADD NEW DRIVER")

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.driver_inputs = {}

        fields = [
            (
                "name",
                "Driver full name",
                "Enter full name"
            ),
            (
                "licence_type",
                "Driving licence type (C1 or B)",
                "Enter C1 or B"
            ),
            (
                "licence_expiry",
                "Driving licence expiry date",
                "DD/MM/YYYY"
            ),
            (
                "defensive_driving_expiry",
                "Defensive driving expiry date",
                "DD/MM/YYYY"
            )
        ]

        for key, label_text, hint in fields:

            form.add_widget(
                Label(
                    text=label_text,
                    font_size="14sp",
                    halign="left",
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            field = TextInput(
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )

            self.driver_inputs[key] = field

            form.add_widget(field)

        save_button = Button(
            text="SAVE DRIVER",
            size_hint_y=None,
            height=dp(50)
        )

        save_button.bind(
            on_release=self.save_new_driver
        )

        form.add_widget(save_button)

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_drivers
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)

    # =====================================
    # SAVE DRIVER
    # =====================================

    def save_new_driver(self, *args):

        name = (
            self.driver_inputs["name"]
            .text.strip()
        )

        licence_type = (
            self.driver_inputs["licence_type"]
            .text.strip().upper()
        )

        licence_expiry = (
            self.driver_inputs["licence_expiry"]
            .text.strip()
        )

        defensive_expiry = (
            self.driver_inputs["defensive_driving_expiry"]
            .text.strip()
        )

        if not all([
            name,
            licence_type,
            licence_expiry,
            defensive_expiry
        ]):

            self.show_message(
                "Missing information",
                "All driver fields are required."
            )

            return

        if licence_type not in ["C1", "B"]:

            self.show_message(
                "Invalid licence type",
                "Enter C1 or B only."
            )

            return

        try:

            parsed_licence_date = datetime.strptime(
                licence_expiry,
                "%d/%m/%Y"
            )

            if (
                parsed_licence_date.strftime("%d/%m/%Y")
                != licence_expiry
            ):

                raise ValueError

        except ValueError:

            self.show_message(
                "Invalid licence expiry date",
                "Enter a valid date using DD/MM/YYYY.\n\n"
                "Example: 05/12/2027"
            )

            return

        try:

            parsed_defensive_date = datetime.strptime(
                defensive_expiry,
                "%d/%m/%Y"
            )

            if (
                parsed_defensive_date.strftime("%d/%m/%Y")
                != defensive_expiry
            ):

                raise ValueError

        except ValueError:

            self.show_message(
                "Invalid defensive driving date",
                "Enter a valid date using DD/MM/YYYY.\n\n"
                "Example: 05/12/2027"
            )

            return

        drivers = fleet_core.read_records(
            fleet_core.DRIVERS_FILE
        )

        if drivers is None:

            self.show_message(
                "Data unavailable",
                "Driver records could not be read.\n"
                "No driver was saved."
            )

            return

        duplicate = any(
            driver["name"].strip().casefold()
            == name.casefold()
            for driver in drivers
        )

        if duplicate:

            self.show_message(
                "Duplicate driver",
                "This driver is already registered."
            )

            return

        record = {
            "name": name,
            "licence_type": licence_type,
            "licence_expiry": licence_expiry,
            "defensive_driving_expiry": defensive_expiry
        }

        saved = fleet_core.save_record(
            fleet_core.DRIVERS_FILE,
            fleet_core.DRIVER_FIELDS,
            record
        )

        if not saved:

            self.show_message(
                "Registration failed",
                "The driver could not be saved.\n\n"
                "Check the Pydroid terminal for details."
            )

            return

        self.show_drivers()

        self.show_message(
            "Driver registered",
            "Driver registered successfully.\n\n"
            f"Name: {name}\n"
            f"Licence Type: {licence_type}\n"
            f"Licence Expiry: {licence_expiry}\n"
            f"Defensive Driving Expiry: {defensive_expiry}"
        )

  

    # =====================================
    # SAVE DRIVER
    # =====================================

    def save_new_driver(self, *args):

        name = (
            self.driver_inputs["name"]
            .text.strip()
        )

        licence_type = (
            self.driver_inputs["licence_type"]
            .text.strip().upper()
        )

        licence_expiry = (
            self.driver_inputs["licence_expiry"]
            .text.strip()
        )

        defensive_expiry = (
            self.driver_inputs["defensive_driving_expiry"]
            .text.strip()
        )

        # Check required fields

        if not all([
            name,
            licence_type,
            licence_expiry,
            defensive_expiry
        ]):

            self.show_message(
                "Missing information",
                "All driver fields are required."
            )

            return

        # Validate licence type

        if licence_type not in ["C1", "B"]:

            self.show_message(
                "Invalid licence type",
                "Enter C1 or B only."
            )

            return

        # Validate driving licence expiry

        try:

            parsed_licence_date = datetime.strptime(
                licence_expiry,
                "%d/%m/%Y"
            )

            if (
                parsed_licence_date.strftime("%d/%m/%Y")
                != licence_expiry
            ):

                raise ValueError

        except ValueError:

            self.show_message(
                "Invalid licence expiry date",
                "Enter a valid date using DD/MM/YYYY.\n\n"
                "Example: 05/12/2026"
            )

            return

        # Validate defensive driving expiry

        try:

            parsed_defensive_date = datetime.strptime(
                defensive_expiry,
                "%d/%m/%Y"
            )

            if (
                parsed_defensive_date.strftime("%d/%m/%Y")
                != defensive_expiry
            ):

                raise ValueError

        except ValueError:

            self.show_message(
                "Invalid defensive driving date",
                "Enter a valid date using DD/MM/YYYY.\n\n"
                "Example: 05/12/2026"
            )

            return

        # Read existing driver records

        drivers = fleet_core.read_records(
            fleet_core.DRIVERS_FILE
        )

        if drivers is None:

            self.show_message(
                "Data unavailable",
                "Driver records could not be read.\n"
                "No driver was saved."
            )

            return

        # Prevent duplicate driver names

        duplicate = any(
            driver["name"].strip().casefold()
            == name.casefold()
            for driver in drivers
        )

        if duplicate:

            self.show_message(
                "Duplicate driver",
                "This driver is already registered."
            )

            return

        # Prepare driver record

        record = {
            "name": name,
            "licence_type": licence_type,
            "licence_expiry": licence_expiry,
            "defensive_driving_expiry": defensive_expiry
        }

        # Save using protected backend function

        saved = fleet_core.save_record(
            fleet_core.DRIVERS_FILE,
            fleet_core.DRIVER_FIELDS,
            record
        )

        if not saved:

            self.show_message(
                "Registration failed",
                "The driver could not be saved.\n\n"
                "Check the Pydroid terminal for details."
            )

            return

        self.show_drivers()

        self.show_message(
            "Driver registered",
            "Driver registered successfully.\n\n"
            f"Name: {name}\n"
            f"Licence Type: {licence_type}\n"
            f"Licence Expiry: {licence_expiry}\n"
            f"Defensive Driving Expiry: {defensive_expiry}"
        )


  
    # =====================================
    # ADD TRIP FORM
    # =====================================

    def show_add_trip(self, *args):

        self.content.clear_widgets()

        self.add_heading("ADD NEW TRIP")

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.trip_inputs = {}

        fields = [
            ("trip_date", "Trip date", "DD/MM/YYYY"),
            ("origin", "Trip origin", "Enter origin"),
            ("destination", "Trip destination", "Enter destination"),
            ("registration", "Vehicle registration", "Enter registered vehicle"),
            ("driver", "Driver name", "Enter registered driver"),
            ("fuel_litres", "Fuel consumed (litres)", "Enter litres"),
            ("fuel_cost_mwk", "Fuel cost (MWK)", "Enter fuel cost"),
            ("purpose", "Trip purpose", "Enter trip purpose")
        ]

        for key, label_text, hint in fields:

            form.add_widget(
                Label(
                    text=label_text,
                    font_size="14sp",
                    halign="left",
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            field = TextInput(
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )

            self.trip_inputs[key] = field

            form.add_widget(field)

        save_button = Button(
            text="SAVE TRIP",
            size_hint_y=None,
            height=dp(50)
        )

        save_button.bind(
            on_release=self.save_new_trip
        )

        form.add_widget(save_button)

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_trips
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)
 
  
    def save_new_trip(self, *args):

        # ==========================================
        # READ FORM DATA
        # ==========================================

        trip_date = self.trip_inputs["trip_date"].text.strip()
        origin = self.trip_inputs["origin"].text.strip()
        destination = self.trip_inputs["destination"].text.strip()
        registration = self.trip_inputs["registration"].text.strip().upper()
        driver = self.trip_inputs["driver"].text.strip()
        fuel_litres_text = self.trip_inputs["fuel_litres"].text.strip()
        fuel_cost_text = self.trip_inputs["fuel_cost_mwk"].text.strip()
        purpose = self.trip_inputs["purpose"].text.strip()

        # ==========================================
        # CHECK REQUIRED FIELDS
        # ==========================================

        if not all([
            trip_date,
            origin,
            destination,
            registration,
            driver,
            fuel_litres_text,
            fuel_cost_text,
            purpose
        ]):

            self.show_message(
                "VALIDATION ERROR",
                "All trip fields are required."
            )
            return

        # ==========================================
        # VALIDATE TRIP DATE
        # ==========================================

        try:

            datetime.strptime(
                trip_date,
                "%d/%m/%Y"
            )

        except ValueError:

            self.show_message(
                "INVALID DATE",
                "Enter trip date in DD/MM/YYYY format."
            )
            return

        # ==========================================
        # VALIDATE FUEL VALUES
        # ==========================================

        try:

            fuel_litres = float(fuel_litres_text)
            fuel_cost = float(fuel_cost_text)

            if not math.isfinite(fuel_litres):
                raise ValueError

            if not math.isfinite(fuel_cost):
                raise ValueError

            if fuel_litres <= 0 or fuel_cost <= 0:
                raise ValueError

        except ValueError:

            self.show_message(
                "INVALID FUEL DETAILS",
                "Fuel litres and fuel cost must be positive numbers."
            )
            return

        # ==========================================
        # LOAD EXISTING RECORDS
        # ==========================================

        vehicles = fleet_core.read_records(
            fleet_core.VEHICLES_FILE
        )

        drivers = fleet_core.read_records(
            fleet_core.DRIVERS_FILE
        )

        trips = fleet_core.read_records(
            fleet_core.TRIPS_FILE
        )

        if vehicles is None or drivers is None or trips is None:

            self.show_message(
                "DATA ERROR",
                "Unable to read fleet records. Trip was not saved."
            )
            return

        # ==========================================
        # VERIFY VEHICLE
        # ==========================================

        vehicle_exists = any(
            v["registration"].strip().upper() == registration
            for v in vehicles
        )

        if not vehicle_exists:

            self.show_message(
                "INVALID VEHICLE",
                "Vehicle registration is not found."
            )
            return

        # ==========================================
        # VERIFY DRIVER
        # ==========================================

        driver_exists = any(
            d["name"].strip().casefold() == driver.casefold()
            for d in drivers
        )

        if not driver_exists:

            self.show_message(
                "INVALID DRIVER",
                "Driver is not registered."
            )
            return

        # ==========================================
        # GENERATE TRIP REFERENCE
        # ==========================================

        try:

            trip_reference = fleet_core.next_trip_reference(
                trips
            )

        except Exception as error:

            self.show_message(
                "REFERENCE ERROR",
                "Unable to generate trip reference: " + str(error)
            )
            return

        # ==========================================
        # PREPARE TRIP RECORD
        # ==========================================

        record = {
            "trip_date": trip_date,
            "origin": origin,
            "destination": destination,
            "registration": registration,
            "driver": driver,
            "fuel_litres": "{:.2f}".format(fuel_litres),
            "fuel_cost_mwk": "{:.2f}".format(fuel_cost),
            "purpose": purpose,
            "trip_reference": trip_reference
        }

        # ==========================================
        # SAVE TRIP
        # ==========================================

        try:

            saved = fleet_core.save_record(
                fleet_core.TRIPS_FILE,
                fleet_core.TRIP_FIELDS,
                record
            )

        except Exception as error:

            self.show_message(
                "SAVE ERROR",
                "Trip could not be saved: " + str(error)
            )
            return

        if not saved:

            self.show_message(
                "SAVE FAILED",
                "Trip was not saved. Please check your data files."
            )
            return

        # ==========================================
        # SUCCESS
        # ==========================================

        self.show_message(
            "TRIP SAVED",
            "Trip registered successfully.\n\n"
            "Reference: " + trip_reference
        )

        self.show_trips()

    
    # =====================================
    # TRIP HISTORY
    # =====================================

   

    def show_trips(self, *args):

        try:

            self.content.clear_widgets()

            # =================================
            # TRIP MANAGEMENT HEADING
            # =================================

            self.add_heading("TRIP MANAGEMENT")

            self.add_information(
                "TRIP HISTORY & RECORDS"
            )

            # =================================
            # ADD TRIP BUTTON
            # =================================

            add_button = Button(
                text="+ ADD NEW TRIP",
                size_hint_y=None,
                height=dp(50),
                bold=True,
                font_size="15sp",
                color=(1, 1, 1, 1),
                background_normal="",
                background_color=(0.02, 0.55, 0.50, 1)
            )

            add_button.bind(
                on_release=self.show_add_trip
            )

            self.content.add_widget(add_button)

            # =================================
            # LOAD TRIP RECORDS
            # =================================

            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            if trips is None:

                self.add_information(
                    "TRIP DATA UNAVAILABLE\n\n"
                    "Trip records could not be loaded."
                )

                return

            if not trips:

                self.add_information(
                    "NO TRIPS RECORDED\n\n"
                    "Use ADD TRIP to register a new trip."
                )

                return

            self.trip_records = trips

            # =================================
            # SEARCH SECTION
            # =================================

            search_label = Label(
                text="SEARCH TRIP HISTORY",
                size_hint_y=None,
                height=dp(35),
                font_size="14sp",
                bold=True,
                color=(0.65, 0.78, 0.88, 1),
                halign="left"
            )

            self.content.add_widget(search_label)

            search_hint = Label(
                text="Reference, vehicle, driver, destination or date",
                size_hint_y=None,
                height=dp(28),
                font_size="12sp",
                color=(0.75, 0.82, 0.90, 1)
            )

            self.content.add_widget(search_hint)

            self.trip_search_input = TextInput(
                hint_text="Enter search term...",
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                background_normal="",
                background_active="",
                background_color=(0.12, 0.18, 0.27, 1),
                foreground_color=(1, 1, 1, 1),
                hint_text_color=(0.65, 0.72, 0.80, 1),
                cursor_color=(0.1, 0.85, 0.75, 1),
                padding=[dp(12), dp(12)]
            )

            self.trip_search_input.bind(
                text=self.filter_trip_history
            )

            self.content.add_widget(
                self.trip_search_input
            )

            # =================================
            # DATE FILTER SECTION
            # =================================

            date_label = Label(
                text="FILTER TRIPS BY DATE RANGE",
                size_hint_y=None,
                height=dp(40),
                font_size="14sp",
                bold=True,
                color=(0.65, 0.78, 0.88, 1),
                halign="left"
            )

            self.content.add_widget(date_label)

            self.date_from_input = TextInput(
                hint_text="Start date: DD/MM/YYYY",
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                background_normal="",
                background_active="",
                background_color=(0.12, 0.18, 0.27, 1),
                foreground_color=(1, 1, 1, 1),
                hint_text_color=(0.65, 0.72, 0.80, 1),
                cursor_color=(0.1, 0.85, 0.75, 1),
                padding=[dp(12), dp(10)]
            )

            self.content.add_widget(
                self.date_from_input
            )

            self.date_to_input = TextInput(
                hint_text="End date: DD/MM/YYYY",
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                background_normal="",
                background_active="",
                background_color=(0.12, 0.18, 0.27, 1),
                foreground_color=(1, 1, 1, 1),
                hint_text_color=(0.65, 0.72, 0.80, 1),
                cursor_color=(0.1, 0.85, 0.75, 1),
                padding=[dp(12), dp(10)]
            )

            self.content.add_widget(
                self.date_to_input
            )

            # =================================
            # DATE FILTER BUTTONS
            # =================================

            date_buttons = BoxLayout(
                orientation="horizontal",
                spacing=dp(10),
                size_hint_y=None,
                height=dp(48)
            )

            apply_date_button = Button(
                text="APPLY FILTER",
                bold=True,
                color=(1, 1, 1, 1),
                background_normal="",
                background_color=(0.02, 0.55, 0.50, 1)
            )

            apply_date_button.bind(
                on_release=self.filter_trip_history
            )

            date_buttons.add_widget(
                apply_date_button
            )

            clear_date_button = Button(
                text="CLEAR FILTER",
                bold=True,
                color=(1, 1, 1, 1),
                background_normal="",
                background_color=(0.30, 0.38, 0.48, 1)
            )

            clear_date_button.bind(
                on_release=self.clear_trip_date_filter
            )

            date_buttons.add_widget(
                clear_date_button
            )

            self.content.add_widget(date_buttons)

            # =================================
            # TRIP HISTORY SCROLL CONTAINER
            # =================================

            scroll = ScrollView(
                do_scroll_x=False
            )

            self.trip_list_container = BoxLayout(
                orientation="vertical",
                spacing=dp(12),
                padding=dp(8),
                size_hint_y=None
            )

            self.trip_list_container.bind(
                minimum_height=
                self.trip_list_container.setter("height")
            )

            scroll.add_widget(
                self.trip_list_container
            )

            self.content.add_widget(scroll)

            # =================================
            # DISPLAY FILTERED TRIPS
            # =================================

            self.filter_trip_history()

        except Exception as error:

            self.content.clear_widgets()

            self.add_heading("TRIP HISTORY ERROR")

            self.add_information(
                "Unable to display trip history.\n\n"
                + str(error)
            )



    def filter_trip_history(self, instance=None, value=None):

        try:

            # =================================
            # CLEAR PREVIOUS RESULTS
            # =================================

            self.trip_list_container.clear_widgets()

            search_text = (
                self.trip_search_input.text.strip().lower()
            )

            start_text = self.date_from_input.text.strip()
            end_text = self.date_to_input.text.strip()

            start_date = None
            end_date = None

            # =================================
            # VALIDATE DATE FILTERS
            # =================================

            if start_text:
                start_date = datetime.strptime(
                    start_text, "%d/%m/%Y"
                ).date()

            if end_text:
                end_date = datetime.strptime(
                    end_text, "%d/%m/%Y"
                ).date()

            if start_date and end_date:

                if start_date > end_date:

                    self.show_message(
                        "INVALID DATE RANGE",
                        "Start date cannot be after end date."
                    )

                    return

            # =================================
            # FILTER TRIP RECORDS
            # =================================

            filtered_trips = []

            for trip in self.trip_records:

                searchable_text = " ".join([
                    trip.get("trip_reference", ""),
                    trip.get("registration", ""),
                    trip.get("driver", ""),
                    trip.get("destination", ""),
                    trip.get("trip_date", "")
                ]).lower()

                if search_text not in searchable_text:
                    continue

                trip_date = datetime.strptime(
                    trip.get("trip_date", ""),
                    "%d/%m/%Y"
                ).date()

                if start_date and trip_date < start_date:
                    continue

                if end_date and trip_date > end_date:
                    continue

                filtered_trips.append(trip)

            # =================================
            # NO MATCHING TRIPS
            # =================================

            if not filtered_trips:

                self.trip_list_container.add_widget(
                    Label(
                        text="NO MATCHING TRIPS FOUND",
                        size_hint_y=None,
                        height=dp(80),
                        color=(0.65, 0.78, 0.88, 1),
                        bold=True,
                        font_size="15sp"
                    )
                )

                return

            # =================================
            # CREATE TRIP CARDS
            # =================================

            for index, trip in enumerate(filtered_trips, 1):

                card = BoxLayout(
                    orientation="vertical",
                    spacing=dp(8),
                    padding=dp(10),
                    size_hint_y=None,
                    height=dp(340)
                )

                # CARD BACKGROUND

                with card.canvas.before:

                    Color(0.07, 0.13, 0.23, 1)

                    background = RoundedRectangle(
                        pos=card.pos,
                        size=card.size,
                        radius=[dp(14)]
                    )

                card.bind(
                    pos=lambda instance, value, bg=background:
                    setattr(bg, "pos", value),

                    size=lambda instance, value, bg=background:
                    setattr(bg, "size", value)
                )

                # =================================
                # TRIP DETAILS
                # =================================

                details = (
                    f"TRIP {index}\n\n"
                    f"Reference: {trip.get('trip_reference', '')}\n"
                    f"Date: {trip.get('trip_date', '')}\n"
                    f"Origin: {trip.get('origin', '')}\n"
                    f"Destination: {trip.get('destination', '')}\n"
                    f"Vehicle: {trip.get('registration', '')}\n"
                    f"Driver: {trip.get('driver', '')}\n"
                    f"Fuel: {trip.get('fuel_litres', '')} litres\n"
                    f"Fuel Cost: MWK {trip.get('fuel_cost_mwk', '')}\n"
                    f"Purpose: {trip.get('purpose', '')}"
                )

                details_label = Label(
                    text=details,
                    font_size="14sp",
                    color=(0.85, 0.92, 1, 1),
                    halign="left",
                    valign="middle",
                    size_hint_y=None,
                    height=dp(230)
                )

                details_label.bind(
                    size=lambda instance, value:
                    setattr(instance, "text_size", value)
                )

                card.add_widget(details_label)

                # =================================
                # ACTION BUTTON ROW
                # =================================

                action_row = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(10),
                    size_hint_y=None,
                    height=dp(45)
                )

                # EDIT TRIP BUTTON

                edit_button = Button(
                    text="EDIT TRIP",
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.02, 0.55, 0.50, 1)
                )

                edit_button.bind(
                    on_release=lambda instance,
                    selected=trip.copy():
                    self.open_edit_trip_safely(selected)
                )

                action_row.add_widget(edit_button)

                # DELETE TRIP BUTTON

                delete_button = Button(
                    text="DELETE TRIP",
                    bold=True,
                    color=(1, 1, 1, 1),
                    background_normal="",
                    background_color=(0.75, 0.12, 0.16, 1)
                )

                delete_button.bind(
                    on_release=lambda instance,
                    selected=trip.copy():
                    self.confirm_delete_trip(selected)
                )

                action_row.add_widget(delete_button)

                card.add_widget(action_row)

                # ADD CARD TO HISTORY

                self.trip_list_container.add_widget(card)

        except ValueError:

            self.show_message(
                "INVALID DATE",
                "Enter dates in DD/MM/YYYY format."
            )

        except Exception as error:

            self.show_message(
                "TRIP FILTER ERROR",
                str(error)
            )

    def clear_trip_date_filter(self, *args):

        self.date_from_input.text = ""
        self.date_to_input.text = ""

        self.filter_trip_history()
                        
   
    # =====================================
    # EDIT TRIP FORM
    # =====================================

    def show_edit_trip(self, selected_trip):

        self.editing_trip = selected_trip.copy()

        self.content.clear_widgets()

        self.add_heading("EDIT TRIP")

        scroll = ScrollView()

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.edit_trip_inputs = {}

        fields = [
            ("trip_date", "Trip date", "DD/MM/YYYY"),
            ("origin", "Trip origin", "Enter origin"),
            ("destination", "Trip destination", "Enter destination"),
            ("registration", "Vehicle registration", "Enter vehicle"),
            ("driver", "Driver name", "Enter driver"),
            ("fuel_litres", "Fuel consumed (litres)", "Enter litres"),
            ("fuel_cost_mwk", "Fuel cost (MWK)", "Enter cost"),
            ("purpose", "Trip purpose", "Enter purpose")
        ]

        for key, label_text, hint in fields:

            form.add_widget(
                Label(
                    text=label_text,
                    font_size="14sp",
                    halign="left",
                    size_hint_y=None,
                    height=dp(30)
                )
            )

            field = TextInput(
                text=str(selected_trip.get(key, "")),
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )

            self.edit_trip_inputs[key] = field

            form.add_widget(field)

        # SAVE CHANGES BUTTON
        save_button = Button(
            text="SAVE CHANGES",
            size_hint_y=None,
            height=dp(50)
        )

        save_button.bind(
            on_release=self.save_edited_trip
        )

        form.add_widget(save_button)

        # CANCEL BUTTON
        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button.bind(
            on_release=self.show_trips
        )

        form.add_widget(cancel_button)

        scroll.add_widget(form)

        self.content.add_widget(scroll)


    # =====================================
    # SAVE EDITED TRIP
    # =====================================

    def save_edited_trip(self, *args):

        try:

            from datetime import datetime
            import math

            # CHECK EDITING DATA
            if not hasattr(self, "editing_trip"):
                self.show_message(
                    "EDIT TRIP ERROR",
                    "Original trip information is missing."
                )
                return

            if not hasattr(self, "edit_trip_inputs"):
                self.show_message(
                    "EDIT TRIP ERROR",
                    "Editing form is unavailable."
                )
                return

            original = self.editing_trip.copy()

            # COLLECT FORM VALUES
            values = {}

            for field, widget in self.edit_trip_inputs.items():
                values[field] = widget.text.strip()

            required_fields = [
                "trip_date",
                "origin",
                "destination",
                "registration",
                "driver",
                "fuel_litres",
                "fuel_cost_mwk",
                "purpose"
            ]

            for field in required_fields:

                if not values.get(field):

                    self.show_message(
                        "VALIDATION ERROR",
                        "All trip fields are required."
                    )
                    return

            # VALIDATE DATE
            try:

                parsed_date = datetime.strptime(
                    values["trip_date"],
                    "%d/%m/%Y"
                )

                if parsed_date.strftime("%d/%m/%Y") != values["trip_date"]:
                    raise ValueError

            except ValueError:

                self.show_message(
                    "VALIDATION ERROR",
                    "Enter the trip date as DD/MM/YYYY."
                )
                return

            # VALIDATE FUEL
            try:

                fuel_litres = float(values["fuel_litres"])
                fuel_cost = float(values["fuel_cost_mwk"])

                if (
                    not math.isfinite(fuel_litres)
                    or not math.isfinite(fuel_cost)
                    or fuel_litres <= 0
                    or fuel_cost < 0
                ):
                    raise ValueError

            except ValueError:

                self.show_message(
                    "VALIDATION ERROR",
                    "Enter valid fuel litres and fuel cost."
                )
                return

            # LOAD CURRENT RECORDS
            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            vehicles = fleet_core.read_records(
                fleet_core.VEHICLES_FILE
            )

            drivers = fleet_core.read_records(
                fleet_core.DRIVERS_FILE
            )

            if trips is None or vehicles is None or drivers is None:

                self.show_message(
                    "SAVE ERROR",
                    "Required fleet records could not be loaded."
                )
                return

            # IDENTIFY ORIGINAL TRIP
            reference = original.get(
                "trip_reference", ""
            ).strip()

            matches = [
                trip for trip in trips
                if trip.get("trip_reference", "").strip() == reference
            ]

            if len(matches) != 1:

                self.show_message(
                    "SAVE ERROR",
                    "Trip reference could not be identified uniquely."
                )
                return

            if matches[0] != original:

                self.show_message(
                    "SAVE ERROR",
                    "Trip information has changed. Reload Trip History "
                    "before editing again."
                )
                return

            # VALIDATE VEHICLE
            vehicle_exists = any(
                vehicle.get("registration", "").strip().upper()
                == values["registration"].strip().upper()
                for vehicle in vehicles
            )

            if not vehicle_exists:

                self.show_message(
                    "VALIDATION ERROR",
                    "Vehicle is not registered."
                )
                return

            # VALIDATE DRIVER
            driver_exists = any(
                driver.get("name", "").strip().casefold()
                == values["driver"].strip().casefold()
                for driver in drivers
            )

            if not driver_exists:

                self.show_message(
                    "VALIDATION ERROR",
                    "Driver is not registered."
                )
                return

            # PREPARE UPDATED TRIP
            updated = {
                "trip_date": values["trip_date"],
                "origin": values["origin"],
                "destination": values["destination"],
                "registration": values["registration"].upper(),
                "driver": values["driver"],
                "fuel_litres": str(fuel_litres),
                "fuel_cost_mwk": str(fuel_cost),
                "purpose": values["purpose"],
                "trip_reference": reference
            }

            # CREATE BACKUP BEFORE CHANGING DATA
            backup_path = fleet_core.backup_data()

            if not backup_path:

                self.show_message(
                    "BACKUP ERROR",
                    "Verified backup could not be created. "
                    "No changes were made."
                )
                return

            # RELOAD AND CHECK FOR CHANGES
            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            if trips is None:

                self.show_message(
                    "SAVE ERROR",
                    "Trip records could not be reloaded."
                )
                return

            matches = [
                trip for trip in trips
                if trip.get("trip_reference", "").strip() == reference
            ]

            if len(matches) != 1 or matches[0] != original:

                self.show_message(
                    "SAVE ERROR",
                    "Trip changed before saving. No changes were made."
                )
                return

            # REPLACE ONLY THE SELECTED TRIP
            updated_trips = [
                updated if trip.get("trip_reference", "").strip() == reference
                else trip
                for trip in trips
            ]

            success = fleet_core.write_records(
                fleet_core.TRIPS_FILE,
                fleet_core.TRIP_FIELDS,
                updated_trips
            )

            if not success:

                self.show_message(
                    "SAVE ERROR",
                    "Updated trip could not be saved."
                )
                return

            # VERIFY SAVED DATA
            verified_trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            verified = [
                trip for trip in (verified_trips or [])
                if trip.get("trip_reference", "").strip() == reference
            ]

            if len(verified) != 1 or verified[0] != updated:

                self.show_message(
                    "VERIFICATION ERROR",
                    "Saved trip could not be verified. "
                    "Check your backup before further changes."
                )
                return

            # SUCCESS
            self.show_message(
                "SUCCESS",
                "Trip updated successfully.\n\n"
                "Reference: " + reference
            )

            self.show_trips()

        except Exception as error:

            self.show_message(
                "EDIT TRIP ERROR",
                str(error)
            )


    # =====================================
    # SAFE EDIT TRIP OPENING
    # =====================================

    def open_edit_trip_safely(self, selected_trip):

        try:

            self.show_edit_trip(selected_trip)

        except Exception as error:

            self.show_message(
                "EDIT TRIP ERROR",
                str(error)
            )
            

    # =====================================
    # CONFIRM DELETE TRIP
    # =====================================

    def confirm_delete_trip(self, selected_trip):

        try:

            reference = selected_trip.get(
                "trip_reference", ""
            ).strip()

            if not reference:

                self.show_message(
                    "DELETE ERROR",
                    "Trip reference is missing."
                )
                return

            # CREATE CONFIRMATION LAYOUT
            layout = BoxLayout(
                orientation="vertical",
                spacing=dp(12),
                padding=dp(15)
            )

            message = Label(
                text=(
                    "Are you sure you want to delete this trip?\n\n"
                    "Reference: " + reference + "\n\n"
                    "This action cannot be undone."
                ),
                halign="center",
                valign="middle"
            )

            layout.add_widget(message)

            # BUTTON ROW
            button_row = BoxLayout(
                orientation="horizontal",
                spacing=dp(10),
                size_hint_y=None,
                height=dp(48)
            )

            cancel_button = Button(
                text="CANCEL"
            )

            delete_button = Button(
                text="DELETE"
            )

            button_row.add_widget(cancel_button)
            button_row.add_widget(delete_button)

            layout.add_widget(button_row)

            popup = Popup(
                title="CONFIRM TRIP DELETION",
                content=layout,
                size_hint=(0.9, 0.45),
                auto_dismiss=False
            )

            # CANCEL ACTION
            cancel_button.bind(
                on_release=lambda instance: popup.dismiss()
            )

            # CONFIRM DELETION
            def delete_confirmed(instance):

                try:

                    popup.dismiss()

                    # LOAD CURRENT TRIPS
                    trips = fleet_core.read_records(
                        fleet_core.TRIPS_FILE
                    )

                    if trips is None:

                        self.show_message(
                            "DELETE ERROR",
                            "Trip records could not be loaded."
                        )
                        return

                    # IDENTIFY SELECTED TRIP
                    matches = [
                        trip for trip in trips
                        if trip.get(
                            "trip_reference", ""
                        ).strip() == reference
                    ]

                    if len(matches) != 1:

                        self.show_message(
                            "DELETE ERROR",
                            "The selected trip could not be "
                            "identified uniquely."
                        )
                        return

                    # CHECK ORIGINAL RECORD
                    if matches[0] != selected_trip:

                        self.show_message(
                            "DELETE CANCELLED",
                            "This trip has changed since it was "
                            "displayed.\n\nReload Trip History "
                            "before deleting."
                        )
                        return

                    # CREATE BACKUP
                    backup_path = fleet_core.backup_data()

                    if not backup_path:

                        self.show_message(
                            "BACKUP ERROR",
                            "A verified backup could not be created.\n\n"
                            "The trip was not deleted."
                        )
                        return

                    # RELOAD BEFORE DELETION
                    latest_trips = fleet_core.read_records(
                        fleet_core.TRIPS_FILE
                    )

                    if latest_trips is None:

                        self.show_message(
                            "DELETE ERROR",
                            "Trip records could not be reloaded."
                        )
                        return

                    latest_matches = [
                        trip for trip in latest_trips
                        if trip.get(
                            "trip_reference", ""
                        ).strip() == reference
                    ]

                    if (
                        len(latest_matches) != 1
                        or latest_matches[0] != selected_trip
                    ):

                        self.show_message(
                            "DELETE CANCELLED",
                            "Trip information changed before deletion. "
                            "No changes were made."
                        )
                        return

                    # REMOVE ONLY THE SELECTED TRIP
                    updated_trips = [
                        trip for trip in latest_trips
                        if trip.get(
                            "trip_reference", ""
                        ).strip() != reference
                    ]

                    # SAVE UPDATED RECORDS
                    success = fleet_core.write_records(
                        fleet_core.TRIPS_FILE,
                        fleet_core.TRIP_FIELDS,
                        updated_trips
                    )

                    if not success:

                        self.show_message(
                            "DELETE FAILED",
                            "The trip could not be deleted."
                        )
                        return

                    # VERIFY DELETION
                    verified_trips = fleet_core.read_records(
                        fleet_core.TRIPS_FILE
                    )

                    if verified_trips is None:

                        self.show_message(
                            "VERIFICATION ERROR",
                            "Trip deletion could not be verified. "
                            "Check your backup before making changes."
                        )
                        return

                    remaining = [
                        trip for trip in verified_trips
                        if trip.get(
                            "trip_reference", ""
                        ).strip() == reference
                    ]

                    if remaining:

                        self.show_message(
                            "VERIFICATION ERROR",
                            "The selected trip still exists in the "
                            "records. Check your backup."
                        )
                        return

                    # SUCCESS
                    self.show_message(
                        "TRIP DELETED",
                        "Trip deleted successfully.\n\n"
                        "Reference: " + reference + "\n\n"
                        "Backup created successfully."
                    )

                    self.show_trips()

                except Exception as error:

                    self.show_message(
                        "DELETE TRIP ERROR",
                        str(error)
                    )

            delete_button.bind(
                on_release=delete_confirmed
            )

            popup.open()

        except Exception as error:

            self.show_message(
                "DELETE TRIP ERROR",
                str(error)
            )


    
    # =====================================
    # SAVE DRIVER EDIT
    # =====================================

    def save_driver_edit(self, original_driver):

        try:

            from datetime import datetime

            old_name = original_driver.get(
                "name", ""
            ).strip()

            name = self.edit_driver_inputs["name"].text.strip()

            licence_type = (
                self.edit_driver_inputs["licence_type"]
                .text.strip().upper()
            )

            licence_expiry = (
                self.edit_driver_inputs["licence_expiry"]
                .text.strip()
            )

            defensive_expiry = (
                self.edit_driver_inputs["defensive_driving_expiry"]
                .text.strip()
            )

            # VALIDATE REQUIRED FIELDS
            if not all([
                name,
                licence_type,
                licence_expiry,
                defensive_expiry
            ]):

                self.show_message(
                    "Missing information",
                    "All driver fields are required."
                )
                return

            # VALIDATE LICENCE TYPE
            if licence_type not in ["C1", "B"]:

                self.show_message(
                    "Invalid licence type",
                    "Enter C1 or B only."
                )
                return

            # VALIDATE DATES
            for date_value, field_name in [
                (licence_expiry, "Driving licence expiry"),
                (defensive_expiry, "Defensive driving expiry")
            ]:

                try:

                    parsed_date = datetime.strptime(
                        date_value,
                        "%d/%m/%Y"
                    )

                    if parsed_date.strftime("%d/%m/%Y") != date_value:
                        raise ValueError

                except ValueError:

                    self.show_message(
                        "Invalid date",
                        field_name + " must use DD/MM/YYYY format."
                    )
                    return

            # LOAD RECORDS
            drivers = fleet_core.read_records(
                fleet_core.DRIVERS_FILE
            )

            trips = fleet_core.read_records(
                fleet_core.TRIPS_FILE
            )

            if drivers is None or trips is None:

                self.show_message(
                    "Data unavailable",
                    "Driver or trip records could not be read. "
                    "No changes were made."
                )
                return

            # FIND ORIGINAL DRIVER
            matching_indices = [
                index
                for index, item in enumerate(drivers)
                if item.get("name", "").strip().casefold()
                == old_name.casefold()
            ]

            if len(matching_indices) != 1:

                self.show_message(
                    "Driver not found",
                    "The original driver could not be identified uniquely."
                )
                return

            driver_index = matching_indices[0]

            # PREVENT DUPLICATE NAMES
            duplicate = any(
                index != driver_index
                and item.get("name", "").strip().casefold()
                == name.casefold()
                for index, item in enumerate(drivers)
            )

            if duplicate:

                self.show_message(
                    "Duplicate driver",
                    "Another registered driver already uses this name."
                )
                return

            # PRESERVE ORIGINAL RECORDS
            original_drivers = [
                dict(item) for item in drivers
            ]

            original_trips = [
                dict(item) for item in trips
            ]

            # PREPARE UPDATED DRIVER
            updated_driver = dict(drivers[driver_index])

            updated_driver["name"] = name
            updated_driver["licence_type"] = licence_type
            updated_driver["licence_expiry"] = licence_expiry
            updated_driver["defensive_driving_expiry"] = defensive_expiry

            drivers[driver_index] = updated_driver

            # CHECK WHETHER DRIVER NAME CHANGED
            name_changed = (
                old_name.casefold() != name.casefold()
            )

            # UPDATE LINKED TRIPS
            if name_changed:

                for trip in trips:

                    if (
                        trip.get("driver", "").strip().casefold()
                        == old_name.casefold()
                    ):

                        trip["driver"] = name

            # CREATE BACKUP
            backup_path = fleet_core.backup_data()

            if not backup_path:

                self.show_message(
                    "Backup failed",
                    "No changes were made because a backup "
                    "could not be completed."
                )
                return

            # SAVE DRIVER RECORDS
            drivers_saved = fleet_core.write_records(
                fleet_core.DRIVERS_FILE,
                fleet_core.DRIVER_FIELDS,
                drivers
            )

            if not drivers_saved:

                self.show_message(
                    "Update failed",
                    "Driver records could not be updated."
                )
                return

            # SAVE TRIPS IF DRIVER NAME CHANGED
            if name_changed:

                trips_saved = fleet_core.write_records(
                    fleet_core.TRIPS_FILE,
                    fleet_core.TRIP_FIELDS,
                    trips
                )

                if not trips_saved:

                    # RESTORE BOTH ORIGINAL FILES
                    drivers_restored = fleet_core.write_records(
                        fleet_core.DRIVERS_FILE,
                        fleet_core.DRIVER_FIELDS,
                        original_drivers
                    )

                    trips_restored = fleet_core.write_records(
                        fleet_core.TRIPS_FILE,
                        fleet_core.TRIP_FIELDS,
                        original_trips
                    )

                    if drivers_restored and trips_restored:

                        self.show_message(
                            "Update cancelled",
                            "Trip records could not be updated.\n\n"
                            "The original driver and trip records "
                            "were restored."
                        )

                    else:

                        self.show_message(
                            "CRITICAL: RECOVERY FAILED",
                            "Automatic recovery was not fully successful.\n\n"
                            "Check your backup folder before making "
                            "further changes."
                        )

                    return

            # SUCCESS
            self.show_drivers()

            self.show_message(
                "Driver updated",
                "Driver details updated successfully.\n\n"
                f"Name: {name}\n"
                f"Licence Type: {licence_type}\n"
                f"Licence Expiry: {licence_expiry}\n"
                f"Defensive Driving Expiry: {defensive_expiry}"
            )

        except Exception as error:

            self.show_message(
                "DRIVER UPDATE ERROR",
                str(error)
            )


    # =====================================
    # RECORD LIST
    # =====================================

 
    def show_record_list(self, records, card_height):

        # =================================
        # SCROLL CONTAINER
        # =================================

        scroll = ScrollView(
            do_scroll_x=False
        )

        record_list = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=[dp(4), dp(8)]
        )

        record_list.bind(
            minimum_height=record_list.setter("height")
        )

        # =================================
        # CREATE RECORD CARDS
        # =================================

        for details in records:

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=card_height,
                padding=[dp(14), dp(12)]
            )

            # CARD BACKGROUND

            with card.canvas.before:

                Color(0.07, 0.13, 0.23, 1)

                background = RoundedRectangle(
                    pos=card.pos,
                    size=card.size,
                    radius=[dp(14)]
                )

            card.bind(
                pos=lambda instance, value, bg=background:
                setattr(bg, "pos", value),

                size=lambda instance, value, bg=background:
                setattr(bg, "size", value)
            )

            # RECORD DETAILS

            details_label = Label(
                text=details,
                font_size="14sp",
                color=(0.85, 0.92, 1, 1),
                halign="left",
                valign="middle",
                size_hint=(1, 1)
            )

            details_label.bind(
                size=lambda instance, value:
                setattr(instance, "text_size", value)
            )

            card.add_widget(details_label)

            record_list.add_widget(card)

        # =================================
        # DISPLAY RECORDS
        # =================================

        scroll.add_widget(record_list)

        self.content.add_widget(scroll)

    # =====================================
    # MESSAGE POPUP
    # =====================================

    def show_message(self, title, message):

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        message_label = Label(
            text=message,
            halign="left",
            valign="middle"
        )

        message_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        popup_content.add_widget(message_label)

        close_button = Button(
            text="OK",
            size_hint_y=None,
            height=dp(45)
        )

        popup_content.add_widget(close_button)

        popup = Popup(
            title=title,
            content=popup_content,
            size_hint=(0.9, 0.55),
            auto_dismiss=False
        )

        close_button.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # =====================================
    # GENERAL UI HELPERS
    # =====================================

    def add_heading(self, text):

        heading = Label(
            text=text,
            font_size="18sp",
            bold=True,
            size_hint_y=None,
            height=dp(45)
        )

        self.content.add_widget(heading)

    def add_information(self, text):

        information = Label(
            text=text,
            font_size="17sp",
            halign="left",
            valign="top"
        )

        information.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.content.add_widget(information)


if __name__ == "__main__":

    FleetApp().run()
    print("FLEET MAIN ENTRY REACHED")
