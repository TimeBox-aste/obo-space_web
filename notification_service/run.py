from consumer import RegistrationProcessor
from settings import RABBITMQ_CONFIG
import time

# Initialize and start the processor
processor = RegistrationProcessor(RABBITMQ_CONFIG)
processor.start()

try:
    # Keep the main thread alive
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    processor.cleanup()