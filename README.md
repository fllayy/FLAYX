<div align="center">
<h1 align="center">
<img src="https://cdn.discordapp.com/attachments/1146153316787699712/1154103449093414942/JDBJcDH.png" width="100" />
<br>FLAYX
</h1>
<h3>◦ Flayx: Empowering seamless collaboration and code excellence</h3>
<h3>◦ Developed with the software and tools listed below.</h3>

<p align="center">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style&logo=Python&logoColor=white" alt="Python" />
</p>
<img src="https://img.shields.io/github/languages/top/fllayy/FLAYX?style&color=5D6D7E" alt="GitHub top language" />
<img src="https://img.shields.io/github/languages/code-size/fllayy/FLAYX?style&color=5D6D7E" alt="GitHub code size in bytes" />
<img src="https://img.shields.io/github/license/fllayy/FLAYX?style&color=5D6D7E" alt="GitHub license" />
</div>

---

## 📒 Table of Contents
- [📒 Table of Contents](#-table-of-contents)
- [📍 Overview](#-overview)
- [⚙️ Features](#-features)
- [📂 Project Structure](#project-structure)
- [🧩 Modules](#modules)
- [🚀 Getting Started](#-getting-started)
- [🗺 Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [👏 Acknowledgments](#-acknowledgments)

---


## 📍 Overview

The project at https://github.com/fllayy/FLAYX is a comprehensive music playback and interaction system for a Discord bot. It allows users to configure their bot with Discord token, Lavalink server details, and MySQL database credentials, enabling functionalities like music playback, data storage, and Discord bot interaction. The project includes features like a customizable help menu with dropdown options for navigating different command categories, a pagination menu for viewing multiple pages of content, voting mechanisms for music control, and a robust queue management system. Overall, the project aims to provide a user-friendly and feature-rich experience for managing music in Discord servers.

---

## ⚙️ Features

| Feature                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **⚙️ Architecture**     | The codebase follows a modular architecture, with separate files and directories for different functional components like music playback, database operations, pagination menu, help menu, etc. The codebase uses object-oriented programming principles and design patterns, such as inheritance and composition, to achieve separation of concerns and modularity.                                                |
| **🔗 Dependencies**    | The codebase relies on external libraries and systems like Discord API, Lavalink for music playback, MySQL for database storage, and various Python libraries like aiohttp, asyncio for asynchronous operations. These dependencies are crucial for the system's functionality and integration with other services.                            |
| **🧩 Modularity**      | The system demonstrates good modularity by organizing functionalities into separate files and folders with clear roles, such as music controls, database operations, pagination menu, help menu, etc. This modular design allows for easy extensibility, maintenance, and code reuse.                                                                                                         |
| **⚡️ Performance**      | The performance of the system can vary based on factors like the server's hardware resources, network connection, and data volume. However, the asynchronous nature of the codebase, the use of efficient algorithms, and the integration with external services like Lavalink help ensure efficient resource usage and minimal bottlenecks in music playback and data operations. |
| **🔐 Security**        | Security measures are expected to be implemented for protecting sensitive data like tokens, database credentials, and ensuring valid user access to the Discord bot and its functionalities. Safeguarding against SQL injection vulnerabilities is also crucial to maintain the system's security. Implementing authorization and updates to follow best practices can reinforce the security measures.      |
| **📶 Scalability**     | The system's scalability depends on factors like server capacity, network infrastructure, and efficient utilization of resources. The codebase follows mod


---

## 🧩 Modules

<details closed><summary>Root</summary>

| File                                                                   | Summary                                                                                                                                                                                                      |
| ---                                                                    | ---                                                                                                                                                                                                          |
| [.env Exemple](https://github.com/fllayy/FLAYX/blob/main/.env%20Exemple) | The code allows you to configure your Discord token, Lavalink server details, and MySQL database credentials to enable functionalities such as Discord bot interaction, music playback, and data storage.    |
| [main.py](https://github.com/fllayy/FLAYX/blob/main/main.py)           | Exception:                                                                                                                                                                                                   |
| [function.py](https://github.com/fllayy/FLAYX/blob/main/function.py)   | This code includes functionalities to connect to a MySQL database, check the connection, ping the database for response time, create database tables, and perform operations like finding and updating data. |

</details>

<details closed><summary>Views</summary>

| File                                                                         | Summary                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---                                                                          | ---                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| [paginator.py](https://github.com/fllayy/FLAYX/blob/main/views/paginator.py) | This code implements a pagination menu for a Discord bot. It allows users to navigate through multiple pages of content using "previous" and "next" buttons. The current page is displayed as an embedded message. The menu is customizable and can handle multiple pages of content.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| [help.py](https://github.com/fllayy/FLAYX/blob/main/views/help.py)           | This code defines a class `HelpDropdown` that extends `discord.ui.Select`, allowing users to select different categories of commands in a dropdown menu. The dropdown menu options include categories like "News" and "Tutorial", as well as dynamically generated options for each category of commands. The code also defines a class `HelpView` that extends `discord.ui.View`, which is used to display the dropdown menu and additional buttons for support and inviting a bot. The `HelpView` class handles user interactions with the dropdown and generates an embed message based on the selected category or button clicked. Overall, this code enables users to easily navigate and access different help categories and commands provided by a bot in a Discord server. The classes and functions in the code facilitate an interactive and user-friendly help menu. |
| [player.py](https://github.com/fllayy/FLAYX/blob/main/views/player.py)       | The code defines a MusicControlsView class in a Discord bot. It handles various functionalities for controlling music playback, including skipping, pausing/resuming, stopping, enabling/disabling autoplay, and shuffling the playlist. It also includes voting mechanisms for certain actions.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

</details>


<details closed><summary>Voicelink</summary>

| File                                                                       | Summary                                                                                                                                                                                                                                                                                                                   |
| ---                                                                        | ---                                                                                                                                                                                                                                                                                                                       |
| [player.py](https://github.com/fllayy/FLAYX/blob/main/voicelink/player.py) | This code creates a custom player class for a music bot in Discord. It includes functionalities such as playing tracks, managing queues, handling autoplay, storing playlist history, and controlling playback. The class also handles on-screen display of the current track and user interactions through a controller. |

</details>

<details closed><summary>Cogs</summary>

| File                                                                | Summary                                                                                                                                                                                                                  |
| ---                                                                 | ---                                                                                                                                                                                                                      |
| [music.py](https://github.com/fllayy/FLAYX/blob/main/cogs/music.py) | HTTPStatus Exception: 400                                                                                                                                                                                                |
| [admin.py](https://github.com/fllayy/FLAYX/blob/main/cogs/admin.py) | This code defines a Discord bot command extension that allows admins to change the volume and prefix of the bot. It checks if the user invoking the commands has admin permissions and updates the settings accordingly. |

</details>

---

## 🚀 Getting Started

### ✔️ Prerequisites

Before you begin, ensure that you have the following prerequisites installed:
> - `ℹ️ python 3.11`
> - `ℹ️ Lavalink 4.0 server`

### 📦 Installation

1. Clone the FLAYX repository:
```sh
git clone https://github.com/fllayy/FLAYX
```

2. Change to the project directory:
```sh
cd FLAYX
```

3. Install the dependencies:
```sh
pip install -r requirements.txt
```

### 🎮 Using FLAYX

```sh
python main.py
```


---


## 🗺 Roadmap

> - [ ] `ℹ️  Bot time server`
> - [ ] `ℹ️  Settings view command`
> - [ ] `ℹ️  Bot leave when alone`


---

## 🤝 Contributing

Contributions are always welcome! Please follow these steps:
1. Fork the project repository. This creates a copy of the project on your account that you can modify without affecting the original project.
2. Clone the forked repository to your local machine using a Git client like Git or GitHub Desktop.
3. Create a new branch with a descriptive name (e.g., `new-feature-branch` or `bugfix-issue-123`).
```sh
git checkout -b new-feature-branch
```
4. Make changes to the project's codebase.
5. Commit your changes to your local branch with a clear commit message that explains the changes you've made.
```sh
git commit -m 'Implemented new feature.'
```
6. Push your changes to your forked repository on GitHub using the following command
```sh
git push origin new-feature-branch
```
7. Create a new pull request to the original project repository. In the pull request, describe the changes you've made and why they're necessary.
The project maintainers will review your changes and provide feedback or merge them into the main branch.

---

## 📄 License

This project is licensed under the `ℹ️  GNU General Public License v3.0` License. See the [LICENSE](https://github.com/fllayy/FLAYX/blob/main/LICENSE) file for additional info.

---
