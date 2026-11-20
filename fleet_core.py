
"""
VEHICLE & FLEET MANAGEMENT SYSTEM
VERSION 2.1

Technology: Python + CSV
Platform: Pydroid 3

Features:
- Fleet dashboard
- Add, view, edit and delete vehicles
- Add, view, edit and delete drivers
- Record, view, edit and delete trips
- Unique trip references
- Service and licence alerts
- Monthly reports
- Automatic CSV backups
- Safe migration from Version 1.0
"""

import csv
import os
import shutil
import math
import filecmp

from datetime import datetime, date

# ==========================================
# SYSTEM CONFIGURATION
# ==========================================

APP_FOLDER = os.path.dirname(os.path.abspath(__file__))

VEHICLES_FILE = os.path.join(APP_FOLDER, "vehicles.csv")
DRIVERS_FILE = os.path.join(APP_FOLDER, "drivers.csv")
TRIPS_FILE = os.path.join(APP_FOLDER, "trips.csv")
MAINTENANCE_FILE = os.path.join(
    APP_FOLDER,
    "maintenance.csv"
)

BACKUP_FOLDER = os.path.join(APP_FOLDER, "fleet_backups")

VEHICLE_FIELDS = [
    "registration",
    "vehicle_type",
    "licence_category",
    "next_service_date"
]

DRIVER_FIELDS = [
    "name",
    "licence_type",
    "licence_expiry",
    "defensive_driving_expiry"
]

# Version 2.0 adds trip_reference.
# Existing Version 1.0 trip fields are preserved.
TRIP_FIELDS = [
    "trip_date",
    "origin",
    "destination",
    "registration",
    "driver",
    "fuel_litres",
    "fuel_cost_mwk",
    "purpose",
    "trip_reference"
]

MAINTENANCE_FIELDS = [
    "maintenance_reference",
    "service_date",
    "registration",
    "service_description",
    "maintenance_cost_mwk",
    "next_service_date"
]

DATE_FORMAT = "%d/%m/%Y"

SERVICE_ALERT_DAYS = 7
LICENCE_ALERT_DAYS = 30


# ==========================================
# GENERAL DISPLAY FUNCTIONS
# ==========================================

def line():
    print("-" * 60)


def heading(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)



def confirm(prompt):

    while True:

        answer = input(
            "\n" + prompt + " (Y/N): "
        ).strip().upper()

        if answer == "Y":
            return True

        if answer == "N":
            return False

        print("Invalid response. Enter Y or N.")


# ==========================================
# BACKUP MANAGEMENT
# ==========================================




def backup_data():

    backup_path = None

    files = [
    VEHICLES_FILE,
    DRIVERS_FILE,
    TRIPS_FILE,
    MAINTENANCE_FILE
]

    try:

        # ==========================================
        # CHECK SOURCE FILES
        # ==========================================

        for filename in files:

            if not os.path.isfile(filename):

                raise FileNotFoundError(
                    "Required file missing: "
                    + os.path.basename(filename)
                )

        os.makedirs(
            BACKUP_FOLDER,
            exist_ok=True
        )

        # ==========================================
        # CREATE UNIQUE BACKUP FOLDER
        # ==========================================

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        backup_path = os.path.join(
            BACKUP_FOLDER,
            "backup_" + timestamp
        )

        os.makedirs(backup_path)

        # ==========================================
        # COPY AND VERIFY FILES
        # ==========================================

        copied = 0

        for filename in files:

            destination = os.path.join(
                backup_path,
                os.path.basename(filename)
            )

            # Record source size and modification time.
            original_size = os.path.getsize(filename)
            original_modified = os.path.getmtime(filename)

            shutil.copy2(
                filename,
                destination
            )

            if not os.path.isfile(destination):

                raise RuntimeError(
                    "Backup file was not created: "
                    + os.path.basename(filename)
                )

            # Verify source did not change during copying.
            if (
                os.path.getsize(filename) != original_size
                or os.path.getmtime(filename) != original_modified
            ):

                raise RuntimeError(
                    "Source file changed during backup: "
                    + os.path.basename(filename)
                )

            # Verify exact file contents.
            if not filecmp.cmp(
                filename,
                destination,
                shallow=False
            ):

                raise RuntimeError(
                    "Backup verification failed: "
                    + os.path.basename(filename)
                )

            copied += 1

        # ==========================================
        # FINAL BACKUP VERIFICATION
        # ==========================================

        if copied != len(files):

            raise RuntimeError(
                "Not all CSV files were backed up."
            )

        for filename in files:

            destination = os.path.join(
                backup_path,
                os.path.basename(filename)
            )

            if not os.path.isfile(destination):

                raise RuntimeError(
                    "Final backup verification failed: "
                    + os.path.basename(filename)
                )

            if not filecmp.cmp(
                filename,
                destination,
                shallow=False
            ):

                raise RuntimeError(
                    "Final content verification failed: "
                    + os.path.basename(filename)
                )

        # ==========================================
        # SUCCESS
        # ==========================================

        print("\nBACKUP CREATED SUCCESSFULLY.")
        print("Backup folder:", backup_path)
        print("Files copied and verified:", copied)

        return backup_path

    except Exception as error:

        print("\nBACKUP FAILED.")
        print("Reason:", error)

        # Remove incomplete backup data.

        if (
            backup_path is not None
            and os.path.isdir(backup_path)
        ):

            try:

                shutil.rmtree(backup_path)

                print("Incomplete backup folder removed.")

            except OSError as cleanup_error:

                print(
                    "WARNING: Could not remove incomplete backup."
                )

                print("Recovery location:", backup_path)
                print("Cleanup error:", cleanup_error)

        print(
            "Original working files were not intentionally changed."
        )

        return None


# ==========================================
# CSV FILE MANAGEMENT
# ==========================================



