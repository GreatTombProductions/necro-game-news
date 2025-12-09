#!/usr/bin/env python3
"""
Discord bot for managing Necro Game News submissions.

Monitors the submissions channel and allows admins to approve/edit games
via reactions and slash commands.

Usage:
    python scripts/discord_bot.py

Environment variables required:
    DISCORD_BOT_TOKEN - Bot token from Discord Developer Portal
    DISCORD_CHANNEL_ID - Channel ID for submissions (optional, defaults to any channel)
"""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
import yaml
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GAMES_YAML_PATH = PROJECT_ROOT / "data" / "games_list.yaml"
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "deploy.sh"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")  # Optional: restrict to specific channel

# Platform ID fields
PLATFORM_ID_FIELDS = ["steam_id", "battlenet_id", "gog_id", "epic_id", "itchio_id"]

# Classification mapping from embed text to YAML values
CENTRALITY_MAP = {
    "core": "a",
    "dedicated spec": "b",
    "dedicated branch": "b",
    "specialization": "b",
    "isolated": "c",
    "minimal": "d",
    "a": "a",
    "b": "b",
    "c": "c",
    "d": "d",
}

POV_MAP = {
    "character": "character",
    "unit": "unit",
    "play as": "character",
    "control units": "unit",
}

NAMING_MAP = {
    "explicit": "explicit",
    "implied": "implied",
}


