"""
AppleTrader Pro - Command Manager
Sends commands from Python GUI to MT5 EA via JSON files
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class CommandManager:
    """
    Manages bidirectional communication with MT5 EA
    Sends commands via JSON file that EA monitors
    """

    def __init__(self):
        # Find MT5 Common Files directory
        self.commands_file = self.find_commands_file()
        self.command_queue = []


    def find_commands_file(self) -> Path:
        """Find or create commands.json in MT5 Common Files"""
        # Try common MT5 paths
        possible_paths = [
            Path.home() / 'AppData' / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files' / 'AppleTrader',
            Path('/home/user/.wine/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/AppleTrader'),
            Path('C:/Users') / os.getenv('USERNAME', 'User') / 'AppData/Roaming/MetaQuotes/Terminal/Common/Files/AppleTrader',
        ]

        for path in possible_paths:
            if path.exists():
                commands_path = path / 'commands.json'

                # Create commands file if it doesn't exist
                if not commands_path.exists():
                    commands_path.write_text(json.dumps({'commands': []}, indent=2))

                return commands_path

        # Fallback: create in local directory
        local_path = Path('./data/commands.json')
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if not local_path.exists():
            local_path.write_text(json.dumps({'commands': []}, indent=2))

        return local_path

    def send_filter_toggle(self, filter_name: str, enabled: bool):
        """
        Send filter toggle command to EA

        Args:
            filter_name: Name of filter (e.g., 'UseVolumeFilter', 'UseSpreadFilter')
            enabled: True to enable, False to disable
        """
        command = {
            'type': 'FILTER_TOGGLE',
            'filter': filter_name,
            'enabled': enabled,
            'timestamp': datetime.now().isoformat(),
        }

        self._send_command(command)

    def send_risk_update(self, risk_percent: float):
        """
        Update risk percentage in EA

        Args:
            risk_percent: Risk per trade (0.1 - 2.0%)
        """
        command = {
            'type': 'RISK_UPDATE',
            'risk_percent': risk_percent,
            'timestamp': datetime.now().isoformat(),
        }

        self._send_command(command)

    def send_trading_mode(self, enabled: bool):
        """
        Enable/disable trading in EA

        Args:
            enabled: True for trading ON, False for OFF
        """
        command = {
            'type': 'TRADING_MODE',
            'enabled': enabled,
            'timestamp': datetime.now().isoformat(),
        }

        self._send_command(command)

    def send_order(self, order_type: str, symbol: str, lot_size: float):
        """
        Send manual order command to EA

        Args:
            order_type: 'BUY' or 'SELL'
            symbol: Trading symbol
            lot_size: Position size
        """
        command = {
            'type': 'MANUAL_ORDER',
            'order_type': order_type,
            'symbol': symbol,
            'lot_size': lot_size,
            'timestamp': datetime.now().isoformat(),
        }

        self._send_command(command)

    def send_visual_toggle(self, visual_name: str, enabled: bool):
        """
        Toggle chart visual elements in EA

        Args:
            visual_name: Name of visual (e.g., 'ShowFVGZones', 'ShowOrderBlocks')
            enabled: True to show, False to hide
        """
        command = {
            'type': 'VISUAL_TOGGLE',
            'visual': visual_name,
            'enabled': enabled,
            'timestamp': datetime.now().isoformat(),
        }

        self._send_command(command)

    def _send_command(self, command: Dict[str, Any]):
        """
        Write command to commands.json file for EA to read

        Args:
            command: Command dictionary
        """
        try:
            # Read existing commands
            if self.commands_file.exists():
                with open(self.commands_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'commands': []}

            # Add new command
            if 'commands' not in data:
                data['commands'] = []

            data['commands'].append(command)

            # Keep only last 100 commands to prevent file bloat
            if len(data['commands']) > 100:
                data['commands'] = data['commands'][-100:]

            # Write back to file
            with open(self.commands_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            pass

    def clear_commands(self):
        """Clear all pending commands"""
        try:
            with open(self.commands_file, 'w') as f:
                json.dump({'commands': []}, f, indent=2)
        except Exception as e:
            pass


# Global command manager instance
command_manager = CommandManager()
