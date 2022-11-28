import json
from pathlib import Path

from utilities import parser
from analysis.parse.network_data import NetworkData


def packet_to_frame():
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])