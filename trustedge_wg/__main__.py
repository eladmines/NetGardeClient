import sys

from trustedge_wg.env import load_dotenv

load_dotenv()

from trustedge_wg.app.main import main

sys.exit(main())
