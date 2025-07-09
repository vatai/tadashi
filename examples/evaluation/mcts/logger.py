import datetime
import json

from mcts import config


class TimestampedJsonLogger:
    """
    A logger that writes timestamped JSON lines to a file.

    The filename is generated based on the timestamp of the first
    call to the log method for a given instance of this class.
    Subsequent calls append to the same file.
    """

    def __init__(self, prefix):
        """Initializes the logger, filename is not yet set."""
        now = datetime.datetime.now()
        # Generate a filename like YYYYMMDD_HHMMSSffffff.jsonl
        # Including microseconds (%f) increases uniqueness chances
        self._filename = f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"
        # print(f"Initializing log file: {self._filename}") # Optional: Inform user

    def log(self, speedup, transforms, source):
        """
        Logs a value to the file.

        Creates the log file on the first call, naming it after the
        current timestamp. Appends a JSON line containing the current
        timestamp and the provided value on every call.

        Args:
            value: The data/value to log. Can be any JSON-serializable type.
        """
        current_timestamp = (
            datetime.datetime.now().isoformat()
        )  # ISO format is standard
        print(config)
        log_entry = {
            "cnt_rollouts": config["cnt_rollouts"],
            "cnt_evals": config["cnt_evals"],
            "timestamp": current_timestamp,
            "speedup": speedup,
            "transform": transforms,
            "source": source,
        }

        try:
            with open(self._filename, "a", encoding="utf-8") as f:
                json_line = json.dumps(log_entry)
                f.write(json_line + "\n")
        except IOError as e:
            print(f"Error: Could not write to log file {self._filename}: {e}")
        except TypeError as e:
            print(f"Error: Value provided is not JSON serializable: {e}")


# --- Example Usage ---

# Create an instance of the logger
# my_logger = TimestampedJsonLogger()

# print("First log call...")
# my_logger.log("System startup") # This call will create the file

# # Wait a bit (optional, just for demonstration)
# import time

# time.sleep(1)

# print("Second log call...")
# my_logger.log({"event": "UserLoggedIn", "user_id": 123})

# time.sleep(1)

# print("Third log call...")
# my_logger.log(42) # Logging a different data type

# print("Finished logging.")

# If you create another instance, it will create a *different* log file
# another_logger = TimestampedJsonLogger()
# another_logger.log("This goes to a new file")
