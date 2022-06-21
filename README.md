![Minecart Rapid Transit Logo](https://www.minecartrapidtransit.net/wp-content/uploads/2015/01/logo-with-title2.png)

# MRT TacoBot Cogs

Custom [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs for use in **"TacoBot"** on the [Minecart Rapid Transit](https://www.minecartrapidtransit.net) Discord server.

**Please note that these cogs are provided as-is, with no further support provided.**

# Installation

With your Red-DiscordBot installed on your Discord server, run the following command where `[p]` is your bot's prefix:

`[p]repo add mrt-tacobot-cogs https://github.com/Frumple/mrt-tacobot-cogs`

After agreeing to add a 3rd-party repository, install one of the cogs below with:

`[p]cog install mrt-tacobot-cogs <name of cog>`

# Cogs

| Name                  | Description                                                                            |
|-----------------------|----------------------------------------------------------------------------------------|
| [Dynmap](#dynmap)     | Allows users to run Dynmap radius renders on a Minecraft server hosted on Pterodactyl. |
| [Password](#password) | Allows users to obtain access passwords for external services.                         |

# Dynmap

## Setup

Allows users to run [Dynmap](https://github.com/webbukkit/dynmap) radius renders on a Minecraft server hosted on [Pterodactyl](https://pterodactyl.io/).

In Pterodactyl, you will need a user with **console permissions** to the Minecraft server you want renders on. In this user's settings, go to **API Credentials** and create a new **API Key** (leave allowed IPs blank). Copy down this key.

You will also need the **Pterodactyl Host URL** (The URL when you log into the Pterodactyl panel up to the first slash), and the **Pterodactyl Server UUID** (seen under "Servers" in the admin panel).

In the Dynmap cog, set up your Pterodactyl credentials with the following commands:

`[p]dynmap config pterodactyl key <PUT API KEY HERE>`

`[p]dynmap config pterodactyl host <PUT HOST URL HERE>`

`[p]dynmap config pterodactyl id <PUT SERVER UUID HERE>`

You will also need to provide the **Dynmap Host URL** (i.e. `https://dynmap.server.com` or `https://server.com:8123`) so that users can click the embed link directly to their render location on Dynmap:

`[p]dynmap config web host <PUT DYNMAP URL HERE>`

## Configuration

You may also configure the following settings to your preference, by running `[p]dynmap config`:

| Submenu    | Setting               | Description                                                                                                            | Default Value |
|------------|-----------------------|------------------------------------------------------------------------------------------------------------------------|---------------|
| `render`   | `world`               | Sets the Minecraft world to render.                                                                                    | `new`         |
| `render`   | `default_radius`      | Sets the default render radius (when radius is not specified in the render command).                                   | `300`         |
| `render`   | `min_radius`          | Sets the minimum render radius.                                                                                        | `100`         |
| `render`   | `max_radius`          | Sets the maximum render radius.                                                                                        | `300`         |
| `render`   | `max_dimension`       | Sets the maximum X and Z coordinate that can be specified for the center of the radius render.                         | `30000`       |
| `render`   | `queue_size`          | Sets the maximum number of renders that can be queued, including the currently running render.                         | `3`           |
| `web`      | `map`                 | Sets the Dynmap map name used in the embed link.                                                                       | `flat`        |
| `web`      | `zoom`                | Sets the Dynmap zoom level used in the embed link.                                                                     | `6`           |
| `web`      | `y`                   | Sets the Dynmap map name used in the embed link.                                                                       | `64`          |
| `delay`    | `queued_render_start` | Sets the number of seconds for a queued render to wait after the current render has finished.                          | `3`           |
| `interval` | `elapsed`             | While a render is in progress, update the elapsed time every X seconds.                                                | `5`           |
| `interval` | `cancel`              | While a render is in progress, check if a cancellation has been requested every X seconds.                             | `1`           |
| `timeout`  | `auth`                | Sets the maximum number of seconds to wait for a successful response after sending a websocket authentication request. | `10`          |
| `timeout`  | `command`             | Sets the maximum number of seconds to wait for a console response after starting or cancelling a Dynmap render.        | `10`          |
| `timeout`  | `render`              | Sets the maximum number of seconds to wait for a console message indicating that a Dynmap render has finished.         | `600`         |

## Usage

### Starting renders

Start a dynmap radius render with the specified X and Z coordinates, using the default radius:

`[p]dynmap render <X> <Z>`

Start a dynmap radius render with the specified X and Z coordinates, and specified radius:

`[p]dynmap render <X> <Z> <radius>`

### Queueing renders

If a render is started while another render is already running, the render will queue until the renders ahead of it are completed or cancelled. If the queue is full, the render will immediately fail.

### Cancelling renders

A render that is running or queued can be cancelled by reacting to the bot's message with the "stop button" emoji ( &#23F9; ). Only the user who initiated the render, or a staff member with Red-DiscordBot mod permissions or above may cancel the render.

# Password

Allows users to obtain access passwords for external services.

On the MRT Server, this cog is used to control access to our Mumble, OpenTTD, and file server, as well as the creation of new accounts on our wiki.

## Setup

Set your passwords with:

`[p]password set <name> <value>`

where `<name>` is the name of the service and `<value>` is the text you want to DM to the user when they request it. This text should contain the password and a description of what the password is.

Passwords can be cleared with:

`[p]password clear <name>`

### Example Password

`` [p]password set openttd **OpenTTD Password:** `ThisIsAPassword` ``

## Usage

Users get passwords with:

`[p]password get <name>`

The text containing the password is DMed to the user. If the user does not have DMs allowed, an error message will indicate this.

# License

These cogs are licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
