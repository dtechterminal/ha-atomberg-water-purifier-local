"""Import the standalone network library without loading Home Assistant."""
from pathlib import Path
import sys
import types

root = Path(__file__).parents[1] / "custom_components" / "atomberg_purifier_local"
package = types.ModuleType("purifier")
package.__path__ = [str(root)]
sys.modules["purifier"] = package
