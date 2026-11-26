import os
import tempfile

# Set before test modules import app.main, which builds the app (and configures logging) at import time.
os.environ["NETPULSE_LOG_FILE"] = os.path.join(tempfile.mkdtemp(prefix="netpulse-tests-"), "test.log")