class GameEntry:
    """Represents a game entry for the YAML file."""

    def __init__(
        self,
        name: str,
        steam_id: Optional[int] = None,
        battlenet_id: Optional[str] = None,
        gog_id: Optional[str] = None,
        epic_id: Optional[str] = None,
        itchio_id: Optional[str] = None,
        dimension_1: Optional[str] = None,
        dimension_2: Optional[str] = None,
        dimension_3: Optional[str] = None,
        notes: Optional[str] = None,
        priority: str = "high",
    ):
        self.name = name
        self.steam_id = steam_id
        self.battlenet_id = battlenet_id
        self.gog_id = gog_id
        self.epic_id = epic_id
        self.itchio_id = itchio_id
        self.dimension_1 = dimension_1
        self.dimension_2 = dimension_2
        self.dimension_3 = dimension_3
        self.notes = notes
        self.priority = priority
        self.date_added = date.today().isoformat()

    def validate(self) -> list[str]:
        """Validate the entry and return list of missing/invalid fields."""
        errors = []

        if not self.name:
            errors.append("name")

        # Check for at least one platform ID
        has_platform = any([
            self.steam_id,
            self.battlenet_id,
            self.gog_id,
            self.epic_id,
            self.itchio_id,
        ])
        if not has_platform:
            errors.append("platform ID (steam_id, battlenet_id, etc.)")

        # Check classification
        if not self.dimension_1:
            errors.append("centrality (dimension_1)")
        elif self.dimension_1 not in ["a", "b", "c", "d"]:
            errors.append(f"centrality must be a/b/c/d, got '{self.dimension_1}'")

        if not self.dimension_2:
            errors.append("pov (dimension_2)")
        elif self.dimension_2 not in ["character", "unit"]:
            errors.append(f"pov must be character/unit, got '{self.dimension_2}'")

        if not self.dimension_3:
            errors.append("naming (dimension_3)")
        elif self.dimension_3 not in ["explicit", "implied"]:
            errors.append(f"naming must be explicit/implied, got '{self.dimension_3}'")

        return errors

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML output."""
        entry = {"name": self.name}

        # Add platform IDs
        if self.steam_id:
            entry["steam_id"] = self.steam_id
        if self.battlenet_id:
            entry["battlenet_id"] = self.battlenet_id
        if self.gog_id:
            entry["gog_id"] = self.gog_id
        if self.epic_id:
            entry["epic_id"] = self.epic_id
        if self.itchio_id:
            entry["itchio_id"] = self.itchio_id

        # Add platforms list
        platforms = []
        if self.steam_id:
            platforms.append("steam")
        if self.battlenet_id:
            platforms.append("battlenet")
        if self.gog_id:
            platforms.append("gog")
        if self.epic_id:
            platforms.append("epic")
        if self.itchio_id:
            platforms.append("itchio")
        if platforms:
            entry["platforms"] = platforms

        # Add classification
        entry["classification"] = {
            "dimension_1": self.dimension_1,
            "dimension_2": self.dimension_2,
            "dimension_3": self.dimension_3,
        }

        # Add optional fields
        if self.notes:
            entry["notes"] = self.notes

        entry["date_added"] = self.date_added
        entry["priority"] = self.priority

        return entry

    def get_identifier(self) -> str:
        """Get a unique identifier for the game (prefer steam_id)."""
        if self.steam_id:
            return f"steam:{self.steam_id}"
        if self.battlenet_id:
            return f"battlenet:{self.battlenet_id}"
        if self.gog_id:
            return f"gog:{self.gog_id}"
        if self.epic_id:
            return f"epic:{self.epic_id}"
        if self.itchio_id:
            return f"itchio:{self.itchio_id}"
        return f"name:{self.name}"


def load_games_yaml() -> dict:
    """Load the games YAML file."""
    with open(GAMES_YAML_PATH, "r") as f:
        return yaml.safe_load(f)


def save_games_yaml(data: dict) -> None:
    """Save the games YAML file."""
    with open(GAMES_YAML_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_existing_game(
    games: list[dict],
    steam_id: Optional[int] = None,
    battlenet_id: Optional[str] = None,
    name: Optional[str] = None,
) -> tuple[Optional[dict], Optional[int]]:
    """Find an existing game by ID or name. Returns (game_dict, index) or (None, None)."""
    for i, game in enumerate(games):
        if steam_id and game.get("steam_id") == steam_id:
            return game, i
        if battlenet_id and game.get("battlenet_id") == battlenet_id:
            return game, i
        if name and game.get("name", "").lower() == name.lower():
            return game, i
    return None, None


def parse_embed_submission(embed: discord.Embed) -> GameEntry:
    """Parse a submission embed into a GameEntry."""
    name = None
    steam_id = None
    battlenet_id = None
    centrality = None
    pov = None
    naming = None
    notes = None

    for field in embed.fields:
        field_name = field.name.lower()
        field_value = field.value.strip() if field.value else ""

        if "game name" in field_name:
            name = field_value

        elif "steam" in field_name and "id" in field_name:
            # Extract numeric ID from potential markdown link
            match = re.search(r"\d+", field_value)
            if match:
                steam_id = int(match.group())

        elif "battlenet" in field_name or "battle.net" in field_name:
            battlenet_id = field_value

        elif "classification" in field_name or "suggested" in field_name:
            # Parse classification from format like:
            # "Centrality: Dedicated Spec\nPOV: Character\nNaming: Explicit"
            lines = field_value.split("\n")
            for line in lines:
                line_lower = line.lower()
                if "centrality" in line_lower:
                    for key in CENTRALITY_MAP:
                        if key in line_lower:
                            centrality = CENTRALITY_MAP[key]
                            break
                elif "pov" in line_lower:
                    for key in POV_MAP:
                        if key in line_lower:
                            pov = POV_MAP[key]
                            break
                elif "naming" in line_lower:
                    for key in NAMING_MAP:
                        if key in line_lower:
                            naming = NAMING_MAP[key]
                            break

        elif "notes" in field_name or "justification" in field_name:
            notes = field_value

    return GameEntry(
        name=name,
        steam_id=steam_id,
        battlenet_id=battlenet_id,
        dimension_1=centrality,
        dimension_2=pov,
        dimension_3=naming,
        notes=notes,
    )


def parse_overrides(args: str) -> dict:
    """
    Parse override arguments from command string.

    Format: field:value field2:value2
    Examples:
        centrality:a pov:unit
        steam_id:12345 centrality:b
        name:Some Game Name  (spaces in value OK if it's the last arg)
    """
    fields = {}
    # Match field:value pairs, handling potential spaces in values
    pattern = r"(\w+):([^\s:]+(?:\s+[^\s:]+)*?)(?=\s+\w+:|$)"
    matches = re.findall(pattern, args.strip())

    for field, value in matches:
        field = field.lower()
        value = value.strip()

        if field == "centrality":
            value = CENTRALITY_MAP.get(value.lower(), value)
            fields["dimension_1"] = value
        elif field == "pov":
            value = POV_MAP.get(value.lower(), value)
            fields["dimension_2"] = value
        elif field == "naming":
            value = NAMING_MAP.get(value.lower(), value)
            fields["dimension_3"] = value
        elif field == "steam_id":
            fields["steam_id"] = int(value)
        elif field == "battlenet_id":
            fields["battlenet_id"] = value
        elif field == "name":
            fields["name"] = value
        elif field == "notes":
            fields["notes"] = value
        elif field == "priority":
            fields["priority"] = value

    return fields


def run_deploy() -> tuple[bool, str]:
    """Run the deploy script with --new-only flag."""
    try:
        result = subprocess.run(
            [str(DEPLOY_SCRIPT), "--new-only"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300,  # 5 minute timeout
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Deploy failed:\n{result.stderr}\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return False, "Deploy timed out after 5 minutes"
    except Exception as e:
        return False, f"Deploy error: {str(e)}"


# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store pending overwrites (message_id -> GameEntry)
pending_overwrites: dict[int, GameEntry] = {}


@bot.event
async def on_ready():
    """Called when bot is ready."""
    print(f"Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Handle reactions on messages."""
    # Ignore bot's own reactions
    if payload.user_id == bot.user.id:
        return

    # Check if this is the submissions channel (if configured)
    if DISCORD_CHANNEL_ID and str(payload.channel_id) != DISCORD_CHANNEL_ID:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    message = await channel.fetch_message(payload.message_id)

    # Handle checkmark reaction for approval
    if str(payload.emoji) == "✅":
        await handle_approval_reaction(message, payload.user_id)

    # Handle X reaction for confirming overwrite
    elif str(payload.emoji) == "🔄" and payload.message_id in pending_overwrites:
        await handle_overwrite_confirmation(message, payload.user_id)


async def handle_approval_reaction(message: discord.Message, user_id: int):
    """Handle approval via checkmark reaction."""
    # Check if message has embeds (submission format)
    if not message.embeds:
        return

    embed = message.embeds[0]

    # Check if this looks like a submission
    if not embed.title or "submission" not in embed.title.lower():
        return

    # Parse the submission
    entry = parse_embed_submission(embed)

    # Validate
    errors = entry.validate()
    if errors:
        await message.reply(
            f"**Cannot approve - missing required fields:**\n"
            f"- {chr(10).join(errors)}\n\n"
            f"Use `/add` command with the missing fields, e.g.:\n"
            f"`/add {entry.steam_id or '[id]'} centrality:a pov:character naming:explicit`"
        )
        return

    # Check for existing game
    data = load_games_yaml()
    existing, idx = find_existing_game(
        data["games"],
        steam_id=entry.steam_id,
        battlenet_id=entry.battlenet_id,
        name=entry.name,
    )

    if existing:
        # Store for potential overwrite
        pending_overwrites[message.id] = entry
        await message.reply(
            f"**Game already exists:** {existing.get('name')}\n"
            f"React with 🔄 to overwrite, or use `/edit` to modify specific fields."
        )
        return

    # Add to YAML
    data["games"].append(entry.to_dict())
    save_games_yaml(data)

    # Run deploy
    status_msg = await message.reply("Adding game and deploying...")

    success, output = run_deploy()

    if success:
        await status_msg.edit(content=f"✅ **Added and deployed:** {entry.name}")
    else:
        await status_msg.edit(content=f"⚠️ **Added but deploy failed:**\n```{output[:1500]}```")


async def handle_overwrite_confirmation(message: discord.Message, user_id: int):
    """Handle overwrite confirmation via 🔄 reaction."""
    entry = pending_overwrites.pop(message.id, None)
    if not entry:
        return

    data = load_games_yaml()
    existing, idx = find_existing_game(
        data["games"],
        steam_id=entry.steam_id,
        battlenet_id=entry.battlenet_id,
        name=entry.name,
    )

    if existing and idx is not None:
        # Replace existing entry
        data["games"][idx] = entry.to_dict()
        save_games_yaml(data)

        status_msg = await message.reply("Overwriting and deploying...")
        success, output = run_deploy()

        if success:
            await status_msg.edit(content=f"✅ **Overwrote and deployed:** {entry.name}")
        else:
            await status_msg.edit(content=f"⚠️ **Overwrote but deploy failed:**\n```{output[:1500]}```")


@bot.tree.command(name="add", description="Add a game with optional fields")
@app_commands.describe(
    identifier="Steam ID, battlenet:slug, or game name",
    fields="Optional fields (e.g., centrality:a pov:unit naming:explicit)",
)
async def add_command(
    interaction: discord.Interaction,
    identifier: str,
    fields: Optional[str] = None,
):
    """
    Approve a submission with optional fields.

    Usage:
        /approve 552500
        /approve 552500 centrality:a pov:character naming:explicit
        /approve battlenet:diablo-4 centrality:a
    """
    await interaction.response.defer()

    # Parse identifier
    steam_id = None
    battlenet_id = None
    name = None

    if identifier.startswith("battlenet:"):
        battlenet_id = identifier.split(":", 1)[1]
    elif identifier.isdigit():
        steam_id = int(identifier)
    else:
        name = identifier

    # Try to find a recent submission in channel
    entry = None
    channel = interaction.channel

    async for message in channel.history(limit=50):
        if message.embeds:
            embed = message.embeds[0]
            if embed.title and "submission" in embed.title.lower():
                parsed = parse_embed_submission(embed)

                # Check if this matches our identifier
                if steam_id and parsed.steam_id == steam_id:
                    entry = parsed
                    break
                elif battlenet_id and parsed.battlenet_id == battlenet_id:
                    entry = parsed
                    break
                elif name and parsed.name and name.lower() in parsed.name.lower():
                    entry = parsed
                    break

    if not entry:
        # Create a minimal entry from the identifier
        entry = GameEntry(
            name=name or f"Game {identifier}",
            steam_id=steam_id,
            battlenet_id=battlenet_id,
        )

    # Apply fields
    if fields:
        override_dict = parse_overrides(fields)
        for key, value in override_dict.items():
            setattr(entry, key, value)

    # Validate
    errors = entry.validate()
    if errors:
        await interaction.followup.send(
            f"**Cannot approve - missing required fields:**\n"
            f"- {chr(10).join(errors)}\n\n"
            f"Add the missing fields as fields."
        )
        return

    # Check for existing game
    data = load_games_yaml()
    existing, idx = find_existing_game(
        data["games"],
        steam_id=entry.steam_id,
        battlenet_id=entry.battlenet_id,
        name=entry.name,
    )

    if existing:
        # Ask for confirmation
        await interaction.followup.send(
            f"**Game already exists:** {existing.get('name')}\n"
            f"Use `/edit {identifier} [fields]` to modify, or reply with 'overwrite' to replace entirely."
        )
        return

    # Add to YAML
    data["games"].append(entry.to_dict())
    save_games_yaml(data)

    # Run deploy
    await interaction.followup.send(f"Adding **{entry.name}** and deploying...")

    success, output = run_deploy()

    if success:
        await interaction.followup.send(f"✅ **Added and deployed:** {entry.name}")
    else:
        await interaction.followup.send(f"⚠️ **Added but deploy failed:**\n```{output[:1500]}```")


@bot.tree.command(name="edit", description="Edit an existing game entry")
@app_commands.describe(
    identifier="Steam ID, battlenet:slug, or game name",
    changes="Fields to change (e.g., centrality:b notes:Updated notes)",
)
async def edit_command(
    interaction: discord.Interaction,
    identifier: str,
    changes: str,
):
    """
    Edit an existing game entry.

    Usage:
        /edit 552500 centrality:a
        /edit battlenet:diablo-4 notes:New notes here
        /edit "Game Name" priority:medium
    """
    await interaction.response.defer()

    # Parse identifier
    steam_id = None
    battlenet_id = None
    name = None

    if identifier.startswith("battlenet:"):
        battlenet_id = identifier.split(":", 1)[1]
    elif identifier.isdigit():
        steam_id = int(identifier)
    else:
        name = identifier

    # Find existing game
    data = load_games_yaml()
    existing, idx = find_existing_game(
        data["games"],
        steam_id=steam_id,
        battlenet_id=battlenet_id,
        name=name,
    )

    if not existing or idx is None:
        await interaction.followup.send(f"**Game not found:** {identifier}")
        return

    # Parse and apply changes
    change_dict = parse_overrides(changes)

    for key, value in change_dict.items():
        if key in ["dimension_1", "dimension_2", "dimension_3"]:
            if "classification" not in existing:
                existing["classification"] = {}
            existing["classification"][key] = value
        else:
            existing[key] = value

    # Update in list
    data["games"][idx] = existing
    save_games_yaml(data)

    # Run deploy
    await interaction.followup.send(f"Updating **{existing.get('name')}** and deploying...")

    success, output = run_deploy()

    if success:
        await interaction.followup.send(f"✅ **Updated and deployed:** {existing.get('name')}")
    else:
        await interaction.followup.send(f"⚠️ **Updated but deploy failed:**\n```{output[:1500]}```")


@bot.tree.command(name="check", description="Check if a game exists in the database")
@app_commands.describe(identifier="Steam ID, battlenet:slug, or game name")
async def check_command(interaction: discord.Interaction, identifier: str):
    """Check if a game exists and show its current data."""
    # Parse identifier
    steam_id = None
    battlenet_id = None
    name = None

    if identifier.startswith("battlenet:"):
        battlenet_id = identifier.split(":", 1)[1]
    elif identifier.isdigit():
        steam_id = int(identifier)
    else:
        name = identifier

    data = load_games_yaml()
    existing, _ = find_existing_game(
        data["games"],
        steam_id=steam_id,
        battlenet_id=battlenet_id,
        name=name,
    )

    if existing:
        classification = existing.get("classification", {})
        await interaction.response.send_message(
            f"**Found:** {existing.get('name')}\n"
            f"```yaml\n"
            f"steam_id: {existing.get('steam_id', 'N/A')}\n"
            f"battlenet_id: {existing.get('battlenet_id', 'N/A')}\n"
            f"classification:\n"
            f"  centrality: {classification.get('dimension_1', 'N/A')}\n"
            f"  pov: {classification.get('dimension_2', 'N/A')}\n"
            f"  naming: {classification.get('dimension_3', 'N/A')}\n"
            f"notes: {existing.get('notes', 'N/A')}\n"
            f"date_added: {existing.get('date_added', 'N/A')}\n"
            f"```"
        )
    else:
        await interaction.response.send_message(f"**Not found:** {identifier}")


def main():
    """Main entry point."""
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not set in .env file")
        print("Create a bot at https://discord.com/developers/applications")
        print("Add DISCORD_BOT_TOKEN=your_token_here to your .env file")
        sys.exit(1)

    print("Starting Necro Game News Discord Bot...")
    print(f"YAML file: {GAMES_YAML_PATH}")
    print(f"Deploy script: {DEPLOY_SCRIPT}")

    if DISCORD_CHANNEL_ID:
        print(f"Monitoring channel: {DISCORD_CHANNEL_ID}")
    else:
        print("Monitoring all channels (set DISCORD_CHANNEL_ID to restrict)")

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()