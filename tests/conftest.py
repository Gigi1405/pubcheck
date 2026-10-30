import pathlib
import sys

# Projektwurzel auf den Importpfad, damit `adapters`, `matching`, `models` gefunden werden
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
