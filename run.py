"""title2doi 启动入口"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app

if __name__ == "__main__":
    print("title2doi 启动中...")
    print("   http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