def read_records(filename):

    expected_files = {
    VEHICLES_FILE: VEHICLE_FIELDS,
    DRIVERS_FILE: DRIVER_FIELDS,
    TRIPS_FILE: TRIP_FIELDS,
    MAINTENANCE_FILE: MAINTENANCE_FIELDS
}

    if filename not in expected_files:

        print("\nDATA READ FAILED.")
        print("Unknown data file:", filename)

        return None

    expected_fields = expected_files[filename]

    try:

        with open(
            filename,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            if reader.fieldnames is None:

                raise ValueError(
                    "CSV headers are missing."
                )

            if len(reader.fieldnames) != len(set(reader.fieldnames)):

                raise ValueError(
                    "Duplicate CSV headers detected."
                )

            if reader.fieldnames != expected_fields:

                raise ValueError(
                    "Incorrect CSV headers. "
                    + "Expected: "
                    + str(expected_fields)
                    + " Found: "
                    + str(reader.fieldnames)
                )

            records = []

            for row_number, row in enumerate(reader, start=2):

                if None in row:

                    raise ValueError(
                        f"Extra CSV values found on row {row_number}."
                    )

                if any(
                    value is None or not value.strip()
                    for value in row.values()
                ):

                    raise ValueError(
                        f"Missing or empty CSV value on row {row_number}."
                    )

                records.append(row)

            return records

    except FileNotFoundError:

        print("\nDATA FILE MISSING.")
        print("File:", os.path.basename(filename))

        return None

    except (
        OSError,
        csv.Error,
        UnicodeDecodeError,
        ValueError
    ) as error:

        print("\nDATA READ FAILED.")
        print("File:", os.path.basename(filename))
        print("Reason:", error)

        return None


def write_records(filename, fields, records):

    expected_files = {
    VEHICLES_FILE: VEHICLE_FIELDS,
    DRIVERS_FILE: DRIVER_FIELDS,
    TRIPS_FILE: TRIP_FIELDS,
    MAINTENANCE_FILE: MAINTENANCE_FIELDS
}

    if filename not in expected_files:

        print("\nDATA WRITE FAILED.")
        print("Unknown data file.")

        return False

    if fields != expected_files[filename]:

        print("\nDATA WRITE FAILED.")
        print("Incorrect CSV field structure.")

        return False

    temp_file = filename + ".tmp"
    recovery_file = filename + ".recovery_tmp"

    original_data = None
    replacement_started = False

    try:

        # Ensure the original file exists.
        if not os.path.isfile(filename):

            raise FileNotFoundError(
                "Original data file does not exist."
            )

        # Preserve original file bytes.
        with open(filename, "rb") as file:
            original_data = file.read()

        # Validate and normalize records.
        normalized_records = []

        for index, record in enumerate(records, 1):

            if not isinstance(record, dict):

                raise ValueError(
                    f"Record {index} is not a valid dictionary."
                )

            if set(record.keys()) != set(fields):

                raise ValueError(
                    f"Record {index} has an incorrect field structure."
                )

            normalized_record = {}

            for field in fields:

                value = record[field]

                if value is None or not str(value).strip():

                    raise ValueError(
                        f"Record {index} has an empty field: {field}"
                    )

                normalized_record[field] = str(value)

            normalized_records.append(normalized_record)

        # Write to a temporary file.
        with open(
            temp_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fields,
                extrasaction="raise"
            )

            writer.writeheader()
            writer.writerows(normalized_records)

            file.flush()
            os.fsync(file.fileno())

        # Verify temporary file.
        with open(
            temp_file,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            if reader.fieldnames != fields:

                raise ValueError(
                    "Temporary file headers failed verification."
                )

            temporary_records = list(reader)

            if temporary_records != normalized_records:

                raise ValueError(
                    "Temporary file contents failed verification."
                )

        # Replace original file.
        replacement_started = True

        os.replace(
            temp_file,
            filename
        )

        # Verify final working file.
        verified_records = read_records(filename)

        if verified_records != normalized_records:

            raise ValueError(
                "Final saved file verification failed."
            )

        return True

    except Exception as error:

        print("\nDATA WRITE FAILED.")
        print("Reason:", error)

        # Restore original bytes if replacement was attempted.
        if replacement_started and original_data is not None:

            try:

                with open(
                    recovery_file,
                    "wb"
                ) as file:

                    file.write(original_data)
                    file.flush()
                    os.fsync(file.fileno())

                with open(
                    recovery_file,
                    "rb"
                ) as file:

                    if file.read() != original_data:

                        raise ValueError(
                            "Recovery file verification failed."
                        )

                os.replace(
                    recovery_file,
                    filename
                )

                with open(
                    filename,
                    "rb"
                ) as file:

                    if file.read() != original_data:

                        raise ValueError(
                            "Original file restoration failed."
                        )

                print("Original data successfully restored.")

            except Exception as recovery_error:

                print("\nCRITICAL: AUTOMATIC RECOVERY FAILED.")
                print("Recovery reason:", recovery_error)
                print("Do not delete the recovery or backup files.")
                print("Manual recovery may be required.")

        else:

            print("The original file was not replaced.")

        return False

    finally:

        for temporary in (temp_file, recovery_file):

            if os.path.exists(temporary):

                try:
                    os.remove(temporary)

                except OSError:
                    print(
                        "WARNING: Could not remove temporary file:",
                        temporary
                    )



def save_record(filename, fields, record):

    expected_files = {
    VEHICLES_FILE: VEHICLE_FIELDS,
    DRIVERS_FILE: DRIVER_FIELDS,
    TRIPS_FILE: TRIP_FIELDS,
    MAINTENANCE_FILE: MAINTENANCE_FIELDS
}

    # Validate destination.
    if filename not in expected_files:

        print("\nRECORD NOT SAVED.")
        print("Unknown data file.")

        return False

    if fields != expected_files[filename]:

        print("\nRECORD NOT SAVED.")
        print("Incorrect CSV field structure.")

        return False

    temp_file = filename + ".save_tmp"
    recovery_file = filename + ".recovery_tmp"

    original_exists = os.path.isfile(filename)
    replacement_started = False
    original_data = None

    try:

        # Validate the new record.
        if not isinstance(record, dict):

            raise ValueError(
                "Record must be a dictionary."
            )

        for field in fields:

            if field not in record:

                raise ValueError(
                    "Missing required field: " + field
                )

            value = record[field]

            if value is None or not str(value).strip():

                raise ValueError(
                    "Required field is empty: " + field
                )

        # Read and preserve the original file bytes.
        if not original_exists:

            raise FileNotFoundError(
                "Original data file does not exist."
            )

        with open(filename, "rb") as file:
            original_data = file.read()

        # Read the original records.
        records = read_records(filename)

        if records is None:

            raise ValueError(
                "Existing records could not be read safely."
            )

        # Prepare updated records.
        original_records = [
            dict(item) for item in records
        ]

        updated_records = original_records + [
            {
                field: str(record[field])
                for field in fields
            }
        ]

        # Write to a separate temporary file.
        with open(
            temp_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fields,
                extrasaction="raise"
            )

            writer.writeheader()
            writer.writerows(updated_records)

            file.flush()
            os.fsync(file.fileno())

        # Verify temporary file.
        with open(
            temp_file,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            if reader.fieldnames != fields:

                raise ValueError(
                    "Temporary file headers are incorrect."
                )

            temporary_records = list(reader)

            if temporary_records != updated_records:

                raise ValueError(
                    "Temporary record verification failed."
                )

        # Replace the working file.
        replacement_started = True

        os.replace(
            temp_file,
            filename
        )

        # Verify the complete saved file.
        verified_records = read_records(filename)

        if verified_records != updated_records:

            raise ValueError(
                "Saved record verification failed."
            )

        return True

    except Exception as error:

        print("\nRECORD SAVE FAILED.")
        print("Reason:", error)

        # Restore original bytes only if replacement was attempted.
        if replacement_started and original_data is not None:

            try:

                # Write exact original bytes to recovery file.
                with open(
                    recovery_file,
                    "wb"
                ) as file:

                    file.write(original_data)
                    file.flush()
                    os.fsync(file.fileno())

                # Verify exact recovery copy.
                with open(
                    recovery_file,
                    "rb"
                ) as file:

                    recovered_data = file.read()

                if recovered_data != original_data:

                    raise ValueError(
                        "Recovery file verification failed."
                    )

                # Restore original file.
                os.replace(
                    recovery_file,
                    filename
                )

                # Verify restored file byte-for-byte.
                with open(
                    filename,
                    "rb"
                ) as file:

                    restored_data = file.read()

                if restored_data != original_data:

                    raise ValueError(
                        "Original file restoration failed."
                    )

                print("Original records successfully restored.")

            except Exception as recovery_error:

                print("\nCRITICAL: AUTOMATIC RECOVERY FAILED.")
                print("Recovery reason:", recovery_error)
                print("Do not delete the recovery or backup files.")
                print("Manual recovery may be required.")

        else:

            print("The original file was not replaced.")

        return False

    finally:

        for temporary in (temp_file, recovery_file):

            if os.path.exists(temporary):

                try:
                    os.remove(temporary)

                except OSError:
                    print(
                        "WARNING: Could not remove temporary file:",
                        temporary
                    )


def next_trip_reference(trips):

    highest = 0
    used_references = set()

    for index, trip in enumerate(trips, 1):

        reference = trip.get(
            "trip_reference", ""
        ).strip()

        if not reference:
            continue

        if (
            not reference.upper().startswith("TRP")
            or not reference[3:].isdigit()
        ):

            raise ValueError(
                f"Invalid trip reference in record {index}: "
                f"{reference}"
            )

        reference_key = reference.casefold()

        if reference_key in used_references:

            raise ValueError(
                f"Duplicate trip reference detected: "
                f"{reference}"
            )

        used_references.add(reference_key)

        highest = max(
            highest,
            int(reference[3:])
        )

    return "TRP" + str(highest + 1).zfill(6)


def next_maintenance_reference(records):

    existing_numbers = []

    for record in records:

        reference = record.get(
            "maintenance_reference", ""
        ).strip().upper()

        if not reference.startswith("MNT"):
            raise ValueError(
                "Invalid maintenance reference found."
            )

        number_part = reference[3:]

        if not number_part.isdigit():
            raise ValueError(
                "Invalid maintenance reference format."
            )

        existing_numbers.append(int(number_part))

    next_number = max(existing_numbers, default=0) + 1

    return "MNT{:06d}".format(next_number)


def delete_vehicle_record(registration):

    registration = str(registration).strip().upper()

    if not registration:
        return False, "Vehicle registration is required."

    # ==========================================
    # LOAD RECORDS
    # ==========================================

    vehicles = read_records(VEHICLES_FILE)
    trips = read_records(TRIPS_FILE)
    maintenance = read_records(MAINTENANCE_FILE)

    if any(
        records is None
        for records in (vehicles, trips, maintenance)
    ):
        return False, "Required records could not be loaded."

    # ==========================================
    # LOCATE VEHICLE
    # ==========================================

    matches = [
        vehicle for vehicle in vehicles
        if vehicle["registration"].strip().upper()
        == registration
    ]

    if len(matches) != 1:
        return False, "Vehicle is missing or duplicated."

    original_vehicle = dict(matches[0])

    # ==========================================
    # PROTECT TRIP HISTORY
    # ==========================================

    linked_trips = [
        trip for trip in trips
        if trip["registration"].strip().upper()
        == registration
    ]

    if linked_trips:
        return False, (
            "Vehicle cannot be deleted because "
            "it has linked trip history."
        )

    # ==========================================
    # PROTECT MAINTENANCE HISTORY
    # ==========================================

    linked_maintenance = [
        record for record in maintenance
        if record["registration"].strip().upper()
        == registration
    ]

    if linked_maintenance:
        return False, (
            "Vehicle cannot be deleted because "
            "it has linked maintenance history."
        )

    # ==========================================
    # CREATE VERIFIED BACKUP
    # ==========================================

    safety_backup = backup_data()

    if (
        not safety_backup
        or not os.path.isdir(safety_backup)
    ):
        return False, "Safety backup failed. No records were changed."

    backup_file = os.path.join(
        safety_backup,
        os.path.basename(VEHICLES_FILE)
    )

    try:

        if not filecmp.cmp(
            VEHICLES_FILE,
            backup_file,
            shallow=False
        ):
            return False, "Vehicle backup verification failed."

    except Exception as error:

        return False, "Backup verification error: " + str(error)

    # ==========================================
    # RECHECK RECORDS AFTER BACKUP
    # ==========================================

    current_vehicles = read_records(VEHICLES_FILE)
    current_trips = read_records(TRIPS_FILE)
    current_maintenance = read_records(MAINTENANCE_FILE)

    if any(
        records is None
        for records in (
            current_vehicles,
            current_trips,
            current_maintenance
        )
    ):
        return False, "Latest records could not be verified."

    current_matches = [
        vehicle for vehicle in current_vehicles
        if vehicle["registration"].strip().upper()
        == registration
    ]

    if (
        len(current_matches) != 1
        or current_matches[0] != original_vehicle
    ):
        return False, "Vehicle changed during deletion. Reload and retry."

    if any(
        trip["registration"].strip().upper() == registration
        for trip in current_trips
    ):
        return False, "Vehicle now has linked trip history."

    if any(
        record["registration"].strip().upper() == registration
        for record in current_maintenance
    ):
        return False, "Vehicle now has linked maintenance history."

    # ==========================================
    # PREPARE DELETION
    # ==========================================

    remaining_vehicles = [
        vehicle for vehicle in current_vehicles
        if vehicle["registration"].strip().upper()
        != registration
    ]

    if len(remaining_vehicles) != len(current_vehicles) - 1:
        return False, "Vehicle deletion could not be prepared."

    # ==========================================
    # SAVE VEHICLE REGISTER
    # ==========================================

    try:

        if not write_records(
            VEHICLES_FILE,
            VEHICLE_FIELDS,
            remaining_vehicles
        ):
            raise RuntimeError(
                "Vehicle register could not be saved."
            )

        # ==========================================
        # VERIFY DELETION
        # ==========================================

        saved_vehicles = read_records(VEHICLES_FILE)

        if saved_vehicles != remaining_vehicles:
            raise RuntimeError(
                "Vehicle deletion verification failed."
            )

        if any(
            vehicle["registration"].strip().upper()
            == registration
            for vehicle in saved_vehicles
        ):
            raise RuntimeError(
                "Deleted vehicle is still present."
            )

    except Exception as error:

        # ==========================================
        # RESTORE ORIGINAL VEHICLE FILE
        # ==========================================

        temporary_file = VEHICLES_FILE + ".rollback_tmp"

        try:

            shutil.copy2(
                backup_file,
                temporary_file
            )

            if not filecmp.cmp(
                backup_file,
                temporary_file,
                shallow=False
            ):
                raise OSError(
                    "Temporary recovery verification failed."
                )

            os.replace(
                temporary_file,
                VEHICLES_FILE
            )

            if not filecmp.cmp(
                backup_file,
                VEHICLES_FILE,
                shallow=False
            ):
                raise OSError(
                    "Restored vehicle file verification failed."
                )

        except Exception as recovery_error:

            return False, (
                "CRITICAL: Vehicle deletion failed and "
                "automatic recovery was incomplete. "
                "Do not modify the backup folder. "
                "Backup: " + str(safety_backup)
                + " Recovery error: " + str(recovery_error)
            )

        finally:

            if os.path.exists(temporary_file):

                try:
                    os.remove(temporary_file)
                except OSError:
                    pass

        return False, (
            "Vehicle deletion failed. "
            "Original vehicle records were restored. "
            + str(error)
        )

    return True, "Vehicle deleted successfully."


def add_maintenance_record(
    service_date,
    registration,
    service_description,
    maintenance_cost_mwk,
    next_service_date
):

    import math
    from datetime import datetime

    # LOAD EXISTING RECORDS

    maintenance = read_records(MAINTENANCE_FILE)
    vehicles = read_records(VEHICLES_FILE)

    if maintenance is None or vehicles is None:

        return False, "Required records could not be loaded.", None

    # VALIDATE REQUIRED FIELDS

    values = [
        service_date,
        registration,
        service_description,
        maintenance_cost_mwk,
        next_service_date
    ]

    if any(
        value is None or not str(value).strip()
        for value in values
    ):

        return False, "All maintenance fields are required.", None

    registration = str(registration).strip().upper()
    service_description = " ".join(
        str(service_description).split()
    )

    # VALIDATE DATES

    try:

        service_parsed = datetime.strptime(
            str(service_date).strip(),
            "%d/%m/%Y"
        )

        next_service_parsed = datetime.strptime(
            str(next_service_date).strip(),
            "%d/%m/%Y"
        )

        if (
            service_parsed.strftime("%d/%m/%Y")
            != str(service_date).strip()
        ):
            raise ValueError

        if (
            next_service_parsed.strftime("%d/%m/%Y")
            != str(next_service_date).strip()
        ):
            raise ValueError

        if next_service_parsed <= service_parsed:
            return False, "Next service date must be later than service date.", None

    except ValueError:

        return False, "Enter valid dates using DD/MM/YYYY.", None

    # VALIDATE MAINTENANCE COST

    try:

        cost = float(maintenance_cost_mwk)

        if not math.isfinite(cost) or cost < 0:
            raise ValueError

    except (ValueError, TypeError):

        return False, "Maintenance cost must be a valid non-negative number.", None

    # VERIFY VEHICLE

    matching_vehicles = [
        vehicle for vehicle in vehicles
        if vehicle.get("registration", "").strip().upper()
        == registration
    ]

    if len(matching_vehicles) != 1:

        return False, "Vehicle registration is not valid or is duplicated.", None

    # GENERATE UNIQUE REFERENCE

    try:

        reference = next_maintenance_reference(maintenance)

    except Exception as error:

        return False, "Reference generation failed: " + str(error), None

    # PREPARE RECORD

    record = {
        "maintenance_reference": reference,
        "service_date": str(service_date).strip(),
        "registration": registration,
        "service_description": service_description,
        "maintenance_cost_mwk": "{:.2f}".format(cost),
        "next_service_date": str(next_service_date).strip()
    }

    # SAVE RECORD

    try:

        saved = save_record(
            MAINTENANCE_FILE,
            MAINTENANCE_FIELDS,
            record
        )

    except Exception as error:

        return False, "Maintenance save failed: " + str(error), None

    if not saved:

        return False, "Maintenance record could not be saved.", None

    # VERIFY SAVED RECORD

    verified = read_records(MAINTENANCE_FILE)

    matches = [
        item for item in (verified or [])
        if item.get("maintenance_reference") == reference
    ]

    if len(matches) != 1 or matches[0] != record:

        return False, "Saved maintenance record failed verification.", None

    return True, "Maintenance record saved successfully.", reference


def update_maintenance_record(
    reference,
    service_date,
    registration,
    service_description,
    maintenance_cost_mwk,
    next_service_date
):

    import math
    from datetime import datetime

    # LOAD EXISTING DATA

    maintenance = read_records(MAINTENANCE_FILE)
    vehicles = read_records(VEHICLES_FILE)

    if maintenance is None or vehicles is None:
        return False, "Required records could not be loaded."

    # LOCATE ORIGINAL RECORD

    reference = str(reference).strip().upper()

    matches = [
        record for record in maintenance
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(matches) != 1:
        return False, "Maintenance record is missing or duplicated."

    original = matches[0]

    # VALIDATE REQUIRED FIELDS

    values = [
        service_date,
        registration,
        service_description,
        maintenance_cost_mwk,
        next_service_date
    ]

    if any(
        value is None or not str(value).strip()
        for value in values
    ):
        return False, "All maintenance fields are required."

    registration = str(registration).strip().upper()
    service_date = str(service_date).strip()
    next_service_date = str(next_service_date).strip()

    service_description = " ".join(
        str(service_description).split()
    )

    # VALIDATE DATES

    try:

        service_parsed = datetime.strptime(
            service_date, "%d/%m/%Y"
        )

        next_service_parsed = datetime.strptime(
            next_service_date, "%d/%m/%Y"
        )

        if (
            service_parsed.strftime("%d/%m/%Y") != service_date
            or next_service_parsed.strftime("%d/%m/%Y")
            != next_service_date
        ):
            raise ValueError

        if next_service_parsed <= service_parsed:
            return False, "Next service date must be later than service date."

    except ValueError:

        return False, "Enter valid dates using DD/MM/YYYY."

    # VALIDATE COST

    try:

        cost = float(maintenance_cost_mwk)

        if not math.isfinite(cost) or cost < 0:
            raise ValueError

    except (ValueError, TypeError):

        return False, "Maintenance cost must be a valid non-negative number."

    # VERIFY VEHICLE

    matching_vehicles = [
        vehicle for vehicle in vehicles
        if vehicle.get("registration", "").strip().upper()
        == registration
    ]

    if len(matching_vehicles) != 1:
        return False, "Vehicle registration is invalid or duplicated."

    # PREPARE UPDATED RECORD

    updated = {
        "maintenance_reference": reference,
        "service_date": service_date,
        "registration": registration,
        "service_description": service_description,
        "maintenance_cost_mwk": "{:.2f}".format(cost),
        "next_service_date": next_service_date
    }

    # CONFIRM RECORD HAS NOT CHANGED

    current = read_records(MAINTENANCE_FILE)

    if current is None:
        return False, "Maintenance records could not be reloaded."

    current_matches = [
        record for record in current
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(current_matches) != 1 or current_matches[0] != original:
        return False, "Record changed during editing. Reload and try again."

    # CREATE BACKUP BEFORE EDITING

    backup_path = backup_data()

    if not backup_path:
        return False, "Backup failed. Maintenance record was not edited."

    # RECHECK BEFORE WRITING

    current = read_records(MAINTENANCE_FILE)

    if current is None:
        return False, "Could not verify records after backup."

    current_matches = [
        record for record in current
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(current_matches) != 1 or current_matches[0] != original:
        return False, "Record changed after backup. Editing cancelled."

    # REPLACE RECORD

    updated_records = []

    for record in current:

        if record.get("maintenance_reference", "").strip().upper() == reference:
            updated_records.append(updated)
        else:
            updated_records.append(record)

    try:

        saved = write_records(
            MAINTENANCE_FILE,
            MAINTENANCE_FIELDS,
            updated_records
        )

    except Exception as error:

        return False, "Maintenance update failed: " + str(error)

    if not saved:
        return False, "Maintenance record could not be updated."

    # VERIFY FINAL DATA

    verified = read_records(MAINTENANCE_FILE)

    if verified is None:
        return False, "Update verification failed. Check the backup."

    final_matches = [
        record for record in verified
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(final_matches) != 1 or final_matches[0] != updated:
        return False, "Updated record failed verification. Check the backup."

    return True, "Maintenance record updated successfully."

def delete_maintenance_record(reference):

    # LOAD EXISTING RECORDS

    maintenance = read_records(MAINTENANCE_FILE)

    if maintenance is None:
        return False, "Maintenance records could not be loaded."

    reference = str(reference).strip().upper()

    # LOCATE RECORD

    matches = [
        record for record in maintenance
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(matches) != 1:
        return False, "Maintenance record is missing or duplicated."

    original = matches[0]

    # RECHECK BEFORE BACKUP

    current = read_records(MAINTENANCE_FILE)

    if current is None:
        return False, "Could not reload maintenance records."

    current_matches = [
        record for record in current
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(current_matches) != 1 or current_matches[0] != original:
        return False, "Maintenance record changed. Deletion cancelled."

    # CREATE VERIFIED BACKUP

    backup_path = backup_data()

    if not backup_path:
        return False, "Backup failed. Maintenance record was not deleted."

    # RECHECK AFTER BACKUP

    current = read_records(MAINTENANCE_FILE)

    if current is None:
        return False, "Could not verify records after backup."

    current_matches = [
        record for record in current
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if len(current_matches) != 1 or current_matches[0] != original:
        return False, "Record changed after backup. Deletion cancelled."

    # PREPARE REMAINING RECORDS

    remaining = [
        record for record in current
        if record.get("maintenance_reference", "").strip().upper()
        != reference
    ]

    if len(remaining) != len(current) - 1:
        return False, "Deletion verification failed before writing."

    # DELETE RECORD

    try:

        saved = write_records(
            MAINTENANCE_FILE,
            MAINTENANCE_FIELDS,
            remaining
        )

    except Exception as error:

        return False, "Maintenance deletion failed: " + str(error)

    if not saved:
        return False, "Maintenance record could not be deleted."

    # VERIFY DELETION

    verified = read_records(MAINTENANCE_FILE)

    if verified is None:
        return False, "Deletion verification failed. Check the backup."

    remaining_matches = [
        record for record in verified
        if record.get("maintenance_reference", "").strip().upper()
        == reference
    ]

    if remaining_matches:
        return False, "Maintenance record still exists after deletion."

    if len(verified) != len(remaining):
        return False, "Final maintenance record count is incorrect."

    return True, "Maintenance record deleted successfully."


def ensure_files():

    try:

        # ==========================================
        # 1. PREPARE BACKUP DIRECTORY
        # ==========================================

        os.makedirs(
            BACKUP_FOLDER,
            exist_ok=True
        )

        if not os.path.isdir(BACKUP_FOLDER):

            raise OSError(
                "Backup path is not a directory."
            )

        # ==========================================
        # 2. DEFINE REQUIRED FILES
        # ==========================================

        core_files = [
            (VEHICLES_FILE, VEHICLE_FIELDS),
            (DRIVERS_FILE, DRIVER_FIELDS),
            (TRIPS_FILE, TRIP_FIELDS)
        ]

        maintenance_file = (
            MAINTENANCE_FILE,
            MAINTENANCE_FIELDS
        )

        all_files = core_files + [
            maintenance_file
        ]

        # ==========================================
        # 3. REJECT INVALID FILE PATHS
        # ==========================================

        for filename, fields in all_files:

            if (
                os.path.exists(filename)
                and not os.path.isfile(filename)
            ):

                print("\nDATA FILE ERROR.")
                print(
                    "Expected a file but found another object:",
                    os.path.basename(filename)
                )

                return False

        # ==========================================
        # 4. CHECK EXISTING CORE FILES
        # ==========================================

        existing_core = [
            os.path.exists(filename)
            for filename, fields in core_files
        ]

        existing_core_files = [
            os.path.isfile(filename)
            for filename, fields in core_files
        ]

        maintenance_exists = os.path.exists(
            MAINTENANCE_FILE
        )

        # ==========================================
        # 5. HANDLE NEW INSTALLATION
        # ==========================================

        if not any(existing_core):

            if maintenance_exists:

                print("\nDATA FILE ERROR.")
                print(
                    "Maintenance file exists without core fleet files."
                )

                print("Automatic initialization stopped.")

                return False

            print("\nNEW INSTALLATION DETECTED.")
            print("Creating initial fleet data files...")

            created_files = []

            try:

                for filename, fields in all_files:

                    with open(
                        filename,
                        "x",
                        newline="",
                        encoding="utf-8"
                    ) as file:

                        writer = csv.DictWriter(
                            file,
                            fieldnames=fields
                        )

                        writer.writeheader()

                        file.flush()
                        os.fsync(file.fileno())

                    created_files.append(filename)

                    print(
                        "Created:",
                        os.path.basename(filename)
                    )

            except Exception:

                print("\nINITIAL FILE CREATION FAILED.")
                print("Removing incomplete new installation files.")

                for filename in created_files:

                    try:
                        os.remove(filename)

                    except OSError:
                        pass

                raise

        # ==========================================
        # 6. PROTECT EXISTING CORE INSTALLATION
        # ==========================================

        else:

            if not all(existing_core_files):

                print("\nDATA FILE ERROR.")
                print("One or more required fleet files are missing.")

                for filename, fields in core_files:

                    if not os.path.isfile(filename):

                        print(
                            "Missing:",
                            os.path.basename(filename)
                        )

                print("\nAUTOMATIC INITIALIZATION STOPPED.")
                print("Existing records have been protected.")
                print("Check your backups before recovery.")

                return False

            # ======================================
            # 7. CREATE NEW MAINTENANCE FILE
            # ======================================

            if not maintenance_exists:

                print("\nMAINTENANCE FILE NOT FOUND.")
                print("Creating maintenance.csv...")

                with open(
                    MAINTENANCE_FILE,
                    "x",
                    newline="",
                    encoding="utf-8"
                ) as file:

                    writer = csv.DictWriter(
                        file,
                        fieldnames=MAINTENANCE_FIELDS
                    )

                    writer.writeheader()

                    file.flush()
                    os.fsync(file.fileno())

                print("Maintenance file created successfully.")

        # ==========================================
        # 8. CHECK FOR EMPTY FILES
        # ==========================================

        for filename, fields in all_files:

            if os.path.getsize(filename) == 0:

                print("\nDATA FILE ERROR.")
                print(
                    "Existing file is empty:",
                    os.path.basename(filename)
                )

                print("Automatic initialization stopped.")
                print("Check your backups before continuing.")

                return False

        # ==========================================
        # 9. VALIDATE VEHICLE AND DRIVER FILES
        # ==========================================

        for filename, fields in (
            (VEHICLES_FILE, VEHICLE_FIELDS),
            (DRIVERS_FILE, DRIVER_FIELDS)
        ):

            records = read_records(filename)

            if records is None:

                print("\nSYSTEM INITIALIZATION STOPPED.")
                print(
                    "Invalid data structure in:",
                    os.path.basename(filename)
                )

                return False

        # ==========================================
        # 10. VALIDATE AND MIGRATE TRIP DATA
        # ==========================================

        if not migrate_trips():

            print("\nSYSTEM INITIALIZATION STOPPED.")
            print("Trip migration or validation failed.")

            return False

        # ==========================================
        # 11. VERIFY ALL DATA FILES
        # ==========================================

        for filename, fields in all_files:

            records = read_records(filename)

            if records is None:

                print("\nSYSTEM INITIALIZATION FAILED.")
                print(
                    "Could not validate:",
                    os.path.basename(filename)
                )

                return False

        # ==========================================
        # 12. INITIALIZATION SUCCESS
        # ==========================================

        print("\nALL REQUIRED DATA FILES ARE AVAILABLE.")
        print("Data initialization completed successfully.")

        return True

    except (OSError, csv.Error) as error:

        print("\nSYSTEM INITIALIZATION FAILED.")
        print("Reason:", error)

        return False


def migrate_trips():

    legacy_fields = TRIP_FIELDS[:-1]

    # ==========================================
    # 1. READ AND VALIDATE VEHICLE RECORDS
    # ==========================================

    vehicles = read_records(VEHICLES_FILE)

    if vehicles is None:

        print("\nMIGRATION STOPPED.")
        print("Vehicle records could not be read.")

        return False

    vehicle_registrations = set()

    for index, vehicle in enumerate(vehicles, 1):

        registration = vehicle.get(
            "registration", ""
        ).strip()

        if not registration:

            print("\nMIGRATION STOPPED.")
            print("Empty vehicle registration at record:", index)

            return False

        key = registration.casefold()

        if key in vehicle_registrations:

            print("\nMIGRATION STOPPED.")
            print("Duplicate vehicle registration:", registration)

            return False

        vehicle_registrations.add(key)

    # ==========================================
    # 2. READ AND VALIDATE DRIVER RECORDS
    # ==========================================

    drivers = read_records(DRIVERS_FILE)

    if drivers is None:

        print("\nMIGRATION STOPPED.")
        print("Driver records could not be read.")

        return False

    driver_names = set()

    for index, driver in enumerate(drivers, 1):

        name = driver.get(
            "name", ""
        ).strip()

        if not name:

            print("\nMIGRATION STOPPED.")
            print("Empty driver name at record:", index)

            return False

        key = name.casefold()

        if key in driver_names:

            print("\nMIGRATION STOPPED.")
            print("Duplicate driver name:", name)

            return False

        driver_names.add(key)

    # ==========================================
    # 3. READ ORIGINAL TRIP DATA
    # ==========================================

    try:

        with open(
            TRIPS_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            old_fields = reader.fieldnames

            if old_fields not in (
                legacy_fields,
                TRIP_FIELDS
            ):

                print("\nMIGRATION STOPPED.")
                print("Unexpected trip CSV structure.")
                print("Found headers:", old_fields)

                return False

            trips = []

            for row_number, row in enumerate(reader, 2):

                if (
                    None in row
                    or any(
                        value is None
                        for value in row.values()
                    )
                ):

                    print("\nMIGRATION STOPPED.")
                    print("Invalid CSV row:", row_number)

                    return False

                if "trip_reference" not in row:

                    row["trip_reference"] = ""

                trips.append(row)

    except (
        OSError,
        csv.Error,
        UnicodeDecodeError
    ) as error:

        print("\nMIGRATION STOPPED.")
        print("Could not read trip data:", error)

        return False

    # ==========================================
    # 4. VALIDATE ALL TRIP RECORDS
    # ==========================================

    used_references = set()
    highest = 0

    required_fields = TRIP_FIELDS[:-1]

    for row_number, trip in enumerate(trips, 2):

        # Check mandatory fields.
        for field in required_fields:

            value = trip.get(field, "")

            if not value.strip():

                print("\nMIGRATION STOPPED.")
                print(
                    "Missing",
                    field,
                    "in trip row",
                    row_number
                )

                return False

        # Validate date and canonical format.
        try:

            parsed_date = datetime.strptime(
                trip["trip_date"],
                DATE_FORMAT
            )

            if (
                parsed_date.strftime(DATE_FORMAT)
                != trip["trip_date"]
            ):

                raise ValueError

        except ValueError:

            print("\nMIGRATION STOPPED.")
            print("Invalid trip date on row:", row_number)

            return False

        # Validate fuel and cost.
        try:

            fuel = float(trip["fuel_litres"])
            cost = float(trip["fuel_cost_mwk"])

            if (
                not math.isfinite(fuel)
                or not math.isfinite(cost)
                or fuel < 0
                or cost < 0
            ):

                raise ValueError

        except (ValueError, TypeError):

            print("\nMIGRATION STOPPED.")
            print(
                "Invalid fuel or cost on row:",
                row_number
            )

            return False

        # Validate vehicle relationship.
        registration_key = (
            trip["registration"].strip().casefold()
        )

        if registration_key not in vehicle_registrations:

            print("\nMIGRATION STOPPED.")
            print(
                "Trip row",
                row_number,
                "references an unregistered vehicle:",
                trip["registration"]
            )

            return False

        # Validate driver relationship.
        driver_key = (
            trip["driver"].strip().casefold()
        )

        if driver_key not in driver_names:

            print("\nMIGRATION STOPPED.")
            print(
                "Trip row",
                row_number,
                "references an unregistered driver:",
                trip["driver"]
            )

            return False

        # Validate existing trip references.
        reference = trip["trip_reference"].strip()

        if reference:

            if (
                not reference.upper().startswith("TRP")
                or not reference[3:].isdigit()
            ):

                print("\nMIGRATION STOPPED.")
                print("Invalid trip reference:", reference)

                return False

            reference_key = reference.casefold()

            if reference_key in used_references:

                print("\nMIGRATION STOPPED.")
                print("Duplicate trip reference:", reference)

                return False

            used_references.add(reference_key)

            highest = max(
                highest,
                int(reference[3:])
            )

    # ==========================================
    # 5. CHECK WHETHER MIGRATION IS REQUIRED
    # ==========================================

    needs_migration = (
        old_fields != TRIP_FIELDS
        or any(
            not trip["trip_reference"].strip()
            for trip in trips
        )
    )

    if not needs_migration:

        print("Trip data structure is up to date.")
        print("Vehicle and driver relationships verified.")
        print("All trip records passed validation.")

        return True

    print("\nPREPARING TRIP DATA MIGRATION...")

    # ==========================================
    # 6. CREATE AND VERIFY SAFETY BACKUP
    # ==========================================

    safety_backup = backup_data()

    if (
        safety_backup is None
        or not os.path.isdir(safety_backup)
    ):

        print("\nMIGRATION STOPPED.")
        print("Safety backup could not be created.")

        return False

    required_files = [
        "vehicles.csv",
        "drivers.csv",
        "trips.csv"
    ]

    for filename in required_files:

        backup_file = os.path.join(
            safety_backup,
            filename
        )

        if not os.path.isfile(backup_file):

            print("\nMIGRATION STOPPED.")
            print("Safety backup is incomplete.")
            print("Missing:", filename)

            return False

    # Verify original trip backup against working file.
    original_backup = os.path.join(
        safety_backup,
        "trips.csv"
    )

    if not filecmp.cmp(
        TRIPS_FILE,
        original_backup,
        shallow=False
    ):

        print("\nMIGRATION STOPPED.")
        print("Original trip backup verification failed.")

        return False

    # ==========================================
    # 7. ASSIGN MISSING TRIP REFERENCES
    # ==========================================

    for trip in trips:

        reference = trip["trip_reference"].strip()

        if not reference:

            while True:

                highest += 1

                new_reference = (
                    "TRP" + str(highest).zfill(6)
                )

                if new_reference.casefold() not in used_references:

                    break

            trip["trip_reference"] = new_reference

            used_references.add(
                new_reference.casefold()
            )

    # ==========================================
    # 8. WRITE MIGRATED TRIP RECORDS
    # ==========================================

    saved = write_records(
        TRIPS_FILE,
        TRIP_FIELDS,
        trips
    )

    verified = False

    if saved:

        saved_trips = read_records(TRIPS_FILE)

        if saved_trips is not None:

            verified = (
                saved_trips == trips
            )

    # ==========================================
    # 9. RECOVER ORIGINAL DATA IF NECESSARY
    # ==========================================

    if not verified:

        print("\nMIGRATION FAILED.")
        print("Attempting automatic recovery...")

        recovery_file = (
            TRIPS_FILE + ".rollback_tmp"
        )

        try:

            shutil.copy2(
                original_backup,
                recovery_file
            )

            if not filecmp.cmp(
                original_backup,
                recovery_file,
                shallow=False
            ):

                raise RuntimeError(
                    "Recovery copy verification failed."
                )

            os.replace(
                recovery_file,
                TRIPS_FILE
            )

            if not filecmp.cmp(
                original_backup,
                TRIPS_FILE,
                shallow=False
            ):

                raise RuntimeError(
                    "Restored trip file verification failed."
                )

            print("Original trip data restored successfully.")

        except Exception as recovery_error:

            print("\nCRITICAL RECOVERY FAILURE.")
            print("Manual recovery may be required.")
            print("Reason:", recovery_error)
            print("Safety backup:", safety_backup)

        finally:

            if os.path.exists(recovery_file):

                try:
                    os.remove(recovery_file)

                except OSError:
                    pass

        return False

    # ==========================================
    # 10. MIGRATION SUCCESS
    # ==========================================

    print("\nTRIP MIGRATION COMPLETED SUCCESSFULLY.")
    print("Existing trip records preserved.")
    print("Trip references assigned and verified.")
    print("Vehicle relationships verified.")
    print("Driver relationships verified.")
    print("Safety backup:", safety_backup)

    return True


# ==========================================
# INPUT VALIDATION
# ==========================================

def ask_text(prompt):

    while True:

        value = input(prompt).strip()

        if value:
            return value

        print("This field cannot be empty.")



def ask_date(prompt):

    while True:

        value = input(
            prompt + " (DD/MM/YYYY): "
        ).strip()

        try:

            if not value:
                raise ValueError

            parsed_date = datetime.strptime(
                value,
                DATE_FORMAT
            )

            return parsed_date.strftime(DATE_FORMAT)

        except ValueError:

            print(
                "Invalid date. Enter a real date "
                "in DD/MM/YYYY format. "
                "Example: 25/12/2026"
            )


import math


def ask_positive_number(prompt, allow_zero=False):

    while True:

        value = input(prompt).strip()

        try:

            if not value:
                raise ValueError

            number = float(value)

            if not math.isfinite(number):
                raise ValueError

            if number < 0 or (
                number == 0 and not allow_zero
            ):

                raise ValueError

            return number

        except ValueError:

            print(
                "Invalid amount. Enter a finite "
                "positive number or zero if allowed."
            )

def ask_category(prompt):

    while True:

        value = input(prompt).strip().upper()

        if value in ("B", "C1"):
            return value

        print("Enter B or C1.")



def ask_updated_text(label, old_value):

    while True:

        value = input(
            label + " [" + str(old_value) + "]: "
        ).strip()

        # Keep the existing value if ENTER is pressed.
        if not value:
            return old_value

        # Normalize repeated whitespace.
        value = " ".join(value.split())

        if any(ord(char) < 32 for char in value):

            print("Invalid text. Avoid control characters.")
            continue

        return value


def ask_updated_date(label, old_value):

    while True:

        value = input(
            label + " [" + str(old_value) + "]: "
        ).strip()

        # Preserve the existing date.
        if not value:
            return old_value

        try:

            parsed_date = datetime.strptime(
                value,
                DATE_FORMAT
            )

            return parsed_date.strftime(DATE_FORMAT)

        except ValueError:

            print(
                "Invalid date. Use DD/MM/YYYY. "
                "Example: 25/12/2026."
            )


def ask_updated_number(label, old_value):

    while True:

        value = input(
            label + " [" + str(old_value) + "]: "
        ).strip()

        # Preserve the existing value.
        if not value:
            return old_value

        try:

            number = float(value)

            if not math.isfinite(number):
                raise ValueError

            if number < 0:
                raise ValueError

            return f"{number:.2f}"

        except ValueError:

            print(
                "Invalid amount. Enter a finite "
                "positive number or zero."
            )


def choose_record(records, label, key):

    if records is None:

        print("\nUnable to read " + label.lower() + " records.")
        return None

    if not records:

        print("No " + label.lower() + " records found.")
        return None

    print("\nAvailable " + label + ":")

    for index, record in enumerate(records, start=1):

        print(
            str(index) + ". " +
            str(record.get(key, ""))
        )

    while True:

        choice = input(
            "\nSelect number (0 to cancel): "
        ).strip()

        if choice == "0":

            print("Selection cancelled.")
            return None

        if (
            choice.isdigit()
            and 1 <= int(choice) <= len(records)
        ):

            return records[int(choice) - 1]

        print(
            "Invalid selection. "
            "Enter a number from 1 to "
            + str(len(records))
            + ", or 0 to cancel."
        )

# ==========================================
# MODULE 1: VEHICLE MANAGEMENT
# ==========================================


def update_vehicle_record(
    old_registration,
    new_registration,
    vehicle_type,
    licence_category,
    next_service_date
):

    from datetime import datetime

    # ==========================================
    # NORMALIZE INPUT
    # ==========================================

    old_registration = str(old_registration).strip().upper()
    new_registration = str(new_registration).strip().upper()
    vehicle_type = str(vehicle_type).strip()
    licence_category = str(licence_category).strip().upper()
    next_service_date = str(next_service_date).strip()

    if not all([
        old_registration,
        new_registration,
        vehicle_type,
        licence_category,
        next_service_date
    ]):
        return False, "All vehicle fields are required."

    if licence_category not in ("B", "C1"):
        return False, "Licence category must be B or C1."

    # ==========================================
    # VALIDATE SERVICE DATE
    # ==========================================

    try:

        parsed_date = datetime.strptime(
            next_service_date,
            "%d/%m/%Y"
        )

        if parsed_date.strftime("%d/%m/%Y") != next_service_date:
            raise ValueError

    except ValueError:

        return False, "Enter a valid service date using DD/MM/YYYY."

    # ==========================================
    # LOAD ALL FOUR DATASETS
    # ==========================================

    vehicles = read_records(VEHICLES_FILE)
    trips = read_records(TRIPS_FILE)
    maintenance = read_records(MAINTENANCE_FILE)

    if any(
        records is None
        for records in (vehicles, trips, maintenance)
    ):
        return False, "Required records could not be loaded."

    # ==========================================
    # LOCATE ORIGINAL VEHICLE
    # ==========================================

    matches = [
        vehicle for vehicle in vehicles
        if vehicle["registration"].strip().upper()
        == old_registration
    ]

    if len(matches) != 1:
        return False, "Vehicle is missing or duplicated."

    original_vehicle = dict(matches[0])

    # ==========================================
    # CHECK DUPLICATE REGISTRATION
    # ==========================================

    if any(
        vehicle["registration"].strip().upper()
        == new_registration
        and vehicle["registration"].strip().upper()
        != old_registration
        for vehicle in vehicles
    ):
        return False, "Another vehicle uses that registration."

    # ==========================================
    # RECHECK LATEST DATA
    # ==========================================

    current_vehicles = read_records(VEHICLES_FILE)
    current_trips = read_records(TRIPS_FILE)
    current_maintenance = read_records(MAINTENANCE_FILE)

    if any(
        records is None
        for records in (
            current_vehicles,
            current_trips,
            current_maintenance
        )
    ):
        return False, "Latest records could not be verified."

    current_matches = [
        vehicle for vehicle in current_vehicles
        if vehicle["registration"].strip().upper()
        == old_registration
    ]

    if (
        len(current_matches) != 1
        or current_matches[0] != original_vehicle
    ):
        return False, "Vehicle changed during editing. Reload and retry."

    if any(
        vehicle["registration"].strip().upper()
        == new_registration
        and vehicle["registration"].strip().upper()
        != old_registration
        for vehicle in current_vehicles
    ):
        return False, "Another vehicle uses that registration."

    # ==========================================
    # PREPARE UPDATED VEHICLE
    # ==========================================

    updated_vehicle = {
        "registration": new_registration,
        "vehicle_type": vehicle_type,
        "licence_category": licence_category,
        "next_service_date": next_service_date
    }

    updated_vehicles = []

    for vehicle in current_vehicles:

        if vehicle["registration"].strip().upper() == old_registration:
            updated_vehicles.append(updated_vehicle)
        else:
            updated_vehicles.append(vehicle)

    registration_changed = (
        old_registration != new_registration
    )

    # ==========================================
    # UPDATE LINKED TRIP HISTORY
    # ==========================================

    updated_trips = []

    for trip in current_trips:

        updated_trip = dict(trip)

        if (
            registration_changed
            and trip["registration"].strip().upper()
            == old_registration
        ):
            updated_trip["registration"] = new_registration

        updated_trips.append(updated_trip)

    # ==========================================
    # UPDATE LINKED MAINTENANCE HISTORY
    # ==========================================

    updated_maintenance = []

    for record in current_maintenance:

        updated_record = dict(record)

        if (
            registration_changed
            and record["registration"].strip().upper()
            == old_registration
        ):
            updated_record["registration"] = new_registration

        updated_maintenance.append(updated_record)

    # ==========================================
    # CREATE VERIFIED BACKUP
    # ==========================================

    safety_backup = backup_data()

    if (
        not safety_backup
        or not os.path.isdir(safety_backup)
    ):
        return False, "Safety backup failed. No records were changed."

    backup_files = [
        VEHICLES_FILE,
        DRIVERS_FILE,
        TRIPS_FILE,
        MAINTENANCE_FILE
    ]

    try:

        for filename in backup_files:

            backup_file = os.path.join(
                safety_backup,
                os.path.basename(filename)
            )

            if (
                not os.path.isfile(backup_file)
                or not filecmp.cmp(
                    filename,
                    backup_file,
                    shallow=False
                )
            ):
                raise OSError(
                    "Backup verification failed: "
                    + os.path.basename(filename)
                )

    except Exception as error:

        return False, "Backup verification failed: " + str(error)

    # ==========================================
    # ROLLBACK HELPER
    # ==========================================

    def rollback_vehicle_files():

        successful = True

        for filename in backup_files:

            backup_file = os.path.join(
                safety_backup,
                os.path.basename(filename)
            )

            temporary_file = filename + ".rollback_tmp"

            try:

                shutil.copy2(
                    backup_file,
                    temporary_file
                )

                if not filecmp.cmp(
                    backup_file,
                    temporary_file,
                    shallow=False
                ):
                    raise OSError("Temporary recovery verification failed.")

                os.replace(
                    temporary_file,
                    filename
                )

                if not filecmp.cmp(
                    backup_file,
                    filename,
                    shallow=False
                ):
                    raise OSError("Restored file verification failed.")

            except Exception as error:

                successful = False

                print(
                    "CRITICAL RECOVERY FAILURE:",
                    os.path.basename(filename),
                    error
                )

            finally:

                if os.path.exists(temporary_file):

                    try:
                        os.remove(temporary_file)
                    except OSError:
                        pass

        return successful

    # ==========================================
    # SAVE AFFECTED FILES
    # ==========================================

    try:

        if not write_records(
            VEHICLES_FILE,
            VEHICLE_FIELDS,
            updated_vehicles
        ):
            raise RuntimeError("Vehicle register could not be saved.")

        if registration_changed:

            if not write_records(
                TRIPS_FILE,
                TRIP_FIELDS,
                updated_trips
            ):
                raise RuntimeError("Trip history could not be saved.")

            if not write_records(
                MAINTENANCE_FILE,
                MAINTENANCE_FIELDS,
                updated_maintenance
            ):
                raise RuntimeError("Maintenance history could not be saved.")

        # ==========================================
        # VERIFY ALL FINAL DATA
        # ==========================================

        saved_vehicles = read_records(VEHICLES_FILE)
        saved_trips = read_records(TRIPS_FILE)
        saved_maintenance = read_records(MAINTENANCE_FILE)

        if (
            saved_vehicles != updated_vehicles
            or saved_trips != updated_trips
            or saved_maintenance != updated_maintenance
        ):
            raise RuntimeError("Final record verification failed.")

    except Exception as error:

        recovered = rollback_vehicle_files()

        if recovered:

            return False, (
                "Vehicle update failed. "
                "Original records were restored. "
                + str(error)
            )

        return False, (
            "CRITICAL: Automatic recovery was incomplete. "
            "Do not modify the backup folder. "
            "Backup: " + safety_backup
        )

    # ==========================================
    # SUCCESS
    # ==========================================

    return True, (
        "Vehicle updated successfully. "
        "Linked trip and maintenance records were verified."
        if registration_changed
        else "Vehicle updated successfully. All records verified."
    )


def add_vehicle():

    heading("ADD VEHICLE")

    vehicles = read_records(VEHICLES_FILE)

    if vehicles is None:
        print("\nVEHICLE DATA UNAVAILABLE.")
        print("Vehicle registration cancelled.")
        return

    registration = ask_text(
        "Vehicle registration: "
    ).strip().upper()

    if not registration:
        print("Vehicle registration cannot be empty.")
        return

    if any(
        v["registration"].strip().upper() == registration
        for v in vehicles
    ):

        print("Vehicle already registered.")
        return

    vehicle_type = ask_text(
        "Vehicle type: "
    ).strip()

    if not vehicle_type:
        print("Vehicle type cannot be empty.")
        return

    category = ask_category(
        "Licence category (C1 or B): "
    )

    service_date = ask_date(
        "Next scheduled service date"
    )

    record = {
        "registration": registration,
        "vehicle_type": vehicle_type,
        "licence_category": category,
        "next_service_date": service_date
    }

    saved = save_record(
        VEHICLES_FILE,
        VEHICLE_FIELDS,
        record
    )

    if not saved:
        print("\nVehicle registration failed.")
        return

    print("\nVehicle registered successfully.")
    print("Registration:", registration)
    print("Vehicle type:", vehicle_type)
    print("Licence category:", category)
    print("Next service date:", service_date)

def view_vehicles():

    heading("REGISTERED VEHICLES")

    vehicles = read_records(VEHICLES_FILE)

    # Check whether the file could be read.
    if vehicles is None:

        print("\nVEHICLE RECORDS UNAVAILABLE.")
        print("The vehicle data file could not be read.")
        print("Check the CSV file and available backups.")

        return

    # Check whether the register is genuinely empty.
    if not vehicles:

        print("No vehicles registered.")
        return

    print("\nTotal registered vehicles:", len(vehicles))
    line()

    for i, vehicle in enumerate(vehicles, 1):

        print(f"{i}. Registration: {vehicle['registration']}")
        print(f"   Type: {vehicle['vehicle_type']}")
        print(f"   Category: {vehicle['licence_category']}")
        print(f"   Next service: {vehicle['next_service_date']}")

        line()

    print("Vehicle records displayed successfully.")





def edit_vehicle():

    heading("EDIT VEHICLE")

    vehicles = read_records(VEHICLES_FILE)

    if vehicles is None:
        print("\nVEHICLE DATA UNAVAILABLE.")
        print("Vehicle editing cancelled.")
        return

    if not vehicles:
        print("No vehicles registered.")
        return

    trips = read_records(TRIPS_FILE)

    if trips is None:
        print("\nTRIP DATA UNAVAILABLE.")
        print("Vehicle editing cancelled.")
        return

    vehicle = choose_record(
        vehicles,
        "VEHICLES",
        "registration"
    )

    if vehicle is None:
        return

    # Preserve the original selected record.
    original_vehicle = dict(vehicle)

    old_registration = vehicle["registration"]

    print("\nLeave a field blank to keep its current value.")

    new_registration = ask_updated_text(
        "Registration",
        old_registration
    ).strip().upper()

    if not new_registration:
        print("Registration cannot be empty.")
        return

    new_type = ask_updated_text(
        "Vehicle type",
        vehicle["vehicle_type"]
    ).strip()

    if not new_type:
        print("Vehicle type cannot be empty.")
        return

    while True:

        new_category = input(
            "Licence category (B or C1) ["
            + vehicle["licence_category"] + "]: "
        ).strip().upper()

        if not new_category:
            new_category = vehicle["licence_category"]
            break

        if new_category in ("B", "C1"):
            break

        print("Enter B or C1.")

    new_service_date = ask_updated_date(
        "Next service date",
        vehicle["next_service_date"]
    )

    if not confirm("Save vehicle changes?"):
        print("Changes cancelled.")
        return

    # ==========================================
    # RECHECK LATEST DATA
    # ==========================================

    current_vehicles = read_records(VEHICLES_FILE)
    current_trips = read_records(TRIPS_FILE)

    if current_vehicles is None or current_trips is None:

        print("\nVEHICLE UPDATE STOPPED.")
        print("Latest records could not be verified.")
        return

    current_vehicle = next(
        (
            item for item in current_vehicles
            if item["registration"].strip().casefold()
            == old_registration.strip().casefold()
        ),
        None
    )

    if current_vehicle is None:

        print("\nVEHICLE UPDATE STOPPED.")
        print("The selected vehicle no longer exists.")
        return

    # Prevent overwriting changes made after selection.
    if current_vehicle != original_vehicle:

        print("\nVEHICLE UPDATE STOPPED.")
        print("This vehicle's details changed during editing.")
        print("Select the vehicle again and retry.")
        return

    # ==========================================
    # CHECK DUPLICATE REGISTRATION
    # ==========================================

    if any(
        item["registration"].strip().casefold()
        == new_registration.casefold()
        and item["registration"].strip().casefold()
        != old_registration.strip().casefold()
        for item in current_vehicles
    ):

        print("\nVEHICLE UPDATE STOPPED.")
        print("Another vehicle uses that registration.")
        return

    registration_changed = (
        new_registration.casefold()
        != old_registration.strip().casefold()
    )

    # ==========================================
    # UPDATE LINKED TRIPS IN MEMORY
    # ==========================================

    if registration_changed:

        for trip in current_trips:

            if (
                trip["registration"].strip().casefold()
                == old_registration.strip().casefold()
            ):

                trip["registration"] = new_registration

    # ==========================================
    # PREPARE UPDATED VEHICLE
    # ==========================================

    current_vehicle["registration"] = new_registration
    current_vehicle["vehicle_type"] = new_type
    current_vehicle["licence_category"] = new_category
    current_vehicle["next_service_date"] = new_service_date

    # ==========================================
    # CREATE SAFETY BACKUP
    # ==========================================

    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if (
        safety_backup is None
        or not os.path.isdir(safety_backup)
    ):

        print("\nVEHICLE UPDATE CANCELLED.")
        print("A safety backup could not be created.")
        return

    # Verify safety backup against current files.
    try:

        for filename in (
            VEHICLES_FILE,
            DRIVERS_FILE,
            TRIPS_FILE
        ):

            backup_file = os.path.join(
                safety_backup,
                os.path.basename(filename)
            )

            if not os.path.isfile(backup_file):

                raise OSError(
                    "Missing safety backup file: "
                    + os.path.basename(filename)
                )

            if not filecmp.cmp(
                filename,
                backup_file,
                shallow=False
            ):

                raise OSError(
                    "Safety backup verification failed: "
                    + os.path.basename(filename)
                )

    except OSError as error:

        print("\nVEHICLE UPDATE CANCELLED.")
        print("Safety backup verification failed.")
        print("Reason:", error)
        return

    print("Safety backup verified successfully.")

    # ==========================================
    # ROLLBACK HELPER
    # ==========================================

    def rollback_vehicle_update(filenames):

        rollback_successful = True

        for filename in filenames:

            original_file = os.path.join(
                APP_FOLDER,
                filename
            )

            safety_file = os.path.join(
                safety_backup,
                filename
            )

            rollback_file = (
                original_file + ".rollback_tmp"
            )

            try:

                shutil.copy2(
                    safety_file,
                    rollback_file
                )

                if not filecmp.cmp(
                    safety_file,
                    rollback_file,
                    shallow=False
                ):

                    raise OSError(
                        "Rollback copy verification failed."
                    )

                os.replace(
                    rollback_file,
                    original_file
                )

                if not filecmp.cmp(
                    safety_file,
                    original_file,
                    shallow=False
                ):

                    raise OSError(
                        "Recovered file verification failed."
                    )

            except Exception as error:

                rollback_successful = False

                print(
                    "\nCRITICAL: Could not recover "
                    + filename
                )

                print("Reason:", error)

            finally:

                if os.path.exists(rollback_file):

                    try:
                        os.remove(rollback_file)
                    except OSError:
                        pass

        return rollback_successful

    # ==========================================
    # SAVE VEHICLE REGISTER
    # ==========================================

    vehicle_saved = write_records(
        VEHICLES_FILE,
        VEHICLE_FIELDS,
        current_vehicles
    )

    if not vehicle_saved:

        print("\nVEHICLE UPDATE FAILED.")
        print("Attempting to restore the original vehicle file...")

        recovered = rollback_vehicle_update([
            "vehicles.csv"
        ])

        if recovered:
            print("Original vehicle file restored successfully.")
        else:
            print("CRITICAL: Manual recovery may be required.")
            print("Safety backup:", safety_backup)

        return

    # ==========================================
    # SAVE LINKED TRIP HISTORY
    # ==========================================

    if registration_changed:

        trips_saved = write_records(
            TRIPS_FILE,
            TRIP_FIELDS,
            current_trips
        )

        if not trips_saved:

            print("\nTRIP HISTORY UPDATE FAILED.")
            print("Attempting automatic rollback...")

            recovered = rollback_vehicle_update([
                "vehicles.csv",
                "trips.csv"
            ])

            if recovered:

                print(
                    "Original vehicle and trip files restored."
                )

            else:

                print(
                    "CRITICAL: Automatic rollback was incomplete."
                )

                print("Safety backup:", safety_backup)

            return

    # ==========================================
    # VERIFY FINAL SAVED RECORDS
    # ==========================================

    saved_vehicles = read_records(VEHICLES_FILE)

    if saved_vehicles != current_vehicles:

        print("\nVEHICLE UPDATE VERIFICATION FAILED.")
        print("Attempting automatic rollback...")

        files_to_restore = ["vehicles.csv"]

        if registration_changed:
            files_to_restore.append("trips.csv")

        recovered = rollback_vehicle_update(
            files_to_restore
        )

        if recovered:
            print("Original records restored successfully.")
        else:
            print("CRITICAL: Manual recovery may be required.")
            print("Safety backup:", safety_backup)

        return

    if registration_changed:

        saved_trips = read_records(TRIPS_FILE)

        if saved_trips != current_trips:

            print("\nTRIP HISTORY VERIFICATION FAILED.")
            print("Attempting automatic rollback...")

            recovered = rollback_vehicle_update([
                "vehicles.csv",
                "trips.csv"
            ])

            if recovered:
                print("Original records restored successfully.")
            else:
                print("CRITICAL: Manual recovery may be required.")
                print("Safety backup:", safety_backup)

            return

    # ==========================================
    # SUCCESS
    # ==========================================

    print("\nVEHICLE UPDATED SUCCESSFULLY.")

    print("Registration:", new_registration)
    print("Vehicle type:", new_type)
    print("Licence category:", new_category)
    print("Next service date:", new_service_date)

    if registration_changed:

        print(
            "Linked trip history updated and verified."
        )

    print("Saved records verified successfully.")
    print("Safety backup:", safety_backup)


def delete_vehicle():

    heading("DELETE VEHICLE")

    vehicles = read_records(VEHICLES_FILE)

    if vehicles is None:
        print("\nVEHICLE DATA UNAVAILABLE.")
        print("Vehicle deletion cancelled.")
        return

    if not vehicles:
        print("No vehicles registered.")
        return

    vehicle = choose_record(
        vehicles,
        "VEHICLES",
        "registration"
    )

    if vehicle is None:
        return

    registration = vehicle["registration"]

    if not confirm(
        "Permanently delete vehicle " + registration + "?"
    ):
        print("Deletion cancelled.")
        return

    # Re-read the latest records before deletion.
    current_vehicles = read_records(VEHICLES_FILE)
    current_trips = read_records(TRIPS_FILE)

    if current_vehicles is None or current_trips is None:
        print("\nVEHICLE DELETION STOPPED.")
        print("Latest records could not be verified.")
        return

    # Confirm the selected vehicle still exists.
    current_vehicle = next(
        (
            item for item in current_vehicles
            if item["registration"].strip().casefold()
            == registration.strip().casefold()
        ),
        None
    )

    if current_vehicle is None:
        print("\nVEHICLE DELETION STOPPED.")
        print("The selected vehicle no longer exists.")
        return

    # Protect all linked trip history.
    linked_trips = [
        trip for trip in current_trips
        if trip["registration"].strip().casefold()
        == registration.strip().casefold()
    ]

    if linked_trips:

        print("\nDELETION BLOCKED.")
        print(
            "This vehicle has "
            + str(len(linked_trips))
            + " recorded trip(s)."
        )
        print("Its trip history must be protected.")
        return

    # Create a verified safety backup.
    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if safety_backup is None:
        print("\nVEHICLE DELETION CANCELLED.")
        print("Safety backup could not be created.")
        return

    # Remove the vehicle from the latest register.
    current_vehicles.remove(current_vehicle)

    saved = write_records(
        VEHICLES_FILE,
        VEHICLE_FIELDS,
        current_vehicles
    )

    if not saved:
        print("\nVEHICLE DELETION FAILED.")
        print("Safety backup:", safety_backup)
        return

    # Verify the deletion.
    verified_vehicles = read_records(VEHICLES_FILE)

    if verified_vehicles is None or any(
        item["registration"].strip().casefold()
        == registration.strip().casefold()
        for item in verified_vehicles
    ):

        print("\nVEHICLE DELETION VERIFICATION FAILED.")
        print("Check the safety backup before recovery.")
        print("Safety backup:", safety_backup)
        return

    print("\nVehicle deleted successfully.")
    print("Registration:", registration)
    print("Safety backup:", safety_backup)

# ==========================================
# MODULE 2: DRIVER MANAGEMENT
# ==========================================


def add_driver():

    heading("ADD DRIVER")

    drivers = read_records(DRIVERS_FILE)

    if drivers is None:
        print("\nDRIVER DATA UNAVAILABLE.")
        print("Driver registration cancelled.")
        return

    name = ask_text(
        "Driver full name: "
    ).strip()

    if not name:
        print("Driver name cannot be empty.")
        return

    if any(
        d["name"].strip().lower() == name.lower()
        for d in drivers
    ):

        print("Driver already registered.")
        return

    licence_type = ask_category(
        "Driving licence type (B or C1): "
    )

    licence_expiry = ask_date(
        "Driving licence expiry date"
    )

    defensive_expiry = ask_date(
        "Defensive driving certificate expiry date"
    )

    record = {
        "name": name,
        "licence_type": licence_type,
        "licence_expiry": licence_expiry,
        "defensive_driving_expiry": defensive_expiry
    }

    saved = save_record(
        DRIVERS_FILE,
        DRIVER_FIELDS,
        record
    )

    if not saved:
        print("\nDriver registration failed.")
        return

    print("\nDriver registered successfully.")
    print("Driver:", name)
    print("Licence type:", licence_type)
    print("Licence expiry:", licence_expiry)
    print("Defensive driving expiry:", defensive_expiry)


def view_drivers():

    heading("REGISTERED DRIVERS")

    drivers = read_records(DRIVERS_FILE)

    if drivers is None:
        print("\nDRIVER RECORDS UNAVAILABLE.")
        print("The driver data file could not be read.")
        print("Check the CSV file and available backups.")
        return

    if not drivers:
        print("No drivers registered.")
        return

    print("\nTotal registered drivers:", len(drivers))
    line()

    for i, driver in enumerate(drivers, 1):

        print(f"{i}. Name: {driver['name']}")
        print(f"   Licence: {driver['licence_type']}")
        print(f"   Licence expiry: {driver['licence_expiry']}")
        print(
            "   Defensive driving expiry: "
            + driver["defensive_driving_expiry"]
        )

        line()

    print("Driver records displayed successfully.")





def edit_driver():

    heading("EDIT DRIVER")

    drivers = read_records(DRIVERS_FILE)

    if drivers is None:
        print("\nDRIVER DATA UNAVAILABLE.")
        print("Driver editing cancelled.")
        return

    if not drivers:
        print("No drivers registered.")
        return

    trips = read_records(TRIPS_FILE)

    if trips is None:
        print("\nTRIP DATA UNAVAILABLE.")
        print("Driver editing cancelled.")
        return

    driver = choose_record(
        drivers,
        "DRIVERS",
        "name"
    )

    if driver is None:
        return

    # Preserve original selected record.
    original_driver = dict(driver)

    old_name = driver["name"]

    print("\nLeave a field blank to keep its current value.")

    new_name = ask_updated_text(
        "Driver name",
        old_name
    ).strip()

    if not new_name:
        print("Driver name cannot be empty.")
        return

    while True:

        new_licence = input(
            "Licence type (B or C1) ["
            + driver["licence_type"] + "]: "
        ).strip().upper()

        if not new_licence:
            new_licence = driver["licence_type"]
            break

        if new_licence in ("B", "C1"):
            break

        print("Enter B or C1.")

    new_expiry = ask_updated_date(
        "Driving licence expiry",
        driver["licence_expiry"]
    )

    new_defensive = ask_updated_date(
        "Defensive driving expiry",
        driver["defensive_driving_expiry"]
    )

    if not confirm("Save driver changes?"):
        print("Changes cancelled.")
        return

    # ==========================================
    # RECHECK LATEST DATA
    # ==========================================

    current_drivers = read_records(DRIVERS_FILE)
    current_trips = read_records(TRIPS_FILE)

    if current_drivers is None or current_trips is None:

        print("\nDRIVER UPDATE STOPPED.")
        print("Latest records could not be verified.")
        return

    current_driver = next(
        (
            item for item in current_drivers
            if item["name"].strip().casefold()
            == old_name.strip().casefold()
        ),
        None
    )

    if current_driver is None:

        print("\nDRIVER UPDATE STOPPED.")
        print("The selected driver no longer exists.")
        return

    # Detect changes made during editing.
    if current_driver != original_driver:

        print("\nDRIVER UPDATE STOPPED.")
        print("This driver's details changed during editing.")
        print("Select the driver again and retry.")
        return

    # ==========================================
    # CHECK DUPLICATE DRIVER NAMES
    # ==========================================

    if any(
        item["name"].strip().casefold()
        == new_name.casefold()
        and item["name"].strip().casefold()
        != old_name.strip().casefold()
        for item in current_drivers
    ):

        print("\nDRIVER UPDATE STOPPED.")
        print("Another driver already uses that name.")
        return

    name_changed = (
        new_name.casefold()
        != old_name.strip().casefold()
    )

    # ==========================================
    # UPDATE LINKED TRIPS
    # ==========================================

    if name_changed:

        for trip in current_trips:

            if (
                trip["driver"].strip().casefold()
                == old_name.strip().casefold()
            ):

                trip["driver"] = new_name

    # ==========================================
    # PREPARE UPDATED DRIVER
    # ==========================================

    current_driver["name"] = new_name
    current_driver["licence_type"] = new_licence
    current_driver["licence_expiry"] = new_expiry
    current_driver["defensive_driving_expiry"] = new_defensive

    # ==========================================
    # CREATE SAFETY BACKUP
    # ==========================================

    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if (
        safety_backup is None
        or not os.path.isdir(safety_backup)
    ):

        print("\nDRIVER UPDATE CANCELLED.")
        print("Safety backup could not be created.")
        return

    # Verify safety backup against current files.

    try:

        for filename in (
            VEHICLES_FILE,
            DRIVERS_FILE,
            TRIPS_FILE
        ):

            backup_file = os.path.join(
                safety_backup,
                os.path.basename(filename)
            )

            if not os.path.isfile(backup_file):

                raise OSError(
                    "Missing safety backup file: "
                    + os.path.basename(filename)
                )

            if not filecmp.cmp(
                filename,
                backup_file,
                shallow=False
            ):

                raise OSError(
                    "Safety backup verification failed: "
                    + os.path.basename(filename)
                )

    except OSError as error:

        print("\nDRIVER UPDATE CANCELLED.")
        print("Safety backup verification failed.")
        print("Reason:", error)
        return

    print("Safety backup verified successfully.")

    # ==========================================
    # ROLLBACK HELPER
    # ==========================================

    def rollback_driver_update(filenames):

        rollback_successful = True

        for filename in filenames:

            original_file = os.path.join(
                APP_FOLDER,
                filename
            )

            safety_file = os.path.join(
                safety_backup,
                filename
            )

            rollback_file = (
                original_file + ".rollback_tmp"
            )

            try:

                shutil.copy2(
                    safety_file,
                    rollback_file
                )

                if not filecmp.cmp(
                    safety_file,
                    rollback_file,
                    shallow=False
                ):

                    raise OSError(
                        "Rollback copy verification failed."
                    )

                os.replace(
                    rollback_file,
                    original_file
                )

                if not filecmp.cmp(
                    safety_file,
                    original_file,
                    shallow=False
                ):

                    raise OSError(
                        "Recovered file verification failed."
                    )

            except Exception as error:

                rollback_successful = False

                print(
                    "\nCRITICAL: Could not recover "
                    + filename
                )

                print("Reason:", error)

            finally:

                if os.path.exists(rollback_file):

                    try:
                        os.remove(rollback_file)
                    except OSError:
                        pass

        return rollback_successful

    # ==========================================
    # SAVE DRIVER REGISTER
    # ==========================================

    driver_saved = write_records(
        DRIVERS_FILE,
        DRIVER_FIELDS,
        current_drivers
    )

    if not driver_saved:

        print("\nDRIVER UPDATE FAILED.")
        print("Attempting to restore the original driver file...")

        recovered = rollback_driver_update([
            "drivers.csv"
        ])

        if recovered:
            print("Original driver file restored successfully.")
        else:
            print("CRITICAL: Manual recovery may be required.")
            print("Safety backup:", safety_backup)

        return

    # ==========================================
    # SAVE LINKED TRIP HISTORY
    # ==========================================

    if name_changed:

        trips_saved = write_records(
            TRIPS_FILE,
            TRIP_FIELDS,
            current_trips
        )

        if not trips_saved:

            print("\nTRIP HISTORY UPDATE FAILED.")
            print("Attempting automatic rollback...")

            recovered = rollback_driver_update([
                "drivers.csv",
                "trips.csv"
            ])

            if recovered:

                print(
                    "Original driver and trip files restored."
                )

            else:

                print(
                    "CRITICAL: Automatic rollback was incomplete."
                )

                print("Safety backup:", safety_backup)

            return

    # ==========================================
    # VERIFY FINAL SAVED RECORDS
    # ==========================================

    saved_drivers = read_records(DRIVERS_FILE)

    if saved_drivers != current_drivers:

        print("\nDRIVER UPDATE VERIFICATION FAILED.")
        print("Attempting automatic rollback...")

        files_to_restore = ["drivers.csv"]

        if name_changed:
            files_to_restore.append("trips.csv")

        recovered = rollback_driver_update(
            files_to_restore
        )

        if recovered:
            print("Original records restored successfully.")
        else:
            print("CRITICAL: Manual recovery may be required.")
            print("Safety backup:", safety_backup)

        return

    if name_changed:

        saved_trips = read_records(TRIPS_FILE)

        if saved_trips != current_trips:

            print("\nTRIP HISTORY VERIFICATION FAILED.")
            print("Attempting automatic rollback...")

            recovered = rollback_driver_update([
                "drivers.csv",
                "trips.csv"
            ])

            if recovered:
                print("Original records restored successfully.")
            else:
                print("CRITICAL: Manual recovery may be required.")
                print("Safety backup:", safety_backup)

            return

    # ==========================================
    # SUCCESS
    # ==========================================

    print("\nDRIVER UPDATED SUCCESSFULLY.")

    print("Driver:", new_name)
    print("Licence type:", new_licence)
    print("Licence expiry:", new_expiry)
    print("Defensive driving expiry:", new_defensive)

    if name_changed:

        print(
            "Linked trip history updated and verified."
        )

    print("Saved records verified successfully.")
    print("Safety backup:", safety_backup)


def delete_driver():

    heading("DELETE DRIVER")

    drivers = read_records(DRIVERS_FILE)

    if drivers is None:
        print("\nDRIVER DATA UNAVAILABLE.")
        print("Driver deletion cancelled.")
        return

    if not drivers:
        print("No drivers registered.")
        return

    driver = choose_record(
        drivers,
        "DRIVERS",
        "name"
    )

    if driver is None:
        return

    name = driver["name"]

    if not confirm(
        "Permanently delete driver " + name + "?"
    ):
        print("Deletion cancelled.")
        return

    # Re-read the latest records.
    current_drivers = read_records(DRIVERS_FILE)
    current_trips = read_records(TRIPS_FILE)

    if current_drivers is None or current_trips is None:
        print("\nDRIVER DELETION STOPPED.")
        print("Latest records could not be verified.")
        return

    # Confirm that the driver still exists.
    current_driver = next(
        (
            item for item in current_drivers
            if item["name"].strip().casefold()
            == name.strip().casefold()
        ),
        None
    )

    if current_driver is None:
        print("\nDRIVER DELETION STOPPED.")
        print("The selected driver no longer exists.")
        return

    # Protect linked trip history.
    linked_trips = [
        trip for trip in current_trips
        if trip["driver"].strip().casefold()
        == name.strip().casefold()
    ]

    if linked_trips:

        print("\nDELETION BLOCKED.")
        print(
            "This driver has "
            + str(len(linked_trips))
            + " recorded trip(s)."
        )
        print("Historical trip records will be protected.")
        return

    # Create a safety backup.
    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if safety_backup is None:
        print("\nDRIVER DELETION CANCELLED.")
        print("Safety backup could not be created.")
        return

    # Remove the driver.
    current_drivers.remove(current_driver)

    saved = write_records(
        DRIVERS_FILE,
        DRIVER_FIELDS,
        current_drivers
    )

    if not saved:
        print("\nDRIVER DELETION FAILED.")
        print("Safety backup:", safety_backup)
        return

    # Verify the deletion.
    verified_drivers = read_records(DRIVERS_FILE)

    if verified_drivers is None or any(
        item["name"].strip().casefold()
        == name.strip().casefold()
        for item in verified_drivers
    ):

        print("\nDRIVER DELETION VERIFICATION FAILED.")
        print("Check the safety backup before recovery.")
        print("Safety backup:", safety_backup)
        return

    print("\nDriver deleted successfully.")
    print("Deleted driver:", name)
    print("Safety backup:", safety_backup)

# ==========================================
# MODULE 3: TRIP MANAGEMENT
# ==========================================






def log_trip():

    heading("LOG NEW TRIP")

    # Read all required records.
    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)
    trips = read_records(TRIPS_FILE)

    if (
        vehicles is None
        or drivers is None
        or trips is None
    ):

        print("\nTRIP REGISTRATION FAILED.")
        print("One or more data files could not be read.")
        return

    if not vehicles:
        print("No vehicles registered.")
        return

    if not drivers:
        print("No drivers registered.")
        return

    # Collect trip information.
    trip_date = ask_date("Trip date")

    origin = input(
        "Origin [Lilongwe]: "
    ).strip()

    if not origin:
        origin = "Lilongwe"

    origin = " ".join(origin.split())

    if not origin:
        print("Origin cannot be empty.")
        return

    destination = ask_text("Destination")

    # Select vehicle.
    vehicle = choose_record(
        vehicles,
        "VEHICLES",
        "registration"
    )

    if vehicle is None:
        print("Trip registration cancelled.")
        return

    original_vehicle = vehicle.copy()

    # Select driver.
    driver = choose_record(
        drivers,
        "DRIVERS",
        "name"
    )

    if driver is None:
        print("Trip registration cancelled.")
        return

    original_driver = driver.copy()

    fuel_litres = ask_positive_number(
        "Fuel consumed (litres): ",
        allow_zero=True
    )

    fuel_cost = ask_positive_number(
        "Fuel cost (MWK): ",
        allow_zero=True
    )

    purpose = ask_text("Trip purpose")

    # Display trip information for confirmation.
    print("\nTRIP DETAILS FOR CONFIRMATION")
    line()

    print("Date:", trip_date)
    print("Origin:", origin)
    print("Destination:", destination)
    print("Vehicle:", original_vehicle["registration"])
    print("Driver:", original_driver["name"])
    print("Fuel consumed:", f"{fuel_litres:.2f}", "litres")
    print("Fuel cost: MWK", f"{fuel_cost:.2f}")
    print("Purpose:", purpose)

    line()

    if not confirm("Save this trip record?"):

        print("Trip registration cancelled.")
        return

    # Re-read the latest records before saving.
    current_vehicles = read_records(VEHICLES_FILE)
    current_drivers = read_records(DRIVERS_FILE)
    current_trips = read_records(TRIPS_FILE)

    if (
        current_vehicles is None
        or current_drivers is None
        or current_trips is None
    ):

        print("\nTRIP REGISTRATION FAILED.")
        print("Could not verify the latest records.")
        return

    # Find the currently registered vehicle.
    matching_vehicles = [
        item for item in current_vehicles
        if item["registration"].strip().casefold()
        == original_vehicle["registration"].strip().casefold()
    ]

    if len(matching_vehicles) != 1:

        print("\nTRIP REGISTRATION STOPPED.")
        print("The selected vehicle is missing or duplicated.")
        return

    current_vehicle = matching_vehicles[0]

    # Detect vehicle changes.
    if current_vehicle != original_vehicle:

        print("\nTRIP REGISTRATION STOPPED.")
        print("The selected vehicle has changed.")
        print("Restart trip registration using the latest details.")
        return

    # Find the currently registered driver.
    matching_drivers = [
        item for item in current_drivers
        if item["name"].strip().casefold()
        == original_driver["name"].strip().casefold()
    ]

    if len(matching_drivers) != 1:

        print("\nTRIP REGISTRATION STOPPED.")
        print("The selected driver is missing or duplicated.")
        return

    current_driver = matching_drivers[0]

    # Detect driver changes.
    if current_driver != original_driver:

        print("\nTRIP REGISTRATION STOPPED.")
        print("The selected driver has changed.")
        print("Restart trip registration using the latest details.")
        return

    # Generate a unique trip reference.
    try:

        reference = next_trip_reference(
            current_trips
        )

    except ValueError as error:

        print("\nTRIP REGISTRATION FAILED.")
        print("Trip reference error:", error)
        return

    # Build the trip record.
    trip = {
        "trip_date": trip_date,
        "origin": origin,
        "destination": destination,
        "registration": current_vehicle["registration"],
        "driver": current_driver["name"],
        "fuel_litres": f"{fuel_litres:.2f}",
        "fuel_cost_mwk": f"{fuel_cost:.2f}",
        "purpose": purpose,
        "trip_reference": reference
    }

    # Save and verify the new trip.
    if save_record(TRIPS_FILE, TRIP_FIELDS, trip):

        print("\nTRIP RECORDED SUCCESSFULLY.")
        print("Trip reference:", reference)

    else:

        print("\nTRIP REGISTRATION FAILED.")
        print("The trip could not be saved and verified.")






def edit_trip():

    heading("EDIT TRIP")

    trips = read_records(TRIPS_FILE)

    if trips is None:
        print("\nTRIP DATA UNAVAILABLE.")
        print("Trip editing cancelled.")
        return

    if not trips:
        print("No trips recorded.")
        return

    trip = choose_record(
        trips,
        "TRIPS",
        "trip_reference"
    )

    if trip is None:
        return

    original_trip = trip.copy()
    reference = trip["trip_reference"]

    print("\nLeave a field blank to keep its current value.")

    new_date = ask_updated_date(
        "Trip date",
        trip["trip_date"]
    )

    new_origin = ask_updated_text(
        "Origin",
        trip["origin"]
    ).strip()

    new_destination = ask_updated_text(
        "Destination",
        trip["destination"]
    ).strip()

    if not new_origin or not new_destination:
        print("Origin and destination cannot be empty.")
        return

    vehicles = read_records(VEHICLES_FILE)

    if vehicles is None or not vehicles:
        print("\nVEHICLE DATA UNAVAILABLE.")
        print("Trip editing cancelled.")
        return

    print("\nSelect replacement vehicle.")
    print("Enter 0 to keep the current vehicle.")

    new_vehicle = choose_record(
        vehicles,
        "VEHICLES",
        "registration"
    )

    new_registration = (
        new_vehicle["registration"]
        if new_vehicle is not None
        else trip["registration"]
    )

    drivers = read_records(DRIVERS_FILE)

    if drivers is None or not drivers:
        print("\nDRIVER DATA UNAVAILABLE.")
        print("Trip editing cancelled.")
        return

    print("\nSelect replacement driver.")
    print("Enter 0 to keep the current driver.")

    new_driver = choose_record(
        drivers,
        "DRIVERS",
        "name"
    )

    new_driver_name = (
        new_driver["name"]
        if new_driver is not None
        else trip["driver"]
    )

    new_fuel = ask_updated_number(
        "Fuel used (litres)",
        trip["fuel_litres"]
    )

    new_cost = ask_updated_number(
        "Fuel cost (MWK)",
        trip["fuel_cost_mwk"]
    )

    new_purpose = ask_updated_text(
        "Trip purpose",
        trip["purpose"]
    ).strip()

    if not new_purpose:
        print("Trip purpose cannot be empty.")
        return

    if not confirm("Save trip changes?"):
        print("Changes cancelled.")
        return

    # Re-read all latest records.
    current_trips = read_records(TRIPS_FILE)
    current_vehicles = read_records(VEHICLES_FILE)
    current_drivers = read_records(DRIVERS_FILE)

    if (
        current_trips is None
        or current_vehicles is None
        or current_drivers is None
    ):

        print("\nTRIP UPDATE STOPPED.")
        print("Latest records could not be verified.")
        return

    # Find the latest version of this trip.
    current_trip = next(
        (
            item for item in current_trips
            if item["trip_reference"].strip().casefold()
            == reference.strip().casefold()
        ),
        None
    )

    if current_trip is None:
        print("\nTRIP UPDATE STOPPED.")
        print("The selected trip no longer exists.")
        return

    # Detect changes made while editing.
    if current_trip != original_trip:

        print("\nTRIP UPDATE STOPPED.")
        print("This trip changed after editing began.")
        print("Restart the edit to avoid overwriting newer data.")
        return

    # Verify vehicle.
    if not any(
        item["registration"].strip().casefold()
        == new_registration.strip().casefold()
        for item in current_vehicles
    ):

        print("\nTRIP UPDATE STOPPED.")
        print("The selected vehicle is no longer registered.")
        return

    # Verify driver.
    if not any(
        item["name"].strip().casefold()
        == new_driver_name.strip().casefold()
        for item in current_drivers
    ):

        print("\nTRIP UPDATE STOPPED.")
        print("The selected driver is no longer registered.")
        return

    # Create safety backup.
    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if safety_backup is None:
        print("\nTRIP UPDATE CANCELLED.")
        print("Safety backup could not be created.")
        return

    backup_file = os.path.join(
        safety_backup,
        os.path.basename(TRIPS_FILE)
    )

    # Verify the original trip backup before changing anything.
    if (
        not os.path.isfile(backup_file)
        or not filecmp.cmp(
            TRIPS_FILE,
            backup_file,
            shallow=False
        )
    ):

        print("\nTRIP UPDATE CANCELLED.")
        print("Safety backup verification failed.")
        print("Original trip data has not been intentionally changed.")
        print("Safety backup:", safety_backup)
        return

    # Recovery procedure.
    
    def restore_original_trip():

        rollback_file = TRIPS_FILE + ".rollback_tmp"

        try:

            if not os.path.isfile(backup_file):
                raise FileNotFoundError(
                    "Original trip backup file is missing."
                )

            shutil.copy2(
                backup_file,
                rollback_file
            )

            if not filecmp.cmp(
                backup_file,
                rollback_file,
                shallow=False
            ):
                raise RuntimeError(
                    "Rollback copy verification failed."
                )

            os.replace(
                rollback_file,
                TRIPS_FILE
            )

            if not filecmp.cmp(
                backup_file,
                TRIPS_FILE,
                shallow=False
            ):
                raise RuntimeError(
                    "Restored trip file verification failed."
                )

            print("Original trip data restored successfully.")
            return True

        except Exception as error:

            print("\nAUTOMATIC RECOVERY FAILED.")
            print("Reason:", error)
            print("Do not delete the safety backup.")
            print("Use it for manual recovery if necessary.")

            return False

    # Prepare updated record.
    updated_trip = current_trip.copy()

    updated_trip["trip_date"] = new_date
    updated_trip["origin"] = new_origin
    updated_trip["destination"] = new_destination
    updated_trip["registration"] = new_registration
    updated_trip["driver"] = new_driver_name
    updated_trip["fuel_litres"] = new_fuel
    updated_trip["fuel_cost_mwk"] = new_cost
    updated_trip["purpose"] = new_purpose

    updated_trips = [
        updated_trip if item is current_trip else item
        for item in current_trips
    ]

    # Save updated records.
    saved = write_records(
        TRIPS_FILE,
        TRIP_FIELDS,
        updated_trips
    )

    if not saved:

        print("\nTRIP UPDATE FAILED.")
        print("Attempting to restore the original trip data...")

        restore_original_trip()

        print("Safety backup:", safety_backup)
        return

    # Verify saved records.
    verified_trips = read_records(TRIPS_FILE)

    if verified_trips is None or verified_trips != updated_trips:

        print("\nTRIP UPDATE VERIFICATION FAILED.")
        print("Attempting to restore the original trip data...")

        restore_original_trip()

        print("Safety backup:", safety_backup)
        return

    print("\nTrip updated successfully.")
    print("Trip reference:", reference)
    print("Vehicle:", new_registration)
    print("Driver:", new_driver_name)
    print("Safety backup:", safety_backup)



def delete_trip():

    heading("DELETE TRIP")

    trips = read_records(TRIPS_FILE)

    if trips is None:
        print("\nTRIP DATA UNAVAILABLE.")
        print("Trip deletion cancelled.")
        return

    if not trips:
        print("No trips recorded.")
        return

    trip = choose_record(
        trips,
        "TRIPS",
        "trip_reference"
    )

    if trip is None:
        return

    original_trip = trip.copy()
    reference = trip["trip_reference"].strip()

    print("\nTRIP SELECTED")
    line()

    print("Reference:", reference)
    print("Date:", trip.get("trip_date", "N/A"))
    print(
        "Route:",
        trip.get("origin", "N/A"),
        "to",
        trip.get("destination", "N/A")
    )
    print("Vehicle:", trip.get("registration", "N/A"))
    print("Driver:", trip.get("driver", "N/A"))
    print(
        "Fuel consumed:",
        trip.get("fuel_litres", "INVALID"),
        "litres"
    )
    print(
        "Fuel cost: MWK",
        trip.get("fuel_cost_mwk", "INVALID")
    )
    print("Purpose:", trip.get("purpose", "N/A"))

    line()

    if not confirm("Permanently delete this trip?"):

        print("Deletion cancelled.")
        return

    # Re-read the latest trip history.
    current_trips = read_records(TRIPS_FILE)

    if current_trips is None:

        print("\nTRIP DELETION STOPPED.")
        print("Latest trip records could not be verified.")
        return

    # Find the selected trip again.
    matching_trips = [
        item for item in current_trips
        if item.get("trip_reference", "").strip().casefold()
        == reference.casefold()
    ]

    if len(matching_trips) != 1:

        print("\nTRIP DELETION STOPPED.")
        print("The selected trip reference is missing or duplicated.")
        return

    current_trip = matching_trips[0]

    # Detect changes made after selection.
    if current_trip != original_trip:

        print("\nTRIP DELETION STOPPED.")
        print("The selected trip has changed.")
        print("Review the latest record before deleting it.")
        return

    # Create a safety backup.
    print("\nCreating safety backup...")

    safety_backup = backup_data()

    if safety_backup is None:

        print("\nTRIP DELETION CANCELLED.")
        print("Safety backup could not be created.")
        return

    backup_file = os.path.join(
        safety_backup,
        os.path.basename(TRIPS_FILE)
    )

    # Verify the original trip backup.
    if (
        not os.path.isfile(backup_file)
        or not filecmp.cmp(
            TRIPS_FILE,
            backup_file,
            shallow=False
        )
    ):

        print("\nTRIP DELETION CANCELLED.")
        print("Safety backup verification failed.")
        print("Original trip data has not been intentionally changed.")
        print("Safety backup:", safety_backup)
        return

    # Recovery procedure.
    
    def restore_original_trip():

        rollback_file = TRIPS_FILE + ".rollback_tmp"

        try:

            if not os.path.isfile(backup_file):
                raise FileNotFoundError(
                    "Original trip backup file is missing."
                )

            shutil.copy2(
                backup_file,
                rollback_file
            )

            if not filecmp.cmp(
                backup_file,
                rollback_file,
                shallow=False
            ):
                raise RuntimeError(
                    "Rollback copy verification failed."
                )

            os.replace(
                rollback_file,
                TRIPS_FILE
            )

            if not filecmp.cmp(
                backup_file,
                TRIPS_FILE,
                shallow=False
            ):
                raise RuntimeError(
                    "Restored trip file verification failed."
                )

            print("Original trip history restored successfully.")
            return True

        except Exception as error:

            print("\nAUTOMATIC RECOVERY FAILED.")
            print("Reason:", error)
            print("Do not delete the safety backup.")
            print("Manual recovery may be required.")

            return False

    # Prepare expected result.
    updated_trips = [
        item for item in current_trips
        if item.get("trip_reference", "").strip().casefold()
        != reference.casefold()
    ]

    if len(updated_trips) != len(current_trips) - 1:

        print("\nTRIP DELETION STOPPED.")
        print("The selected reference is not unique.")
        print("No trip records were intentionally changed.")
        return

    # Write updated trip history.
    saved = write_records(
        TRIPS_FILE,
        TRIP_FIELDS,
        updated_trips
    )

    if not saved:

        print("\nTRIP DELETION FAILED.")
        print("Attempting to restore the original trip history...")

        restore_original_trip()

        print("Safety backup:", safety_backup)
        return

    # Verify complete saved trip history.
    verified_trips = read_records(TRIPS_FILE)

    if verified_trips is None or verified_trips != updated_trips:

        print("\nTRIP DELETION VERIFICATION FAILED.")
        print("Attempting to restore the original trip history...")

        restore_original_trip()

        print("Safety backup:", safety_backup)
        return

    print("\nTRIP DELETED SUCCESSFULLY.")
    print("Deleted trip reference:", reference)
    print("Remaining trips:", len(verified_trips))
    print("Safety backup:", safety_backup)

# ==========================================
# MODULE 4: ALERT MANAGEMENT
# ==========================================



def days_until(date_text):

    if not isinstance(date_text, str):

        raise ValueError(
            "Date must be provided as text."
        )

    date_text = date_text.strip()

    if not date_text:

        raise ValueError(
            "Date cannot be empty."
        )

    try:

        due_date = datetime.strptime(
            date_text,
            DATE_FORMAT
        ).date()

        if due_date.strftime(DATE_FORMAT) != date_text:
            raise ValueError

    except ValueError:

        raise ValueError(
            "Invalid date. Expected format: DD/MM/YYYY."
        )

    return (
        due_date - date.today()
    ).days



def get_alert_counts():

    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)

    if vehicles is None or drivers is None:

        print("\nALERT CALCULATION FAILED.")
        print("Vehicle or driver data could not be read.")
        print("Alert totals cannot be trusted.")

        return None

    service_count = 0
    licence_count = 0

    invalid_service_dates = 0
    invalid_licence_dates = 0

    for vehicle in vehicles:

        try:

            remaining = days_until(
                vehicle["next_service_date"]
            )

            if remaining <= SERVICE_ALERT_DAYS:
                service_count += 1

        except (ValueError, KeyError, TypeError):

            invalid_service_dates += 1

    for driver in drivers:

        for field in (
            "licence_expiry",
            "defensive_driving_expiry"
        ):

            try:

                remaining = days_until(
                    driver[field]
                )

                if remaining <= LICENCE_ALERT_DAYS:
                    licence_count += 1

            except (ValueError, KeyError, TypeError):

                invalid_licence_dates += 1

    if invalid_service_dates or invalid_licence_dates:

        print("\nWARNING: ALERT DATA IS INCOMPLETE.")

        print(
            "Invalid vehicle service dates:",
            invalid_service_dates
        )

        print(
            "Invalid driver expiry dates:",
            invalid_licence_dates
        )

    return service_count, licence_count


def show_alerts():

    heading("VEHICLE & DRIVER ALERTS")

    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)

    # Stop if either data file cannot be read.
    if vehicles is None or drivers is None:

        print("\nALERT CHECK FAILED.")
        print("Vehicle or driver data could not be read.")
        print("Check your CSV files and backups.")

        return

    print("\nVEHICLE SERVICE ALERTS")
    line()

    service_alerts = 0
    invalid_service_dates = 0

    for vehicle in vehicles:

        reg = vehicle.get(
            "registration", ""
        ).strip()

        try:

            if not reg:
                raise ValueError("Missing vehicle registration.")

            remaining = days_until(
                vehicle["next_service_date"]
            )

        except (ValueError, KeyError, TypeError):

            print(
                "DATA ERROR: Invalid service information "
                "for vehicle:",
                reg if reg else "UNKNOWN"
            )

            invalid_service_dates += 1
            continue

        if remaining < 0:

            print(
                f"OVERDUE: Vehicle {reg} service "
                f"was due {abs(remaining)} day(s) ago."
            )

            service_alerts += 1

        elif remaining == 0:

            print(
                f"DUE TODAY: Vehicle {reg} service is due today."
            )

            service_alerts += 1

        elif remaining <= SERVICE_ALERT_DAYS:

            print(
                f"ALERT: Vehicle {reg} service due "
                f"in {remaining} day(s)."
            )

            service_alerts += 1

    if service_alerts == 0:

        if invalid_service_dates == 0:
            print("No vehicle service alerts.")
        else:
            print("No valid service alert total can be confirmed.")

    print("\nDRIVER LICENCE ALERTS")
    line()

    licence_alerts = 0
    invalid_licence_dates = 0

    for driver in drivers:

        name = driver.get(
            "name", ""
        ).strip()

        expiry_fields = [
            ("licence_expiry", "driving licence"),
            (
                "defensive_driving_expiry",
                "defensive driving certificate"
            )
        ]

        for field, label in expiry_fields:

            try:

                if not name:
                    raise ValueError("Missing driver name.")

                remaining = days_until(
                    driver[field]
                )

            except (ValueError, KeyError, TypeError):

                print(
                    f"DATA ERROR: Invalid {label} "
                    f"expiry information for "
                    f"{name if name else 'UNKNOWN DRIVER'}."
                )

                invalid_licence_dates += 1
                continue

            if remaining < 0:

                print(
                    f"EXPIRED: {name}'s {label} expired "
                    f"{abs(remaining)} day(s) ago."
                )

                licence_alerts += 1

            elif remaining == 0:

                print(
                    f"EXPIRES TODAY: {name}'s "
                    f"{label} expires today."
                )

                licence_alerts += 1

            elif remaining <= LICENCE_ALERT_DAYS:

                print(
                    f"ALERT: {name}'s {label} expires "
                    f"in {remaining} day(s)."
                )

                licence_alerts += 1

    if licence_alerts == 0:

        if invalid_licence_dates == 0:
            print("No driver licence alerts.")
        else:
            print("No valid licence alert total can be confirmed.")

   
    # Display final summary.
    print("\nALERT SUMMARY")
    line()

    print("Vehicle service alerts:", service_alerts)
    print("Driver licence alerts:", licence_alerts)

    print("Invalid service dates:", invalid_service_dates)
    print("Invalid licence dates:", invalid_licence_dates)

    if (
        service_alerts == 0
        and licence_alerts == 0
        and invalid_service_dates == 0
        and invalid_licence_dates == 0
    ):

        print("\nAll service and expiry checks are clear.")

    elif invalid_service_dates > 0 or invalid_licence_dates > 0:

        print("\nWARNING: Some records require data correction.")
        print("Alert totals may be incomplete.")

    else:

        print("\nAttention: One or more alerts require action.")


def get_alert_counts():

    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)

    # Stop if either data file cannot be read.
    if vehicles is None or drivers is None:

        print("\nALERT CALCULATION FAILED.")
        print("Vehicle or driver data could not be read.")
        print("Alert totals cannot be trusted.")

        return None

    service_count = 0
    licence_count = 0

    invalid_service_dates = 0
    invalid_licence_dates = 0

    # Check vehicle service dates.
    for vehicle in vehicles:

        try:

            remaining = days_until(
                vehicle["next_service_date"]
            )

            if remaining <= SERVICE_ALERT_DAYS:
                service_count += 1

        except (ValueError, KeyError, TypeError):

            invalid_service_dates += 1

    # Check driver licence expiry dates.
    for driver in drivers:

        for field in (
            "licence_expiry",
            "defensive_driving_expiry"
        ):

            try:

                remaining = days_until(
                    driver[field]
                )

                if remaining <= LICENCE_ALERT_DAYS:
                    licence_count += 1

            except (ValueError, KeyError, TypeError):

                invalid_licence_dates += 1

    # Report invalid dates.
    if invalid_service_dates:

        print(
            "\nWARNING: "
            + str(invalid_service_dates)
            + " vehicle service date(s) are invalid."
        )

    if invalid_licence_dates:

        print(
            "WARNING: "
            + str(invalid_licence_dates)
            + " driver licence date(s) are invalid."
        )

    return service_count, licence_count



def show_alerts():

    heading("VEHICLE & DRIVER ALERTS")

    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)

    # Stop if either data file cannot be read.
    if vehicles is None or drivers is None:

        print("\nALERT CHECK FAILED.")
        print("Vehicle or driver data could not be read.")
        print("Check your CSV files and backups.")

        return

    print("\nVEHICLE SERVICE ALERTS")
    line()

    service_alerts = 0
    invalid_service_dates = 0

    for vehicle in vehicles:

        reg = vehicle.get(
            "registration", ""
        ).strip()

        try:

            if not reg:
                raise ValueError("Missing vehicle registration.")

            remaining = days_until(
                vehicle["next_service_date"]
            )

        except (ValueError, KeyError, TypeError):

            print(
                "DATA ERROR: Invalid service information "
                "for vehicle:",
                reg if reg else "UNKNOWN"
            )

            invalid_service_dates += 1
            continue

        if remaining < 0:

            print(
                f"OVERDUE: Vehicle {reg} service "
                f"was due {abs(remaining)} day(s) ago."
            )

            service_alerts += 1

        elif remaining == 0:

            print(
                f"DUE TODAY: Vehicle {reg} service is due today."
            )

            service_alerts += 1

        elif remaining <= SERVICE_ALERT_DAYS:

            print(
                f"ALERT: Vehicle {reg} service due "
                f"in {remaining} day(s)."
            )

            service_alerts += 1

    if service_alerts == 0:

        if invalid_service_dates == 0:
            print("No vehicle service alerts.")
        else:
            print("No valid service alert total can be confirmed.")

    print("\nDRIVER LICENCE ALERTS")
    line()

    licence_alerts = 0
    invalid_licence_dates = 0

    for driver in drivers:

        name = driver.get(
            "name", ""
        ).strip()

        expiry_fields = [
            ("licence_expiry", "driving licence"),
            (
                "defensive_driving_expiry",
                "defensive driving certificate"
            )
        ]

        for field, label in expiry_fields:

            try:

                if not name:
                    raise ValueError("Missing driver name.")

                remaining = days_until(
                    driver[field]
                )

            except (ValueError, KeyError, TypeError):

                print(
                    f"DATA ERROR: Invalid {label} "
                    f"expiry information for "
                    f"{name if name else 'UNKNOWN DRIVER'}."
                )

                invalid_licence_dates += 1
                continue

            if remaining < 0:

                print(
                    f"EXPIRED: {name}'s {label} expired "
                    f"{abs(remaining)} day(s) ago."
                )

                licence_alerts += 1

            elif remaining == 0:

                print(
                    f"EXPIRES TODAY: {name}'s "
                    f"{label} expires today."
                )

                licence_alerts += 1

            elif remaining <= LICENCE_ALERT_DAYS:

                print(
                    f"ALERT: {name}'s {label} expires "
                    f"in {remaining} day(s)."
                )

                licence_alerts += 1

    if licence_alerts == 0:

        if invalid_licence_dates == 0:
            print("No driver licence alerts.")
        else:
            print("No valid licence alert total can be confirmed.")

    # Display final summary.
    print("\nALERT SUMMARY")
    line()

    print("Vehicle service alerts:", service_alerts)
    print("Driver licence alerts:", licence_alerts)

    print("Invalid service dates:", invalid_service_dates)
    print("Invalid licence dates:", invalid_licence_dates)

    if (
        service_alerts == 0
        and licence_alerts == 0
        and invalid_service_dates == 0
        and invalid_licence_dates == 0
    ):

        print("\nAll service and expiry checks are clear.")

    elif invalid_service_dates > 0 or invalid_licence_dates > 0:

        print(
            "\nWARNING: Some records require data correction."
        )
        print(
            "The alert totals may be incomplete."
        )

# ==========================================
# MODULE 5: MONTHLY REPORTS
# ==========================================


def monthly_report():

    heading("MONTHLY FLEET REPORT")

    month = input(
        "Enter month (YYYY-MM), e.g. 2026-11: "
    ).strip()

    try:

        parsed_month = datetime.strptime(
            month,
            "%Y-%m"
        )

        if parsed_month.strftime("%Y-%m") != month:
            raise ValueError

    except ValueError:

        print("Invalid month. Use YYYY-MM.")
        return

    trips = read_records(TRIPS_FILE)

    if trips is None:

        print("\nMONTHLY REPORT UNAVAILABLE.")
        print("The trip data file could not be read.")
        print("Check the CSV file and available backups.")
        return

    selected = []
    invalid_dates = 0

    for trip in trips:

        try:

            trip_date_text = trip["trip_date"].strip()

            trip_date = datetime.strptime(
                trip_date_text,
                DATE_FORMAT
            )

            if (
                trip_date.strftime(DATE_FORMAT)
                != trip_date_text
            ):
                raise ValueError

            if trip_date.strftime("%Y-%m") == month:

                selected.append(trip)

        except (ValueError, KeyError, TypeError, AttributeError):

            invalid_dates += 1

    fuel_values = []
    cost_values = []

    invalid_fuel = 0
    invalid_cost = 0

    print("\nREPORTING PERIOD: " + month)
    line()

    print("Total trips:", len(selected))

    if selected:

        print("\nTRIP DETAILS")
        line()

        for trip in selected:

            # Validate fuel independently.

            try:

                fuel = float(trip["fuel_litres"])

                if (
                    not math.isfinite(fuel)
                    or fuel < 0
                ):
                    raise ValueError

                fuel_values.append(fuel)

                fuel_display = f"{fuel:,.2f} L"

            except (ValueError, KeyError, TypeError):

                invalid_fuel += 1
                fuel_display = "INVALID"

            # Validate cost independently.

            try:

                cost = float(trip["fuel_cost_mwk"])

                if (
                    not math.isfinite(cost)
                    or cost < 0
                ):
                    raise ValueError

                cost_values.append(cost)

                cost_display = f"MWK {cost:,.2f}"

            except (ValueError, KeyError, TypeError):

                invalid_cost += 1
                cost_display = "INVALID"

            print(
                f"{trip.get('trip_reference', 'NO REF')} | "
                f"{trip.get('trip_date', 'N/A')} | "
                f"{trip.get('origin', 'N/A')} to "
                f"{trip.get('destination', 'N/A')} | "
                f"{trip.get('registration', 'N/A')} | "
                f"{trip.get('driver', 'N/A')} | "
                f"{fuel_display} | "
                f"{cost_display}"
            )

    else:

        print("\nNo trips found for this month.")

    # Calculate totals using only valid figures.

    try:

        total_fuel = math.fsum(fuel_values)
        total_cost = math.fsum(cost_values)

        if (
            not math.isfinite(total_fuel)
            or not math.isfinite(total_cost)
        ):
            raise OverflowError

    except (OverflowError, ValueError):

        print("\nREPORT CALCULATION FAILED.")
        print("The figures are too large to calculate safely.")
        print("Check the trip records before generating the report.")
        return

    line()

    print("\nMONTHLY TOTALS")
    print(f"Total fuel used: {total_fuel:,.2f} litres")
    print(f"Total fuel cost: MWK {total_cost:,.2f}")

    if invalid_dates:

        print(
            "Records excluded because of invalid dates:",
            invalid_dates
        )

    if invalid_fuel:

        print(
            "Trips with invalid fuel figures:",
            invalid_fuel
        )

    if invalid_cost:

        print(
            "Trips with invalid cost figures:",
            invalid_cost
        )

    line()

    if invalid_fuel or invalid_cost or invalid_dates:

        print("\nWARNING: REPORT CONTAINS DATA QUALITY ISSUES.")
        print("Some records or figures were excluded from calculations.")

    print("\nMonthly report generated.")

# ==========================================
# MODULE 6: FLEET DASHBOARD
# ==========================================




def dashboard():

    heading("FLEET MANAGEMENT DASHBOARD")

    # Load all three data files.
    vehicles = read_records(VEHICLES_FILE)
    drivers = read_records(DRIVERS_FILE)
    trips = read_records(TRIPS_FILE)

    # Stop if any data file cannot be read.
    if (
        vehicles is None
        or drivers is None
        or trips is None
    ):

        print("\nDASHBOARD GENERATION FAILED.")
        print("One or more data files could not be read.")
        print("Check your CSV files and backups.")

        return

    fuel_values = []
    cost_values = []

    invalid_fuel = 0
    invalid_cost = 0

    invalid_trip_dates = 0

    # Calculate fuel and cost independently.
    for trip in trips:

        # Validate fuel.
        try:

            fuel = float(trip["fuel_litres"])

            if (
                not math.isfinite(fuel)
                or fuel < 0
            ):
                raise ValueError

            fuel_values.append(fuel)

        except (ValueError, KeyError, TypeError):

            invalid_fuel += 1

        # Validate cost.
        try:

            cost = float(trip["fuel_cost_mwk"])

            if (
                not math.isfinite(cost)
                or cost < 0
            ):
                raise ValueError

            cost_values.append(cost)

        except (ValueError, KeyError, TypeError):

            invalid_cost += 1

        # Validate trip date.
        try:

            trip_date_text = trip["trip_date"].strip()

            parsed_date = datetime.strptime(
                trip_date_text,
                DATE_FORMAT
            )

            if (
                parsed_date.strftime(DATE_FORMAT)
                != trip_date_text
            ):
                raise ValueError

        except (ValueError, KeyError, TypeError, AttributeError):

            invalid_trip_dates += 1

    # Calculate totals safely.
    try:

        total_fuel = math.fsum(fuel_values)
        total_cost = math.fsum(cost_values)

        if (
            not math.isfinite(total_fuel)
            or not math.isfinite(total_cost)
        ):
            raise OverflowError

    except (OverflowError, ValueError):

        print("\nDASHBOARD CALCULATION FAILED.")
        print("Financial totals could not be calculated safely.")
        print("Check the trip records.")

        return

    # Retrieve outstanding alerts.
    alert_counts = get_alert_counts()

    if alert_counts is None:

        print("\nDASHBOARD GENERATION FAILED.")
        print("Alert information is unavailable.")
        print("Dashboard totals cannot be considered complete.")

        return

    service_alerts, licence_alerts = alert_counts

    # Display fleet summary.
    print("\nFLEET SUMMARY")
    line()

    print("Registered vehicles:", len(vehicles))
    print("Registered drivers:", len(drivers))
    print("Recorded trips:", len(trips))

    line()

    print("FUEL AND COST SUMMARY")
    line()

    print(f"Total fuel recorded: {total_fuel:,.2f} litres")
    print(f"Total fuel cost recorded: MWK {total_cost:,.2f}")

    line()

    print("OUTSTANDING ALERTS")
    line()

    print("Vehicle service alerts:", service_alerts)
    print("Driver compliance alerts:", licence_alerts)

    line()

    print("DATA QUALITY SUMMARY")
    line()

    print("Trips with invalid fuel figures:", invalid_fuel)
    print("Trips with invalid cost figures:", invalid_cost)
    print("Trips with invalid dates:", invalid_trip_dates)

    if (
        invalid_fuel > 0
        or invalid_cost > 0
        or invalid_trip_dates > 0
    ):

        print("\nWARNING: DASHBOARD CONTAINS DATA QUALITY ISSUES.")
        print("Some financial figures may be incomplete.")

    line()

    print("SYSTEM DATA FILES")
    print("vehicles.csv")
    print("drivers.csv")
    print("trips.csv")

    if (
        invalid_fuel == 0
        and invalid_cost == 0
        and invalid_trip_dates == 0
    ):

        print("\nDashboard generated successfully.")

    else:

        print("\nDashboard generated with data warnings.")

# ==========================================
# MODULE 7: BACKUP MENU
# ==========================================


def backup_menu():

    heading("DATA BACKUP")

    print("This creates copies of all existing CSV files.")
    print("Your working files will not be moved.")

    if not confirm("Create a backup now?"):

        print("Backup cancelled.")
        return

    backup_path = backup_data()

    if backup_path is None:

        print("\nBACKUP OPERATION FAILED.")
        print("Your original CSV files have not been intentionally changed.")

    else:

        print("\nBACKUP OPERATION COMPLETED.")
        print("Backup location:", backup_path)

# ==========================================
# MAIN MENU
# ==========================================




  
def restore_backup():

    heading("RESTORE CSV BACKUP")

    files = {
        "vehicles.csv": VEHICLE_FIELDS,
        "drivers.csv": DRIVER_FIELDS,
        "trips.csv": TRIP_FIELDS
    }

    # ==========================================
    # BACKUP VALIDATION
    # ==========================================

    def validate_backup_folder(folder):

        records = {}

        def validate_date(value, filename):

            try:

                parsed = datetime.strptime(
                    value,
                    DATE_FORMAT
                )

                if parsed.strftime(DATE_FORMAT) != value:
                    raise ValueError

            except ValueError:

                raise ValueError(
                    "Invalid date format in "
                    + filename
                    + ": "
                    + value
                    + ". Expected DD/MM/YYYY."
                )

        # Validate CSV files.

        for filename, expected_fields in files.items():

            source = os.path.join(
                folder,
                filename
            )

            if not os.path.isfile(source):

                raise ValueError(
                    "Missing file: " + filename
                )

            with open(
                source,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                if reader.fieldnames != expected_fields:

                    raise ValueError(
                        "Invalid column headers in "
                        + filename
                    )

                if (
                    len(reader.fieldnames)
                    != len(set(reader.fieldnames))
                ):

                    raise ValueError(
                        "Duplicate CSV headers in "
                        + filename
                    )

                rows = []

                for row_number, row in enumerate(reader, 2):

                    if (
                        None in row
                        or any(
                            value is None or not value.strip()
                            for value in row.values()
                        )
                    ):

                        raise ValueError(
                            f"Missing or invalid data on row "
                            f"{row_number} in {filename}"
                        )

                    rows.append(row)

                records[filename] = rows

        vehicles = records["vehicles.csv"]
        drivers = records["drivers.csv"]
        trips = records["trips.csv"]

        # Check duplicate vehicle registrations.

        registrations = [
            vehicle["registration"].strip().casefold()
            for vehicle in vehicles
        ]

        if len(registrations) != len(set(registrations)):

            raise ValueError(
                "Duplicate vehicle registrations found."
            )

        # Check duplicate driver names.

        driver_names = [
            driver["name"].strip().casefold()
            for driver in drivers
        ]

        if len(driver_names) != len(set(driver_names)):

            raise ValueError(
                "Duplicate driver names found."
            )

        # Validate vehicle service dates.

        for vehicle in vehicles:

            validate_date(
                vehicle["next_service_date"],
                "vehicles.csv"
            )

        # Validate driver expiry dates.

        for driver in drivers:

            validate_date(
                driver["licence_expiry"],
                "drivers.csv"
            )

            validate_date(
                driver["defensive_driving_expiry"],
                "drivers.csv"
            )

        # Validate trip records.

        trip_references = set()

        for trip in trips:

            validate_date(
                trip["trip_date"],
                "trips.csv"
            )

            try:

                fuel = float(trip["fuel_litres"])
                cost = float(trip["fuel_cost_mwk"])

            except (ValueError, TypeError):

                raise ValueError(
                    "Invalid fuel or cost in trip "
                    + trip["trip_reference"]
                )

            if (
                not math.isfinite(fuel)
                or not math.isfinite(cost)
                or fuel < 0
                or cost < 0
            ):

                raise ValueError(
                    "Invalid fuel or cost in trip "
                    + trip["trip_reference"]
                )

            reference = trip["trip_reference"].strip()

            if (
                not reference.upper().startswith("TRP")
                or not reference[3:].isdigit()
            ):

                raise ValueError(
                    "Invalid trip reference: "
                    + reference
                )

            reference_key = reference.casefold()

            if reference_key in trip_references:

                raise ValueError(
                    "Duplicate trip reference: "
                    + reference
                )

            trip_references.add(reference_key)

        # Validate trip vehicle and driver links.

        vehicle_set = set(registrations)
        driver_set = set(driver_names)

        for trip in trips:

            if (
                trip["registration"].strip().casefold()
                not in vehicle_set
            ):

                raise ValueError(
                    "Trip references an unknown vehicle: "
                    + trip["registration"]
                )

            if (
                trip["driver"].strip().casefold()
                not in driver_set
            ):

                raise ValueError(
                    "Trip references an unknown driver: "
                    + trip["driver"]
                )

        return True

    # ==========================================
    # LOCATE AVAILABLE BACKUPS
    # ==========================================

    if not os.path.isdir(BACKUP_FOLDER):

        print("No backup folder found.")
        return

    folders = []

    try:

        for name in os.listdir(BACKUP_FOLDER):

            path = os.path.join(
                BACKUP_FOLDER,
                name
            )

            if (
                name.startswith("backup_")
                and os.path.isdir(path)
            ):

                folders.append(path)

    except OSError as error:

        print("\nBACKUP SEARCH FAILED.")
        print("Reason:", error)
        return

    folders.sort(reverse=True)

    if not folders:

        print("No backups are available.")
        return

    print("AVAILABLE BACKUPS")
    line()

    for index, folder in enumerate(folders, 1):

        print(
            f"{index}. {os.path.basename(folder)}"
        )

    print("0. Cancel")

    choice = input(
        "\nSelect backup to restore: "
    ).strip()

    if choice == "0":

        print("Restore cancelled.")
        return

    if (
        not choice.isdigit()
        or not (1 <= int(choice) <= len(folders))
    ):

        print("Invalid selection.")
        return

    selected_folder = folders[int(choice) - 1]

    # ==========================================
    # VALIDATE SELECTED BACKUP
    # ==========================================

    print("\nValidating backup files...")

    try:

        validate_backup_folder(selected_folder)

    except (
        OSError,
        csv.Error,
        UnicodeDecodeError,
        ValueError,
        TypeError
    ) as error:

        print("\nRESTORE REJECTED.")
        print("Backup validation failed:", error)
        print("Current working files were not changed.")

        return

    print("All three backup files passed validation.")

    if not confirm(
        "This will replace your current working records. Continue?"
    ):

        print("Restore cancelled.")
        return

    # ==========================================
    # CREATE SAFETY BACKUP
    # ==========================================

    print("\nCreating safety backup of current data...")

    safety_backup = backup_data()

    if (
        not safety_backup
        or not os.path.isdir(safety_backup)
    ):

        print("\nRESTORE STOPPED.")
        print("Safety backup could not be confirmed.")
        return

    required_files = list(files.keys())

    if not all(
        os.path.isfile(
            os.path.join(safety_backup, filename)
        )
        for filename in required_files
    ):

        print("\nRESTORE STOPPED.")
        print("Safety backup is incomplete.")
        return

    # Verify safety backup against working files.

    try:

        for filename in required_files:

            original_file = os.path.join(
                APP_FOLDER,
                filename
            )

            safety_file = os.path.join(
                safety_backup,
                filename
            )

            if not filecmp.cmp(
                original_file,
                safety_file,
                shallow=False
            ):

                raise OSError(
                    "Safety backup verification failed: "
                    + filename
                )

    except OSError as error:

        print("\nRESTORE STOPPED.")
        print("Safety backup verification failed.")
        print("Reason:", error)
        return

    print("Safety backup verified successfully.")

    # ==========================================
    # PREPARE STAGING AREA
    # ==========================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    staging_folder = os.path.join(
        APP_FOLDER,
        ".restore_staging_" + timestamp
    )

    restore_started = False

    try:

        os.makedirs(staging_folder)

        # Copy selected backup files into staging.

        for filename in files:

            source = os.path.join(
                selected_folder,
                filename
            )

            staged_path = os.path.join(
                staging_folder,
                filename
            )

            shutil.copy2(
                source,
                staged_path
            )

            if not filecmp.cmp(
                source,
                staged_path,
                shallow=False
            ):

                raise OSError(
                    "Staged copy verification failed: "
                    + filename
                )

        # Validate staged files again.

        validate_backup_folder(staging_folder)

        print("Staged files passed verification.")

        # ==========================================
        # REPLACE WORKING FILES
        # ==========================================

        restore_started = True

        for filename in files:

            staged_path = os.path.join(
                staging_folder,
                filename
            )

            destination = os.path.join(
                APP_FOLDER,
                filename
            )

            os.replace(
                staged_path,
                destination
            )

        # Verify restored files.

        for filename in files:

            restored_file = os.path.join(
                APP_FOLDER,
                filename
            )

            backup_file = os.path.join(
                selected_folder,
                filename
            )

            if not filecmp.cmp(
                restored_file,
                backup_file,
                shallow=False
            ):

                raise OSError(
                    "Restored file verification failed: "
                    + filename
                )

        print("\nRESTORE COMPLETED SUCCESSFULLY.")

        print(
            "Restored from:",
            os.path.basename(selected_folder)
        )

        print("Files restored and verified: 3")
        print("Safety backup:", safety_backup)

    except Exception as error:

        print("\nRESTORE FAILED.")
        print("Reason:", error)

        if restore_started:

            print(
                "Attempting to recover previous working data..."
            )

            rollback_success = True

            for filename in files:

                try:

                    safety_file = os.path.join(
                        safety_backup,
                        filename
                    )

                    destination = os.path.join(
                        APP_FOLDER,
                        filename
                    )

                    rollback_file = (
                        destination + ".rollback_tmp"
                    )

                    shutil.copy2(
                        safety_file,
                        rollback_file
                    )

                    if not filecmp.cmp(
                        safety_file,
                        rollback_file,
                        shallow=False
                    ):

                        raise OSError(
                            "Rollback copy verification failed."
                        )

                    os.replace(
                        rollback_file,
                        destination
                    )

                    if not filecmp.cmp(
                        safety_file,
                        destination,
                        shallow=False
                    ):

                        raise OSError(
                            "Recovered file verification failed."
                        )

                except Exception as rollback_error:

                    rollback_success = False

                    print(
                        f"Could not recover {filename}: "
                        f"{rollback_error}"
                    )

            if rollback_success:

                print(
                    "Previous working data successfully recovered."
                )

            else:

                print(
                    "CRITICAL: Manual recovery may be required."
                )

                print("Safety backup:", safety_backup)

        else:

            print(
                "Working files were not replaced."
            )

    finally:

        # Remove staging directory.

        if os.path.isdir(staging_folder):

            try:

                shutil.rmtree(staging_folder)

            except OSError as cleanup_error:

                print(
                    "WARNING: Could not remove staging folder:",
                    cleanup_error
                )

        # Remove leftover rollback temporary files.

        for filename in files:

            temporary = os.path.join(
                APP_FOLDER,
                filename + ".rollback_tmp"
            )

            if os.path.exists(temporary):

                try:

                    os.remove(temporary)

                except OSError:
                    pass


def view_trip_history():

    heading("TRIP HISTORY")

    trips = read_records(TRIPS_FILE)

    if trips is None:

        print("\nTRIP HISTORY UNAVAILABLE.")
        print("The trip data file could not be read.")
        print("Check the CSV file and available backups.")

        return

    if not trips:

        print("No trip records found.")
        return

    print("\nTOTAL TRIPS:", len(trips))
    line()

    for index, trip in enumerate(trips, 1):

        print(f"TRIP {index}")
        line()

        print(
            "Reference:",
            trip.get("trip_reference", "N/A")
        )

        print(
            "Date:",
            trip.get("trip_date", "N/A")
        )

        print(
            "Origin:",
            trip.get("origin", "N/A")
        )

        print(
            "Destination:",
            trip.get("destination", "N/A")
        )

        print(
            "Vehicle:",
            trip.get("registration", "N/A")
        )

        print(
            "Driver:",
            trip.get("driver", "N/A")
        )

        print(
            "Fuel consumed:",
            trip.get("fuel_litres", "INVALID"),
            "litres"
        )

        print(
            "Fuel cost: MWK",
            trip.get("fuel_cost_mwk", "INVALID")
        )

        print(
            "Purpose:",
            trip.get("purpose", "N/A")
        )

        line()

    print("Trip history displayed successfully.")



def main_menu():

    while True:

        heading("VEHICLE & FLEET MANAGEMENT SYSTEM")

        print("VERSION 2.1")
        line()

        print("1.  Fleet dashboard")
        print("2.  Add vehicle")
        print("3.  Add driver")
        print("4.  Log trip")
        print("5.  View vehicles")
        print("6.  View drivers")
        print("7.  View trip history")
        print("8.  Edit vehicle")
        print("9.  Delete vehicle")
        print("10. Edit driver")
        print("11. Delete driver")
        print("12. Edit trip")
        print("13. Delete trip")
        print("14. Service and licence alerts")
        print("15. Monthly fuel and trip report")
        print("16. Create CSV backup")
        print("17. Restore CSV backup")
        print("18. Exit")

        line()

        choice = input(
            "Select an option (1-18): "
        ).strip()

        if choice == "1":
            dashboard()

        elif choice == "2":
            add_vehicle()

        elif choice == "3":
            add_driver()

        elif choice == "4":
            log_trip()

        elif choice == "5":
            view_vehicles()

        elif choice == "6":
            view_drivers()

        elif choice == "7":
            view_trip_history()

        elif choice == "8":
            edit_vehicle()

        elif choice == "9":
            delete_vehicle()

        elif choice == "10":
            edit_driver()

        elif choice == "11":
            delete_driver()

        elif choice == "12":
            edit_trip()

        elif choice == "13":
            delete_trip()

        elif choice == "14":
            show_alerts()

        elif choice == "15":
            monthly_report()

        elif choice == "16":
            backup_menu()

        elif choice == "17":
            restore_backup()

        elif choice == "18":

            print(
                "\nExiting Vehicle & Fleet Management System."
            )

            print("Thank you for using the system.")

            break

        else:

            print(
                "\nInvalid selection. "
                "Enter a number from 1 to 18."
            )

        input(
            "\nPress ENTER to return to the main menu..."
        )





required_functions = [
    "dashboard",
    "add_vehicle",
    "add_driver",
    "log_trip",
    "view_vehicles",
    "view_drivers",
    "view_trip_history",
    "edit_vehicle",
    "delete_vehicle",
    "edit_driver",
    "delete_driver",
    "edit_trip",
    "delete_trip",
    "days_until",
    "get_alert_counts",
    "show_alerts",
    "monthly_report",
    "backup_menu",
    "restore_backup",
    "ensure_files",
    "backup_data"
]

for name in required_functions:
    if callable(globals().get(name)):
        print("[OK]      " + name)
    else:
        print("[MISSING] " + name)

print("==========================================")



for name in globals():
    if "alert" in name.lower() or "service" in name.lower() or "licence" in name.lower():
        if callable(globals()[name]):
            print("FOUND:", name)

print("===========================================")



# ==========================================
# PROGRAM START
# ==========================================

if __name__ == "__main__":

    try:

        print(
            "\nInitializing Vehicle & Fleet Management System..."
        )

        initialization_successful = ensure_files()

        if initialization_successful:

            print("\nSYSTEM INITIALIZED SUCCESSFULLY.")
            print("Starting Version 2.1...")

            main_menu()

        else:

            print("\nSYSTEM STARTUP ABORTED.")
            print("Initialization or data migration failed.")

            print(
                "Do not delete or modify your CSV files."
            )

            print(
                "Check your backup folder before recovery."
            )

    except KeyboardInterrupt:

        print("\nProgram interrupted safely.")

    except Exception as error:

        print("\nSYSTEM ERROR:")
        print(str(error))

        print(
            "Do not delete your CSV files. "
            "Check your backup folder before making changes."
        )

    finally:

        print(
            "\nVehicle & Fleet Management System stopped."
        )
