![Minecart Rapid Transit Logo](https://github.com/Frumple/mrt-docker-services/assets/68396/32a557d8-f5ad-44ae-9d71-da1ad7d31a55)

# MRT TacoBot Cogs

Custom [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs for use in **"TacoBot"** on the [Minecart Rapid Transit](https://www.minecartrapidtransit.net) Discord server.

**Please note that these cogs are provided as-is, with no further support provided.**

# Installation

With your Red-DiscordBot installed on your Discord server, run the following command where `[p]` is your bot's prefix:

`[p]repo add mrt-tacobot-cogs https://github.com/Frumple/mrt-tacobot-cogs`

After agreeing to add a 3rd-party repository, install one of the cogs below with:

`[p]cog install mrt-tacobot-cogs <name of cog>`

# Cogs

| Name                  | Description                                                             |
|-----------------------|-------------------------------------------------------------------------|
| [Dynmap](#dynmap)     | Runs Dynmap radius renders on a Minecraft server hosted on Pterodactyl. |
| [Password](#password) | Buttons that provide access passwords to external services.             |

# Dynmap

## Setup

This cog allows users to run [Dynmap](https://github.com/webbukkit/dynmap) radius renders on a Minecraft server hosted on [Pterodactyl](https://pterodactyl.io/).

In Pterodactyl, you will need a user with **console permissions** to the Minecraft server you want renders on. In this user's settings, go to **API Credentials** and create a new **API Key** (leave allowed IPs blank). Copy down this key.

You will also need the **Pterodactyl Host URL** (The URL when you log into the Pterodactyl panel up to the first slash), and the **Pterodactyl Server UUID** (seen under "Servers" in the admin panel).

In the Dynmap cog, set up your Pterodactyl credentials with the following commands:

`[p]dynmap_config pterodactyl_key <PUT API KEY HERE>`

`[p]dynmap_config pterodactyl_host <PUT HOST URL HERE>`

`[p]dynmap_config pterodactyl_id <PUT SERVER UUID HERE>`

You will also need to provide the **Dynmap Host URL** (i.e. `https://dynmap.server.com` or `https://server.com:8123`) so that users can click the embed link directly to their render location on Dynmap:

`[p]dynmap_config web_host <PUT DYNMAP URL HERE>`

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

`[p]dynmap render <X> <Z>`

Start a dynmap radius render with the specified X and Z coordinates, and specified radius:

`[p]dynmap render <X> <Z> <radius>`

Start a dynmap radius render centred on a player currently on the Minecraft server, using the default radius:

`[p]dynmap player <player_name>`

Start a dynmap radius render centred on a player currently on the Minecraft server, using a specified radius:

`[p]dynmap player <player_name> <radius>`

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

Create a new, empty, read-only Discord channel where your "password buttons" will reside.

Register this channel in the cog:

`[p]password_config set_message_channel <channel_id>`

Set the text of the message that will contain the buttons (can include Markdown formatting):

`[p]password_config set_message_text <message_text>`

Optionally, you may specify a separate channel where a log message will be sent each time a user clicks one of the buttons:

`[p]password_config set_log_channel <channel_id>`

To stop sending log messages, run:

`[p]password_config set_log_channel`

### Services and Passwords

Add a new service:

`[p]password_config add_service <service_name>`

Remove an existing service:

`[p]password_config remove_service <service_name>`

Set the button text for a service:

`[p]password_config set_button_text <service_name> <button_text>`

Set the description for a service (can include Markdown formatting):

`[p]password_config set_description <service_name> <description>`

Set the password for a service:

`[p]password_config set_password <service_name> <password>`

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

# License

These cogs are licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
