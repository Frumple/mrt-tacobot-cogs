![Minecart Rapid Transit Logo](https://github.com/Frumple/mrt-docker-services/assets/68396/32a557d8-f5ad-44ae-9d71-da1ad7d31a55)

# MRT TacoBot Cogs

Custom [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs for use in **"TacoBot"** on the [Minecart Rapid Transit](https://www.minecartrapidtransit.net) Discord server.

**Please note that these cogs are provided as-is, with no further support provided.**

# Installation

With your Red-DiscordBot installed on your Discord server, run the following command where `[p]` is your bot's prefix:
```
[p]repo add mrt-tacobot-cogs https://github.com/Frumple/mrt-tacobot-cogs
```

After agreeing to add a 3rd-party repository, install one of the cogs below with:
```
[p]cog install mrt-tacobot-cogs <name of cog>
```

# Cogs

| Name                  | Description                                                             |
|-----------------------|-------------------------------------------------------------------------|
| [Dynmap](#dynmap)     | Runs Dynmap radius renders on a Minecraft server hosted on Pterodactyl. |
| [Password](#password) | Buttons that provide access passwords to external services.             |
| [Proposal](#proposal) | Manages a forum channel for user-submitted proposals and staff voting.  |

# Dynmap

This cog allows users to run [Dynmap](https://github.com/webbukkit/dynmap) radius renders on a Minecraft server hosted on [Pterodactyl](https://pterodactyl.io/).

## Setup

In Pterodactyl, you will need a user with **console permissions** to the Minecraft server you want renders on. In this user's settings, go to **API Credentials** and create a new **API Key** (leave allowed IPs blank). Copy down this key.

You will also need the **Pterodactyl Host URL** (The URL when you log into the Pterodactyl panel up to the first slash), and the **Pterodactyl Server UUID** (seen under "Servers" in the admin panel).

In the Dynmap cog, set up your Pterodactyl credentials with the following commands:
```
[p]dynmap_config pterodactyl_key <PUT API KEY HERE>
[p]dynmap_config pterodactyl_host <PUT HOST URL HERE>
[p]dynmap_config pterodactyl_id <PUT SERVER UUID HERE>
```
You will also need to provide the **Dynmap Host URL** (i.e. `https://dynmap.server.com` or `https://server.com:8123`) so that users can click the embed link directly to their render location on Dynmap:
```
[p]dynmap_config web_host <PUT DYNMAP URL HERE>
```

## Configuration

### Settings

You may also configure the following settings to your preference, by running `[p]dynmap_config`:

| Setting               | Description                                                                                                            | Default Value |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|---------------|
| `render_world`               | Sets the Minecraft world to render.                                                                                    | `new`         |
| `render_dimension`           | Sets the Minecraft dimension to render. This is usually the same as the world, except if the dimension is 'overworld'. | `overworld`   |
| `render_default_radius`      | Sets the default render radius (when radius is not specified in the render command).                                   | `300`         |
| `render_queue_size`          | Sets the maximum number of renders that can be queued, including the currently running render.                         | `3`           |
| `web_map`                 | Sets the Dynmap map name used in the embed link.                                                                       | `flat`        |
| `web_zoom`                | Sets the Dynmap zoom level used in the embed link.                                                                     | `6`           |
| `web_y`                   | Sets the Dynmap map name used in the embed link.                                                                       | `64`          |
| `queued_render_start_delay` | Sets the number of seconds for a queued render to wait after the current render has finished.                          | `3`           |
| `elapsed_interval`             | While a render is in progress, update the elapsed time every X seconds.                                                | `5`           |
| `cancel_interval`              | While a render is in progress, check if a cancellation has been requested every X seconds.                             | `1`           |
| `auth_timeout`                | Sets the maximum number of seconds to wait for a successful response after sending a websocket authentication request. | `10`          |
| `command_timeout`             | Sets the maximum number of seconds to wait for a console response after starting or cancelling a Dynmap render.        | `10`          |
| `render_timeout`              | Sets the maximum number of seconds to wait for a console message indicating that a Dynmap render has finished.         | `600`         |

### Slash Commands

Enable the slash commands `/dynmap render` and `/dynmap player`:

1. Run `[p]slash enable dynmap`
2. Run `[p]slash sync`
3. Go to **Server Settings** => **Integrations** => **\<your bot name\>** and configure permissions.

The commands under `/dynmap_config` can also be enabled as slash commands, but can be left disabled since they are only used by administrators.

### Constants

Due to a limitation in Discord.py, some settings are stored as constants directly in the `dynmap.py` file so that they can be used as parameter limits in the slash commands.

After updating these constants, you will need to restart the bot and run `[p]slash sync` again.

| Constant               | Description                                                                                                            | Default Value |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|---------------|
| `MIN_RADIUS`          | Sets the minimum render radius.                                                                                        | `100`         |
| `MAX_RADIUS`          | Sets the maximum render radius.                                                                                        | `300`         |
| `MAX_DIMENSION`       | Sets the maximum X and Z coordinate that can be specified for the center of the radius render.                         | `30000`       |


## Usage

### Starting renders

Start a dynmap radius render with the specified X and Z coordinates, using the default radius:
```
[p]dynmap render <X> <Z>
```

Start a dynmap radius render with the specified X and Z coordinates, and specified radius:
```
[p]dynmap render <X> <Z> <radius>
```

Start a dynmap radius render centred on a player currently on the Minecraft server, using the default radius:
```
[p]dynmap player <player_name>
```

Start a dynmap radius render centred on a player currently on the Minecraft server, using a specified radius:
```
[p]dynmap player <player_name> <radius>
```

### Queueing renders

If a render is started by the bot while another render is already running, the following will happen:
- If the currently running render was started by the bot, the new render will queue until the renders ahead of it are completed or cancelled. If the queue is full, the render will immediately fail.
- If the currently running render was started in-game using the `/dynmap` command, the new render will immediately fail. You will need to wait until the running render is complete before starting the new render.

### Cancelling renders

A render that is running or queued can be cancelled by reacting to the bot's message with the "stop button" emoji ( :stop_button: ). Only the user who initiated the render, or a staff member with Red-DiscordBot mod permissions or above may cancel the render.

# Password

This cog creates buttons that users can click on to obtain access passwords for external services.

On the MRT Server, this cog is used to control access to our Mumble, OpenTTD, and file server, as well as the creation of new accounts on our wiki.

## Setup

### Mandatory Settings

Create a new, empty, read-only Discord channel where your "password buttons" will reside.

Register this channel in the cog:
```
[p]password_config set_message_channel <channel_id>
```

Set the text of the message that will contain the buttons (can include Markdown formatting):
```
[p]password_config set_message_text <message_text>
```

### Optional Settings

You may specify a separate channel where a log message will be sent each time a user clicks one of the buttons:
```
[p]password_config set_log_channel <channel_id>
```

To stop sending log messages, run:
```
[p]password_config set_log_channel
```

You may also specify how many seconds a response message (containing the password) should persist after a button is pressed:
```
[p]password_config set_response_lifespan <number_of_seconds>
```

This lifespan can be disabled with:
```
[p]password_config set_response_lifespan
```

### Services and Passwords

Add a new service:
```
[p]password_config add_service <service_name>
```

Remove an existing service:
```
[p]password_config remove_service <service_name>
```

Set the button text for a service:
```
[p]password_config set_button_text <service_name> <button_text>
```

Set the description for a service (can include Markdown formatting):
```
[p]password_config set_description <service_name> <description>
```

Set the password for a service:
```
[p]password_config set_password <service_name> <password>
```

### Example
```
[p]password_config set_message_channel 999999999
[p]password_config set_message_text **Click these buttons to obtain passwords:**
[p]password_config set_log_channel 888888888

[p]password_config add_service sample
[p]password_config set_button_text sample Sample
[p]password_config set_description sample **Sample Password**
[p]password_config set_password sample ThisIsAPassword
```

Given the above example, when the "Sample" button is pressed, the following ephemeral message will be sent to the user and will only be visible to the user:

> **Sample Password**: `ThisIsAPassword`

### Updating / Restarting the cog

Whenever the bot or cog is updated/restarted, you will need to run the following command to refresh the password buttons:
```
[p]password_config update
```

# Proposal

This cog manages a Discord forum channel intended for user-submitted proposals and staff voting.

Users submit proposals by creating a new post in the designated forum channel. Staff members (Discord moderators or above) will then vote on these proposals by adding these specific reactions to the first message in the post:

| Vote    | Emoji              | Description |
| ------- | ------------------ | ----------- |
| Approve | :white_check_mark: | Approve the proposal.                                       |
| Reject  | :x:                | Reject the proposal.                                        |
| Extend  | :hourglass:        | Extend the voting period of the proposal.                   |
| Defer   | :calendar:         | Defer the proposal to the next General Staff Meeting (GSM). |

When a proposal has received the minimum number of votes for quorum, an administrator will review the proposal and make a final decision based on the votes tallied.

If a proposal has not reached quorum by the end of the standard voting period (default: 7 days since proposal creation), the proposal will automatically be :hourglass: **extended**.

If an extended proposal reaches the end of its extended voting period (default: 14 days since proposal creation), the proposal will automatically be :calendar: **deferred to the next GSM**.

This cog will make announcements in the proposal post whenever the following events occur:
- The proposal is first created
- A staff member has voted or rescinded a vote
- The proposal has reached or lost quorum
- An administrator has run a command to approve, reject, extend, or defer a proposal
- The proposal has reached the end of the initial voting period and is automatically extended
- The proposal has reached the end of the extended voting period and is automatically deferred

The bot will also ensure that only staff can add reactions to the first message of a proposal post. The bot will remove any reactions made by non-staff, and it will also DM the user reminding them not to add reactions there.

## Setup

Set the forum channel where proposals will be made:
```
[p]proposal_config channel <channel_id>
```

Set the quorum (minimum number of votes for approval, rejection, etc.):
```
[p]proposal_config quorum <number_of_votes>
```

Set tags for approved, rejected, extended, and deferred proposal states. You may need to get the tag IDs first with `[p] proposal_config list_tags`:
```
[p]proposal_config approved_tag <tag_id>
[p]proposal_config rejected_tag <tag_id>
[p]proposal_config extended_tag <tag_id>
[p]proposal_config deferred_tag <tag_id>
```

Set the minimum, standard, and extended voting periods (defaults: minimum = 2 days, standard = 7 days, extended = 14 days, all after the creation date of the proposal)
```
[p]proposal_config minimum_voting_days <number_of_days>
[p]proposal_config standard_voting_days <number_of_days>
[p]proposal_config extended_voting_days <number_of_days>
```

## Usage

Administrators can run the following commands in a proposal post to approve, reject, extend, or defer it:
```
[p]proposal approve
[p]proposal reject
[p]proposal extend
[p]proposal defer
```

These commands will perform the following tasks on the proposal post:
- Add the appropriate approved/rejected/extended/deferred tag to the post.
- Make an announcement in the post and list all votes made at the time the command was run (except for `[p]proposal extend`).
- Close and lock the post (except for `[p]proposal extend`).

# License

These cogs are licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
