import os
import discord
from discord.ext import commands

# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "$"

# ============================================================
# ROLE IDS
# ============================================================

# Role automatically given to new members
AUTOROLE_ID = 1461242044306685973

# Role required to use $roleall
OWNER_ROLE_ID = 1463291530268643503

# ============================================================
# BOT SETUP
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents
)

# ============================================================
# OWNER ROLE CHECK
# ============================================================

def is_owner_role():
    async def predicate(ctx):

        if ctx.guild is None:
            return False

        return any(
            role.id == OWNER_ROLE_ID
            for role in ctx.author.roles
        )

    return commands.check(predicate)

# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("===================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Autorole ID: {AUTOROLE_ID}")
    print(f"Owner Role ID: {OWNER_ROLE_ID}")
    print("===================================")

# ============================================================
# AUTOROLE
# ============================================================

@bot.event
async def on_member_join(member):

    role = member.guild.get_role(AUTOROLE_ID)

    if role is None:
        print(
            f"[AUTOROLE] Role {AUTOROLE_ID} "
            f"was not found in {member.guild.name}"
        )
        return

    if role == member.guild.default_role:
        return

    if role.managed:
        return

    if role >= member.guild.me.top_role:
        print(
            f"[AUTOROLE] Cannot give {role.name} "
            f"because it is too high."
        )
        return

    try:

        await member.add_roles(
            role,
            reason="Automatic autorole"
        )

        print(
            f"[AUTOROLE] Gave {role.name} "
            f"to {member}"
        )

    except discord.Forbidden:

        print(
            f"[AUTOROLE] Missing permission "
            f"in {member.guild.name}"
        )

    except discord.HTTPException as error:

        print(
            f"[AUTOROLE] Discord error: {error}"
        )

# ============================================================
# FIND ROLE BY ID OR NAME
# ============================================================

def find_role(guild, role_input):

    role_input = role_input.strip()

    # Try role ID first
    if role_input.isdigit():

        role = guild.get_role(
            int(role_input)
        )

        if role is not None:
            return role

    # Try exact role name
    role = discord.utils.find(
        lambda r: r.name.lower() == role_input.lower(),
        guild.roles
    )

    return role

# ============================================================
# $ROLEALL
# ACCEPTS ROLE ID OR ROLE NAME
# ============================================================

@bot.command(name="roleall")
@is_owner_role()
async def roleall(
    ctx,
    *,
    role_input: str
):

    role = find_role(
        ctx.guild,
        role_input
    )

    if role is None:

        return await ctx.send(
            f"❌ I couldn't find the role `{role_input}`."
        )

    if role == ctx.guild.default_role:

        return await ctx.send(
            "❌ You cannot give the @everyone role."
        )

    if role.managed:

        return await ctx.send(
            "❌ You cannot manually assign a managed role."
        )

    if role >= ctx.guild.me.top_role:

        return await ctx.send(
            "❌ I cannot give that role because it is "
            "equal to or higher than my highest role."
        )

    await ctx.send(
        f"⏳ Giving {role.mention} to all members..."
    )

    added = 0
    skipped = 0

    for member in ctx.guild.members:

        # Skip bots
        if member.bot:
            skipped += 1
            continue

        # Already has role
        if role in member.roles:
            skipped += 1
            continue

        try:

            await member.add_roles(
                role,
                reason=f"$roleall used by {ctx.author}"
            )

            added += 1

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            skipped += 1

    await ctx.send(
        f"✅ **Roleall finished!**\n\n"
        f"👤 Added: **{added}**\n"
        f"⏭️ Skipped: **{skipped}**"
    )

# ============================================================
# ROLEALL ERROR
# ============================================================

@roleall.error
async def roleall_error(ctx, error):

    if isinstance(
        error,
        commands.CheckFailure
    ):

        return await ctx.send(
            "❌ You don't have permission to use this command."
        )

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$roleall Role Name` or `$roleall ROLE_ID`"
        )

# ============================================================
# GENERAL ERROR
# ============================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    # Ignore errors already handled above
    if isinstance(
        error,
        commands.CheckFailure
    ):
        return

    print(
        f"[ERROR] {type(error).__name__}: {error}"
    )

# ============================================================
# TOKEN CHECK
# ============================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is not set."
    )

# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
